#!/usr/bin/env python3
"""Verifica que un perfil Hermes se pueda publicar sin filtrar datos de cliente.

Uso:
    verificar_privacidad_perfil.py <ruta-perfil>          # audita y lista
    verificar_privacidad_perfil.py <ruta-perfil> --json   # salida maquina

Sale 0 si NO hay hallazgos bloqueantes, 1 si los hay.

Por que existe: los perfiles comerciales de CONECTA (SOUL.md, memoria, skills)
contienen nombres de clientes, montos, rutas internas y modelos. Un repo PUBLICO
con eso encima es una fuga. La regla en prosa no alcanza: este script es la regla.

Niveles:
  BLOQUEA  el patron aparece fuera de un lugar permitido -> no publicar
  AVISO    aparece en un archivo declarado como interno -> verificar a mano

Stdlib puro (Python 3.9+). No importa nada de hermes-agent a proposito: el arnes
viaja con el perfil a otros entornos.
"""

import argparse
import json
import os
import re
import sys

# --- reglas de datos de cliente / casa -------------------------------------
# (nombre, regex, descripcion)
BLOQUEANTES = [
    ("cliente-chileno",
     r"\b(Transelec|CGE|Enel|Colb[uú]n|AES Andes|Codelco|Escondida|BHP|SQM|"
     r"Antofagasta Minerals|Centinela|Chilquinta|SAESA|Frontel|Guacolda|"
     r"Arauco|CMPC|Cemento Mel[oó]n|Mel[oó]n|Pampa Camarones|ENAPAC|"
     r"Comasa|Agrosuper|Carozzi|Sopraval|Watts|CCU)\b",
     "nombre de cliente real de CONECTA"),
    ("rut-chileno",
     r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b",
     "RUT de persona o empresa"),
    ("monto-clp",
     r"\b\d{1,3}(?:\.\d{3}){2,}\b",
     "cifra con separador de miles (posible monto)"),
    ("correo-persona",
     r"\b[A-Za-z0-9._%+-]+@(?!example\.|acme\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
     "correo electronico"),
    ("telefono-cl",
     r"(?:\+?56\s?)?9\s?\d{4}\s?\d{4}\b",
     "celular chileno"),
    ("ruta-mac-usuario",
     r"/Users/[a-z][a-z0-9._-]+/",
     "ruta absoluta del Mac (revela estructura interna)"),
    ("ip-privada",
     r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}|"
     r"192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b",
     "IP privada / Tailscale (infra de Victor)"),
    ("api-key",
     r"\b(?:sk-[A-Za-z0-9]{20,}|gho_[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,}|"
     r"AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,})\b",
     "credencial con formato de API key"),
]

AVISOS = [
    ("tarifa-hh",
     r"\b(?:HH|UF|UTM)\b\s*[:=]?\s*\d",
     "tarifa o valor economico (politica interna)"),
    ("margen",
     r"\bmargen\b[^\n]{0,40}\d+\s?%",
     "margen interno"),
    ("nombre-persona-conecta",
     r"\b(Catal[aá]n|Travaglini|Camoglino|Quintanilla|Fuentealba|Travaglini|"
     r"Urra|C[aá]rdenas|Vilche|Etcheberry|Pe[nñ]a|M[aá]rquez|Medina|Arenas)\b",
     "nombre de persona del equipo"),
]

# --- lugares permitidos por nombre de archivo -------------------------------
# Los .example no son secretos: son plantillas. Pero IGUAL se auditan con AVISOS.
PLANTILLAS = re.compile(r"\.(example|template|sample)$", re.I)
BINARIOS = re.compile(r"\.(png|jpg|jpeg|gif|pdf|zip|npy|faiss|db|pyc|so|dylib)$", re.I)
IGNORAR_DIRS = {".git", "__pycache__", "node_modules", "vendor", ".venv", "venv",
                "sessions", "logs", "cache", "sessions_archived"}


def archivos_texto(raiz):
    for dirpath, dirnames, filenames in os.walk(raiz):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR_DIRS]
        for f in filenames:
            p = os.path.join(dirpath, f)
            if BINARIOS.search(f):
                continue
            try:
                with open(p, "r", encoding="utf-8", errors="ignore") as fh:
                    yield p, fh.read()
            except OSError:
                continue


def auditar(raiz):
    bloqueos, avisos = [], []
    total = 0
    for ruta, texto in archivos_texto(raiz):
        total += 1
        rel = os.path.relpath(ruta, raiz)
        plantilla = bool(PLANTILLAS.search(rel))
        lineas = texto.splitlines()
        for nombre, patron, desc in BLOQUEANTES:
            if plantilla:
                continue  # una plantilla puede llevar <TU_RUT> y DEMO_USER
            for i, linea in enumerate(lineas, 1):
                if re.search(patron, linea):
                    bloqueos.append({
                        "archivo": rel, "linea": i, "regla": nombre,
                        "descripcion": desc, "muestra": linea.strip()[:120],
                    })
        for nombre, patron, desc in AVISOS:
            for i, linea in enumerate(lineas, 1):
                if re.search(patron, linea):
                    avisos.append({
                        "archivo": rel, "linea": i, "regla": nombre,
                        "descripcion": desc, "muestra": linea.strip()[:120],
                    })
    return total, bloqueos, avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("perfil")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--max-por-regla", type=int, default=5)
    a = ap.parse_args()

    raiz = os.path.abspath(os.path.expanduser(a.perfil))
    if not os.path.isdir(raiz):
        print("ERROR: no existe el directorio %s" % raiz)
        return 2

    total, bloqueos, avisos = auditar(raiz)

    if a.json:
        print(json.dumps({"archivos": total, "bloqueos": bloqueos,
                          "avisos": avisos}, ensure_ascii=False, indent=1))
        return 1 if bloqueos else 0

    print("Perfil: %s" % raiz)
    print("Archivos de texto revisados: %d" % total)

    if bloqueos:
        print("\n== BLOQUEANTES (%d) — NO PUBLICAR ==" % len(bloqueos))
        por_regla = {}
        for b in bloqueos:
            por_regla.setdefault(b["regla"], []).append(b)
        for regla, items in por_regla.items():
            print("  %s (%s): %d hallazgo(s)" % (regla, items[0]["descripcion"], len(items)))
            for it in items[:a.max_por_regla]:
                print("    %s:%d  %s" % (it["archivo"], it["linea"], it["muestra"]))
            if len(items) > a.max_por_regla:
                print("    ... %d mas (usar --json para la lista completa)"
                      % (len(items) - a.max_por_regla))
    if avisos:
        print("\n== AVISOS (%d) — revisar a mano ==" % len(avisos))
        por_regla = {}
        for b in avisos:
            por_regla.setdefault(b["regla"], []).append(b)
        for regla, items in por_regla.items():
            print("  %s (%s): %d" % (regla, items[0]["descripcion"], len(items)))
            for it in items[:a.max_por_regla]:
                print("    %s:%d  %s" % (it["archivo"], it["linea"], it["muestra"]))

    if bloqueos:
        print("\nRESULTADO: BLOQUEADO. Limpiar los bloqueantes antes de publicar.")
        return 1
    print("\nRESULTADO: sin bloqueantes. Revisar los avisos y seguir.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
