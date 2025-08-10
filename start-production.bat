@echo off
REM Production startup script for MindCoach (Windows)

setlocal enabledelayedexpansion

echo 🚀 Starting MindCoach in production mode...

REM Check if Docker is available
where docker >nul 2>nul
if %errorlevel% equ 0 (
    where docker-compose >nul 2>nul
    if %errorlevel% equ 0 (
        echo [INFO] Docker detected, using containerized deployment
        
        REM Check if .env file exists
        if not exist ".env" (
            echo [WARNING] .env file not found, creating from template...
            echo # Production environment variables > .env
            echo SECRET_KEY=change-this-in-production >> .env
            echo CORS_ORIGINS=https://mindcoach.com,https://www.mindcoach.com >> .env
            echo DATABASE_URL=sqlite:///data/learning_path_prod.db >> .env
            echo REACT_APP_API_BASE_URL=https://api.mindcoach.com/api >> .env
            echo. >> .env
            echo # Optional monitoring >> .env
            echo GRAFANA_PASSWORD=admin123 >> .env
            echo [INFO] Created .env file with default values. Please review and update as needed.
        )
        
        REM Create necessary directories
        if not exist "data" mkdir data
        if not exist "users" mkdir users
        if not exist "logs" mkdir logs
        if not exist "logs\nginx" mkdir logs\nginx
        if not exist "logs\backend" mkdir logs\backend
        if not exist "logs\celery" mkdir logs\celery
        
        REM Start services
        echo [INFO] Starting services with Docker Compose...
        docker-compose -f docker-compose.prod.yml up -d
        if %errorlevel% neq 0 (
            echo [ERROR] Failed to start Docker services
            exit /b 1
        )
        
        REM Wait for services to be ready
        echo [INFO] Waiting for services to be ready...
        timeout /t 10 /nobreak >nul
        
        REM Health check
        echo [INFO] Performing health check...
        curl -f http://localhost/api/health >nul 2>nul
        if %errorlevel% equ 0 (
            echo [SUCCESS] ✅ Application is running and healthy!
            echo [INFO] Frontend: http://localhost
            echo [INFO] API: http://localhost/api
            echo [INFO] Health check: http://localhost/api/health
        ) else (
            echo [ERROR] ❌ Health check failed
            echo [INFO] Checking service logs...
            docker-compose -f docker-compose.prod.yml logs --tail=20
            exit /b 1
        )
        
        goto :end
    )
)

echo [INFO] Docker not available, using direct deployment

REM Check if virtual environment exists
if not exist "backend\venv" (
    echo [ERROR] Virtual environment not found. Please run deployment script first.
    exit /b 1
)

REM Check if frontend build exists
if not exist "frontend\build" (
    echo [ERROR] Frontend build not found. Please run deployment script first.
    exit /b 1
)

REM Start backend
echo [INFO] Starting backend server...
cd backend
call venv\Scripts\activate.bat

REM Set production environment
set FLASK_ENV=production
if "%SECRET_KEY%"=="" set SECRET_KEY=change-this-in-production
if "%CORS_ORIGINS%"=="" set CORS_ORIGINS=http://localhost:3000

REM Start with gunicorn if available, otherwise use Flask
where gunicorn >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Starting with Gunicorn...
    start /b gunicorn --bind 0.0.0.0:5000 --workers 4 --worker-class gevent run:app
) else (
    echo [WARNING] Gunicorn not found, starting with Flask development server (not recommended for production)
    start /b python run.py
)

cd ..

REM Start frontend server
echo [INFO] Starting frontend server...
cd frontend

where serve >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Starting with serve...
    start /b serve -s build -l 3000
) else (
    echo [WARNING] serve not found, please install: npm install -g serve
    echo [INFO] You can manually serve the build directory with any static file server
)

cd ..

REM Health check
timeout /t 5 /nobreak >nul
echo [INFO] Performing health check...
curl -f http://localhost:5000/api/health >nul 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] ✅ Backend is running and healthy!
    echo [INFO] Backend API: http://localhost:5000/api
    echo [INFO] Frontend: http://localhost:3000
    echo [INFO] Health check: http://localhost:5000/api/health
) else (
    echo [ERROR] ❌ Backend health check failed
    exit /b 1
)

:end
echo [SUCCESS] 🎉 MindCoach is now running in production mode!
echo.
echo [INFO] Useful commands:
echo   - View logs: docker-compose -f docker-compose.prod.yml logs -f
echo   - Stop services: docker-compose -f docker-compose.prod.yml down
echo   - Restart services: docker-compose -f docker-compose.prod.yml restart
echo.
echo [INFO] Monitoring:
echo   - Application health: http://localhost/api/health
echo   - Detailed health: http://localhost/api/health/detailed
echo   - Performance metrics: http://localhost/api/admin/performance

endlocal