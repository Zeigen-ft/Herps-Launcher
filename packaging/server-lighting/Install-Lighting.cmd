@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0Install-Lighting.ps1"
set "lighting_exit=%ERRORLEVEL%"
echo.
pause
exit /b %lighting_exit%
