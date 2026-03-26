@echo off
cls
echo ====================================
echo CV-LinkedIn Comparator - Iniciador
echo ====================================
echo.

REM Obtener la ruta del script
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

echo Ruta actual: %CD%
echo.
echo Buscando archivos del proyecto...
echo.

REM Verificar si backend existe
if exist "backend\main.py" (
    echo [OK] Encontrado: backend\main.py
) else (
    echo [ERROR] No se encuentra backend\main.py
    echo.
    echo Estructura encontrada:
    dir /b
    echo.
    echo Por favor, asegurate de ejecutar este script desde la carpeta principal
    echo donde estan las carpetas backend y frontend
    pause
    exit /b 1
)

REM Verificar si frontend existe
if exist "frontend\app.py" (
    echo [OK] Encontrado: frontend\app.py
) else (
    echo [ERROR] No se encuentra frontend\app.py
    pause
    exit /b 1
)

echo.
echo ====================================
echo Estructura verificada correctamente
echo ====================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en PATH
    echo Por favor instala Python desde https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version
echo.

REM Verificar si las dependencias estan instaladas
echo Verificando dependencias...
pip show fastapi >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] Las dependencias no estan instaladas
    echo Deseas instalarlas ahora? (S/N)
    set /p INSTALAR=
    if /i "%INSTALAR%"=="S" (
        echo.
        echo Instalando dependencias...
        cd backend
        pip install -r requirements.txt
        cd ..
        echo.
        echo Dependencias instaladas!
        echo.
    ) else (
        echo.
        echo No se pueden iniciar los servicios sin las dependencias
        pause
        exit /b 1
    )
)

echo.
echo ====================================
echo Iniciando servicios...
echo ====================================
echo.

echo [1/2] Iniciando Backend (FastAPI)...
start "Backend - FastAPI" cmd /k "cd /d "%SCRIPT_DIR%backend" && echo Iniciando backend... && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

echo Esperando 5 segundos para que el backend inicie...
timeout /t 5 /nobreak >nul

echo [2/2] Iniciando Frontend (Streamlit)...
start "Frontend - Streamlit" cmd /k "cd /d "%SCRIPT_DIR%frontend" && echo Iniciando frontend... && streamlit run app.py"

echo.
echo ====================================
echo SERVICIOS INICIADOS
echo ====================================
echo.
echo Backend API:  http://localhost:8000
echo              http://localhost:8000/docs (documentacion)
echo.
echo Frontend UI:  http://localhost:8501
echo              (deberia abrirse automaticamente)
echo.
echo ====================================
echo.
echo Para detener los servicios, cierra las ventanas que se abrieron
echo o presiona Ctrl+C en cada una
echo.
echo Presiona cualquier tecla para cerrar esta ventana...
pause >nul
