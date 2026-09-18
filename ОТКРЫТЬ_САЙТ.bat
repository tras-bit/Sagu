@echo off
rem SUBSISTENCE model catalog: tiny local web server + browser.
rem Close this window when done viewing.
cd /d "%~dp0site"
start "" "http://localhost:8377/"
where python >nul 2>nul
if %errorlevel%==0 (
  python -m http.server 8377
  exit /b
)
where py >nul 2>nul
if %errorlevel%==0 (
  py -m http.server 8377
  exit /b
)
echo Python not found. Install Python or use the GitHub Pages URL.
pause
