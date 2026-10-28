<#
.SYNOPSIS
    Instalador de CatalanIA para Windows. Un solo comando deja el agente funcionando.

.DESCRIPTION
    Que hace, en orden:
      1. Verifica PowerShell y que exista Hermes; si no esta, lo instala.
      2. Clona (o actualiza) el repo catalan-ia.
      3. Descomprime las 230 skills en %USERPROFILE%\.hermes\skills.
      4. Crea el perfil y le pasa config, SOUL, memorias.
      5. Empaqueta las skills en el perfil y verifica el resultado.

    Al final imprime VERDE si quedo operativo, o ROJO con la causa exacta.
    No pide claves de API: eso lo hace `hermes setup`, un paso humano a proposito.

.PARAMETER Repo
    Ruta donde clonar el repositorio. Default: %USERPROFILE%\catalan-ia

.PARAMETER ZipSkills
    ZIP con las skills. Default: busca catalania-skills.zip junto a este script.

.PARAMETER SkipHermes
    No intenta instalar Hermes. Para reinstalar solo el perfil.

.EXAMPLE
    .\INSTALAR-CATALANIA.ps1

.EXAMPLE
    .\INSTALAR-CATALANIA.ps1 -ZipSkills "C:\Users\fcatalan\OneDrive\catalania-skills.zip"
#>
[CmdletBinding()]
param(
    [string]$Repo    = "$env:USERPROFILE\catalan-ia",
    [string]$ZipSkills = "",
    [switch]$SkipHermes
)

$ErrorActionPreference = "Stop"
$ProgressPreference    = "SilentlyContinue"

# ---------- utilidades de salida ----------
$script:Fallos = @()
function Paso($n, $t)  { Write-Host ""; Write-Host "[$n] $t" -ForegroundColor Cyan }
function Ok($m)        { Write-Host "    OK    $m" -ForegroundColor Green }
function Aviso($m)     { Write-Host "    AVISO $m" -ForegroundColor Yellow }
function Falla($m)     {
    Write-Host "    FALLA $m" -ForegroundColor Red
    $script:Fallos += $m
}
function Muere($m)     {
    Write-Host ""
    Write-Host "=================================================" -ForegroundColor Red
    Write-Host " INSTALACION DETENIDA" -ForegroundColor Red
    Write-Host " $m" -ForegroundColor Red
    Write-Host "=================================================" -ForegroundColor Red
    Write-Host ""
    exit 1
}

Write-Host ""
Write-Host "=================================================" -ForegroundColor White
Write-Host "  CatalanIA - instalador para Windows" -ForegroundColor White
Write-Host "  Agente comercial CONECTA (Power)" -ForegroundColor Gray
Write-Host "=================================================" -ForegroundColor White

# ---------- 0. PowerShell ----------
Paso 0 "Entorno"
if ($PSVersionTable.PSVersion.Major -lt 5) {
    Muere "Se necesita PowerShell 5.1 o superior. Tenes $($PSVersionTable.PSVersion)."
}
Ok "PowerShell $($PSVersionTable.PSVersion)"

$Perfil  = "$env:USERPROFILE\.hermes\profiles\catalania"
$Skills  = "$env:USERPROFILE\.hermes\skills"

# ---------- 1. Hermes ----------
Paso 1 "Hermes"
$hermes = Get-Command hermes -ErrorAction SilentlyContinue
if (-not $hermes) {
    if ($SkipHermes) { Muere "Hermes no esta instalado y se pidio -SkipHermes." }
    Aviso "Hermes no esta instalado. Se instala ahora (tarda unos minutos)."
    try {
        iex (irm https://hermes-agent.nousresearch.com/install.ps1)
    } catch {
        Muere "Fallo el instalador de Hermes: $($_.Exception.Message). Revisa la conexion y volve a intentar."
    }
    Aviso "Cerra esta ventana, abri una nueva, y volve a correr este script."
    Aviso "El instalador de Hermes necesita que el PATH se recargue."
    exit 2
}
$ver = (& hermes --version 2>&1 | Select-Object -First 1)
Ok "Hermes presente: $ver"

# Python del venv: puede estar en dos ubicaciones segun como se instalo
$candidatos = @(
    "$env:USERPROFILE\.hermes\hermes-agent\venv\Scripts\python.exe",
    "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe"
)
$PY = $candidatos | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $PY) {
    # Solo busca en los directorios que existen: Get-ChildItem con una ruta inexistente aborta.
    $bases = @("$env:USERPROFILE\.hermes", "$env:LOCALAPPDATA\hermes") |
             Where-Object { Test-Path $_ }
    foreach ($b in $bases) {
        $hit = Get-ChildItem $b -Filter python.exe -Recurse -ErrorAction SilentlyContinue |
               Where-Object { $_.FullName -match "venv" } | Select-Object -First 1
        if ($hit) { $PY = $hit.FullName; break }
    }
}
if (-not $PY) { Muere "No encuentro el Python de Hermes. Verifica con: hermes --version" }
Ok "Python: $PY"

