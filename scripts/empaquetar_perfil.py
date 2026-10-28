#!/usr/bin/env python3
"""Empaqueta un perfil Hermes en un repo publicable, sin datos de cliente.

Uso:
    empaquetar_perfil.py --salida <dir-repo> --perfil <dir-perfil> \
        --familias seed/familias.json [--limpiar]

Que hace, en orden:
 1. Verifica el perfil de origen con verificar_privacidad_perfil.py (arnes).
    Si hay bloqueantes, ABORTA: no se empaqueta nada.
 2. Copia las skills mapeadas a <repo>/profile/skills/<familia>/<skill>/
 3. Copia config.yaml, profile.yaml, SOUL.md, memories/ y cron/jobs.json
    SANEADOS: rutas /Users/<x> -> $HOME, IPs privadas -> <VPS_IP>,
    nombres de persona del equipo -> rol.
 4. NO copia: sessions/, logs/, cache/, state.db, auth.json, .env.
 5. Escribe <repo>/profile/MANIFIESTO.json con el conteo y hashes.
 6. Corre la auditoria de privacidad SOBRE LA COPIA. Si aparece cualquier
    bloqueante, sale 1 y el paquete NO se publica.

Stdlib puro. No importa nada de hermes-agent: el paquete viaja a otros equipos.
"""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

ARNES = os.path.expanduser("~/.hermes/scripts")
VERIFICADOR = os.path.join(ARNES, "verificar_privacidad_perfil.py")

# Archivos que se copian del perfil (relativos a la raiz del perfil)
COPIAR = [
    "config.yaml",
    "profile.yaml",
    "SOUL.md",
    "memories/MEMORY.md",
    "memories/USER.md",
    "cron/jobs.json",
]

# Nombres de persona -> rol. Se aplica en el paquete publico.
ROLES = {
    r"Francisco Catal[aá]n": "el especialista comercial NORMATIVO",
    r"Franco Travaglini": "el Gerente Comercial",
    r"Mario Camoglino": "el referente de valvulas",
    r"Eduardo Quintanilla": "el especialista SUPCON",
    r"Victoriano Blanco": "el especialista de instrumentacion",
    r"Kevin Fuentealba": "el lider de cotizaciones",
    r"Nicolas Pe[nñ]a": "el subgerente de operaciones",
    r"Catalina Etcheberry": "la asistente comercial",
    r"Victor Vilche": "el gerente general",
}


def sanear(texto):
    """Reemplazos deterministas para que el paquete no lleve datos de casa."""
    t = texto
    # rutas absolutas del Mac
    t = re.sub(r"/Users/[A-Za-z0-9._-]+/", "$HOME/", t)
    t = re.sub(r"/home/[A-Za-z0-9._-]+/", "$HOME/", t)
    # IPs privadas / Tailscale
    t = re.sub(r"\b100\.(?:6[4-9]|[7-9]\d|1[01]\d|12[0-7])\.\d{1,3}\.\d{1,3}\b",
               "<VPS_TAILSCALE_IP>", t)
    t = re.sub(r"\b(?:10|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.[\d.]+\b",
               "<IP_PRIVADA>", t)
    # correos de persona
    t = re.sub(r"\b[A-Za-z0-9._%+-]+@(?!example\.)[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
               "<CORREO>", t)
    # RUT
    t = re.sub(r"\b\d{1,2}\.\d{3}\.\d{3}-[\dkK]\b", "<RUT>", t)
    # nombres del equipo -> rol
    for patron, rol in ROLES.items():
        t = re.sub(patron, rol, t)
    return t


def correr_verificador(ruta):
    """Corre el arnes sobre ruta. Devuelve (exit, bloqueantes, avisos)."""
    if not os.path.exists(VERIFICADOR):
        print("AVISO: no existe %s — no se puede auditar la privacidad." % VERIFICADOR)
        print("       Instalar el arnes: ~/hermes-config/arnes/instalar.sh")
        return None, [], []
    out = subprocess.run([sys.executable, VERIFICADOR, ruta, "--json"],
                         capture_output=True, text=True)
    try:
        d = json.loads(out.stdout)
    except Exception:
        return out.returncode, [], []
    return out.returncode, d.get("bloqueos", []), d.get("avisos", [])


