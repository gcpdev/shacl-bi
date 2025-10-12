#!/bin/bash

# Optimized Docker build script for frontend with Bake
# Usage: ./scripts/docker-build.sh

set -e

echo "🚀 Starting optimized frontend Docker build with Bake..."

# Create build cache directory if it doesn't exist
mkdir -p .docker-cache

# Enable Docker BuildKit and Bake for maximum performance
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
export COMPOSE_BAKE=true

echo "📦 Building with Bake optimization..."
# Use docker-compose with Bake for optimal performance
cd .. && docker-compose build --build

echo "✅ Frontend build completed successfully with Bake optimization!"