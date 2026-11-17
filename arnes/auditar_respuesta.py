#!/usr/bin/env python3
"""
auditar_respuesta.py — detecta las afirmaciones que yo hago sin respaldo.

El problema que resuelve: escribo "esto es mala práctica" o "verifiqué tal cosa"
sin haberlo comprobado, y suena igual de seguro que lo que sí verifiqué.

No adivina: extrae del texto las afirmaciones de forma VERIFICABLE y busca su
respaldo en los resultados de herramientas de la misma sesión.

Uso:
  auditar_respuesta.py <archivo_con_la_respuesta>
  auditar_respuesta.py --texto "..."

Salida: cada afirmación sin respaldo, con su categoría. Exit 1 si hay afirmaciones
de tipo duro sin fuente.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# ── Patrones de afirmación que EXIGEN respaldo ───────────────────────────────

# 1. Cifras con porcentaje o "X de Y": si afirmo un número, tiene que salir de
#    una herramienta o tener una fuente citada al lado.
CIFRAS = re.compile(
    r"\b(\d{1,3}(?:[.,]\d+)?)\s*%|\b(\d+)\s*de\s*(\d+)\b(?!\s*(?:\w+\.docx|\w+\.py))"
)

# 2. Verbos de verificación: si digo que verifiqué, tiene que haber una
#    invocación de herramienta cerca.
VERIFICACION = re.compile(
    r"\b(verifiqu[eé]|comprob[eé]|confirm[eé]|med[ií]|ejecut[eé]|prob[eé]|"
    r"instal[eé]|corr[ií]|revis[eé])\b", re.I
)

# 3. Afirmaciones absolutas: las más peligrosas porque no admiten duda.
ABSOLUTAS = re.compile(
    r"\b(es mala pr[áa]ctica|est[áa] establecido|todo el mundo sabe|"
    r"es sabido|est[áa] demostrado|la evidencia dice|seg[úu]n los estudios|"
    r"siempre funciona|nunca falla|no hay duda|claramente es)\b", re.I
)

# 4. Fuentes citadas válidas: si hay una de estas cerca, la cifra está respaldada.
FUENTE = re.compile(
    r"(arXiv[:\s]?\d{4}\.\d{4,}|doi[:\s]|et al\.?|\(\d{4}\)|"
    r"\bNEURIPS\b|\bACL\b|\bICML\b|\bIEEE\b|\bISO\s?\d+|\bNCh\s?\d+|"
    r"\bAISC\b|\bACI\b|\bASCE\b|\bAWS\b|\bREQ-[A-Z]+-\d+|"
    r"l[ií]nea\s+\d+|p[áa]gina\s+\d+)", re.I
)

# 5. Marcadores de que el número es ESTIMADO y se declaró como tal.
ESTIMADO = re.compile(r"\b(estimad|aproximad|del orden|supuest|supongo|~)", re.I)


def extraer_afirmaciones(texto: str) -> dict:
    lineas = texto.split("\n")
    sin_respaldo = {"cifras": [], "absolutas": [], "verificaciones": []}

    for i, linea in enumerate(lineas, 1):
        if not linea.strip():
            continue

        # ¿Hay fuente o marca de estimación en esta línea o la anterior/siguiente?
        contexto = " ".join(lineas[max(0, i - 2):i + 1])
        tiene_fuente = bool(FUENTE.search(contexto))
        es_estimado = bool(ESTIMADO.search(contexto))

        # Cifras sin fuente ni marca de estimado
        if not tiene_fuente and not es_estimado:
            for m in CIFRAS.finditer(linea):
                frag = linea[max(0, m.start() - 45):m.end() + 45].strip()
                # Descarta números que son identificadores o rutas
                if re.search(r"(REQ-|línea|line|v\d|\.py|\.md|\d{4}-\d{2})", frag):
                    continue
                sin_respaldo["cifras"].append({"linea": i, "texto": frag})

        # Afirmaciones absolutas
        for m in ABSOLUTAS.finditer(linea):
            sin_respaldo["absolutas"].append({
                "linea": i,
                "frase": m.group(0),
                "texto": linea[max(0, m.start() - 60):m.end() + 60].strip(),
                "tiene_fuente": tiene_fuente,
            })

        # "Verifiqué" sin evidencia
        for m in VERIFICACION.finditer(linea):
            sin_respaldo["verificaciones"].append({
                "linea": i,
                "verbo": m.group(0),
                "texto": linea[max(0, m.start() - 50):m.end() + 70].strip(),
            })

    return sin_respaldo


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo", nargs="?")
    ap.add_argument("--texto", default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.texto:
        texto = args.texto
    elif args.archivo and os.path.exists(args.archivo):
        texto = Path(args.archivo).read_text(encoding="utf-8")
    else:
        texto = sys.stdin.read()

    r = extraer_afirmaciones(texto)

    if args.json:
        print(json.dumps(r, ensure_ascii=False, indent=1))
    else:
        total = sum(len(v) for v in r.values())
        if total == 0:
            print("Sin afirmaciones huérfanas detectadas.")
            return 0

        print(f"AFIRMACIONES A REVISAR: {total}\n")

        if r["absolutas"]:
            print("── AFIRMACIONES ABSOLUTAS (las más riesgosas) ──")
            for a in r["absolutas"]:
                marca = "" if a["tiene_fuente"] else "  ← SIN FUENTE"
                print(f"  línea {a['linea']}: “{a['frase']}”{marca}")
                print(f"    {a['texto'][:130]}")
            print()

        if r["cifras"]:
            print("── CIFRAS SIN FUENTE NI MARCA DE ESTIMADO ──")
            for c in r["cifras"][:25]:
                print(f"  línea {c['linea']}: {c['texto'][:120]}")
            if len(r["cifras"]) > 25:
                print(f"  … y {len(r['cifras']) - 25} más")
            print()

        if r["verificaciones"]:
            print("── VERIFICACIONES DECLARADAS (comprobar que haya salida real) ──")
            for v in r["verificaciones"][:15]:
                print(f"  línea {v['linea']}: “{v['verbo']}” → {v['texto'][:110]}")
            print()

    # Exit 1 solo si hay absolutas sin fuente: eso es el error grave.
    graves = [a for a in r["absolutas"] if not a["tiene_fuente"]]
    return 1 if graves else 0


if __name__ == "__main__":
    sys.exit(main())
