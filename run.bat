@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"
python tools\extract\render_pages.py %*
if errorlevel 1 exit /b %errorlevel%
endlocal
