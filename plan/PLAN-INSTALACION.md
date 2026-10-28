# CatalanIA — Plan de instalación

Gemelo comercial de Francisco Catalán (uid 18, línea NORMATIVO, transición a SCADA 2026-2027).
Especialista en venta CONECTA: Escalera al Éxito, radar normativo CEN, InfoTecnica, cotización,
Odoo, recolección de datos web.

Repo: `vvilche/catalan-ia` — **público**. Eso obliga a que el paquete no lleve nombres de
cliente, montos, nombres del equipo, rutas ni IPs. Lo verifica `verificar_privacidad_perfil.py`.

---

## 1. Qué es este agente (y qué no es)

Un perfil Hermes independiente, no un prompt. La diferencia importa: tiene su propio `SOUL.md`,
su memoria, sus skills, su cron y su config. Vive en `~/.hermes/profiles/catalania/` y no ve
nada del perfil `default` salvo lo que se le copie a propósito.

**Qué es:** índice + skills + motor determinístico, con un LLM que sintetiza al final.
**Qué no es:** un modelo. Si mañana cambia el proveedor, el perfil se reinstala y sigue.

## 2. Anatomía

CatalanIA se audita contra los 7 subsistemas del harness (D1 bucle · D2 integración LLM · D3
herramientas · D4 memoria · D5 seguridad · D6 orquestación · D7 extensibilidad), base
arXiv:2609.00006v1. La auditoría completa, con lo verificado y las brechas declaradas, está en
`docs/arquitectura-7-subsistemas.md`. Resumen: 15 de 18 recomendaciones cumplidas, orquestación en
ausencia deliberada, y **una brecha estructural abierta: no hay sandbox de sistema operativo**.

```
~/.hermes/profiles/catalania/
├── SOUL.md                 contrato de conducta: 13 reglas, se carga en cada sesión
├── memories/
│   ├── MEMORY.md           hechos de entorno (no procedimientos)
│   └── USER.md             quién es Victor y cómo quiere que le hable
├── config.yaml             modelo, verify_on_stop, hard_stop
├── profile.yaml            descripción de la silla
├── skills/                 93 skills en 11 familias (ver seed/familias.json)
└── cron/jobs.json          radar normativo semanal + backup
```

## 3. Las 11 familias de skills (93 skills)

| Familia | N | Para qué |
|---|---|---|
| `escalera` | 13 | P×M×R · N×Pv×Map · F×Mt×E · Pv×Mt×Pc, dolor oculto, objeciones, score, prospección |
| `radar_normativo` | 6 | Cartas CEN, scraping, mora, multas SEC, campaña NTSyCS |
| `info_tecnica` | 3 | InfoTecnica CEN, datos del SEN, diagnóstico de coordinado |
| `producto` | 9 | CONECTA, SUPCON, NovaTech, Vizimax, SATEC, leads BESS/PCI/Ruido/SCED |
| `cotizacion` | 6 | BOM + HH, valorización, multimarca, datos financieros, verificación de cálculos |
| `odoo` | 3 | Leads, OTs, facturas, JSON-RPC |
| `material_venta` | 8 | Correos, propuestas, presentaciones, landings, brand |
| `informes` | 6 | Informes técnicos y memorias de cálculo con control de revisiones, .docx editable, Gantt, librerías de ingeniería |
| `datos` | 7 | Extracción determinística, xlsx/pdf/docx, OCR, citas verificables |
| `seguridad` | 6 | Reglas de Victor, dónde va cada regla, Mac/VPS, patrones de agentes |
| `busqueda_web` | 26 | AISA (search, deep research, X, rumor), Perplexity, company teardown, SEIA |

**Criterio de corte:** entró lo que el rol usa para vender, calificar, cotizar, buscar y
publicar con evidencia. Quedó fuera lo que no es de la silla: `science` (38), `tier0-*`,
`supcon-*` de producto profundo, gaming, smart-home, media. Se pueden agregar después sin
tocar el SOUL: una skill extra no cambia la conducta, cambia el alcance.

