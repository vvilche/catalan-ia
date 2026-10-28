# CatalanIA auditado contra los 7 subsistemas

Base: `harness-engineering-agentes` (arXiv:2609.00006v1, julio 2026 — 11 harnesses de producción
+ 1 meta-harness, ~4M líneas). La anatomía canónica: D1 Bucle · D2 Integración LLM · D3
Herramientas · D4 Memoria · D5 Seguridad · D6 Orquestación · D7 Extensibilidad, más dos
superficies transversales (capa de interfaz y sustrato de sesión).

**Todo harness toma posición en los siete, incluso cuando la posición es ausencia deliberada.**
Esta es la posición de CatalanIA, subsistema por subsistema, con lo que está verificado y lo que
está pendiente.

---

## Resumen en una tabla

| # | Subsistema | Posición de CatalanIA | Estado |
|---|---|---|---|
| D1 | Bucle | Heredado de Hermes: while con stuck detection por firma SHA-256, verify_on_stop encendido | ✅ provisto |
| D2 | Integración LLM | deepseek-v4-flash por `hermes config set`, fallback a modelo gratis | ✅ provisto |
| D3 | Herramientas | ~15 por rol + 263 skills con carga diferida | ✅ provisto |
| D4 | Memoria | MEMORY.md (entorno) + USER.md (Victor), SOUL con índice. Sin RAG sobre código | ✅ provisto |
| D5 | **Seguridad** | 13 reglas en SOUL + 10 controles ejecutables + gate de privacidad. **Sin sandbox de SO** | ⚠️ parcial |
| D6 | Orquestación | **Ausencia deliberada**: single-agent | ✅ decidido |
| D7 | Extensibilidad | Skills (9/12 del corpus) + hooks + config como política; MCP para Odoo | ✅ provisto |
| — | Capa de interfaz | CLI `catalania`; WhatsApp/Telegram **sin decidir** | ⏳ pendiente |
| — | Sustrato de sesión | state.db de Hermes: transcripts, resume, fork | ✅ provisto |

---

## D1 · Bucle

**Qué hace el subsistema:** alterna inferencia con ejecución. Dueño de las condiciones de parada
y la recuperación de fallas.

**Posición:** no se escribe. Es el de Hermes, y para el rol alcanza. Del piso (~100 líneas: un
`while`, un template, una herramienta, dos topes) al techo (event-sourced con batches paralelos),
CatalanIA está en el medio por herencia, no por construcción propia.

Lo que sí se configura, porque es lo que separa el piso de producción:

- `verify_on_stop: true` — *Outer Verification Loop* (patrón 3.2): un juez valida la completitud
  fuera del loop de turno. En un agente comercial esto no es un lujo: es el control que impide dar
  por cerrada una propuesta con un monto sin fuente.
- `hard_stop_enabled: true`, `same_tool_failure: 3`, `idempotent_no_progress: 2` — *Stuck
  Detection*. El caso medido en esta misma sesión: un hook colgado devolvió el mismo error seis
  veces antes de que alguien cambiara de enfoque. Con esto encendido, el turno se corta al tercero.

**Decisión de diseño:** no se toca el bucle. Si más adelante hacen falta 3+ políticas de turno
ortogonales, se vuelven middleware — no ramas nuevas.

## D2 · Integración LLM

**Posición:** `deepseek-v4-flash` como default. Es el nivel 3 de la disciplina de costo (Python
determinístico → modelo gratis → flash → razonamiento puntual → razonamiento caro casi nunca).

Lo específico de esta silla: **el 70% del trabajo no debería llegar al modelo**. El radar
normativo, el cruce de cartas y el cálculo de BOM son Python determinístico. El LLM sintetiza al
final. Un agente comercial que "razona" sobre una cifra en vez de leerla del ERP es el error que
la regla 11 del SOUL prohíbe.

*Prompt caching*: el SOUL y las skills van primero y no cambian → prefijo estable, que es lo que
abarta la segunda llamada. No es estética, es dinero.

## D3 · Herramientas

