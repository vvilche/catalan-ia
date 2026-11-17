#!/usr/bin/env python
"""Avisa cuando la ventana de contexto de la sesion activa supera el umbral (default 35%).

Mide el TAMANO REAL de la ventana sumando los caracteres de los mensajes activos
de la sesion (la columna token_count viene vacia en esta version de Hermes), y
estima tokens con chars/3.5.

Al superar el umbral:
  1. verifica que el hook de parada exista y sea reciente,
  2. avisa en pantalla que hay que reiniciar.

NO reinicia la sesion. El reinicio lo ejecuta el usuario con /new.
Si el agente se reiniciara solo, lo haria mientras escribe el hook y perderia
justo lo que quiere salvar.

Uso:
    python check_contexto.py               # mide y avisa
    python check_contexto.py --estado      # solo el numero
    python check_contexto.py --umbral 50   # otro umbral
    python check_contexto.py --hook <ruta> # otro hook

Salida: 0 bajo el umbral · 10 superado (permite encadenar en un alias/prompt).
"""
import argparse
import os
import sqlite3
import sys
import time

STATE_DB = os.path.expanduser("~/.hermes/state.db")
HOOK_DEFAULT = os.path.expanduser(
    "~/orca/projects/InstrumentacionTipoGuacolda/PUNTO_DE_PARADA.md")

# tokens por caracter: ~3.5 chars/token es la razon medida en trazas en espanol
CHARS_POR_TOKEN = 3.5
VENTANA_DEFAULT = 128_000


def ventana_activa(umbral_viejo=None):
    """(session_id, chars, tokens_estimados, ventana) de la sesion mas reciente."""
    con = sqlite3.connect(f"file:{STATE_DB}?mode=ro", uri=True, timeout=5)
    con.row_factory = sqlite3.Row
    row = con.execute("""
        SELECT session_id, SUM(LENGTH(COALESCE(content,''))) AS chars,
               MAX(timestamp) AS ultimo
        FROM messages
        WHERE active = 1
        GROUP BY session_id
        ORDER BY ultimo DESC
        LIMIT 1
    """).fetchone()
    if not row:
        con.close()
        return None
    sid = row["session_id"]
    chars = int(row["chars"] or 0)
    # ventana segun el modelo usado en esa sesion
    modelo = ""
    m = con.execute("""
        SELECT model FROM session_model_usage
        WHERE session_id = ? ORDER BY last_seen DESC LIMIT 1
    """, (sid,)).fetchone()
    if m:
        modelo = m["model"] or ""
    con.close()
    ventanas = {"deepseek": 128_000, "claude": 200_000, "gpt-5": 400_000, "kimi": 128_000}
    ventana = VENTANA_DEFAULT
    for clave, v in ventanas.items():
        if clave in modelo.lower():
            ventana = v
            break
    tokens = chars / CHARS_POR_TOKEN
    return sid, modelo, chars, tokens, ventana


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--umbral", type=float, default=35.0)
    ap.add_argument("--estado", action="store_true")
    ap.add_argument("--hook", default=HOOK_DEFAULT)
    args = ap.parse_args()

    if not os.path.exists(STATE_DB):
        print(f"No existe {STATE_DB}")
        return 0
    datos = ventana_activa()
    if not datos:
        print("No se pudo leer ninguna sesion activa.")
        return 0
    sid, modelo, chars, tokens, ventana = datos
    pct = 100.0 * tokens / ventana

    lleno = int(30 * min(pct, 100) / 100)
    barra = "#" * lleno + "." * (30 - lleno)

    print(f"Sesion : {sid}")
    print(f"Modelo : {modelo or '(desconocido)'}   ventana {ventana:,} tokens")
    print(f"Uso    : {tokens:,.0f} tokens  [{barra}] {pct:.1f}%")
    print(f"Umbral : {args.umbral:.0f}%")

    if args.estado:
        return 0

    if pct < args.umbral:
        print(f"\nOK. Margen hasta el {args.umbral:.0f}%: "
              f"{max(0, args.umbral*ventana/100 - tokens):,.0f} tokens.")
        return 0

    print()
    print("=" * 68)
    print(f"  LLEGASTE AL {pct:.0f}% DE LA VENTANA (umbral {args.umbral:.0f}%)")
    print("=" * 68)
    if os.path.exists(args.hook):
        edad_min = (time.time() - os.path.getmtime(args.hook)) / 60
        print(f"  Hook de parada : {args.hook}")
        print(f"  Actualizado    : hace {edad_min:.0f} min")
        if edad_min > 60:
            print("  AVISO: el hook tiene mas de 1 hora. ACTUALIZALO antes de reiniciar.")
        else:
            print("  El hook esta fresco. Podes reiniciar.")
    else:
        print(f"  FALTA el hook de parada: {args.hook}")
        print("  Escribilo ANTES de reiniciar o perdes el estado de la tarea.")
    print()
    print("  REINICIAR AHORA ->  escribe:  /new")
    print("  (el agente no puede reiniciarse solo: /new lo ejecuta el usuario)")
    print("=" * 68)
    return 10


if __name__ == "__main__":
    sys.exit(main())
