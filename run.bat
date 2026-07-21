@echo off
setlocal

cd /d "%~dp0"

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [ERROR] venv not found in "%~dp0venv".
    echo Run install.bat first.
    pause
    exit /b 1
)

if not exist "%~dp0ComfyUI\main.py" (
    echo [ERROR] ComfyUI not found at "%~dp0ComfyUI".
    echo Run install.bat first ^(or check it completed the git clone step without errors^).
    pause
    exit /b 1
)

call "%~dp0venv\Scripts\activate.bat"

echo Starting ComfyUI backend (low VRAM mode)...
start "Krea2 Backend - ComfyUI" cmd /k "cd /d "%~dp0ComfyUI" && "%~dp0venv\Scripts\python.exe" main.py --listen 127.0.0.1 --port 8188 --lowvram --reserve-vram 0.5"

echo Waiting for backend to come online...
set /a tries=0

:waitloop
set /a tries+=1
if %tries% GTR 40 (
    echo [WARN] Backend did not respond in time, continuing anyway...
    goto :launchui
)
powershell -Command "try { $r = Invoke-WebRequest -Uri http://127.0.0.1:8188/system_stats -UseBasicParsing -TimeoutSec 2; exit 0 } catch { exit 1 }" >nul 2>nul
if errorlevel 1 (
    timeout /t 2 /nobreak >nul
    goto :waitloop
)

:launchui
echo Backend is up. Starting Krea 2 WebUI...
"%~dp0venv\Scripts\python.exe" "%~dp0app.py"

pause
