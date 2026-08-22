# Metamatematico — lanzador de escritorio.
# Arranca Streamlit si no esta corriendo y abre la app en el navegador.

$ErrorActionPreference = "SilentlyContinue"

$python = "C:\Users\Leonardo\anaconda3\envs\ai_cuda\python.exe"
$appDir = "E:\Metamatematico"
$port   = 8501
$url    = "http://localhost:$port"

# Temporales y cachés al disco E: (C: va sin espacio)
. "$appDir\env_local.ps1"

function Get-AppProcess {
    $c = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $c) { return $null }
    Get-Process -Id ($c | Select-Object -First 1).OwningProcess -ErrorAction SilentlyContinue
}

function Test-AppUp { [bool](Get-AppProcess) }

# Si la app corre pero con codigo mas viejo que los fuentes, hay que REINICIARLA.
#
# Antes este script solo comprobaba "el puerto escucha?". Si escuchaba, no
# lanzaba nada y se limitaba a abrir el navegador contra el proceso viejo. Se
# podia pulsar el acceso directo durante horas creyendo que se reiniciaba, sin
# reiniciar nada: los cambios en el codigo no se veian jamas.
#
# Es especialmente enganoso porque Streamlit SI recarga app.py en caliente pero
# NO reimporta de forma fiable los modulos de nucleo/, asi que el proceso acaba
# mezclando versiones de distintas horas y el sintoma no tiene sentido.
$proc = Get-AppProcess
if ($proc) {
    $masNuevo = Get-ChildItem -Path "$appDir\app.py", "$appDir\nucleo", "$appDir\pages" `
                    -Recurse -Include *.py -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($masNuevo -and $masNuevo.LastWriteTime -gt $proc.StartTime) {
        "[$(Get-Date)] Codigo mas nuevo que el proceso ($($masNuevo.Name)) - reiniciando" |
            Add-Content "$appDir\logs\launcher.log"
        Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
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
