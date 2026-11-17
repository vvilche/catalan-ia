#!/usr/bin/env python3
"""
editar_seguro.py — edita un archivo SIN fallar por contenido desactualizado.

El problema que resuelve: intento un patch con un texto que creía que estaba en
el archivo, pero el archivo cambió (por mí mismo hace 10 minutos, o por otra
sesión) y el patch falla. Repetir el patch con el texto viejo falla otra vez.

Qué hace distinto:
  1. Lee el archivo FRESCO en este momento, nunca de memoria.
  2. Localiza el ancla por coincidencia difusa (normaliza espacios y comillas).
  3. Si no encuentra el ancla, dice dónde está lo más parecido — no falla a ciegas.
  4. Guarda un respaldo con fecha antes de escribir.
  5. Verifica que el cambio entró, releyendo.

Uso:
  editar_seguro.py <archivo> --ancla "texto a buscar" --nuevo "texto nuevo"
  editar_seguro.py <archivo> --ancla "..." --nuevo "..." --seccion "## Pitfalls"
  editar_seguro.py <archivo> --buscar "texto"      # solo muestra donde está

Exit 0 si editó, 1 si no encontró el ancla (con sugerencias).
"""

from __future__ import annotations

import argparse
import difflib
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path


def normalizar(s: str) -> str:
    """Normaliza para comparar: espacios, comillas, guiones."""
    s = s.replace("\u00a0", " ")
    s = re.sub(r"[“”‘’]", '"', s)
    s = re.sub(r"[–—]", "-", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def leer_fresco(ruta: Path) -> str:
    """Siempre del disco, con su mtime para detectar cambios."""
    return ruta.read_text(encoding="utf-8")


def buscar_ancla(texto: str, ancla: str) -> tuple[int, int, float]:
    """
    Devuelve (inicio, fin, confianza). Confianza 1.0 = exacta.
    Si no encuentra, devuelve (-1, -1, 0).
    """
    # 1. Exacta
    idx = texto.find(ancla)
    if idx >= 0:
        return idx, idx + len(ancla), 1.0

    # 2. Normalizada (una sola línea, espacios colapsados)
    tn = normalizar(texto)
    an = normalizar(ancla)
    idx_n = tn.find(an)
    if idx_n >= 0:
        # Mapear de vuelta aproximando por conteo de líneas
        antes = tn[:idx_n]
        # buscar el bloque en el original por su primera y última palabra
        primera = an.split()[0] if an.split() else ""
        ultima = an.split()[-1] if an.split() else ""
        m1 = re.search(re.escape(primera), texto)
        if m1:
            # intentar crecer desde ahí hasta cubrir la longitud
            largo_aprox = len(an) + abs(len(an) - len(ancla)) + 40
            ini = m1.start()
            frag = texto[ini:ini + largo_aprox + 200]
            m2 = frag.rfind(ultima)
            fin = ini + m2 + len(ultima) if m2 >= 0 else ini + largo_aprox
            return ini, fin, 0.8

    # 3. Línea por línea con difflib: la mejor coincidencia
    lineas = texto.split("\n")
    anc_lines = ancla.split("\n")
    mejor, mejor_ratio = -1, 0.0
    for i in range(len(lineas)):
        bloque = "\n".join(lineas[i:i + len(anc_lines)])
        r = difflib.SequenceMatcher(None, normalizar(bloque),
                                    normalizar(ancla)).ratio()
        if r > mejor_ratio:
            mejor_ratio, mejor = r, i
    if mejor_ratio > 0.72:
        ini = len("\n".join(lineas[:mejor])) + (1 if mejor else 0)
        fin = ini + len("\n".join(lineas[mejor:mejor + len(anc_lines)]))
        return ini, fin, mejor_ratio

    return -1, -1, mejor_ratio


def sugerir(texto: str, ancla: str, n: int = 3) -> list[str]:
    """Muestra lo más parecido al ancla, para corregirla sin adivinar."""
    palabras = [p for p in re.findall(r"\w{4,}", ancla)][:6]
    if not palabras:
        return []
    lineas = texto.split("\n")
    puntajes = []
    for i, ln in enumerate(lineas):
        if all(p.lower() in ln.lower() for p in palabras[:2]):
            puntajes.append((i + 1, ln.strip()[:140]))
    return [f"  línea {n}: {t}" for n, t in puntajes[:n]]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("archivo")
    ap.add_argument("--ancla", default=None)
    ap.add_argument("--nuevo", default=None)
    ap.add_argument("--buscar", default=None, help="solo muestra coincidencias")
    ap.add_argument("--seccion", default=None, help="restringe la búsqueda a una sección")
    ap.add_argument("--sin-respaldo", action="store_true")
    args = ap.parse_args()

    ruta = Path(os.path.expanduser(args.archivo))
    if not ruta.exists():
        print(f"NO EXISTE: {ruta}")
        return 2

    texto = leer_fresco(ruta)
    mtime = datetime.fromtimestamp(ruta.stat().st_mtime)
    print(f"archivo: {ruta}")
    print(f"leído fresco: {len(texto):,} chars, última modificación {mtime:%Y-%m-%d %H:%M:%S}")

    # Modo buscar
    if args.buscar:
        idx, fin, conf = buscar_ancla(texto, args.buscar)
        if idx < 0:
            print(f"\nNO encontrado (confianza {conf:.2f}). Candidatos:")
            for s in sugerir(texto, args.buscar):
                print(s)
            return 1
        print(f"\nENCONTRADO (confianza {conf:.2f}) en offset {idx}:")
        print("─" * 60)
        print(texto[max(0, idx - 100):fin + 100])
        print("─" * 60)
        return 0

    if not args.ancla or args.nuevo is None:
        print("Falta --ancla y --nuevo")
        return 2

    # Restringir a una sección si se pidió
    base = 0
    objetivo = texto
    if args.seccion:
        s_idx = texto.find(args.seccion)
        if s_idx < 0:
            print(f"\nNO encuentro la sección '{args.seccion}'")
            return 1
        # hasta la próxima sección del mismo nivel
        nivel = len(args.seccion) - len(args.seccion.lstrip("#"))
        siguiente = texto.find("\n" + "#" * nivel + " ", s_idx + 1)
        fin_sec = siguiente if siguiente > 0 else len(texto)
        objetivo = texto[s_idx:fin_sec]
        base = s_idx
        print(f"restringido a sección: {args.seccion} ({len(objetivo)} chars)")

    idx, fin, conf = buscar_ancla(objetivo, args.ancla)

    if idx < 0:
        print(f"\nANCLA NO ENCONTRADA (mejor similitud {conf:.2f} < 0.72)")
        print("No se modificó nada. Candidatos parecidos:")
        for s in sugerir(objetivo, args.ancla):
            print(s)
        print("\nRelee la sección y usa --ancla con el texto real.")
        return 1

    idx += base
    fin += base

    if conf < 1.0:
        print(f"\ncoincidencia difusa ({conf:.2f}). Fragmento que se reemplazará:")
        print("─" * 60)
        print(texto[idx:fin])
        print("─" * 60)

    nuevo_texto = texto[:idx] + args.nuevo + texto[fin:]

    # Respaldo
    if not args.sin_respaldo:
        marca = datetime.now().strftime("%Y%m%d_%H%M%S")
        resp = ruta.with_suffix(ruta.suffix + f".bak-{marca}")
        shutil.copy2(ruta, resp)
        print(f"respaldo: {resp.name}")

    ruta.write_text(nuevo_texto, encoding="utf-8")

    # Verificar releyendo
    releido = leer_fresco(ruta)
    if args.nuevo.strip() and args.nuevo.strip() not in releido:
        print("\nADVERTENCIA: el texto nuevo no aparece literal al releer.")
        print("El archivo se escribió pero conviene revisarlo.")
        return 1

    print(f"OK: {len(texto):,} → {len(releido):,} chars "
          f"({len(releido) - len(texto):+d})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
