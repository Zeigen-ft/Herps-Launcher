@echo off
setlocal
py -3.12 "%~dp0inspect_rlcraft_293.py"
set "inspection_exit=%ERRORLEVEL%"
echo.
pause
exit /b %inspection_exit%
