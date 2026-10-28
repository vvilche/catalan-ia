# CatalanIA

Agente comercial de **Power** en CONECTA Ingeniería: cubre las **tres líneas del sistema eléctrico
de potencia** — NORMATIVO, SCADA y PAC-SSEE.

Silla de origen: Francisco Catalán (NORMATIVO, transición a SCADA 2026-2027). Pero el conocimiento
no vive en la persona: vive en las skills versionadas. Por eso cubre las tres líneas y sobrevive a
la rotación de quien lo usaba.

**Procesos está fuera de alcance** (válvulas, instrumentación, DCS): no está hecho todavía. Las
skills identificadas quedan como referencia en `_procesos_pendiente`, aparte, sin instalarse.

## Qué sabe hacer

- **Radar normativo**: cartas y requerimientos del CEN, mora, multas de la SEC, cambios de norma
  → oportunidad comercial con nombre de cuenta.
- **Calificar**: Escalera al Éxito completa (P×M×R → N×Pv×Map → F×Mt×E → Pv×Mt×Pc).
- **Las 3 líneas de Power**: PDC/SITR/SLRP/EDAC/EDAG/PMU · ELIPSE · RTU/protecciones/IEC 61850.
- **Preparar el ataque**: dolor oculto, matriz de objeciones, campeón interno, plan de cuenta.
- **Cotizar**: BOM y HH reales desde el motor, no inventadas.
- **Producir material**: informe técnico, memoria de cálculo, correo, propuesta, presentación.
- **Buscar**: AISA, Perplexity, company teardown, SEIA, importaciones, contactos.

230 skills en 12 familias (3 líneas + 9 capas compartidas). Ver `seed/familias.json`.

## Auditoría de arquitectura

CatalanIA está auditado contra los 7 subsistemas del harness de agentes (bucle, integración LLM,
herramientas, memoria, seguridad, orquestación, extensibilidad) — `docs/arquitectura-7-subsistemas.md`.
15 de 18 recomendaciones cumplidas, orquestación en ausencia deliberada, y una brecha declarada:
no hay sandbox de sistema operativo. Las reglas de seguridad son de conducta, no de permisos.

## Reglas que no se negocian

13 reglas en `profile/SOUL.md`: las 10 heredadas del agente de Victor (medidas sobre 1.464
sesiones) más tres del rol comercial — el dato de cliente sale de Odoo y no de la memoria,
brief ≠ estado de cuenta, y nada sale hacia afuera sin OK explícito.

## Instalación: un solo comando

En el PC Windows de destino:

1. Poner `INSTALAR-CATALANIA.ps1` y `catalania-skills.zip` en la misma carpeta.
2. Doble clic, o abrir PowerShell ahí y correr:

```powershell
powershell -ExecutionPolicy Bypass -File .\INSTALAR-CATALANIA.ps1
```

Hace todo: verifica e instala Hermes si falta, clona el repo, descomprime las 230 skills,
crea el perfil, lo endurece y verifica. Al final dice **VERDE** (quedó) o **ROJO** con la causa.

Si la política de ejecución bloquea el script, el `-ExecutionPolicy Bypass` de arriba lo evita
sin cambiar la configuración del equipo.

Las 230 skills viajan en el ZIP porque el empaquetador las copia desde `~/.hermes/skills` de la
máquina local: en un PC nuevo ese directorio nace vacío.

### A mano, paso por paso

Detalle completo: `plan/PLAN-INSTALACION.md`.

```powershell
# 0. Hermes (nativo en Windows, sin WSL). Después cerrar y reabrir PowerShell.
iex (irm https://hermes-agent.nousresearch.com/install.ps1)
hermes setup
```

```powershell
# 1. Repo y variables
git clone https://github.com/vvilche/catalan-ia.git "$env:USERPROFILE\catalan-ia"
$Repo   = "$env:USERPROFILE\catalan-ia"
$PY     = "$env:USERPROFILE\.hermes\hermes-agent\venv\Scripts\python.exe"
$Perfil = "$env:USERPROFILE\.hermes\profiles\catalania"
Set-Location $Repo

# 2. Perfil vacío + config
hermes profile create catalania --no-skills --description "Agente comercial CONECTA - Power"
Copy-Item "$env:USERPROFILE\.hermes\config.yaml" "$Perfil\config.yaml" -Force
hermes config set agent.verify_on_stop true --profile catalania

# 3. Persona y memorias
Copy-Item "$Repo\profile\SOUL.md"      "$Perfil\SOUL.md" -Force
Copy-Item "$Repo\profile\profile.yaml" "$Perfil\profile.yaml" -Force
New-Item -ItemType Directory -Force -Path "$Perfil\memories" | Out-Null
Copy-Item "$Repo\profile\memories\*.md" "$Perfil\memories\" -Force

# 4. Skills (230 de Power) — instaladas EN EL PERFIL, no en el repo
& $PY "$Repo\scripts\empaquetar_perfil.py" --perfil $Perfil --salida $Perfil `
   --familias "$Repo\seed\familias.json" --limpiar
```

**Antes del paso 4**, las 230 skills tienen que existir en `$env:USERPROFILE\.hermes\skills`:
el empaquetador copia desde ahí, no desde el repo. Si el perfil sale vacío, esa es la causa.

## Estructura

```
profile/            lo que se instala en ~/.hermes/profiles/catalania/
  SOUL.md           contrato de conducta (13 reglas)
  memories/         MEMORY.md (entorno) y USER.md (Victor)
  config.yaml       punto de partida: modelo, verify_on_stop, hard_stop
  profile.yaml      descripción de la silla
scripts/
  mapear_skills.py  resuelve las 230 skills por familia desde ~/.hermes/skills
  empaquetar_perfil.py  copia y SANEA el perfil; aborta si hay datos de cliente
seed/familias.json  el mapa familia → skills (fuente única)
plan/               este plan
```

## Privacidad

Este repo es **público**. `verificar_privacidad_perfil.py` (del arnés) bloquea la publicación
si encuentra nombres de cliente, montos, correos, teléfonos, rutas del Mac, IPs privadas o
credenciales. Probado: 6 bloqueantes en un perfil sucio, 0 en uno limpio.

Lo que **no** detecta: un criterio comercial escrito en prosa. Eso se revisa a mano.

## Estado

Esqueleto verificado, perfil aún no instalado. Pendiente y por qué:
ver la sección 9 de `plan/PLAN-INSTALACION.md`.
