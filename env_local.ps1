# Entorno compartido de Metamatematico.
# Redirige TODO lo que la app escribe (temporales y cachés) al disco E:,
# porque C: va justo de espacio. Lo cargan Metamatematico.ps1 y launch_local.ps1.

$appDir   = "E:\Metamatematico"
$cacheDir = "$appDir\cache"
$tmpDir   = "$appDir\tmp"

foreach ($d in @($tmpDir, "$cacheDir\huggingface", "$cacheDir\torch", "$cacheDir\pip", "$appDir\logs")) {
    New-Item -ItemType Directory -Force -Path $d | Out-Null
}

# Temporales (Lean escribe .lean via tempfile.NamedTemporaryFile)
$env:TMP  = $tmpDir
$env:TEMP = $tmpDir

# Cachés de modelos y datasets
$env:HF_HOME            = "$cacheDir\huggingface"
$env:HUGGINGFACE_HUB_CACHE = "$cacheDir\huggingface\hub"
$env:TORCH_HOME         = "$cacheDir\torch"
$env:XDG_CACHE_HOME     = $cacheDir
$env:PIP_CACHE_DIR      = "$cacheDir\pip"

# Streamlit: sin telemetria ni carpeta de estado en C:
$env:STREAMLIT_BROWSER_GATHER_USAGE_STATS = "false"

# Traza detallada del nucleo (area detectada, tactica, resultado de Lean).
# Las librerias de red se mantienen en WARNING desde app.py. Pon "INFO" para
# volver a la traza corta.
$env:NLE_LOG_LEVEL = "DEBUG"
