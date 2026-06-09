$ErrorActionPreference = "Stop"

param(
  [switch]$Outlook
)

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path

if ($Outlook) {
  $env:AUTOMAIL_EMAIL_GATEWAY = "outlook_com"
  Push-Location $RootDir
  python -m pip install -e ".[outlook]"
  Pop-Location
} else {
  Push-Location $RootDir
  python -m pip install -e "."
  Pop-Location
}

if (!(Test-Path "$RootDir\web\node_modules")) {
  Push-Location "$RootDir\web"
  npm install
  Pop-Location
}

$api = Start-Process -FilePath python -ArgumentList @("-m","automail.web_api") -WorkingDirectory $RootDir -PassThru
$web = Start-Process -FilePath npm -ArgumentList @("run","dev","--","--host","0.0.0.0","--port","5173") -WorkingDirectory "$RootDir\web" -PassThru

Write-Host "Web: http://localhost:5173/"
Write-Host "API: http://localhost:8000/"

Wait-Process -Id @($api.Id, $web.Id)
