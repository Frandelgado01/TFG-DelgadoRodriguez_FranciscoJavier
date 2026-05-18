# =============================================================================
# rebuild_env.ps1 — Reconstrucción limpia del entorno virtual Python
# =============================================================================
# Autor : TFG - Delgado Rodríguez, Francisco Javier
# Uso   : Ejecutar desde la carpeta backend/ en una terminal PowerShell
#
#   cd <raiz-proyecto>\backend
#   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
#   .\rebuild_env.ps1
# =============================================================================

$ErrorActionPreference = "Stop"   # Detener el script ante cualquier error

# ── Colores de consola ────────────────────────────────────────────────────────
function Write-Step  ($msg) { Write-Host "`n[+] $msg" -ForegroundColor Cyan    }
function Write-OK    ($msg) { Write-Host "    ✔  $msg" -ForegroundColor Green   }
function Write-Warn  ($msg) { Write-Host "    ⚠  $msg" -ForegroundColor Yellow  }
function Write-Fatal ($msg) { Write-Host "`n[✗] $msg" -ForegroundColor Red; exit 1 }

# ── Verificar que el script se ejecuta desde backend/ ────────────────────────
if (-not (Test-Path ".\requirements.txt")) {
    Write-Fatal "No se encontró requirements.txt. Ejecuta el script desde la carpeta backend/."
}

# ── PASO 1: Desactivar entorno activo (si lo hay) ────────────────────────────
Write-Step "PASO 1 — Desactivando entorno virtual activo (si existe)..."
if ($env:VIRTUAL_ENV) {
    Write-Warn "Entorno activo detectado: $env:VIRTUAL_ENV"
    # En PowerShell no existe 'deactivate' como comando nativo;
    # limpiar las variables de entorno es suficiente para el script.
    $env:VIRTUAL_ENV = $null
    $env:PATH = ($env:PATH -split ";" | Where-Object { $_ -notlike "*\venv\*" }) -join ";"
    Write-OK "Variables de entorno limpiadas."
} else {
    Write-OK "No había entorno activo. Continuando."
}

# ── PASO 2: Borrar la carpeta venv corrupta ───────────────────────────────────
Write-Step "PASO 2 — Eliminando carpeta 'venv' corrupta..."
if (Test-Path ".\venv") {
    Remove-Item -Recurse -Force ".\venv"
    Write-OK "Carpeta 'venv' eliminada correctamente."
} else {
    Write-OK "No existía carpeta 'venv'. Continuando."
}

# ── PASO 3: Crear nuevo entorno virtual ───────────────────────────────────────
Write-Step "PASO 3 — Creando nuevo entorno virtual con 'python -m venv venv'..."
python -m venv venv
if (-not (Test-Path ".\venv\Scripts\python.exe")) {
    Write-Fatal "Falló la creación del entorno virtual. ¿Está Python instalado y en el PATH?"
}
Write-OK "Entorno virtual creado en .\venv\"

# ── PASO 4: Actualizar pip ────────────────────────────────────────────────────
Write-Step "PASO 4 — Actualizando pip al interior del nuevo entorno..."
.\venv\Scripts\python.exe -m pip install --upgrade pip --quiet
Write-OK "pip actualizado correctamente."

# ── PASO 5: Instalar PyTorch CPU (índice especial, debe ir primero) ──────────
Write-Step "PASO 5 — Instalando PyTorch CPU-only (índice especial de PyTorch)..."
Write-Warn "Este paso puede tardar varios minutos (~200 MB de descarga). Por favor, espera."
.\venv\Scripts\pip.exe install `
    torch==2.6.0 `
    --index-url https://download.pytorch.org/whl/cpu `
    --quiet
Write-OK "PyTorch CPU instalado."

# ── PASO 6: Instalar el resto de dependencias desde requirements.txt ─────────
Write-Step "PASO 6 — Instalando dependencias desde requirements.txt..."
Write-Warn "Este paso puede tardar varios minutos. Por favor, espera."
# Excluimos la línea de torch del requirements para no reinstalarla con índice erróneo
.\venv\Scripts\pip.exe install `
    --requirement requirements.txt `
    --ignore-requires-python `
    --quiet
Write-OK "Todas las dependencias instaladas."

# ── PASO 7: Verificación rápida de imports críticos ──────────────────────────
Write-Step "PASO 7 — Verificando imports críticos..."

$imports = @(
    "fastapi",
    "uvicorn",
    "langchain",
    "langchain_community",
    "langchain_text_splitters",
    "langchain_huggingface",
    "langchain_groq",
    "langchain_core",
    "chromadb",
    "sentence_transformers",
    "pypdf",
    "dotenv",
    "pydantic"
)

$failed = @()
foreach ($pkg in $imports) {
    $result = .\venv\Scripts\python.exe -c "import $pkg" 2>&1
    if ($LASTEXITCODE -ne 0) {
        $failed += $pkg
        Write-Warn "FALLO: No se pudo importar '$pkg'"
    } else {
        Write-OK "OK → $pkg"
    }
}

if ($failed.Count -gt 0) {
    Write-Fatal "Los siguientes módulos fallaron: $($failed -join ', '). Revisa el log de pip."
}

# ── RESUMEN FINAL ─────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "  ✔  Entorno reconstruido y verificado correctamente." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Para arrancar el servidor, ejecuta desde la RAIZ del proyecto:" -ForegroundColor White
Write-Host ""
Write-Host "  cd .." -ForegroundColor Yellow
Write-Host "  .\backend\venv\Scripts\uvicorn backend.main:app --reload --port 8000" -ForegroundColor Yellow
Write-Host ""
Write-Host "Swagger UI disponible en: http://127.0.0.1:8000/docs" -ForegroundColor Cyan
Write-Host ""
