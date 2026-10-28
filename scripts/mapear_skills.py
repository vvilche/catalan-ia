"""Resuelve el mapa familia -> skills de CatalanIA contra ~/.hermes/skills.

CatalanIA es un agente TRANSVERSAL: cubre las 4 lineas de negocio de CONECTA
(NORMATIVO, SCADA, PAC-SSEE, Procesos) mas las capas compartidas. Por eso el eje
de las familias es el NEGOCIO, no una persona.

Los nombres se buscan por el campo `name:` del frontmatter, NO por el directorio:
hay skills cuyo directorio no coincide con su name
(ej. sitr-base -> evaluating-sitr-compliance).
"""
import os
import re
import glob
import json

SK = os.path.expanduser('~/.hermes/skills')
OUT = os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'seed', 'familias.json'))


def index_skills():
    idx = {}
    for p in glob.glob(SK + '/**/SKILL.md', recursive=True):
        try:
            txt = open(p, encoding='utf-8', errors='ignore').read()
        except OSError:
            continue
        m = re.search(r'^name:\s*(.+)$', txt, re.M)
        n = (m.group(1).strip().strip('"\'') if m else os.path.basename(os.path.dirname(p)))
        idx.setdefault(n, []).append(os.path.dirname(p))
    return idx


# ── eje de NEGOCIO ──────────────────────────────────────────────────────────
# CatalanIA = POWER: NORMATIVO + SCADA + PAC-SSEE (el sistema electrico de
# potencia). PROCESOS QUEDA FUERA: esta sin hacer y el agente no lo cubre.
# Las skills de Procesos se conservan abajo en _procesos_pendiente para que el
# trabajo ya identificado no se pierda cuando esa linea se aborde.
FAMILIAS = {
    # ===== las 3 lineas de POWER =====
    "linea_normativo": [
        "escalera-al-exito", "conecta-ventas-metodologia", "conecta-ventas", "conecta-sales",
        "conecta-dolor-oculto", "conecta-objeciones", "score-potencial-cliente",
        "radar-normativo-cen", "cen-cartas-leads", "cartas-cen-scraping",
        "motor-leads-normativo", "campana-ntsycs", "sec-multas-leads", "cen-datos-operacion",
        "diagnostico-coordinado", "evaluating-sitr-compliance", "evaluating-ecap-study",
        "evaluating-edac-edag-erag-compliance", "conecta-edac", "prs-pruebas-cen",
        "conecta-documentos-cen", "conecta-escalera-graph",
    ],
    "linea_scada": [
        "elipse-conecta", "scada", "scada-tecnica-conecta", "scada-valorizacion",
        "conecta-unilineal-scada", "comasa-uns-elipse", "bombin", "iaiops",
        "industrial-iot-lab", "industrial-mqtt-simulator", "industrial-dashboard-generator",
        "industrial-digitalization-kickoff", "industrial-tier0-pilot",
        "conecta-solutions",
    ],
    "linea_pac_ssee": [
        "protecciones-reles", "slrp-protecciones", "coordinating-electrical-protections",
        "calculating-short-circuit", "novatech-rtu-retrofit", "industrial-diagram-ai",
        "novatech-products", "vizimax-products", "satec-products",
    ],
    # PROCESOS NO ENTRA: esta sin hacer. Se conserva aparte para no perder el trabajo.
    "_procesos_pendiente": [
        "supcon-products", "supcon-dcs-ecs700", "supcon-hardware", "supcon-instruments",
        "supcon-valves", "supcon-sis-tcs", "supcon-software-platform", "supcon-control-room",
        "supcon-pride", "supcon-nyx-ucs", "supcon-mining-chile", "supcon-pulp-paper",
        "supcon-competitive", "product-catalog-teardown", "cement-plant-simulator",
        "pipeline-hydraulics-sim", "guacolda-tier0-simulator",
        "tier0", "tier0-api", "tier0-uns-modeling", "tier0-modelar-industrial",
        "tier0-edge", "tier0-namespace-reference", "tier0-populate-namespace",
        "tier0-populate-eventflow", "tier0-populate-grafana", "tier0-populate-sourceflow",
        "tier0-content-population", "tier0-preventa-subestaciones", "tier0-openapi-reference",
        "tier0-pcba-pattern", "uns-namespace-generator", "substation-tier0-pipeline",
    ],

    # ===== capas compartidas por las 3 lineas de POWER =====
    "comun_leads": [
        "conecta-leads", "conecta-leads-bess", "conecta-leads-pci", "conecta-leads-ruido",
        "conecta-leads-sced", "leads-skill-template", "producto-industria-mapping",
        "conecta-prospeccion", "priorizacion-cruce-senales", "sscc-prospeccion-pipeline",
        "sscc-medicion-cen", "conecta-business-intel", "chile-ciberseguridad-compliance",
        "chile-ciberseguridad-regulatoria", "cumplimiento-regulatorio-chile",
        "estudio-mercado-importaciones", "catalogo-empresas",
    ],
    "comun_normativa_sen": [
        "evaluating-generation-compliance", "evaluating-transmission-compliance",
        "evaluating-distribution-compliance", "evaluating-pmgd-pmg-compliance",
        "evaluating-sscc-compliance", "energia-regulatoria-chile", "mercado-electrico-chile",
        "infotecnica-cen", "radar-noticias-conecta", "rag-normativo-chile", "normativacen-rag",
        "chile-normativa-ingestion", "aisa-rumor-scanner",
        "monitoring-regulatory-changes",
    ],
    "comun_cotizacion": [
        "conecta-cotizacion-workflow", "conecta-valorizacion", "conecta-presupuestaria",
        "cotizaciones-multimarca", "conecta-datos-financieros",
        "verificacion-calculos-financieros", "conecta-bom-replicacion", "conecta-ebitda-bono",
        "conecta-cotizador-agents", "conecta-orquestador-odoo", "odoo-jsonrpc-integration",
        "odoo-operaciones-campo",
    ],
    "comun_informes": [
        "generating-technical-report", "documento-docx-editable", "carta-gantt-msproject",
        "librerias-ingenieria-python", "pdf", "xlsx", "docx", "powerpoint",
        "conecta-pptx-pitch", "conecta-presentaciones", "conecta-proposals",
        "conecta-correos", "conecta-web-landings", "conecta-brand-strategy",
        "supcon-presentaciones", "landing-pages-marketing", "popular-web-designs",
        "claude-design", "conecta-data-dashboards", "conecta-landing-marketing",
        "claude-design", "sld-generator", "architecture-diagram", "excalidraw", "sketch",
        "svg-layout-audit", "harness-engineering-agentes",
    ],
    "comun_datos": [
        "deterministic-data-extraction", "ocr-and-documents", "research-grounded-answers",
        "grounded-citations", "vision-gemini-bridge", "image-ocr", "macos-image-ocr",
        "browser-testing-with-devtools", "dogfood", "auditoria-expediente-cliente",
        "comasa-cuenta-clave", "analisis-proyecto-terceros",
        "perfilar-organizacion-investigacion", "industrial-research-workflows",
        "session-history-mining", "session-librarian",
    ],
    "comun_busqueda_web": [
        "aisa-cli", "aisa-search", "aisa-multisearch", "aisa-deep-research",
        "aisa-tavily-extract", "aisa-x-intel", "aisa-rumor-scanner", "aisa-marketpulse",
        "aisa-trend-forecast", "aisa-seo-keywords", "aisa-youtube-search", "perplexity-search",
        "scholar-search", "web-search", "web-research", "tavily-extract",
        "blocked-page-recovery", "company-teardown", "teardown-competidor-radar",
        "competitor-news-monitor", "contact-enrichment", "twitter-autopilot",
        "x-intelligence-automation", "twitter-command-center-search-post", "seia-ingenieria",
        "fuentes-proyectos-chile", "gestores-pmgd-chile", "seo-keyword-research",
        "oportunidades-exposicion-ia",
    ],
    "comun_seguridad": [
        "victor-rules", "agent-behavior-enforcement", "hermes-mac-vps-split",
        "conecta-agent-patterns", "doubt-driven-development", "source-driven-development",
        "constraint-driven-development", "code-review-and-quality", "security-and-hardening",
        "spec-driven-development", "planning-and-task-breakdown",
        "incremental-implementation", "debugging-and-error-recovery", "shipping-and-launch",
    ],
    "comun_plataforma": [
        "hermes-agent", "hermes-profiles", "hermes-model-config", "hermes-mcp", "native-mcp",
        "hermes-cron-audit", "hermes-vps-ops", "hermes-gateway-operations",
        "hermes-update-migration", "respaldo-soul-hermes", "hermes-web-interfaces",
        "webhook-subscriptions", "free-model-orchestration", "kimi-moonshot-api",
        "llm-gateway-providers", "nvidia-model-router", "deepseek-harness",
        "vps-webapp-deploy", "vps-deployment", "hermes-setup-teaching",
        "kanban-orchestrator", "kanban-worker", "orchestration",
    ],
    "comun_comercial": [
        "b2b-sales-multiagent", "negotiation", "negotiate-for-principal",
        "proposal", "partnership-plans", "weekly-review-planning", "meeting-action-items",
        "document-to-action-items", "posicionamiento-agente-industrial",
        "monetizacion-5-plays", "innovacion-frameworks", "ten-types-innovation",
        "lean-startup", "running-lean", "innovators-dilemma", "book-to-skill", "ideation",
        "conecta-cursos", "conecta-video", "conecta-web", "conecta-web-deploy",
        "conecta-mcp-agent", "conecta-rag-pipeline", "rag-architecture", "audit-rag-generator",
        "corpus-ingesta-sin-perdidas", "corpus-dedup-por-contenido", "corpus-molde-mining",
        "corpus-multilingue-indexacion", "llm-wiki", "port-agent-skills", "espanol-chileno",
        "calendario-fae", "usach-cursos", "ttung-design-system",
    ],
}

