@echo off
"%~dp0Herspers-Minecraft.exe" %*
set "herspers_exit=%ERRORLEVEL%"
if "%herspers_exit%"=="0" exit /b 0
echo.
pause
exit /b %herspers_exit%
