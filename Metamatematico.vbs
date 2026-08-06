' Metamatematico — arranca el lanzador de PowerShell sin mostrar ventana de consola.
CreateObject("WScript.Shell").Run _
  "powershell.exe -NoProfile -ExecutionPolicy Bypass -File ""E:\Metamatematico\Metamatematico.ps1""", 0, False
