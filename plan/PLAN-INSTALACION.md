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
%USERPROFILE%\.hermes\profiles\catalania\
├── SOUL.md                 contrato de conducta: 13 reglas, se carga en cada sesión
├── memories\
│   ├── MEMORY.md           hechos de entorno + equivalencias de PowerShell
│   └── USER.md             quién es Victor y cómo quiere que le hable
├── config.yaml             modelo, verify_on_stop, hard_stop
├── profile.yaml            descripción de la silla
└── skills\                 230 skills en 12 familias (ver seed/familias.json)
```

**Plataforma: Windows con PowerShell.** No hay `cp`, `export`, `~` ni `open -a`. El perfil trae la
tabla de equivalencias en `memories/MEMORY.md` y el SOUL prohíbe dar comandos de bash.

## 3. Las 12 familias de skills (230 skills) — Power

CatalanIA cubre **Power**: las 3 líneas del sistema eléctrico de potencia más las capas
compartidas. **Procesos no está en el agente**: se conserva aparte como referencia.

### Las 3 líneas de Power — 45 skills

| Familia | N | Qué cubre |
|---|---|---|
| `linea_normativo` | 22 | Escalera, radar CEN, cartas, SITR, ECAP, EDAC/EDAG, PRS, escalera graph |
| `linea_scada` | 14 | ELIPSE, SCADA, unilineales, COMASA, gemelo digital, IoT industrial |
| `linea_pac_ssee` | 9 | Protecciones, SLRP, coordinación, cortocircuito, retrofit RTU, NovaTech/Vizimax/SATEC |

### Las 9 capas compartidas — 185 slots

| Familia | N | Qué cubre |
|---|---|---|
| `comun_leads` | 17 | Leads BESS/PCI/Ruido/SCED, prospección, score, cruce de señales, ciberseguridad, mercado |
| `comun_normativa_sen` | 14 | Generación, transmisión, distribución, PMGD, SSCC, InfoTecnica, RAG normativo |
| `comun_cotizacion` | 12 | BOM + HH, valorización, multimarca, EBITDA, orquestador Odoo |
| `comun_informes` | 26 | Informes técnicos, .docx, Gantt, presentaciones, propuestas, landings, diagramas |
| `comun_datos` | 16 | Extracción determinística, OCR, visión, expedientes, research de proyecto |
| `comun_busqueda_web` | 29 | AISA completo, Perplexity, teardown, SEIA, importaciones, contactos, X |
| `comun_seguridad` | 14 | Reglas de Victor, dónde va cada regla, harness, revisión, especificación |
| `comun_plataforma` | 23 | Hermes, MCP, cron, VPS, modelos, gateway, kanban |
| `comun_comercial` | 35 | B2B, negociación, innovación, RAG, corpus, cursos, marca |

### Fuera de alcance: Procesos

`_procesos_pendiente` tiene 33 skills identificadas (SUPCON DCS/instrumentos/válvulas/SIS/Tier0).
**No se instalan**: el prefijo `_` hace que el empaquetador las omita. Quedan ahí para no perder el
trabajo cuando esa línea se aborde. Si una cuenta pide Procesos, el agente declara que no está
cubierto en vez de improvisar (regla 13 del SOUL ampliada en "Quién sos").

**Verificado:** 230 skills únicas al perfil, todas existen en `~/.hermes/skills`. Solapamiento
entre Procesos y lo activo: 2 skills.

**Criterio de corte:** entró todo lo que Power usa para vender, calificar, cotizar, buscar y
publicar con evidencia. Quedó fuera lo que no es del negocio: `science` (38), `gaming`,
`smart-home`, `mlops` profundo. Una línea nueva se agrega sin tocar el SOUL: una skill extra
cambia el alcance, no la conducta.

**Advertencia de arquitectura (skill `conecta-agent-patterns`):** el conocimiento de una línea
NO puede vivir en la silla de una persona. Si Francisco rota a SCADA, su criterio queda en skills
versionadas en el repo, no en su perfil personal. Eso es lo que hace este paquete — y es la razón
por la que cubre las tres líneas de Power y no es "el agente de Francisco".

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

## 6. Instalación en Windows, desde cero (PowerShell)

Esta sección arranca en una PC Windows **sin nada instalado**. Al final hay un perfil
`catalania` funcionando.

**Este perfil corre en Windows.** Los comandos son PowerShell, no bash.

### Paso 0 — Instalar Hermes

Hermes corre nativo en Windows: no hace falta WSL. Abrir PowerShell y ejecutar:

```powershell
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
```

El instalador trae Python 3.14, Node.js, npm, ripgrep y FFmpeg sin intervención. Si no hay Git,
deja una copia verificada en el almacén de herramientas de Hermes (no reemplaza el Git del
sistema). La instalación nativa vive en `%LOCALAPPDATA%\hermes`.

Cerrar y reabrir PowerShell, después:

```powershell
hermes --version
hermes setup
```

`hermes setup` pide la clave del proveedor de modelo. Sin eso el agente arranca pero no piensa.

> **Si el antivirus marca `uv.exe` como malware:** es un falso positivo. `uv` es el gestor de
> Python de Astral que Hermes incluye, y los antivirus con ML marcan binarios Rust sin firma.
> Se resuelve con una exclusión: PowerShell como administrador →
> `Add-MpPreference -ExclusionPath "$env:LOCALAPPDATA\hermes\bin"`

> **Si preferís WSL2:** el instalador de Linux (`curl -fsSL https://hermes-agent.nousresearch.com/install.sh | bash`)
> funciona ahí y el perfil queda en `~/.hermes`, como en Linux. Todo el resto del plan es
> PowerShell nativo; con WSL2 los comandos vuelven a ser bash.