# ---------- 2. Repo ----------
Paso 2 "Repositorio"
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Aviso "Git no esta instalado. Se instala con winget."
    try {
        winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
    } catch {
        Muere "No se pudo instalar Git. Instalalo a mano desde https://git-scm.com/download/win"
    }
    # winget deja git instalado pero el PATH de esta sesion no lo ve.
    Muere "Git se instalo recien. Cerra y reabri PowerShell, y volve a correr este script."
}
if (Test-Path (Join-Path $Repo ".git")) {
    Ok "Repo ya existe en $Repo"
    Push-Location $Repo
    & git pull --ff-only 2>&1 | Out-Null
    Pop-Location
} else {
    & git clone --depth 1 https://github.com/vvilche/catalan-ia.git $Repo 2>&1 | Out-Null
    if (-not (Test-Path (Join-Path $Repo "profile\SOUL.md"))) {
        Muere "El clone no trajo el repo completo. Revisa acceso a GitHub."
    }
    Ok "Clonado en $Repo"
}

$SOUL = Join-Path $Repo "profile\SOUL.md"
$Familias = Join-Path $Repo "seed\familias.json"
$Empaquetador = Join-Path $Repo "scripts\empaquetar_perfil.py"
foreach ($f in @($SOUL, $Familias, $Empaquetador)) {
    if (-not (Test-Path $f)) { Muere "Falta un archivo del repo: $f" }
}

# ---------- 3. Skills ----------
Paso 3 "Skills de Power (230)"
if (-not $ZipSkills) {
    $ZipSkills = Join-Path $PSScriptRoot "catalania-skills.zip"
}
if (-not (Test-Path $ZipSkills)) {
    Muere @"
No encuentro el ZIP de skills: $ZipSkills

Tenes dos opciones:
  1. Poner catalania-skills.zip junto a este script (o pasar -ZipSkills <ruta>).
  2. Pedirselo a Victor y volver a correr el script.
"@
}
$tmpSkills = Join-Path $env:TEMP "catalania-skills-$([guid]::NewGuid().ToString('N'))"
New-Item -ItemType Directory -Force -Path $tmpSkills | Out-Null
try {
    Expand-Archive -Path $ZipSkills -DestinationPath $tmpSkills -Force
    $origenSkills = Join-Path $tmpSkills "skills"
    if (-not (Test-Path $origenSkills)) { Muere "El ZIP no tiene la carpeta 'skills'. Archivo incorrecto." }
    $enZIP = (Get-ChildItem $origenSkills -Recurse -Filter SKILL.md).Count
    if ($enZIP -lt 200) { Muere "El ZIP trae solo $enZIP skills (se esperan 230). Archivo incompleto." }
    New-Item -ItemType Directory -Force -Path $Skills | Out-Null
    Copy-Item (Join-Path $origenSkills "*") $Skills -Recurse -Force
    $instaladas = (Get-ChildItem $Skills -Recurse -Filter SKILL.md).Count
    Ok "$instaladas skills en $Skills"
} finally {
    Remove-Item $tmpSkills -Recurse -Force -ErrorAction SilentlyContinue
}

