#!/usr/bin/env python3
"""
antes_de_crear.py — frena la creación de algo que YA EXISTE.

El error que evita: crear un proyecto/carpeta/skill nuevo sin mirar que ya hay
uno que hace lo mismo. Pasó con `CotizadorConecta` cuando ya existía
`ConectaCotizador` con motor BOM, cuestionarios y write-back a Odoo.

No es una regla en prosa: es un chequeo que se corre ANTES de escribir.

Uso:
  antes_de_crear.py cotizador
  antes_de_crear.py "revisor docx"
  antes_de_crear.py <nombre> --json

Salida: candidatos existentes ordenados por similitud. Exit 1 si hay colisión
fuerte (>= 0.6), exit 0 si el nombre es realmente nuevo.

Qué busca:
  ~/orca/projects/*        repos por nombre y por README
  ~/orca/workspaces/*      workspaces
  ~/.hermes/skills/**      skills por nombre y descripción
  ~/conecta-agentes/       artefactos e índices
  ~/.hermes/scripts/*.py   scripts existentes
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from pathlib import Path

HOME = Path.home()
ORCA_PROJECTS = HOME / "orca" / "projects"
ORCA_WORKSPACES = HOME / "orca" / "workspaces"
SKILLS = HOME / ".hermes" / "skills"
AGENTES = HOME / "conecta-agentes"
SCRIPTS = HOME / ".hermes" / "scripts"

UMBRAL_COLISION = 0.60
UMBRAL_RELACIONADO = 0.40


def normalizar(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9áéíóúñ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def parecido(a: str, b: str) -> float:
    """Similitud por nombre y por palabras contenidas.

    El bono de "palabra compartida" de abajo sube el puntaje y era la fuente de
    falsos positivos (ver main) hasta que se exigieron DOS palabras. Mantiene un
    bono único por subconjunto ('todas mis palabras están en el candidato').
    """
    na, nb = normalizar(a), normalizar(b)
    if not na or not nb:
        return 0.0
    r = difflib.SequenceMatcher(None, na, nb).ratio()
    pa = set(na.split())
    pb = set(nb.split())
    # Todas las palabras del término están en el candidato: identificación real.
    if pa and pa <= pb:
        r = max(r, 0.85)
    # Dos o más palabras compartidas de 4+ letras también son señal real; una
    # sola no basta (era la causa de 'plot_controller' vs 'panel-control-bodega').
    comunes = {p for p in (pa & pb) if len(p) >= 4}
    if len(comunes) >= 2:
        r = max(r, 0.5 + 0.1 * len(comunes))
    return min(r, 1.0)


def es_relevante(texto: str, terminos: list[str]) -> float:
    """Aplica parecido contra todos los términos y devuelve el mejor."""
    return max((parecido(t, texto) for t in terminos), default=0.0)


# Un término es "identificador" cuando es el nombre completo que se busca, no una
# sub-palabra suelta. Solo un identificador puede producir COLISIÓN; una
# sub-palabra ('conecta', 'harness') sirve para mostrar RELACIONADOS, nunca para
# frenar. Sin esta distinción, 'auditoria-harness-conecta' frenaba contra los 259
# archivos de skills y contra todo proyecto llamado ...Conecta.
def recolectar(terminos: list[str], identificador: str | None = None) -> list[dict]:
    ident = normalizar(identificador) if identificador else None

    def relevancia(texto: str) -> tuple[float, bool]:
        """(mejor similitud, ¿la alcanzó el nombre completo?)."""
        mejor = 0.0
        por_ident = False
        for t in terminos:
            p = parecido(t, texto)
            mejor = max(mejor, p)
            if ident is not None and normalizar(t) == ident and p >= UMBRAL_COLISION:
                # Los empates exactos en el umbral (0.60) por UNA palabra común no
                # cuentan como identificación: medido, 'auditoria-harness-conecta'
                # daba 0.60 contra 'Agentes CONECTA' (solo comparten 'conecta') y
                # marcaba por_nombre_completo. Exigir estrictamente > umbral.
                por_ident = p > UMBRAL_COLISION
        return mejor, por_ident

    hallazgos: list[dict] = []

    # 1. Proyectos
    if ORCA_PROJECTS.is_dir():
        for d in sorted(ORCA_PROJECTS.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            p, por_ident = relevancia(d.name)
            if p >= UMBRAL_RELACIONADO:
                hallazgos.append({
                    "tipo": "proyecto",
                    "nombre": d.name,
                    "ruta": str(d),
                    "similitud": round(p, 2),
                    "por_nombre_completo": por_ident,
                })

    # 2. Workspaces
    if ORCA_WORKSPACES.is_dir():
        for d in sorted(ORCA_WORKSPACES.iterdir()):
            if not d.is_dir() or d.name.startswith("."):
                continue
            p, por_ident = relevancia(d.name)
            if p >= UMBRAL_RELACIONADO:
                hallazgos.append({
                    "tipo": "workspace",
                    "nombre": d.name,
                    "ruta": str(d),
                    "similitud": round(p, 2),
                    "por_nombre_completo": por_ident,
                })

    # 3. Skills (nombre + primera línea de descripción)
    if SKILLS.is_dir():
        for skill_md in SKILLS.rglob("SKILL.md"):
            nombre = skill_md.parent.name
            desc = ""
            try:
                for linea in skill_md.read_text(encoding="utf-8").split("\n")[:12]:
                    if linea.startswith("description:"):
                        desc = linea.split(":", 1)[1].strip().strip('"')
                        break
            except OSError:
                pass
            p_nombre, ident_nombre = relevancia(nombre)
            p_desc, _ = relevancia(desc) if desc else (0.0, False)
            p = max(p_nombre, p_desc * 0.9)
            if p >= UMBRAL_RELACIONADO:
                hallazgos.append({
                    "tipo": "skill",
                    "nombre": nombre,
                    "ruta": str(skill_md.parent),
                    "similitud": round(p, 2),
                    "detalle": desc[:90],
                    "por_nombre_completo": ident_nombre,
                })

    # 4. Artefactos de conecta-agentes
    if AGENTES.is_dir():
        for f in sorted(AGENTES.rglob("*")):
            if f.is_file() and f.suffix in (".json", ".jsonl", ".py", ".md"):
                p, por_ident = relevancia(f.stem)
                if p >= UMBRAL_COLISION:
                    hallazgos.append({
                        "tipo": "artefacto",
                        "nombre": f.name,
                        "ruta": str(f),
                        "similitud": round(p, 2),
                        "por_nombre_completo": por_ident,
                    })

    # 5. Scripts
    if SCRIPTS.is_dir():
        for f in sorted(SCRIPTS.glob("*")):
            if f.is_file():
                p, por_ident = relevancia(f.stem)
                if p >= UMBRAL_RELACIONADO:
                    hallazgos.append({
                        "tipo": "script",
                        "nombre": f.name,
                        "ruta": str(f),
                        "similitud": round(p, 2),
                        "por_nombre_completo": por_ident,
                    })

    # Deduplicar por ruta y ordenar
    vistos, unicos = set(), []
    for h in sorted(hallazgos, key=lambda x: -x["similitud"]):
        if h["ruta"] in vistos:
            continue
        vistos.add(h["ruta"])
        unicos.append(h)
    return unicos


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("nombre", help="lo que se quiere crear")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--terminos", nargs="*", default=[],
                    help="sinónimos a buscar además del nombre")
    args = ap.parse_args()
    identificador = args.nombre

    # El nombre se busca COMO UNIDAD contra proyectos/workspaces, y sus
    # sub-palabras NO se vuelven términos de búsqueda autónomos. Partir el
    # nombre ('auditoria-harness-conecta' → buscar 'conecta') fue el defecto
    # medido el 26-oct-2026: 'conecta' es subconjunto de casi toda skill CONECTA
    # y marcaba 0.85 contra cientos. Resultado: nombres nuevos frenaban siempre.
    #
    # Lo que SÍ aporta: los sinónimos explícitos del usuario (--terminos), que
    # son intencionales. Esos buscan como unidad, nunca como sub-palabras.
    terminos_busqueda = list(args.terminos)

    hallazgos = recolectar([identificador] + terminos_busqueda, identificador=identificador)

    # Ruido: en skills/artefactos solo mostrar lo que compite de verdad.
    # Un proyecto o workspace se muestra desde 0.40; una skill, desde 0.62.
    def ruido(h: dict) -> bool:
        if h["tipo"] in ("skill", "artefacto", "script"):
            return h["similitud"] < 0.62
        return False

    hallazgos = [h for h in hallazgos if not ruido(h)]

    if args.json:
        print(json.dumps(hallazgos, ensure_ascii=False, indent=1))
    else:
        print(f"Buscando: {args.nombre!r}")
        if hallazgos:
            agrupados: dict[str, list[dict]] = {}
            for h in hallazgos:
                agrupados.setdefault(h["tipo"], []).append(h)
            print()
            for tipo in ("proyecto", "workspace", "skill", "artefacto", "script"):
                if tipo not in agrupados:
                    continue
                print(f"── {tipo.upper()}S ──")
                for h in agrupados[tipo]:
                    # La etiqueta va alineada con lo que frena: una colisión real
                    # es la alcanzada por el nombre completo, no por una palabra
                    # suelta. Antes el display decía COLISION por similitud >= 0.6
                    # y el FRENO por por_nombre_completo, y discrepaban.
                    es_colision = h.get("por_nombre_completo") and h["similitud"] >= UMBRAL_COLISION
                    marca = "COLISION" if es_colision else "relacionado"
                    print(f"  [{marca:11s}] {h['similitud']:.2f}  {h['nombre']}")
                    if h.get("detalle"):
                        print(f"                 {h['detalle']}")
                print()
        else:
            print("  (nada parecido)")

    # Una COLISIÓN frena; un "relacionado" se informa y no frena. Solo el nombre
    # completo puede producir colisión (ver recolectar()).
    colisiones = [h for h in hallazgos
                  if h["similitud"] >= UMBRAL_COLISION and h.get("por_nombre_completo")]
    relacionados = [h for h in hallazgos
                    if not (h["similitud"] >= UMBRAL_COLISION and h.get("por_nombre_completo"))]

    if colisiones:
        print(f"FRENO: {len(colisiones)} coincidencia(s) fuerte(s) con el nuevo nombre.")
        print("Antes de crear algo nuevo, mirar el proyecto que ya existe:")
        for h in colisiones[:3]:
            print(f"   [{h['tipo']}] {h['nombre']}  ({h['similitud']:.2f})")
            print(f"   ls {h['ruta']}")
        print("Si de verdad es distinto, seguir y decir en qué se diferencia.")
        return 1

    if relacionados:
        print(f"(sin colisión fuerte; {len(relacionados)} relacionado(s) informados arriba)")
    print("Sin colisión fuerte. Se puede crear.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