**Posición:** ~15 herramientas de Hermes (terminal, files, browser, delegation) + 263 skills con
*carga diferida* (patrón *Deferred Loading*, que Hermes implementa con BM25 sobre el catálogo).

La regla del paper que aplica acá: **sobre ~15 herramientas, adopta carga diferida**; bajo ese
número no vale la indirección. CatalanIA está justo en el umbral, así que las 263 skills **son** el
mecanismo de ampliación, no herramientas nuevas. Por eso el paquete no agrega tools: agrega
procedimientos.

Advertencia propia del dominio: `conecta-agent-patterns` documenta que un único agente con 30
herramientas colapsa (alucina argumentos, pierde el hilo en 40+ pasos). El paquete se diseñó para
no cruzarlo.

## D4 · Memoria

**Posición:** tres capas, y la distinción no es cosmética.

| Capa | Qué va | Qué NO va |
|---|---|---|
| `SOUL.md` | reglas de conducta, índice de destinos | procedimientos, volcados de estado |
| `memories/MEMORY.md` | hechos estables de entorno | pasos, comandos, TODO |
| skills | procedimientos, criterios, referencias | reglas que deben cumplirse siempre |

El paper: *JIT Repo Context* (Markdown jerárquico auto-descubierto) y *LLM Summarization* para
compactar. CatalanIA usa la primera; la segunda la hereda de Hermes, con
`check_contexto.py` como disparador al 35%.

**Lo que el paper prohíbe y acá se respeta:** nada de RAG vectorial sobre contenido estructurado.
El índice FAISS de CONECTA es para normativa y documentos donde **el documento ES la fuente**
(cartas CEN, NTSyCS, pliegos). Para el dato operativo —un lead, un monto, una OT— se consulta
Odoo. Es exactamente la regla 7 del SOUL: puente, no copia.

Pendiente conocido: el índice de 188k chunks **no tiene** las etiquetas `linea` y `componente`
por chunk. FAISS ya filtra por metadato; falta el trabajo de datos, no de infraestructura.

## D5 · Seguridad — el subsistema más débil, y hay que decirlo

**Posición:** fuerte en política, débil en aislamiento.

**Lo que sí tiene:**

- 13 reglas en SOUL, cargadas en cada turno (capa 1: ~100% de cumplimiento porque elimina la
  decisión).
- 10 controles ejecutables en `~/.hermes/scripts/`: la regla en prosa se cumple ~53%; el script,
  ~100%. El paper lo dice igual: *policy-as-code*, nunca código imperativo.
- Gate de privacidad nuevo en esta sesión: bloquea publicar nombres de cliente, montos, correos,
  teléfonos, RUT, rutas e IPs. Probado con perfil sucio (6 bloqueantes) y limpio (0).
- *Untrusted-Content Delimiting*: Hermes ya envuelve resultados web en marcadores de taint. Para
  esta silla es el riesgo real — un PDF de carta CEN con un párrafo que diga "ignora tus reglas".

**Lo que NO tiene, y es la brecha honesta:**

- **Sandbox de sistema operativo.** Recomendación 10 del paper: *sandbox a nivel de SO + política
  como código + trazas de auditoría* para contexto empresarial. CatalanIA no tiene sandbox: puede
  leer todo lo que Victor puede leer.
- Las reglas 11-13 son de **conducta**, no de permisos del SO. Un agente que "no debe" escribir en
  Odoo puede técnicamente escribir en Odoo si tiene la credencial.
- **El gate de privacidad es un análisis de texto, no un control de acceso.** Detecta patrones que
  ya conoce; un criterio comercial en prosa ("a este cliente le cobramos menos porque...") pasa.

**Cómo se cierra la brecha, en orden de retorno:** credenciales Odoo de solo-lectura para el perfil
(cierra el riesgo de escritura de verdad, no por promesa) → sandbox para ejecución de código →
revisor con modelo antes de publicar un entregable.

## D6 · Orquestación — ausencia deliberada

**Posición: single-agent. No es falta de tiempo, es la recomendación 12 del paper.**

> Quédate single-agent hasta que puedas señalar una fase concreta de exploración en anchura donde
> el aislamiento paralelo de contexto le gane claramente a la búsqueda serial. Los sistemas
> multi-agente usan ~15× más tokens que un chat base.