# ---------- 4. Perfil ----------
Paso 4 "Perfil catalania"
$existe = Test-Path $Perfil
if (-not $existe) {
    & hermes profile create catalania --no-skills `
        --description "Agente comercial CONECTA - Power (NORMATIVO, SCADA, PAC-SSEE)" 2>&1 | Out-Null
    if (-not (Test-Path $Perfil)) { Muere "No se pudo crear el perfil en $Perfil" }
    Ok "Perfil creado"
} else {
    $n = (Get-ChildItem "$Perfil\skills" -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue).Count
    Aviso "El perfil ya existia ($n skills). Se reemplaza SOUL, memorias y skills."
}

# config: hereda claves y MCP del perfil base si todavia no tiene
if (-not (Test-Path "$Perfil\config.yaml")) {
    if (Test-Path "$env:USERPROFILE\.hermes\config.yaml") {
        Copy-Item "$env:USERPROFILE\.hermes\config.yaml" "$Perfil\config.yaml" -Force
        Ok "config heredado del perfil base"
    } else {
        Aviso "No hay config base. Se crea uno minimo."
        Copy-Item (Join-Path $Repo "profile\config.yaml") "$Perfil\config.yaml" -Force
    }
} else {
    Ok "config propio conservado"
}

foreach ($par in @(
    @("agent.verify_on_stop", "true"),
    @("tool_loop_guardrails.hard_stop_enabled", "true"),
    @("model.provider", "deepseek"),
    @("model.model", "deepseek-v4-flash"))) {
    $clave = $par[0]
    $valor = $par[1]
    & hermes config set $clave $valor --profile catalania 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { Falla "no se pudo fijar $clave" }
}
Ok "config endurecido (verify_on_stop, hard_stop, deepseek-v4-flash)"

Copy-Item $SOUL "$Perfil\SOUL.md" -Force
Copy-Item (Join-Path $Repo "profile\profile.yaml") "$Perfil\profile.yaml" -Force
New-Item -ItemType Directory -Force -Path "$Perfil\memories" | Out-Null
Copy-Item (Join-Path $Repo "profile\memories\*.md") "$Perfil\memories\" -Force
Ok "SOUL, descripcion y memorias"

# ---------- 5. Empaquetar y verificar ----------
Paso 5 "Empaquetar el perfil"
# Se captura la salida en vez de encadenar ForEach-Object: dentro de una tuberia
# $LASTEXITCODE no refleja el del proceso, y el fallo del empaquetado pasaba inadvertido.
$salidaEmpaq = & $PY $Empaquetador --perfil $Perfil --salida $Perfil --familias $Familias --limpiar 2>&1
$codigoEmpaq = $LASTEXITCODE
$salidaEmpaq | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }
if ($codigoEmpaq -ne 0) {
    Muere "El empaquetado fallo (exit $codigoEmpaq). Ver la salida de arriba."
}

Paso 6 "Verificar"
$final = (Get-ChildItem "$Perfil\skills" -Recurse -Filter SKILL.md -ErrorAction SilentlyContinue).Count
if ($final -eq 230)   { Ok "230 skills en el perfil" }
elseif ($final -gt 0) { Aviso "$final skills en el perfil (se esperaban 230)" }
else                  { Falla "El perfil no tiene skills" }

foreach ($f in @("SOUL.md","profile.yaml","config.yaml","memories\MEMORY.md","memories\USER.md")) {
    if (Test-Path (Join-Path $Perfil $f)) { Ok $f } else { Falla "falta $f" }
}

$enLista = (& hermes profile list 2>&1 | Select-String -SimpleMatch "catalania")
if ($enLista) { Ok "el perfil aparece en hermes profile list" } else { Falla "el perfil no aparece en la lista" }

$gate = Join-Path $env:USERPROFILE ".hermes\scripts\verificar_privacidad_perfil.py"
if (Test-Path $gate) {
    & $PY $gate $Perfil 2>&1 | Out-Null
    Ok "gate de privacidad corrido (bloqueantes: revisar salida si hubo)"
} else {
    Aviso "gate de privacidad no instalado en esta maquina (no bloquea el uso)"
}

# ---------- resultado ----------
Write-Host ""
if ($script:Fallos.Count -eq 0) {
    Write-Host "=================================================" -ForegroundColor Green
    Write-Host " CATALANIA QUEDO INSTALADO" -ForegroundColor Green
    Write-Host "=================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Para hablar con el agente:" -ForegroundColor White
    Write-Host "    catalania" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  Si es la primera vez, falta la clave del modelo:" -ForegroundColor White
    Write-Host "    hermes --profile catalania setup" -ForegroundColor Yellow
    Write-Host ""
    exit 0
} else {
    Write-Host "=================================================" -ForegroundColor Yellow
    Write-Host " INSTALADO CON $($script:Fallos.Count) PROBLEMA(S)" -ForegroundColor Yellow
    Write-Host "=================================================" -ForegroundColor Yellow
    foreach ($f in $script:Fallos) { Write-Host "  - $f" -ForegroundColor Yellow }
    Write-Host ""
    Write-Host " Copia este texto completo y mandaselo a Victor." -ForegroundColor White
    Write-Host ""
    exit 1
}
