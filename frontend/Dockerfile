# Build stage
FROM node:18-alpine as build-stage

# Install build dependencies for better caching
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package files first to leverage Docker cache
COPY package*.json ./

# Use npm ci for faster, reliable installs with better caching
# Configure npm for optimal performance in CI/CD
RUN npm ci --prefer-offline --no-audit --no-fund --cache=/tmp/.npm --maxsockets=4

# Copy source code
COPY . .

# Optimize build for production
ENV NODE_ENV=production
ENV VITE_CJS_IGNORE_WARNING=true

# Build with Vite (automatically uses production mode when NODE_ENV=production)
RUN npm run build

# Production stage
FROM nginx:alpine as production-stage

# Copy built files from build stage
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]