**Advertencia de arquitectura (skill `conecta-agent-patterns`):** el conocimiento de una línea
NO puede vivir en la silla de una persona. Si Francisco rota a SCADA, su criterio queda en skills
versionadas en el repo, no en su perfil personal. Eso es exactamente lo que hace este paquete.

## 4. Las reglas de conducta (SOUL.md)

10 heredadas del agente de Victor, medidas sobre 1.464 sesiones — los errores 1-9 concentran
~85% de las correcciones:

1. El entregable es la salida real de la herramienta (14,6%)
2. Respondé la pregunta textual (32,5% — el error nº1)
3. Reversible: actuá. Irreversible: preguntá (24,4%)
4. Antes de improvisar, verificá si ya tenés la herramienta (14,8%)
5. Verificá contra casos conocidos, no contra el agregado
6. Ningún número ni afirmación de hecho sin fuente
7. Preguntá de dónde sale el dato de verdad: puente, no copia
8. Memoria vs skill — y si dudás, preguntá
9. Agotá el contexto que ya existe en el Mac
10. Verificá lo suficiente para no reportar algo falso, y no más que eso

Tres propias del rol comercial:

11. **El dato de cliente sale de Odoo, nunca de la memoria.** Prohibido completar un campo
    "razonablemente": un monto inventado en una propuesta es una pérdida.
12. **Brief ≠ estado de cuenta.** Toda afirmación de cliente con fuente y fecha; verificar el
    hito que cambia la calificación antes de calificar.
13. **Nada sale hacia afuera sin OK explícito.** No escribe en Odoo, no manda correo a un
    cliente, no publica ni toca el VPS sin autorización dicha en la sesión.

Por qué 13 y no 40: el cumplimiento se degrada al crecer el número de reglas. Cada incidente
que agrega una regla empeora el cumplimiento general. Las que se pueden automatizar van a
script, no al SOUL.

## 5. Los controles ejecutables (el arnés)

Una regla en prosa se cumple ~53% de las veces. Un script, ~100%. Por eso:

| Control | Qué impide |
|---|---|
| `antes_de_crear.py` | crear algo que ya existe (pasó: spec de 392 líneas con repo ya hecho) |
| `editar_seguro.py` | editar sin releer (patch fallido 3 veces seguidas) |
| `auditar_respuesta.py` | afirmaciones sin fuente |
| `check_contexto.py` | perder el trabajo al compactar sin hook de parada |
| `verificar_privacidad_perfil.py` | **publicar un perfil con datos de cliente** |
| `manifest_verificar.sh` | que la base cambie sin saberlo |

El último es nuevo en esta sesión y es el que hace posible un repo público.

## 6. Instalación, paso por paso

Requisitos: Hermes instalado, `gh` autenticado como `vvilche`, el arnés en
`~/hermes-config/arnes/`.

```bash
export PY=~/.hermes/hermes-agent/venv/bin/python
cd ~/orca/projects/CatalanIA

# 0. Colisión
$PY ~/.hermes/scripts/antes_de_crear.py "catalania"     # exit 0 obligatorio

# 1. Arnés (11 scripts)
~/hermes-config/arnes/instalar.sh
~/hermes-config/arnes/instalar.sh --check               # 11 OK

# 2. Crear el perfil
hermes profile create catalania --no-skills \
  --description "Especialista comercial CONECTA — NORMATIVO, transición a SCADA"

# 3. Config: heredar claves y MCP, después endurecer
cp ~/.hermes/config.yaml ~/.hermes/profiles/catalania/config.yaml
hermes config set agent.verify_on_stop true                     --profile catalania
hermes config set tool_loop_guardrails.hard_stop_enabled true    --profile catalania
hermes config set model.provider deepseek                       --profile catalania
hermes config set model.model deepseek-v4-flash                 --profile catalania

# 4. SOUL, memorias y descripción
cp profile/SOUL.md           ~/.hermes/profiles/catalania/SOUL.md
cp profile/profile.yaml      ~/.hermes/profiles/catalania/profile.yaml
mkdir -p ~/.hermes/profiles/catalania/memories
cp profile/memories/MEMORY.md profile/memories/USER.md \
   ~/.hermes/profiles/catalania/memories/

# 5. Skills (87, por familia)
$PY scripts/empaquetar_perfil.py \
   --perfil ~/.hermes/profiles/catalania \
   --salida . --familias seed/familias.json --limpiar

# 6. Verificar
$PY ~/.hermes/scripts/verificar_privacidad_perfil.py ~/.hermes/profiles/catalania
hermes profile list | grep catalania                     # modelo visible, no "—"
find ~/.hermes/profiles/catalania/skills -name SKILL.md | wc -l   # ~87
```