### Paso 0.5 — Clonar el repo

```powershell
winget install --id Git.Git -e   # solo si no hay Git
git clone https://github.com/vvilche/catalan-ia.git "$env:USERPROFILE\catalan-ia"
```

### Paso 1 — Variables de la sesión

```powershell
$PY     = "$env:USERPROFILE\.hermes\hermes-agent\venv\Scripts\python.exe"
$ARNES  = "$env:USERPROFILE\.hermes\scripts"
$Repo   = "$env:USERPROFILE\catalan-ia"
$Perfil = "$env:USERPROFILE\.hermes\profiles\catalania"
Set-Location $Repo
```

> **Ojo con la ruta del Python.** Una instalación nativa de Windows puede dejar Hermes en
> `%LOCALAPPDATA%\hermes`. Verificar con `hermes --version` y, si el venv no está donde dice
> `$PY`, buscar el intérprete real antes de seguir:
> `Get-ChildItem "$env:LOCALAPPDATA\hermes" -Filter python.exe -Recurse -ErrorAction SilentlyContinue | Select-Object -First 3 FullName`

### Paso 2 — Colisión y controles

```powershell
& $PY "$ARNES\antes_de_crear.py" "catalania"     # exit 0 obligatorio
```

Los scripts del arnés son Python de stdlib puro. Si el repo no los trae, copiarlos a
`$ARNES`; no necesitan `pip install` ni bash.

### Paso 3 — Crear el perfil vacío

```powershell
hermes profile create catalania --no-skills --description "Agente comercial CONECTA - Power (NORMATIVO, SCADA, PAC-SSEE)"
```

### Paso 4 — Config: heredar claves y MCP, después endurecer

```powershell
Copy-Item "$env:USERPROFILE\.hermes\config.yaml" "$Perfil\config.yaml" -Force
hermes config set agent.verify_on_stop true                     --profile catalania
hermes config set tool_loop_guardrails.hard_stop_enabled true    --profile catalania
hermes config set model.provider deepseek                       --profile catalania
hermes config set model.model deepseek-v4-flash                 --profile catalania
```

### Paso 5 — SOUL, descripción y memorias

```powershell
Copy-Item "$Repo\profile\SOUL.md"      "$Perfil\SOUL.md" -Force
Copy-Item "$Repo\profile\profile.yaml" "$Perfil\profile.yaml" -Force
New-Item -ItemType Directory -Force -Path "$Perfil\memories" | Out-Null
Copy-Item "$Repo\profile\memories\*.md" "$Perfil\memories\" -Force
```

### Paso 6 — Skills: 230 de Power, INSTALADAS EN EL PERFIL

```powershell
& $PY "$Repo\scripts\empaquetar_perfil.py" --perfil $Perfil --salida $Perfil `
   --familias "$Repo\seed\familias.json" --limpiar
