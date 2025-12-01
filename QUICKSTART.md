# Quick Start Guide - Local Development

This guide helps you quickly set up and run the chatroom application locally using Docker Compose.

## 📋 Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+
- Git (to clone the repository)

## 🚀 Start the Application

```bash
# Clone the repository (if not already done)
git clone <repository-url>
cd Chatroom-Microservice

# Start all services (PostgreSQL, MongoDB, Redis, Auth, Backend, Frontend)
docker compose up -d

# Wait for all services to be healthy (about 30 seconds)
docker compose ps

# Initialize database with sample users
curl http://localhost:5000/generate_db

# View logs from all services
docker compose logs -f
```

## 🌐 Access the Application

**Main Application**: http://localhost:3000

**Service Endpoints**:
- Frontend: http://localhost:3000
- Chat Backend: http://localhost:8000
- Auth Service: http://localhost:5000
- PostgreSQL: localhost:5432
- MongoDB: localhost:27017
- Redis: localhost:6379

## 👤 Using the App

### As a Guest (No Registration Required)
1. App opens → automatically assigned guest username
2. Start chatting immediately in any room
3. Click "Login / Register" button anytime to create account

### Creating an Account
1. Click "Login / Register" button
2. Click "Register" tab
3. Choose username (3-20 chars, alphanumeric + underscore)
4. Enter password (min 6 characters)
5. Confirm password
6. Click "Register" button
7. Instantly logged in with your new username!

### Logging In
1. Click "Login / Register" button
2. Enter username and password
3. Click "Login" button

### Sample Accounts (for testing)
- `alice` / `pass123`
- `bob` / `qwerty123`
- `charlie` / `hello123`

## 🛑 Stop the Application

```bash
# Stop all services
docker compose down

# Stop and remove volumes (WARNING: deletes database data)
docker compose down -v
```

## 🔄 Rebuild After Code Changes

```bash
# Rebuild and restart all services
docker compose up --build -d

# Rebuild specific service only
docker compose up -d --build backend
docker compose up -d --build frontend
docker compose up -d --build auth-service
```

## 📊 Check Status

```bash
# View all running containers
docker compose ps

# Check service health
curl http://localhost:5000/health  # Auth service
curl http://localhost:8000/health  # Chat backend

# View logs for specific service
docker compose logs -f backend
docker compose logs -f auth-service
docker compose logs -f frontend

# Check database connections
docker compose exec postgres pg_isready -U chatuser
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"
docker compose exec redis redis-cli ping
```

## 🐛 Troubleshooting

### Container Won't Start
```bash
# Check logs for the problematic service
docker compose logs [service-name]
# Examples: frontend, backend, auth-service, postgres, mongodb, redis

# Check if port is already in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Mac/Linux

# Restart specific service
docker compose restart [service-name]
```

### Database Not Initialized
```bash
# Initialize sample users
curl http://localhost:5000/generate_db

# Verify PostgreSQL is running
docker compose exec postgres psql -U chatuser -d chatroom -c "\dt"

# Verify MongoDB is running
docker compose exec mongodb mongosh chatroom --eval "db.rooms.find()"
```

### WebSocket Connection Fails
```bash
# Check backend is running
docker compose logs -f backend

# Verify Redis connection
docker compose exec redis redis-cli ping

# Check MongoDB connection
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Restart backend
docker compose restart backend
```

### Authentication Issues
```bash
# Check auth service logs
docker compose logs -f auth-service

# Verify PostgreSQL connection
docker compose exec postgres pg_isready -U chatuser

# Reinitialize database
curl http://localhost:5000/generate_db
```

### Port Already in Use
```powershell
# Windows: Find and kill process
netstat -ano | findstr :3000
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml
```

### Frontend Not Loading
```bash
# Rebuild frontend with no cache
docker compose build --no-cache frontend
docker compose up -d frontend

# Clear browser cache and reload
```

### Database Persistence Issues
```bash
# Check volumes
docker volume ls

# Remove volumes and start fresh (WARNING: deletes all data)
docker compose down -v
docker compose up -d
curl http://localhost:5000/generate_db
```

## 💡 Development Tips

### Working with the Code
- **Backend code**: Changes require rebuilding: `docker compose up -d --build backend`
- **Frontend code**: Changes require rebuilding: `docker compose up -d --build frontend`
- **Auth service code**: Changes require rebuilding: `docker compose up -d --build auth-service`
- **Live logs**: Use `docker compose logs -f [service]` to debug issues in real-time

### Database Management
- **Persistent data**: Database data persists in Docker volumes even after stopping containers
- **Fresh start**: Use `docker compose down -v` to delete all data and start clean
- **Sample users**: Run `curl http://localhost:5000/generate_db` to recreate test users

### Application Features
- **Guest mode**: Guest usernames persist across page reloads
- **Authentication**: Users stay logged in automatically via JWT tokens
- **Multiple rooms**: Switch between general, python, devops, and random rooms
- **User presence**: See who's online with real-time presence indicators
- **Message history**: Past messages load automatically from MongoDB

### Next Steps
- **Production deployment**: See [DEPLOYMENT.md](DEPLOYMENT.md) for Kubernetes setup
- **Load testing**: See [LOAD-TESTING.md](LOAD-TESTING.md) for k6 load testing
- **Docker reference**: See [DOCKER.md](DOCKER.md) for more Docker commands
- **Architecture details**: See [AUTH-INTEGRATION.md](AUTH-INTEGRATION.md) for auth flow

That's it! Enjoy your chatroom! 🎉
