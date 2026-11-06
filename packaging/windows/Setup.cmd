@echo off
"%~dp0Herspers-Minecraft.exe" --setup %*
set "herspers_exit=%ERRORLEVEL%"
echo.
pause
exit /b %herspers_exit%
