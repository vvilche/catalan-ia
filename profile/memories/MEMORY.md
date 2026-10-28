# CatalanIA — memoria del agente

Hechos estables de entorno. **No procedimientos**: esos van en skills.
Si dudás de dónde va algo, preguntá antes de escribir.

## Quién es Victor

- Victor Vilche Díaz, CEO de CONECTA, ingeniero eléctrico. RUT y datos personales **no** se guardan acá.
- Idioma de trabajo: español, tuteo chileno. Si respondés en inglés, es un error.
- Prefiere UI minimalista, una sola vista por herramienta, agrupada por capas.
- Matrices, tablas y diagramas: HTML con SVG. Nunca .md ni ASCII para mostrarlos.
- Cuando el trabajo se alarga sin hitos explicados, se desconecta: re-explicar objetivo, por qué
  y qué se midió, y esperar OK antes de tocar producción.

## Entorno

- Mac local: acá viven los datos, el corpus y los índices. Python de Hermes:
  `~/.hermes/hermes-agent/venv/bin/python` (3.11). El `python3` del sistema es 3.9 y no sirve
  para paquetes modernos.
- En el Mac **no existe** el comando `timeout`: usar `gtimeout` o el timeout del propio tool.
- VPS de producción: acceso por SSH (Tailscale). Tocar el VPS es **efecto externo**: backup de
  `config.yaml` antes, y avisar porque reiniciar el gateway corta los canales de mensajería.
- El corpus y el índice RAG viven en el Mac, **no** en el VPS. No subirlos.
- Para abrir un HTML: `open -a "Google Chrome" <ruta absoluta>`.

## CONECTA, operativa

- Líneas (eje comercial de Odoo `x_studio_linea_3`): NORMATIVO · SCADA · PAC-SSEE · Procesos.
  Las subdivisiones (PDC, SITR, SLRP, EDAC, EDAG, PMU, RTU, PROTECCIONES, IEC61850, VÁLVULAS,
  INSTRUMENTOS, DCS) cuelgan de esas cuatro. Un solo eje: no armar un quinto.
- Indicios digeridos en `~/conecta-agentes/indices/`: BOMs, tarifarios y chunks de las tres
  áreas (comercial, cotizador, operaciones). **Revisar ahí antes de abrir planillas crudas.**
- Odoo: las facturas se ligan a OT por `account.move.line.analytic_distribution`.
  `invoice_origin` y `ref` vienen vacíos. Saldo = `amount_residual`.
- Odoo: el jefe de proyecto de una OT es `project.project.user_id`.
- Odoo: darle un lead a alguien es `crm.lead.user_id` (vendedor), **no** crear `project.task`.
- La IP del Mac está bloqueada por el WAF de Odoo: las consultas salen por el VPS o por túnel SSH.

## Skills que ya existen y hay que buscar antes de improvisar

`escalera-al-exito` (metodología de venta), `radar-normativo-cen`, `cen-cartas-leads`,
`infotecnica-cen`, `conecta-cotizacion-workflow`, `conecta-orquestador-odoo`,
`deterministic-data-extraction`, `conecta-correos`. Si el procedimiento ya está escrito,
no se reinventa.

## Controles ejecutables

- `~/.hermes/scripts/antes_de_crear.py <nombre>` — colisiones antes de crear.
- `~/.hermes/scripts/editar_seguro.py <archivo> --buscar "<ancla>"` — releer antes de editar.
- `~/.hermes/scripts/auditar_respuesta.py <archivo>` — afirmaciones sin fuente.
- `~/.hermes/scripts/check_contexto.py` — ventana de contexto.
- `~/.hermes/scripts/verificar_privacidad_perfil.py <perfil>` — antes de publicar nada.
