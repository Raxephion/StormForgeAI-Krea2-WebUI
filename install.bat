@echo off
setlocal enabledelayedexpansion

cd /d "%~dp0"

echo ============================================
echo   Krea 2 WebUI - Installer
echo   Installing into: %CD%
echo ============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python was not found on PATH.
    echo Install Python 3.10, 3.11, or 3.12 from https://www.python.org/downloads/
    echo and make sure "Add python.exe to PATH" is checked during install.
    pause
    exit /b 1
)

where git >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Git was not found on PATH.
    echo Install Git from https://git-scm.com/download/win and re-run this script.
    pause
    exit /b 1
)

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
) else (
    echo Virtual environment already exists, skipping creation.
)

call venv\Scripts\activate.bat

echo.
echo Upgrading pip...
python -m pip install --upgrade pip

echo.
echo Installing PyTorch with CUDA 13.0 support...
echo (Needed for optimized fp8/LoRA CUDA kernels. If you have an older GPU driver
echo  that doesn't support CUDA 13.0, change cu130 below to cu126 or cu124.)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130

if not exist ComfyUI (
    echo.
    echo Cloning ComfyUI - inference backend...
    git clone https://github.com/comfyanonymous/ComfyUI.git
) else (
    echo.
    echo ComfyUI folder already exists, skipping clone.
    echo To update it later, run: cd ComfyUI, then git pull
)

if not exist ComfyUI\main.py (
    echo.
    echo [ERROR] ComfyUI\main.py not found - the git clone did not complete successfully.
    echo Check your internet connection and re-run install.bat.
    pause
    exit /b 1
)

echo.
echo Installing ComfyUI requirements...
pip install -r ComfyUI\requirements.txt

echo.
echo Installing Krea 2 WebUI requirements...
pip install -r requirements.txt

echo.
echo Creating model folders...
if not exist ComfyUI\models\diffusion_models mkdir ComfyUI\models\diffusion_models
if not exist ComfyUI\models\text_encoders mkdir ComfyUI\models\text_encoders
if not exist ComfyUI\models\vae mkdir ComfyUI\models\vae

echo.
echo ============================================
echo   Install complete.
echo ============================================
echo.
echo Copy your files into these folders:
echo   Krea 2 Turbo fp8 model     -^> ComfyUI\models\diffusion_models\
echo   Qwen3-VL fp8 text encoder  -^> ComfyUI\models\text_encoders\
echo   Qwen-Image VAE             -^> ComfyUI\models\vae\
echo.
echo Then start the app with run.bat
echo.
pause
