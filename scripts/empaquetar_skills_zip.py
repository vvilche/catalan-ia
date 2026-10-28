#!/usr/bin/env python3
"""Empaqueta las 230 skills de CatalanIA en un ZIP para llevarlas a otro equipo.

Uso:
    python empaquetar_skills_zip.py [--salida <ruta.zip>]

Por que existe: el empaquetador de perfil copia las skills DESDE ~/.hermes/skills de la
maquina donde corre. En el PC de destino ese directorio nace vacio, asi que hay que llevarlas.
Este script produce el ZIP con la estructura que espera el perfil:

    skills/<familia>/<skill>/SKILL.md ...

y ademas un INSTALAR-SKILLS.ps1 que las descomprime en %USERPROFILE%\.hermes\skills.

Lee seed/familias.json (unica fuente de verdad del que se instala) y omite las familias
con prefijo "_" (Procesos: fuera de alcance).

No incluye credenciales: verifica que no haya claves con formato real antes de escribir.
"""
import argparse
import json
import os
import re
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)
SK = os.path.expanduser(os.path.join("~", ".hermes", "skills"))

# Formatos de credencial REAL (no las plantillas tipo sk-xxx...xxxx de la documentacion)
CRED = re.compile(
    r"(sk-[A-Za-z0-9]{32,}"
    r"|ghp_[A-Za-z0-9]{30,}"
    r"|gho_[A-Za-z0-9]{30,}"
    r"|AKIA[A-Z0-9]{16}"
    r"|xox[bap]-[A-Za-z0-9-]{20,}"
    r"|AIza[A-Za-z0-9_-]{35})")

PS1 = r"""# Instala las skills de CatalanIA en este equipo (Windows PowerShell).
# Uso:  .\INSTALAR-SKILLS.ps1
$ErrorActionPreference = "Stop"
$Destino = "$env:USERPROFILE\.hermes\skills"
$Origen  = Join-Path $PSScriptRoot "skills"

if (-not (Test-Path $Origen)) { throw "No encuentro la carpeta 'skills' junto a este script." }

New-Item -ItemType Directory -Force -Path $Destino | Out-Null

$antes = (Get-ChildItem $Destino -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue).Count
Write-Host "Skills ya presentes: $antes"

Copy-Item (Join-Path $Origen "*") $Destino -Recurse -Force

$despues = (Get-ChildItem $Destino -Recurse -Filter SKILL.md).Count
Write-Host "Skills despues de copiar: $despues"
Write-Host ""
Write-Host "Ahora corre el empaquetado del perfil (desde el repo catalan-ia):" -ForegroundColor Cyan
Write-Host '  & $PY "$Repo\scripts\empaquetar_perfil.py" --perfil $Perfil --salida $Perfil --familias "$Repo\seed\familias.json" --limpiar'
"""


def familias():
    with open(os.path.join(RAIZ, "seed", "familias.json"), encoding="utf-8") as f:
        return json.load(f)


def recolectar():
    """devuelve [(familia, nombre, src)] sin duplicados, omitiendo familias '_'."""
    vistas, out = set(), []
    for fam, items in familias().items():
        if fam.startswith("_"):
            print("  omitida (referencia, no se instala): %s (%d)" % (fam, len(items)))
            continue
        for it in items:
            if it["name"] in vistas:
                continue
            vistas.add(it["name"])
            out.append((fam, it["name"], it["src"]))
    return out


def hijas_que_son_skills(items):
    """Subrutas de cada src que son, a su vez, una skill propia.

    Ej: src="scada" contiene "slrp-protecciones", que ya se empaqueta por su cuenta en otra
    familia. Copiar el contenedor entero las duplicaria en el destino.
    """
    srcs = {s for _, _, s in items}
    dentro = {}
    for _, _, s in items:
        pref = s + "/"
        hijas = [o for o in srcs if o.startswith(pref)]
        if hijas:
            dentro[s] = hijas
    return dentro


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--salida", default=os.path.join(RAIZ, "dist", "catalania-skills.zip"))
    a = ap.parse_args()

    items = recolectar()
    faltan = [s for _, n, s in items if not os.path.isdir(os.path.join(SK, s))]
    if faltan:
        print("ABORTA: %d skills no existen en %s: %s" % (len(faltan), SK, faltan[:5]))
        return 2

    anidadas = hijas_que_son_skills(items)
    for cont, hijas in anidadas.items():
        print("  %s: se excluyen %d skill(s) anidada(s) que van por separado: %s"
              % (cont, len(hijas), ", ".join(os.path.basename(h) for h in hijas)))

    os.makedirs(os.path.dirname(a.salida), exist_ok=True)
    creds, archivos, total = [], 0, 0
    with zipfile.ZipFile(a.salida, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for fam, nombre, src in items:
            raiz_skill = os.path.join(SK, src)
            excluir = {os.path.join(SK, h) for h in anidadas.get(src, [])}
            for dp, dn, fn in os.walk(raiz_skill):
                dn[:] = [d for d in dn
                         if d not in ("__pycache__", ".git")
                         and os.path.join(dp, d) not in excluir]
                for f in fn:
                    if f.endswith((".pyc", ".DS_Store")):
                        continue
                    ruta = os.path.join(dp, f)
                    rel = os.path.relpath(ruta, raiz_skill)
                    arc = "skills/%s/%s/%s" % (fam, nombre, rel.replace(os.sep, "/"))
                    try:
                        datos = open(ruta, "rb").read()
                    except OSError:
                        continue
                    if f.endswith((".md", ".py", ".json", ".yaml", ".yml", ".env", ".sh", ".txt")):
                        try:
                            if CRED.search(datos.decode("utf-8", "ignore")):
                                creds.append(arc)
                        except Exception:
                            pass
                    z.writestr(arc, datos)
                    archivos += 1
                    total += len(datos)
        z.writestr("INSTALAR-SKILLS.ps1", PS1)

    print("\n=== PAQUETE ===")
    print("skills:      %d" % len(items))
    print("archivos:    %d" % archivos)
    print("peso:        %.1f MB" % (total / 1024 / 1024))
    print("zip:         %s (%.1f MB)" % (a.salida, os.path.getsize(a.salida) / 1024 / 1024))
    if creds:
        print("\nABORTA: credenciales con formato real en %d archivos:" % len(creds))
        for c in creds[:10]:
            print("  " + c)
        os.remove(a.salida)
        return 1
    print("credenciales: 0 (solo plantillas de documentacion)")
    print("\nEn el PC de destino: descomprimir y correr .\\INSTALAR-SKILLS.ps1")
    return 0


if __name__ == "__main__":
    sys.exit(main())
