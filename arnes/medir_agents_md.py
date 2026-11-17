#!/usr/bin/env python3
"""Mide que AGENTS.md llegan VIVOS al agente para un directorio dado.

Pregunta que responde: de todos los AGENTS.md que hay en el arbol, cuales
suman reglas y cuales quedaron tapados por otro de mas arriba.

Uso:  python medir_agents_md.py <directorio>   [--json]

Sale 0 si todo lo encontrado en el path suma (concatenacion), 1 si detecta
que algun archivo quedo tapado (primer-encontrado-gana).
"""
import json
import os
import sys

# Nombres que Hermes mira, en el orden de prioridad DENTRO de un directorio
# (el primero no vacío gana). De acá sale tanto el barrido como el desempate.
NOMBRES = ["AGENTS.override.md", "AGENTS.md", "agents.md"]
EXTRA = ["CLAUDE.md", "HERMES.md"]


def ancestros(path):
    """Del raiz al directorio, en orden."""
    path = os.path.abspath(path)
    partes = []
    while True:
        partes.append(path)
        padre = os.path.dirname(path)
        if padre == path:
            break
        path = padre
    return list(reversed(partes))


def medir(objetivo):
    """Qué archivos de contexto llegan VIVOS al agente para este directorio.

    Hermes CONCATENA la cadena de directorios (prompt_builder.py:1804, "merged
    directory chain"): de la raíz al cwd, cada directorio aporta el suyo. Por eso
    un AGENTS.md en un ancestro NO queda tapado por uno más abajo. El único
    solapamiento real es DENTRO del mismo directorio, donde gana el de mayor
    prioridad en NOMBRES (el primero no vacío).
    """
    cadena = ancestros(objetivo)
    presentes = []
    vistos = set()  # (st_dev, st_ino): macOS es case-insensitive, agents.md y
    # AGENTS.md pueden ser el MISMO archivo. Deduplicar por inodo, no por nombre.
    for d in cadena:
        for n in NOMBRES:
            p = os.path.join(d, n)
            if not os.path.isfile(p):
                continue
            st = os.stat(p)
            clave = (st.st_dev, st.st_ino)
            if clave in vistos:
                continue
            vistos.add(clave)
            presentes.append({"ruta": p, "dir": d, "nombre": n, "bytes": st.st_size})
    # Aviso aparte: mismos nombres en otra jerarquía que Hermes NO lee acá.
    ausentes = [os.path.join(d, n) for d in cadena for n in EXTRA
                if os.path.isfile(os.path.join(d, n))]
    por_dir = {}
    for item in presentes:
        por_dir.setdefault(item["dir"], []).append(item)
    orden = {n: i for i, n in enumerate(NOMBRES)}
    tapados = [i for items in por_dir.values() if len(items) > 1
               for i in sorted(items, key=lambda x: orden[x["nombre"]])[1:]]
    return {
        "objetivo": os.path.abspath(objetivo),
        "profundidad": len(cadena),
        "presentes": presentes,
        "tapados_si_primer_gana": tapados,
        "otros_formatos_no_leidos": ausentes,
        "total_bytes": sum(p["bytes"] for p in presentes),
    }


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print("uso: medir_agents_md.py <directorio> [--json]", file=sys.stderr)
        return 2
    r = medir(args[0])
    # exit coherente en ambos modos: 1 si cero reglas o si hay solape por nombre.
    code = 1 if (not r["presentes"] or r["tapados_si_primer_gana"]) else 0
    if "--json" in sys.argv:
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return code
    print(f"AGENTS.md VIVOS — {r['objetivo']}")
    print(f"Anidamiento: {r['profundidad']} niveles hasta la raiz\n")
    if not r["presentes"]:
        print("  (ninguno) — Hermes carga CERO reglas de proyecto acá")
    else:
        print(f"{'nivel':<6} {'bytes':>7}  ruta")
        for i, p in enumerate(r["presentes"], 1):
            print(f"{i:<6} {p['bytes']:>7}  {p['ruta']}")
        print(f"\nTotal: {len(r['presentes'])} archivo(s), {r['total_bytes']} bytes")
    if r["tapados_si_primer_gana"]:
        print("\nMismo directorio, varios nombres: gana el de mayor prioridad.")
        print("Estos NO llegan:")
        for p in r["tapados_si_primer_gana"]:
            print(f"  TAPADO  {p['ruta']} ({p['bytes']} bytes)")
    for p in r["otros_formatos_no_leidos"]:
        print(f"  AVISO   {p} existe pero Hermes no lo lee si ya hay AGENTS.md")
    return code


if __name__ == "__main__":
    sys.exit(main())
