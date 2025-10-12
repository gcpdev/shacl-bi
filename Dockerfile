# ============================================
# STAGE 1: Build Frontend
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /build

# Copy package files
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy source files (excluding node_modules if it exists)
COPY frontend/ ./

# Build the frontend
RUN npm run build

# ============================================
# STAGE 2: Final Image
# ============================================
FROM python:3.9-slim

WORKDIR /app

# ============================================
# BACKEND SETUP
# ============================================
# Copy only requirements first for better layer caching
COPY backend/requirements.txt ./backend/requirements.txt
WORKDIR /app/backend
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy the rest of backend files
COPY backend/ ./

# ============================================
# COPY FRONTEND BUILD ARTIFACTS
# ============================================
# Copy only the built frontend from the builder stage (Vite builds to 'dist')
COPY --from=frontend-builder /build/dist ./static/

# Set final working directory
WORKDIR /app/backend

# Expose the necessary port
EXPOSE 80

# Run the Python backend server