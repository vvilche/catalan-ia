# CatalanIA

Agente comercial **transversal** de CONECTA Ingeniería: cubre las **cuatro líneas de negocio** —
NORMATIVO, SCADA, PAC-SSEE y Procesos — no una.

Silla de origen: Francisco Catalán (NORMATIVO, transición a SCADA 2026-2027). Pero el conocimiento
no vive en la persona: vive en las skills versionadas. Por eso cubre todo el portafolio y sobrevive
a la rotación de quien lo usaba.

## Qué sabe hacer

- **Radar normativo**: cartas y requerimientos del CEN, mora, multas de la SEC, cambios de norma
  → oportunidad comercial con nombre de cuenta.
- **Calificar**: Escalera al Éxito completa (P×M×R → N×Pv×Map → F×Mt×E → Pv×Mt×Pc).
- **Las 4 líneas**: PDC/SITR/SLRP/EDAC/EDAG/PMU · ELIPSE · RTU/protecciones/IEC 61850 ·
  válvulas/instrumentos/DCS (SUPCON) + Tier0.
- **Preparar el ataque**: dolor oculto, matriz de objeciones, campeón interno, plan de cuenta.
- **Cotizar**: BOM y HH reales desde el motor, no inventadas.
- **Producir material**: informe técnico, memoria de cálculo, correo, propuesta, presentación.
- **Buscar**: AISA, Perplexity, company teardown, SEIA, importaciones, contactos.

263 skills en 13 familias (4 líneas + 9 capas compartidas). Ver `seed/familias.json`.

## Auditoría de arquitectura

CatalanIA está auditado contra los 7 subsistemas del harness de agentes (bucle, integración LLM,
herramientas, memoria, seguridad, orquestación, extensibilidad) — `docs/arquitectura-7-subsistemas.md`.
15 de 18 recomendaciones cumplidas, orquestación en ausencia deliberada, y una brecha declarada:
no hay sandbox de sistema operativo. Las reglas de seguridad son de conducta, no de permisos.

## Reglas que no se negocian

13 reglas en `profile/SOUL.md`: las 10 heredadas del agente de Victor (medidas sobre 1.464
sesiones) más tres del rol comercial — el dato de cliente sale de Odoo y no de la memoria,
brief ≠ estado de cuenta, y nada sale hacia afuera sin OK explícito.

## Instalación

```bash
export PY=~/.hermes/hermes-agent/venv/bin/python
cd ~/orca/projects/CatalanIA

~/hermes-config/arnes/instalar.sh
hermes profile create catalania --no-skills --description "Especialista comercial CONECTA — NORMATIVO"
cp ~/.hermes/config.yaml ~/.hermes/profiles/catalania/config.yaml
hermes config set agent.verify_on_stop true --profile catalania

cp profile/SOUL.md      ~/.hermes/profiles/catalania/SOUL.md
cp profile/profile.yaml ~/.hermes/profiles/catalania/profile.yaml
mkdir -p ~/.hermes/profiles/catalania/memories
cp profile/memories/*.md ~/.hermes/profiles/catalania/memories/

$PY scripts/empaquetar_perfil.py --perfil ~/.hermes/profiles/catalania \
   --salida . --familias seed/familias.json --limpiar
```

Detalle completo, verificación y riesgos: `plan/PLAN-INSTALACION.md`.

## Estructura

```
profile/            lo que se instala en ~/.hermes/profiles/catalania/
  SOUL.md           contrato de conducta (13 reglas)
  memories/         MEMORY.md (entorno) y USER.md (Victor)
  config.yaml       punto de partida: modelo, verify_on_stop, hard_stop
  profile.yaml      descripción de la silla
scripts/
  mapear_skills.py  resuelve las 263 skills por familia desde ~/.hermes/skills
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
