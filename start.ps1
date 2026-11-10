$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$theaterPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $theaterPython)) {
    py -3.11 -m venv .venv
    if ($LASTEXITCODE -ne 0) { throw 'Install Python 3.11 or create .venv using Python 3.11+.' }
}
& $theaterPython -m pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed. Run start.ps1 again to retry.' }
& $theaterPython main.py
