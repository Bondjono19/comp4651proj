# Docker Quick Reference

## First Time Setup

```bash
# Build and start containers
docker-compose up --build

# Access the app at http://localhost:3000
```

## Daily Development

```bash
# Start containers (after initial build)
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f

# Stop containers
docker-compose down
```

## Rebuilding After Code Changes

```bash
# Rebuild both services
docker-compose up --build

# Rebuild specific service
docker-compose up -d --build backend
docker-compose up -d --build frontend
```

## Debugging

```bash
# Check container status
docker-compose ps

# View backend logs
docker-compose logs -f backend

# View frontend logs
docker-compose logs -f frontend

# Access backend container shell
docker-compose exec backend sh

# Access frontend container shell
docker-compose exec frontend sh

# Test backend health
curl http://localhost:8000/health
```

## Clean Up

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove everything including images
docker-compose down -v --rmi all

# Clean up Docker system (use with caution)
docker system prune -a
```

## AWS Deployment

```bash
# 1. Login to AWS ECR
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <aws-account-id>.dkr.ecr.<region>.amazonaws.com

# 2. Tag images for ECR
docker tag chatroom-backend:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-backend:latest
docker tag chatroom-frontend:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-frontend:latest

# 3. Push to ECR
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-backend:latest
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-frontend:latest
```

## Common Issues

### Port Already in Use
```bash
# Windows: Find process using port 8000
netstat -ano | findstr :8000
# Kill process: taskkill /PID <PID> /F

# Mac/Linux: Find and kill process
lsof -ti:8000 | xargs kill -9
```

### Container Won't Start
```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend

# Rebuild without cache
docker-compose build --no-cache
docker-compose up
```

### WebSocket Connection Failed
1. Check backend is running: `docker-compose ps`
2. Verify backend logs: `docker-compose logs backend`
3. Check CORS settings in `backend/main.py`
4. Ensure frontend can reach backend network: `docker network inspect chatroom-microservice_chatroom-network`

## Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit environment variables
# VITE_BACKEND_URL=ws://your-domain.com
# HOSTNAME=backend-1
```

## Performance Monitoring

```bash
# View resource usage
docker stats

# View backend metrics
curl http://localhost:8000/metrics

# Check health
curl http://localhost:8000/health
```