```

### Paso 7 — Verificar

```powershell
& $PY "$ARNES\verificar_privacidad_perfil.py" $Perfil
hermes profile list | Select-String catalania
(Get-ChildItem "$Perfil\skills" -Recurse -Filter SKILL.md).Count   # debe dar 230
catalania                                                          # arrancar el agente
```

**Tres cosas del orden que importan:**

1. `--perfil` es **de dónde saca** (el perfil recién creado) y `--salida` es **dónde deja**
   (las mismas rutas del perfil). Si `--salida` apunta al repo, las skills se copian al repo y
   no se instalan.
2. El `Copy-Item` del config va **antes** del `hermes config set`, para no pisar lo heredado.
3. Las memorias se copian **antes** del empaquetado, porque el gate audita el perfil completo.

`hermes profile create` deja el lanzador en el PATH de Hermes. Se entra con `catalania` o con
`hermes --profile catalania`.

### Si el empaquetador falla diciendo que no encuentra skills

Significa que el perfil de origen está vacío: el empaquetador copia **desde `~/.hermes/skills`**
(las skills base de la máquina), no desde el repo. En el PC de Francisco esas 230 skills no
existen todavía.

**Esa es la brecha real de la instalación en su equipo, y no la resuelve este repo.** Hay que
llevar las skills al `~/.hermes/skills` de su máquina (copia directa o repo aparte). Verificar
antes:

```powershell
(Get-ChildItem "$env:USERPROFILE\.hermes\skills" -Recurse -Filter SKILL.md).Count
```

## 7. Publicar el repo

```powershell
& $PY "$ARNES\verificar_privacidad_perfil.py" "$Repo\profile"   # exit 0 obligatorio
gh repo create vvilche/catalan-ia --public --source . --push `
  --description "CatalanIA - agente comercial CONECTA (Power: NORMATIVO, SCADA, PAC-SSEE)"
```

Antes del primer push, revisar a mano los **AVISOS** (no bloquean): tarifas HH, márgenes y
nombres de persona. Un aviso que se publica es una decisión, no un accidente.

## 8. Operación diaria

| Cuándo | Qué |
|---|---|
| Lunes 08:00 | Radar normativo CEN → oportunidades por cuenta |
| Diario | Revisar cartas nuevas, cruzar con clientes, cross-sell |
| Al pedir un lead | Leer Odoo (`crm.lead`), calificar con la Escalera, proponer plan |
| Antes de un correo | Borrador + OK de quien corresponda. El envío no lo hace el agente solo |
| Al cerrar sesión | Respaldar el SOUL con el script del arnés |

**El radar normativo del cron no viene con este repo.** El job que hoy corre en el Mac de Victor
apunta a rutas que en Windows no existen. Para que funcione en el equipo de Francisco hay que
llevar el proyecto del radar y reconfigurar el job con la ruta real. Eso es trabajo pendiente, no
algo que la instalación resuelva sola.

## 9. Qué queda pendiente y depende de una decisión

1. **Canales** — CLI, WhatsApp, Telegram, cron. Sin esto el agente existe pero no se usa.
2. **Permisos** — qué puede hacer sin preguntar. Propuesta: leer todo, escribir nada.
3. **Procesos** — línea fuera del alcance, queda para cuando se aborde (33 skills ya identificadas
   en `_procesos_pendiente`).
4. **Vigencia del tarifario** — el gate R09 ("tarifario con más de 12 meses no emite") no puede
   evaluar porque falta el campo de vigencia versionado. Sin eso el agente cotiza con precios
   que no puede fechar.
5. **Etiquetado de chunks** — el índice es uno (188k chunks). Falta la etiqueta `linea` y
   `componente` por chunk, sale del CONTENIDO y no del path. Es trabajo de datos, no de
   infraestructura: FAISS ya filtra por metadato.
6. **Las rutas del corpus** — el material digerido (BOMs, tarifarios, chunks) hoy vive en el Mac
   de Victor. En el PC de Francisco hay que decidir si se copia, se comparte por red o se consulta
   remoto. Sin eso, el agente no tiene el contexto que lo hace útil.

## 10. Riesgos declarados

- **Repo público con material de CONECTA.** El detector cubre clientes, montos, correos,
  teléfonos, rutas, IPs y credenciales. **No cubre** un criterio comercial escrito en prosa
  ("a este cliente le vendemos barato porque..."). Eso se revisa a mano, no hay regex que lo atrape.
- **Skills de terceros con licencia.** 230 skills incluyen material de vendors y de libros. Antes
  de un repo público, verificar que cada una se pueda redistribuir.
- **El empaquetador sanea, pero el SOUL se escribe a mano.** Si alguien edita el SOUL en el repo
  y no en el perfil, quedan dos verdades. Una cifra, un solo origen: el SOUL vivo es el del
  perfil, el del repo es su copia versionada.
- **Un perfil no es un sandbox.** El agente puede leer todo lo que el usuario puede leer. Las
  reglas 11-13 son de conducta, no de permisos del sistema operativo.
