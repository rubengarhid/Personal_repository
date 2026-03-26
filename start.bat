@echo off
echo ====================================
echo Iniciando CV_LINKEDIN_COMPARATOR
echo ====================================
echo.

:: Obtener la ruta base donde esta este archivo .bat
set BASE_DIR=%~dp0

echo Ruta del proyecto: %BASE_DIR%
echo.

:: Verificar que existen las carpetas
if not exist "%BASE_DIR%backend" (
    echo ERROR: No se encuentra la carpeta "backend" en %BASE_DIR%
    pause
    exit /b 1
)

if not exist "%BASE_DIR%frontend" (
    echo ERROR: No se encuentra la carpeta "frontend" en %BASE_DIR%
    pause
    exit /b 1
)

if not exist "%BASE_DIR%venv" (
    echo ERROR: No se encuentra la carpeta "venv" en %BASE_DIR%
    pause
    exit /b 1
)

:: Ruta al activate del entorno virtual
set ACTIVATE=%BASE_DIR%venv\Scripts\activate.bat

echo [1/2] Iniciando Backend API con venv...
start "Backend API" cmd /k "call "%ACTIVATE%" && cd /d "%BASE_DIR%backend" && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando Frontend (Streamlit) con venv...
start "Frontend - Streamlit" cmd /k "call "%ACTIVATE%" && cd /d "%BASE_DIR%frontend" && streamlit run app.py"

echo.
echo ====================================
echo Aplicacion iniciada!
echo ====================================
echo.
echo Backend API:  http://localhost:8000
echo Frontend UI:  http://localhost:8501
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
