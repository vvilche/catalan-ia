# CatalanIA — memoria del agente

Hechos estables de entorno. **No procedimientos**: esos van en skills.
Si dudás de dónde va algo, preguntá antes de escribir.

CatalanIA es de **Power**: cubre las 3 líneas del sistema eléctrico de potencia (NORMATIVO, SCADA,
PAC-SSEE). **Procesos queda fuera**: no está hecho todavía, y el agente no lo improvisa.

## Entorno: Windows con PowerShell (condicional)

**Si el perfil corre en Windows**, los comandos son de **PowerShell**, no de bash ni de CMD.
Un agente que da instrucciones de Mac a un usuario de Windows no le sirve: es el mismo error que
darle una cifra sin fuente. Si corre en Mac o Linux, esta tabla no aplica y hay que usar el shell
del sistema — verificar el entorno antes de dar comandos, no asumirlo.

| Necesito | En Windows PowerShell | 
|---|---|
| Python de Hermes | `$env:USERPROFILE\.hermes\hermes-agent\venv\Scripts\python.exe` |
| Home del usuario | `$env:USERPROFILE` (no se usa `~`) |
| Copiar archivo | `Copy-Item` (no `cp`) |
| Crear carpeta | `New-Item -ItemType Directory -Force` (no `mkdir -p`) |
| Variable de entorno | `$env:PY = "..."` (no `export PY=...`) |
| Ver un archivo | `Get-Content` (no `cat`) |
| Abrir un HTML | `Start-Process chrome "<ruta>"` (no `open -a`) |
| Ruta con espacios | Entre comillas dobles: `"$env:USERPROFILE\Mis documentos"` |

**Pitfalls de PowerShell que ya costaron tiempo:**
- **`Set-Content` sobrescribe.** Para agregar sin destruir: `Add-Content` o `Out-File -Append`.
- **`-Encoding utf8` en PowerShell 5.1 mete BOM.** Para un `.env` que se lee valor por valor,
  escribir con `-Encoding ascii`.
- **Un patrón de verificación no se enmascara nunca.** `Select-String -Pattern '^GEMINI_API_KEY=' -Quiet`
  devuelve `$true`/`$false` sin imprimir el valor. Enmascarar con asteriscos puede truncar el
  comando y PowerShell **no da error**: la línea simplemente no corre.
- **`timeout` en Windows existe, pero NO es el de Linux**: espera teclas y hace otra cosa. Para
  limitar tiempo usar el timeout del propio tool, nunca `timeout N comando`.

## Quién usa el agente

- La silla, no la persona: comercial/preventa de las tres líneas de Power. El detalle está en
  `USER.md`, que es lo que hay que leer antes de asumir preferencias.
- Idioma de trabajo: español, tuteo chileno. Si respondés en inglés, es un error.
- Datos personales del usuario (RUT, teléfono, correo privado) **no se guardan acá**.
- No confundir al dueño del negocio con el usuario de este equipo: los datos de dirección
  comercial viven en Odoo, no en la memoria del agente.

## CONECTA, operativa

- Líneas que cubre este agente (eje comercial de Odoo `x_studio_linea_3`): NORMATIVO · SCADA ·
  PAC-SSEE. Las subdivisiones (PDC, SITR, SLRP, EDAC, EDAG, PMU, RTU, PROTECCIONES, IEC61850)
  cuelgan de esas tres. Un solo eje: no armar un cuarto.
- **Procesos (VÁLVULAS, INSTRUMENTOS, DCS) existe en la empresa pero NO en este agente.**
  No está hecho. Si una cuenta lo pide, se declara no cubierto y se deriva.
- Indicios digeridos del negocio: BOMs, tarifarios y chunks de las tres áreas (comercial,
  cotizador, operaciones). **Revisar lo ya digerido antes de abrir planillas crudas.**
- Odoo: las facturas se ligan a OT por `account.move.line.analytic_distribution`.
  `invoice_origin` y `ref` vienen vacíos. Saldo = `amount_residual`.
- Odoo: el jefe de proyecto de una OT es `project.project.user_id`.
- Odoo: darle un lead a alguien es `crm.lead.user_id` (vendedor), **no** crear `project.task`.
- Odoo está detrás de un WAF que bloquea algunas IPs: si una consulta muere con "connection reset",
  no es un problema de credenciales ni de datos — es el WAF. Reportarlo, no reintentar en bucle.

## Skills que ya existen y hay que buscar antes de improvisar

`escalera-al-exito` (metodología de venta), `radar-normativo-cen`, `cen-cartas-leads`,
`infotecnica-cen`, `conecta-cotizacion-workflow`, `conecta-orquestador-odoo`,
`deterministic-data-extraction`, `conecta-correos`. Si el procedimiento ya está escrito,
no se reinventa.

## Controles ejecutables

Viven en `$env:USERPROFILE\.hermes\scripts\`. Todos son Python de stdlib: corren igual en Windows.

- `antes_de_crear.py <nombre>` — colisiones antes de crear.
- `editar_seguro.py <archivo> --buscar "<ancla>"` — releer antes de editar.
- `auditar_respuesta.py <archivo>` — afirmaciones sin fuente.
- `check_contexto.py` — ventana de contexto.
- `verificar_privacidad_perfil.py <perfil>` — antes de publicar nada.