Nota: `hermes profile create` crea el wrapper `~/.local/bin/catalania`. A partir de ahí se
entra con `catalania` o con `hermes --profile catalania`.

## 7. Publicar el repo

```bash
$PY ~/.hermes/scripts/verificar_privacidad_perfil.py ./profile   # exit 0 obligatorio
gh repo create vvilche/catalan-ia --public --source . --push \
  --description "CatalanIA — perfil Hermes del especialista comercial CONECTA (NORMATIVO)"
```

Antes del primer push, revisar a mano los **AVISOS** (no bloquean): tarifas HH, márgenes y
nombres de persona. Un aviso que se publica es una decisión, no un accidente.

## 8. Operación diaria

| Cuándo | Qué |
|---|---|
| Lunes 08:00 | Radar normativo CEN → oportunidades por cuenta |
| Diario | Revisar cartas nuevas, cruzar con clientes, cross-sell |
| Al pedir un lead | Leer Odoo (`crm.lead`), calificar con la Escalera, proponer plan |
| Antes de un correo | Borrador + OK de Victor. El envío no lo hace el agente solo |
| Al cerrar sesión | `respaldar-soul.sh catalania` (versiona el SOUL) |

Cron heredado del radar: job `f71496cbf722`, lunes 08:00, corre
`~/orca/projects/RadarNormativoCEN/src/sincronizar.sh`. El correo lo manda el script; el agente
no redacta otro. **`--deliver local` no avisa en CLI**: si se quiere notificación, apuntar a
Telegram o WhatsApp.

## 9. Qué queda pendiente y depende de una decisión

1. **Canales** — CLI, WhatsApp, Telegram, cron. Sin esto el agente existe pero no se usa.
2. **Permisos** — qué puede hacer sin preguntar. Propuesta: leer todo, escribir nada.
3. **Transición a SCADA** — cuándo se declara y qué skills de SCADA entran.
4. **Vigencia del tarifario** — el gate R09 ("tarifario con más de 12 meses no emite") no puede
   evaluar porque falta el campo de vigencia versionado. Sin eso el agente cotiza con precios
   que no puede fechar.
5. **Etiquetado de chunks** — el índice es uno (188k chunks). Falta la etiqueta `linea` y
   `componente` por chunk, sale del CONTENIDO y no del path. Es trabajo de datos, no de
   infraestructura: FAISS ya filtra por metadato.

## 10. Riesgos declarados

- **Repo público con material de CONECTA.** El detector cubre clientes, montos, correos,
  teléfonos, rutas, IPs y credenciales. **No cubre** un criterio comercial escrito en prosa
  ("a este cliente le vendemos barato porque..."). Eso se revisa a mano, no hay regex que lo atrape.
- **Skills de terceros con licencia.** 93 skills incluyen material de vendors y de libros. Antes
  de un repo público, verificar que cada una se pueda redistribuir.
- **El empaquetador sanea, pero el SOUL se escribe a mano.** Si alguien edita el SOUL en el repo
  y no en el perfil, quedan dos verdades. Una cifra, un solo origen: el SOUL vivo es el del
  perfil, el del repo es su copia versionada.
- **Un perfil no es un sandbox.** El agente puede leer todo lo que el usuario puede leer. Las
  reglas 11-13 son de conducta, no de permisos del sistema operativo.
