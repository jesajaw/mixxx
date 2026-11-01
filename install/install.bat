@echo off
rem Double-click launcher for install.ps1 (bypasses the PowerShell execution policy for this one run).
rem Pass the same options as for install.ps1, e.g.: install\install.bat -Copy   or   -Uninstall
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0install.ps1" %*
if errorlevel 1 (
  echo.
  echo Installation failed - see the message above.
)
if "%~1"=="" pause
