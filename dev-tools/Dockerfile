# Development tools container
FROM node:18-alpine

# Install system dependencies
RUN apk add --no-cache \
    python3 \
    py3-pip \
    curl \
    bash \
    git \
    docker-cli

# Set working directory
WORKDIR /app

# Install global npm packages for development
RUN npm install -g \
    nodemon \
    concurrently \
    http-server \
    json-server

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p logs

# Expose ports
EXPOSE 8080 9090 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start development dashboard
CMD ["npm", "start"]