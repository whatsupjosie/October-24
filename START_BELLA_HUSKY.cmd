@echo off
setlocal
cd /d "%~dp0"
set "PORT=8765"
set "WALK_URL=http://127.0.0.1:%PORT%/static/world_walk.html?view=green_room/main&demo=husky&pads=0"
where py >nul 2>nul
if not errorlevel 1 goto use_py
where python >nul 2>nul
if not errorlevel 1 goto use_python
echo Python 3 was not found. Install Python, then run this launcher again.
pause
exit /b 1
:use_py
start "" "%WALK_URL%"
echo Bella Faux Pas Studio - real local room images and bundled Husky model
echo Browser: %WALK_URL%
echo Keep this window open. Press Ctrl+C to stop.
py -3 -m http.server %PORT% --bind 127.0.0.1
goto end
:use_python
start "" "%WALK_URL%"
echo Bella Faux Pas Studio - real local room images and bundled Husky model
echo Browser: %WALK_URL%
echo Keep this window open. Press Ctrl+C to stop.
python -m http.server %PORT% --bind 127.0.0.1
:end
if errorlevel 1 pause
