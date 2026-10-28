import os, re, glob, json

SK = os.path.expanduser('~/.hermes/skills')
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'seed', 'familias.json')
OUT = os.path.normpath(OUT)


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


FAMILIAS = {
    "escalera": [
        "escalera-al-exito", "conecta-ventas-metodologia", "conecta-ventas", "conecta-sales",
        "conecta-dolor-oculto", "conecta-objeciones", "score-potencial-cliente",
        "priorizacion-cruce-senales", "leads-skill-template", "producto-industria-mapping",
        "conecta-prospeccion", "b2b", "b2b-sales-multiagent", "negotiation",
    ],
    "radar_normativo": [
        "radar-normativo-cen", "cen-cartas-leads", "cartas-cen-scraping",
        "motor-leads-normativo", "campana-ntsycs", "sec-multas-leads", "vigilancia-normativa",
    ],
    "info_tecnica": [
        "infotecnica-cen", "cen-datos-operacion", "diagnostico-coordinado",
        "externo-fuentes",
    ],
    "producto": [
        "conecta-solutions", "supcon-products", "novatech-products", "vizimax-products",
        "satec-products", "conecta-leads-bess", "conecta-leads-pci", "conecta-leads-ruido",
        "conecta-leads-sced",
    ],
    "cotizacion": [
        "conecta-cotizacion-workflow", "conecta-valorizacion", "conecta-presupuestaria",
        "cotizaciones-multimarca", "conecta-datos-financieros",
        "verificacion-calculos-financieros",
    ],
    "odoo": [
        "conecta-orquestador-odoo", "odoo-jsonrpc-integration", "odoo-operaciones-campo",
    ],
    "material_venta": [
        "conecta-correos", "conecta-proposals", "conecta-presentaciones",
        "conecta-pptx-pitch", "conecta-web-landings", "supcon-presentaciones",
        "conecta-brand-strategy", "landing-pages-marketing",
    ],
    "informes": [
        "generating-technical-report", "documento-docx-editable", "carta-gantt-msproject",
        "librerias-ingenieria-python", "pdf", "xlsx",
    ],
    "datos": [
        "deterministic-data-extraction", "xlsx", "pdf", "docx", "ocr-and-documents",
        "research-grounded-answers", "grounded-citations",
    ],
    "seguridad": [
        "victor-rules", "agent-behavior-enforcement", "hermes-mac-vps-split",
        "conecta-agent-patterns", "doubt-driven-development",
        "source-driven-development",
    ],
    "busqueda_web": [
        "aisa-cli", "aisa-search", "aisa-multisearch", "aisa-deep-research",
        "aisa-tavily-extract", "aisa-x-intel", "aisa-rumor-scanner", "perplexity-search",
        "scholar-search", "web-search", "company-teardown", "teardown-competidor-radar",
        "competitor-news-monitor", "catalogo-empresas", "estudio-mercado-importaciones",
        "cumplimiento-regulatorio-chile", "chile-ciberseguridad-compliance",
        "chile-ciberseguridad-regulatoria", "seia-ingenieria", "fuentes-proyectos-chile",
        "gestores-pmgd-chile", "contact-enrichment", "twitter-autopilot", "web",
        "blocked-page-recovery", "tavily-extract", "web-research",
    ],
}

if __name__ == "__main__":
    idx = index_skills()
    res, faltan = {}, []
    for fam, names in FAMILIAS.items():
        ok = []
        for n in names:
            if n in idx:
                ok.append({"name": n, "src": os.path.relpath(idx[n][0], SK)})
            else:
                faltan.append("%s/%s" % (fam, n))
        res[fam] = ok
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w"), ensure_ascii=False, indent=1)
    for fam, items in res.items():
        print("%-16s %2d  %s" % (fam, len(items), ", ".join(x["name"] for x in items)))
    total = sum(len(v) for v in res.values())
    print("\nTOTAL %d (unicas %d)" % (total, len({x["name"] for v in res.values() for x in v})))
    print("FALTAN:", ", ".join(faltan) if faltan else "ninguna")
