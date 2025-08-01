# Docker Deployment Guide

## 🐳 Docker Setup for Delhi High Court Scraper

This guide covers the Docker containerization setup for the Delhi High Court case scraper application.

## 📋 Files Added

### `Dockerfile`
- **Base Image**: Python 3.11 slim
- **Security**: Non-root user for container security
- **Health Check**: Automatic health monitoring
- **Port**: Exposes port 5000
- **Optimizations**: Multi-stage copying for Docker cache efficiency

### `docker-compose.yml`
- **Service Definition**: Complete application stack
- **Volume Mapping**: Persistent downloads and logs
- **Health Checks**: Container health monitoring
- **Network**: Isolated bridge network
- **Restart Policy**: Automatic restart on failure

### `.dockerignore`
- **Build Optimization**: Excludes unnecessary files from Docker context
- **Security**: Prevents sensitive files from entering container
- **Size Reduction**: Reduces image size by excluding cache and temp files

## 🚀 Quick Start

### Using Docker Compose (Recommended)
```bash
# Build and start the application
docker-compose up --build

# Run in background
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the application
docker-compose down
```

### Using Docker Commands
```bash
# Build the image
docker build -t delhi-court-scraper .

# Run the container
docker run -d \
  --name delhi-court-scraper \
  -p 5000:5000 \
  -v $(pwd)/downloads:/app/downloads \
  delhi-court-scraper

# View logs
docker logs delhi-court-scraper

# Stop and remove
docker stop delhi-court-scraper
docker rm delhi-court-scraper
```

## 🔧 Configuration

### Environment Variables
- `FLASK_ENV=production`: Sets Flask to production mode
- `PYTHONUNBUFFERED=1`: Ensures real-time log output
- `FLASK_APP=app.py`: Specifies the Flask application file

### Volume Mounts
- `./downloads:/app/downloads`: Persists downloaded PDF files
- `./logs:/app/logs`: Persists application logs (optional)

### Health Checks
- **URL**: `http://localhost:5000/`
- **Interval**: Every 30 seconds
- **Timeout**: 10 seconds
- **Retries**: 3 attempts
- **Start Period**: 40 seconds grace period

## 🔍 Monitoring

### Check Container Status
```bash
# View running containers
docker ps

# Check health status
docker inspect delhi-court-scraper | grep Health -A 10

# View resource usage
docker stats delhi-court-scraper
```

### Access Logs
```bash
# Real-time logs
docker-compose logs -f delhi-court-scraper

# Last 100 lines
docker-compose logs --tail=100 delhi-court-scraper
```

## 🛠️ Development

### Development Mode
```bash
# Override for development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Debugging
```bash
# Run container interactively
docker run -it --rm delhi-court-scraper /bin/bash

# Execute commands in running container
docker exec -it delhi-court-scraper /bin/bash
```

## 🔐 Security Features

1. **Non-root User**: Container runs as non-privileged user
2. **Minimal Base Image**: Uses slim Python image
3. **Health Checks**: Automatic failure detection
4. **Isolated Network**: Custom bridge network
5. **Read-only Filesystem**: Application files are read-only

## 📊 Benefits

### Deployment
- **Consistency**: Same environment across all deployments
- **Isolation**: No conflicts with host system
- **Portability**: Runs on any Docker-enabled system
- **Scalability**: Easy to scale with orchestration tools

### Maintenance
- **Easy Updates**: Simple image rebuild and redeploy
- **Rollback**: Quick rollback to previous versions
- **Monitoring**: Built-in health checks and logging
- **Cleanup**: Complete environment cleanup with single command

## 🌐 Production Considerations

### Reverse Proxy
Consider using nginx or traefik for production:
```yaml
# Add to docker-compose.yml
nginx:
  image: nginx:alpine
  ports:
    - "80:80"
  volumes:
    - ./nginx.conf:/etc/nginx/nginx.conf
  depends_on:
    - delhi-court-scraper
```

### SSL/TLS
For HTTPS in production:
```yaml
# Use with Let's Encrypt or other SSL providers
environment:
  - VIRTUAL_HOST=your-domain.com
  - LETSENCRYPT_HOST=your-domain.com
```

### Resource Limits
Add resource constraints for production:
```yaml
deploy:
  resources:
    limits:
      cpus: '0.5'
      memory: 512M
    reservations:
      cpus: '0.25'
      memory: 256M
```

This Docker setup provides a robust, production-ready deployment option for the Delhi High Court scraper application.
