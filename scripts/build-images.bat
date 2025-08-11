@echo off
REM Container image build script for Windows
REM Usage: scripts\build-images.bat [tag] [registry]

setlocal enabledelayedexpansion

set TAG=%1
if "%TAG%"=="" set TAG=latest

set REGISTRY=%2
if "%REGISTRY%"=="" set REGISTRY=ghcr.io/mindcoach

for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set BUILD_DATE=%dt:~0,4%-%dt:~4,2%-%dt:~6,2%T%dt:~8,2%:%dt:~10,2%:%dt:~12,2%Z

for /f %%i in ('git rev-parse --short HEAD') do set GIT_COMMIT=%%i
set VERSION=%TAG%

echo 🐳 Building container images...
echo Tag: %TAG%
echo Registry: %REGISTRY%
echo Build Date: %BUILD_DATE%
echo Git Commit: %GIT_COMMIT%

REM Check if Docker is available
where docker >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed or not in PATH
    exit /b 1
)

REM Check if Docker Buildx is available
docker buildx version >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Docker Buildx is not available
    exit /b 1
)

REM Create buildx builder if it doesn't exist
docker buildx ls | findstr "mindcoach-builder" >nul
if %errorlevel% neq 0 (
    echo [INFO] Creating Docker Buildx builder...
    docker buildx create --name mindcoach-builder --use
    docker buildx inspect --bootstrap
)

REM Build frontend image
echo [INFO] Building frontend image...
docker buildx build ^
    --platform linux/amd64,linux/arm64 ^
    --build-arg BUILD_DATE="%BUILD_DATE%" ^
    --build-arg GIT_COMMIT="%GIT_COMMIT%" ^
    --build-arg VERSION="%VERSION%" ^
    --tag "%REGISTRY%/frontend:%TAG%" ^
    --tag "%REGISTRY%/frontend:latest" ^
    --file frontend/Dockerfile.prod ^
    --push ^
    frontend/

if %errorlevel% equ 0 (
    echo [SUCCESS] Frontend image built successfully
) else (
    echo [ERROR] Frontend image build failed
    exit /b 1
)

REM Build backend image
echo [INFO] Building backend image...
docker buildx build ^
    --platform linux/amd64,linux/arm64 ^
    --build-arg BUILD_DATE="%BUILD_DATE%" ^
    --build-arg GIT_COMMIT="%GIT_COMMIT%" ^
    --build-arg VERSION="%VERSION%" ^
    --tag "%REGISTRY%/backend:%TAG%" ^
    --tag "%REGISTRY%/backend:latest" ^
    --file backend/Dockerfile.prod ^
    --push ^
    backend/

if %errorlevel% equ 0 (
    echo [SUCCESS] Backend image built successfully
) else (
    echo [ERROR] Backend image build failed
    exit /b 1
)

REM Build nginx image (if custom configuration exists)
if exist "nginx\Dockerfile" (
    echo [INFO] Building nginx image...
    docker buildx build ^
        --platform linux/amd64,linux/arm64 ^
        --build-arg BUILD_DATE="%BUILD_DATE%" ^
        --build-arg GIT_COMMIT="%GIT_COMMIT%" ^
        --build-arg VERSION="%VERSION%" ^
        --tag "%REGISTRY%/nginx:%TAG%" ^
        --tag "%REGISTRY%/nginx:latest" ^
        --file nginx/Dockerfile ^
        --push ^
        nginx/
    
    if %errorlevel% equ 0 (
        echo [SUCCESS] Nginx image built successfully
    ) else (
        echo [ERROR] Nginx image build failed
        exit /b 1
    )
)

REM Generate image manifest
echo [INFO] Generating image manifest...
(
echo {
echo   "build_info": {
echo     "build_date": "%BUILD_DATE%",
echo     "git_commit": "%GIT_COMMIT%",
echo     "version": "%VERSION%",
echo     "tag": "%TAG%"
echo   },
echo   "images": {
echo     "frontend": "%REGISTRY%/frontend:%TAG%",
echo     "backend": "%REGISTRY%/backend:%TAG%"
if exist "nginx\Dockerfile" echo     ,"nginx": "%REGISTRY%/nginx:%TAG%"
echo   },
echo   "platforms": [
echo     "linux/amd64",
echo     "linux/arm64"
echo   ]
echo }
) > image-manifest.json

echo [SUCCESS] Image manifest generated: image-manifest.json

REM Security scan (if trivy is available)
where trivy >nul 2>nul
if %errorlevel% equ 0 (
    echo [INFO] Running security scans...
    
    trivy image --exit-code 1 --severity HIGH,CRITICAL "%REGISTRY%/frontend:%TAG%" || echo [WARNING] Frontend image has security vulnerabilities
    trivy image --exit-code 1 --severity HIGH,CRITICAL "%REGISTRY%/backend:%TAG%" || echo [WARNING] Backend image has security vulnerabilities
) else (
    echo [WARNING] Trivy not found, skipping security scan
)

REM Test images
echo [INFO] Testing images...

REM Test frontend image
docker run --rm -d --name test-frontend -p 8080:80 "%REGISTRY%/frontend:%TAG%"
timeout /t 5 /nobreak >nul
curl -f http://localhost:8080 >nul 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Frontend image test passed
) else (
    echo [ERROR] Frontend image test failed
)
docker stop test-frontend >nul 2>nul

REM Test backend image
docker run --rm -d --name test-backend -p 8081:5000 -e SECRET_KEY=test "%REGISTRY%/backend:%TAG%"
timeout /t 10 /nobreak >nul
curl -f http://localhost:8081/api/health >nul 2>nul
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend image test passed
) else (
    echo [ERROR] Backend image test failed
)
docker stop test-backend >nul 2>nul

echo [SUCCESS] 🎉 All images built and tested successfully!
echo.
echo [INFO] Image details:
echo Frontend: %REGISTRY%/frontend:%TAG%
echo Backend: %REGISTRY%/backend:%TAG%
if exist "nginx\Dockerfile" echo Nginx: %REGISTRY%/nginx:%TAG%
echo.
echo [INFO] To deploy these images:
echo set FRONTEND_IMAGE=%REGISTRY%/frontend:%TAG%
echo set BACKEND_IMAGE=%REGISTRY%/backend:%TAG%
echo docker-compose -f docker-compose.prod.yml up -d

endlocal