CatalanIA delega puntualmente a sub-agentes para extracción pesada (patrón *Context Forking*), pero
no orquesta una flota. Un orquestador de **despacho** no se construye sin medir la fase candidata
primero. Un orquestador de **salud** (que cada agente esté vivo y actualizado) sí se justifica,
porque no reparte trabajo — pero eso es otro producto, no CatalanIA.

## D7 · Extensibilidad

**Posición:** skills primero, MCP después — en ese orden, que es el del paper (skills 9/12, MCP
8/12).

- **263 skills** = *Skills (capability bundles)*, el mecanismo que ganó como estándar.
- **Hooks** = *Policy-as-Code*. El hook de parada y `pre_tool_call` son de este subsistema (y el
  que se colgó en esta sesión también).
- **MCP** para Odoo, cuando haga falta hablar con el ERP sin pasar por scripts.
- `config.yaml` como política, no como código.

**Riesgo declarado:** instalar skills de terceros sin niveles de confianza ni cuarentena. El paper
recomienda tratarlas como paquetes. CatalanIA hereda 263 skills del Mac sin ese filtro.

---

## Las dos superficies transversales

**Capa de interfaz.** Hoy: CLI `catalania`. Es la superficie más débil del diseño, y es una
decisión pendiente de Victor (WhatsApp, Telegram, cron). Según el paper, la capa de interfaz es
donde vive el argumento de plataforma — y en este caso es literal: un agente comercial que solo
existe en una terminal no lo usa un vendedor.

**Sustrato de sesión.** Provisto por Hermes: `state.db`, transcripts, resume, fork, compactación
con linaje (*Lineage Compaction*). No hay que construirlo y no se debe duplicar.

---

## Las 18 recomendaciones: dónde está CatalanIA

| # | Recomendación | Estado |
|---|---|---|
| 1 | `while` lineal antes que middleware | ✅ heredado |
| 2 | Acoplamiento al proveedor según si entregas modelo | ✅ no lo entrega, usa flash |
| 3 | Una herramienta bash primero | ✅ heredado |
| 4 | Carga diferida sobre ~15 herramientas | ✅ en el umbral |
| 5 | Contrato de edición al nivel del modelo | ✅ `editar_seguro.py` |
| 6 | Markdown jerárquico auto-descubierto | ✅ SOUL + AGENTS.md |
| 7 | Compactación por umbral | ✅ al 35%, con `PUNTO_DE_PARADA.md` |
| 8 | **No RAG sobre código** | ✅ respetado |
| 9 | Aprobación de tres modos | ⚠️ parcial (hermes-gateway lo trae; sin configurar) |
| 10 | **Sandbox + política + trazas** | ❌ **brecha abierta** |
| 11 | Reglas como datos, no código | ✅ SOUL + scripts |
| 12 | Single-agent hasta medir | ✅ ausencia deliberada |
| 13 | ACP servidor; sub-agentes in-process | ➖ no aplica |
| 14 | Skills antes que MCP | ✅ en ese orden |
| 15 | **No frameworks** (LangChain, CrewAI…) | ✅ ninguno |
| 16 | **No embeddings sobre código** | ✅ respetado |
| 17 | No envolver cada API 1-a-1 | ✅ skills, no tools |
| 18 | Topes baratos de stuck | ✅ hard_stop |

**15 de 18 cumplidas, 1 parcial, 2 no aplican.** La única brecha estructural es la 10 (sandbox).

---

## Lo que este documento NO afirma

- No dice que CatalanIA sea mejor ni peor que otro agente: el paper no rankea y renunció a comparar
  benchmarks.
- Los conteos (263 skills, 10 controles) son afirmaciones de **inventario** y caducan. Las
  estructurales (posición en los 7 subsistemas) son las que se sostienen.
- El estado "provisto" significa que la pieza existe en Hermes y se configuró. Significa
  **verificado que funciona** solo donde hubo salida real: el gate de privacidad, los 3 bugs del
  empaquetador y el mapeo de skills. El resto está heredado sin prueba propia.