if __name__ == '__main__':
    idx = index_skills()
    res, faltan = {}, []
    for fam, names in FAMILIAS.items():
        ok, visto = [], set()
        for n in names:
            if n in visto:
                continue
            visto.add(n)
            if n in idx:
                ok.append({'name': n, 'src': os.path.relpath(idx[n][0], SK)})
            else:
                faltan.append(n)
        res[fam] = ok

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, 'w'), ensure_ascii=False, indent=1)

    print("=== FAMILIAS (POWER: NORMATIVO + SCADA + PAC-SSEE) ===")
    for fam, items in res.items():
        marca = "  [no se instala]" if fam.startswith("_") else ""
        print("%-22s %3d%s" % (fam, len(items), marca))
    instala = {k: v for k, v in res.items() if not k.startswith("_")}
    todas = {x['name'] for v in instala.values() for x in v}
    print("\nSuma por familia (instalables): %d" % sum(len(v) for v in instala.values()))
    print("Skills UNICAS al perfil:        %d" % len(todas))
    pend = {x['name'] for k, v in res.items() if k.startswith("_") for x in v}
    print("Skills en _pendiente (aparte):  %d" % len(pend))
    print("Solapamiento pendiente/activo:  %d" % len(pend & todas))
    if faltan:
        print("\nNO ENCONTRADAS (%d): %s" % (len(set(faltan)), ", ".join(sorted(set(faltan)))))
    else:
        print("\nTodas las skills referenciadas existen.")
