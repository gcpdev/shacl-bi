@echo off
echo 🚀 Starting optimized frontend Docker build with Bake...

REM Create build cache directory if it doesn't exist
if not exist ".docker-cache" mkdir .docker-cache

REM Enable Docker BuildKit and Bake for maximum performance
set DOCKER_BUILDKIT=1
set COMPOSE_DOCKER_CLI_BUILD=1
set COMPOSE_BAKE=true

echo 📦 Building with Bake optimization...
REM Use docker-compose with Bake for optimal performance
cd .. && docker-compose build --build

echo ✅ Frontend build completed successfully with Bake optimization!
pause