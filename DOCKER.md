# Docker Compose Quick Reference

This document provides quick Docker Compose commands for local development. For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md).

## 🏗️ Services Architecture

- **PostgreSQL**: User authentication database (port 5432)
- **MongoDB**: Message and room storage (port 27017)
- **Redis**: Pub/Sub for distributed messaging (port 6379)
- **Auth Service**: Flask authentication API (port 5000)
- **Backend**: FastAPI WebSocket server (port 8000)
- **Frontend**: React + Nginx web app (port 3000)

## 🚀 First Time Setup

```bash
# Clone repository
git clone <repository-url>
cd Chatroom-Microservice

# Build and start all containers
docker compose up --build -d

# Initialize database with sample users
curl http://localhost:5000/generate_db

# Access the app at http://localhost:3000
```

## 📅 Daily Development

```bash
# Start all containers (after initial build)
docker compose up -d

# View logs from all services
docker compose logs -f

# View logs from specific service
docker compose logs -f backend

# Stop all containers
docker compose down
```

## 🔨 Rebuilding After Code Changes

```bash
# Rebuild all services
docker compose up --build -d

# Rebuild specific service only
docker compose up -d --build backend
docker compose up -d --build frontend
docker compose up -d --build auth-service
```

## 🔍 Debugging & Monitoring

```bash
# Check status of all containers
docker compose ps

# View logs from specific services
docker compose logs -f backend           # Chat backend
docker compose logs -f frontend          # React frontend
docker compose logs -f auth-service      # Auth service
docker compose logs -f postgres          # PostgreSQL
docker compose logs -f mongodb           # MongoDB
docker compose logs -f redis             # Redis

# View last 50 lines of logs
docker compose logs --tail=50 backend

# Access container shell
docker compose exec backend sh           # Python backend
docker compose exec frontend sh          # Nginx frontend
docker compose exec auth-service sh      # Flask auth
docker compose exec postgres bash        # PostgreSQL
docker compose exec mongodb mongosh      # MongoDB shell
docker compose exec redis redis-cli      # Redis CLI

# Test service health
curl http://localhost:5000/health        # Auth service
curl http://localhost:8000/health        # Chat backend

# Check database connections
docker compose exec postgres pg_isready -U chatuser
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker compose exec redis redis-cli ping

# Inspect container details
docker compose exec backend env          # View environment variables
docker inspect chatroom-backend          # Full container details
```

## 🗄️ Database Management

```bash
# Access PostgreSQL
docker compose exec postgres psql -U chatuser -d chatroom

# Backup PostgreSQL
docker compose exec postgres pg_dump -U chatuser chatroom > backup.sql

# Restore PostgreSQL
cat backup.sql | docker compose exec -T postgres psql -U chatuser -d chatroom

# Access MongoDB
docker compose exec mongodb mongosh chatroom

# View MongoDB collections
docker compose exec mongodb mongosh chatroom --eval "db.getCollectionNames()"

# Access Redis
docker compose exec redis redis-cli

# View Redis keys
docker compose exec redis redis-cli KEYS "*"
```

## 🧹 Clean Up

```bash
# Stop all containers
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v

# Remove everything including images
docker compose down -v --rmi all

# Clean up Docker system (removes all unused resources)
docker system prune -a --volumes
```

## 🐳 Building & Pushing Images

### Build Locally
```bash
# Build specific service
docker compose build backend
docker compose build frontend
docker compose build auth-service

# Build with no cache (force fresh build)
docker compose build --no-cache backend
```

### Push to Container Registry

**GitHub Container Registry (ghcr.io)**:
```bash
# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u USERNAME --password-stdin

# Tag images
docker tag chatroom-backend:latest ghcr.io/username/chatroom-backend:latest
docker tag chatroom-frontend:latest ghcr.io/username/chatroom-frontend:latest
docker tag chatroom-auth:latest ghcr.io/username/chatroom-auth:latest

# Push images
docker push ghcr.io/username/chatroom-backend:latest
docker push ghcr.io/username/chatroom-frontend:latest
docker push ghcr.io/username/chatroom-auth:latest
```

**AWS ECR**:
```bash
# Login to AWS ECR
aws ecr get-login-password --region us-west-1 | \
  docker login --username AWS --password-stdin \
  123456789.dkr.ecr.us-west-1.amazonaws.com

# Tag images
docker tag chatroom-backend:latest 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-backend:latest
docker tag chatroom-frontend:latest 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-frontend:latest
docker tag chatroom-auth:latest 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-auth:latest

# Push images
docker push 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-backend:latest
docker push 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-frontend:latest
docker push 123456789.dkr.ecr.us-west-1.amazonaws.com/chatroom-auth:latest
```

## 🐛 Common Issues

### Port Already in Use
```powershell
# Windows: Find and kill process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Mac/Linux: Find and kill process
lsof -ti:8000 | xargs kill -9
```

### Service Not Starting
```bash
# Check logs for errors
docker compose logs backend
docker compose logs auth-service

# Check if dependencies are healthy
docker compose ps

# Rebuild without cache
docker compose build --no-cache backend
docker compose up -d
```

### Database Connection Failed
```bash
# Check if databases are running
docker compose ps postgres mongodb redis

# Check database health
docker compose exec postgres pg_isready -U chatuser
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker compose exec redis redis-cli ping

# Restart database services
docker compose restart postgres mongodb redis
```

### WebSocket Connection Failed
```bash
# Check backend is running
docker compose ps backend

# Verify backend logs
docker compose logs -f backend

# Check Redis connection (required for WebSocket)
docker compose exec redis redis-cli ping

# Restart backend
docker compose restart backend
```

### Authentication Issues
```bash
# Check auth service logs
docker compose logs -f auth-service

# Verify PostgreSQL database
docker compose exec postgres psql -U chatuser -d chatroom -c "\dt"

# Reinitialize database with sample users
curl http://localhost:5000/generate_db
```

## 📊 Performance Monitoring

```bash
# View real-time resource usage for all containers
docker stats

# Check service health endpoints
curl http://localhost:5000/health        # Auth service
curl http://localhost:8000/health        # Chat backend

# Monitor PostgreSQL connections
docker compose exec postgres psql -U chatuser -d chatroom -c "SELECT * FROM pg_stat_activity;"

# Monitor Redis
docker compose exec redis redis-cli INFO memory

# Monitor MongoDB
docker compose exec mongodb mongosh --eval "db.currentOp()"
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file (optional):
```bash
VITE_BACKEND_URL=ws://custom-domain.com
VITE_AUTH_URL=http://custom-domain.com
JWT_SECRET=your-custom-secret-key
HOSTNAME=backend-instance-1
```

### Network Inspection
```bash
# List Docker networks
docker network ls

# Inspect network
docker network inspect chatroom-microservice_default

# Test connectivity
docker compose exec frontend ping backend
docker compose exec backend ping postgres
```

---

**For production deployment, see [DEPLOYMENT.md](DEPLOYMENT.md)**