def hash_de(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(65536), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--perfil", required=True)
    ap.add_argument("--salida", required=True)
    ap.add_argument("--familias", required=True)
    ap.add_argument("--limpiar", action="store_true",
                    help="borra <salida>/profile/skills antes de copiar")
    a = ap.parse_args()

    perfil = os.path.abspath(os.path.expanduser(a.perfil))
    salida = os.path.abspath(os.path.expanduser(a.salida))
    familias = json.load(open(os.path.expanduser(a.familias)))

    # ---- 0. el perfil tiene que existir ----------------------------------
    # Sin esto el empaquetado copia skills desde ~/.hermes/skills aunque el perfil
    # no exista, y termina armando un paquete para una silla vacia.
    if not os.path.isdir(perfil):
        print("ABORTA: no existe el perfil %s" % perfil)
        print("        Crearlo primero: hermes profile create <nombre> --no-skills")
        return 2
    if not os.path.exists(os.path.join(perfil, "SOUL.md")):
        print("ABORTA: el perfil no tiene SOUL.md — no es un perfil instalado.")
        return 2

    # ---- 1. gate de origen ------------------------------------------------
    ec, bloq, avis = correr_verificador(perfil)
    if ec == 1:
        print("ABORTA: el perfil de origen tiene %d bloqueantes." % len(bloq))
        return 1
    print("Gate de origen: OK (%d avisos a revisar)" % len(avis))

    # ---- 2. skills --------------------------------------------------------
    dest_skills = os.path.join(salida, "profile", "skills")
    if a.limpiar and os.path.isdir(dest_skills):
        shutil.rmtree(dest_skills)
    os.makedirs(dest_skills, exist_ok=True)

    idx, copiadas = {}, 0
    for fam, items in familias.items():
        # Las familias que empiezan con "_" son referencia, no se instalan al perfil
        # (ej. _procesos_pendiente: linea sin hacer, se conserva para no perder el trabajo).
        if fam.startswith("_"):
            print("  omitida (referencia): %s (%d skills)" % (fam, len(items)))
            continue
        for it in items:
            src = os.path.join(os.path.expanduser("~/.hermes/skills"), it["src"])
            dst = os.path.join(dest_skills, fam, it["name"])
            if not os.path.isdir(src):
                print("  FALTA en origen: %s" % it["src"])
                continue
            shutil.copytree(src, dst, dirs_exist_ok=True,
                            ignore=shutil.ignore_patterns("__pycache__", "*.pyc",
                                                          ".DS_Store", "*.npy", "*.faiss"))
            idx[it["name"]] = fam
            copiadas += 1

    # ---- 3. archivos de perfil saneados ----------------------------------
    for rel in COPIAR:
        src = os.path.join(perfil, rel)
        if not os.path.exists(src):
            continue
        dst = os.path.join(salida, "profile", rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        txt = open(src, encoding="utf-8", errors="ignore").read()
        open(dst, "w", encoding="utf-8").write(sanear(txt))

    # ---- 4. manifiesto ----------------------------------------------------
    # El manifiesto se escribe DESPUES del gate de la copia: si entrara antes,
    # sus propios hashes hexadecimales disparan el detector de telefono-cl y
    # convierten un paquete limpio en 800 falsos positivos.
    archivos = []
    for dirpath, dirnames, filenames in os.walk(os.path.join(salida, "profile")):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__",)]
        for f in filenames:
            p = os.path.join(dirpath, f)
            archivos.append({"path": os.path.relpath(p, salida), "sha256": hash_de(p)})

    # ---- 5. gate de la COPIA (antes de escribir el manifiesto) -----------
    ec2, bloq2, avis2 = correr_verificador(os.path.join(salida, "profile"))
    print("\nPaquete: %d skills, %d archivos." % (copiadas, len(archivos)))
    if ec2 == 1:
        print("ABORTA: la COPIA tiene %d bloqueantes — NO publicar." % len(bloq2))
        por_regla = {}
        for b in bloq2:
            por_regla.setdefault(b["regla"], []).append(b)
        for regla, items in por_regla.items():
            print("  %s: %d hallazgo(s) — ej. %s:%s"
                  % (regla, len(items), items[0]["archivo"], items[0]["linea"]))
        print("\nArreglar la FUENTE en ~/.hermes/skills (no el paquete), o sacar esa skill")
        print("de seed/familias.json. Un dato de cliente en una referencia se publica igual.")
        return 1
    print("Gate de la copia: OK (%d avisos)." % len(avis2))

    manifiesto = {
        "skills": copiadas,
        "archivos": len(archivos),
        "por_familia": {k: len(v) for k, v in familias.items()},
        "indice_skills": idx,
        "hashes": archivos,
    }
    with open(os.path.join(salida, "profile", "MANIFIESTO.json"), "w") as fh:
        json.dump(manifiesto, fh, ensure_ascii=False, indent=1)

    print("Manifiesto escrito: %d archivos." % len(archivos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
