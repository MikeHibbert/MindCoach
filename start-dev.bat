@echo off
echo Starting MindCoach Development Environment...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running. Please start Docker Desktop first.
    pause
    exit /b 1
)

echo Docker is running. Starting services...
echo.

REM Start the development environment
docker-compose -f docker-compose.simple.yml up -d

echo.
echo Waiting for services to start...
timeout /t 30 /nobreak >nul

echo.
echo Development environment is starting up!
echo.
echo Access points:
echo - Frontend: http://localhost:3000
echo - Backend API: http://localhost:5000
echo - API Health: http://localhost:5000/api/health
echo - Database: localhost:5433 (postgres/devpassword)
echo - Redis: localhost:6380
echo.
echo To view logs: docker-compose -f docker-compose.simple.yml logs -f
echo To stop: docker-compose -f docker-compose.simple.yml down
echo.
pause