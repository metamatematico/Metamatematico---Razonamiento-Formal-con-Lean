# Metamatemático — Launcher local persistente
# Lanzado automáticamente por el Programador de Tareas al iniciar sesión.

$ErrorActionPreference = "SilentlyContinue"

$python  = "C:\Users\Leonardo\anaconda3\envs\ai_cuda\python.exe"
$appDir  = "E:\Metamatematico"
$appFile = "app.py"
$port    = 8501
$log     = "$appDir\logs\streamlit_local.log"

# Temporales y cachés al disco E: (C: va sin espacio); tambien crea logs\
. "$appDir\env_local.ps1"

# Matar instancias anteriores de Streamlit en ese puerto
Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }

Start-Sleep -Seconds 2

# Lanzar Streamlit
$proc = Start-Process -FilePath $python `
    -ArgumentList "-u -m streamlit run $appFile --server.port=$port --server.address=localhost --server.headless=true" `
    -WorkingDirectory $appDir `
    -RedirectStandardOutput $log `
    -RedirectStandardError "$appDir\logs\streamlit_error.log" `
    -WindowStyle Hidden `
    -PassThru

"[$(Get-Date)] Metamatemático iniciado (PID $($proc.Id)) en http://localhost:$port" |
    Add-Content "$appDir\logs\launcher.log"
