# Metamatematico — lanzador de escritorio.
# Arranca Streamlit si no esta corriendo y abre la app en el navegador.

$ErrorActionPreference = "SilentlyContinue"

$python = "C:\Users\Leonardo\anaconda3\envs\ai_cuda\python.exe"
$appDir = "E:\Metamatematico"
$port   = 8501
$url    = "http://localhost:$port"

# Temporales y cachés al disco E: (C: va sin espacio)
. "$appDir\env_local.ps1"

function Test-AppUp {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

if (-not (Test-AppUp)) {
    if (-not (Test-Path $python)) {
        Add-Type -AssemblyName System.Windows.Forms
        [System.Windows.Forms.MessageBox]::Show("No se encontro Python en:`n$python", "Metamatematico") | Out-Null
        exit 1
    }

    Start-Process -FilePath $python `
        -ArgumentList "-u -m streamlit run app.py --server.port=$port --server.address=localhost --server.headless=true" `
        -WorkingDirectory $appDir `
        -RedirectStandardOutput "$appDir\logs\streamlit_local.log" `
        -RedirectStandardError  "$appDir\logs\streamlit_error.log" `
        -WindowStyle Hidden

    # Esperar a que el servidor levante (max 90 s: la primera carga es lenta)
    for ($i = 0; $i -lt 90; $i++) {
        Start-Sleep -Seconds 1
        if (Test-AppUp) { break }
    }

    "[$(Get-Date)] Metamatematico iniciado en $url" | Add-Content "$appDir\logs\launcher.log"
}

Start-Process $url
