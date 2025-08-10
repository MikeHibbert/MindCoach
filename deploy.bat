@echo off
REM Deployment script for Personalized Learning Path Generator (Windows)
REM Usage: deploy.bat [environment]

setlocal enabledelayedexpansion

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production

set PROJECT_NAME=mindcoach
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set TIMESTAMP=%dt:~0,8%_%dt:~8,6%

echo 🚀 Starting deployment for environment: %ENVIRONMENT%

REM Check if required tools are installed
echo [INFO] Checking dependencies...

where node >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Node.js is required but not installed. Aborting.
    exit /b 1
)

where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] npm is required but not installed. Aborting.
    exit /b 1
)

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python is required but not installed. Aborting.
    exit /b 1
)

where pip >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] pip is required but not installed. Aborting.
    exit /b 1
)

echo [SUCCESS] All dependencies are installed

REM Validate environment variables
echo [INFO] Validating environment variables for %ENVIRONMENT%...

if "%ENVIRONMENT%"=="production" (
    if "%SECRET_KEY%"=="" (
        echo [ERROR] SECRET_KEY environment variable is required for production
        exit /b 1
    )
    
    if "%CORS_ORIGINS%"=="" (
        echo [ERROR] CORS_ORIGINS environment variable is required for production
        exit /b 1
    )
    
    if "%DATABASE_URL%"=="" (
        echo [WARNING] DATABASE_URL not set, using default SQLite database
    )
)

echo [SUCCESS] Environment validation passed

REM Build frontend
echo [INFO] Building frontend...
cd frontend

echo [INFO] Installing frontend dependencies...
call npm ci --production=false
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install frontend dependencies
    exit /b 1
)

echo [INFO] Running frontend tests...
call npm run test:run
if %errorlevel% neq 0 (
    echo [ERROR] Frontend tests failed
    exit /b 1
)

echo [INFO] Building frontend for production...
if "%ENVIRONMENT%"=="production" (
    call npm run build:prod
) else (
    call npm run build
)
if %errorlevel% neq 0 (
    echo [ERROR] Frontend build failed
    exit /b 1
)

if not exist "build" (
    echo [ERROR] Frontend build failed - build directory not found
    exit /b 1
)

echo [SUCCESS] Frontend build completed
cd ..

REM Setup backend
echo [INFO] Setting up backend...
cd backend

if not exist "venv" (
    echo [INFO] Creating Python virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

echo [INFO] Installing backend dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERROR] Failed to install backend dependencies
    exit /b 1
)

echo [INFO] Running database migrations...
python migrations\add_performance_indexes.py
if %errorlevel% neq 0 (
    echo [WARNING] Database migration failed, continuing...
)

echo [INFO] Running backend tests...
python -m pytest tests\ -v
if %errorlevel% neq 0 (
    echo [ERROR] Backend tests failed
    exit /b 1
)

echo [SUCCESS] Backend setup completed
cd ..

REM Create production configuration
if "%ENVIRONMENT%"=="production" (
    echo [INFO] Creating production configuration...
    
    echo FLASK_ENV=production > backend\.env.production
    echo SECRET_KEY=%SECRET_KEY% >> backend\.env.production
    if not "%DATABASE_URL%"=="" (
        echo DATABASE_URL=%DATABASE_URL% >> backend\.env.production
    ) else (
        echo DATABASE_URL=sqlite:///learning_path_prod.db >> backend\.env.production
    )
    echo CORS_ORIGINS=%CORS_ORIGINS% >> backend\.env.production
    echo LOG_LEVEL=INFO >> backend\.env.production
    
    if not exist "frontend\.env.production" (
        echo GENERATE_SOURCEMAP=false > frontend\.env.production
        if not "%REACT_APP_API_BASE_URL%"=="" (
            echo REACT_APP_API_BASE_URL=%REACT_APP_API_BASE_URL% >> frontend\.env.production
        ) else (
            echo REACT_APP_API_BASE_URL=https://api.mindcoach.com/api >> frontend\.env.production
        )
        echo REACT_APP_ENVIRONMENT=production >> frontend\.env.production
        echo REACT_APP_ENABLE_CACHE=true >> frontend\.env.production
        echo REACT_APP_ENABLE_ANALYTICS=true >> frontend\.env.production
    )
    
    echo [SUCCESS] Production configuration created
)

REM Run performance optimizations
echo [INFO] Running performance optimizations...

cd frontend
if exist "build" (
    if "%ENVIRONMENT%"=="production" (
        echo [INFO] Removing source maps from production build...
        del /s /q build\*.map 2>nul
    )
)
cd ..

cd backend
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    
    echo [INFO] Cleaning Python cache files...
    for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
    del /s /q *.pyc 2>nul
)
cd ..

echo [SUCCESS] Performance optimizations completed

REM Health check
echo [INFO] Running health checks...

if not exist "frontend\build\index.html" (
    echo [ERROR] Frontend build is missing index.html
    exit /b 1
)

if not exist "frontend\build\static" (
    echo [ERROR] Frontend build is missing static assets
    exit /b 1
)

if not exist "backend\run.py" (
    echo [ERROR] Backend is missing run.py
    exit /b 1
)

if not exist "backend\requirements.txt" (
    echo [ERROR] Backend is missing requirements.txt
    exit /b 1
)

echo [SUCCESS] Health checks passed

REM Create deployment package
echo [INFO] Creating deployment package...

set PACKAGE_NAME=%PROJECT_NAME%_%ENVIRONMENT%_%TIMESTAMP%.zip

if not exist "dist" mkdir dist

REM Use PowerShell to create zip file
powershell -command "& {Add-Type -AssemblyName System.IO.Compression.FileSystem; $compressionLevel = [System.IO.Compression.CompressionLevel]::Optimal; [System.IO.Compression.ZipFile]::CreateFromDirectory('frontend\build', 'dist\frontend_build.zip', $compressionLevel, $false); [System.IO.Compression.ZipFile]::CreateFromDirectory('backend', 'dist\backend.zip', $compressionLevel, $false)}"

echo [SUCCESS] Deployment package created: dist\%PACKAGE_NAME%

echo [SUCCESS] 🎉 Deployment completed successfully!
echo [INFO] Environment: %ENVIRONMENT%
echo [INFO] Timestamp: %TIMESTAMP%
echo.
echo [INFO] Next steps:
echo 1. Upload the deployment package to your server
echo 2. Extract the package
echo 3. Run the application using Docker Compose or directly
echo 4. Configure your web server (nginx) to serve the frontend and proxy API requests

endlocal