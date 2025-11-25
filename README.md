# COMP4651 Chatroom Microservice as a Containerized Application

This repository contains a simple chatroom microservice implemented as a containerized application with Docker and Docker Compose, ready for deployment to AWS or Kubernetes.

## Architecture

- **Backend**: Python FastAPI WebSocket server (Port 8000)
- **Frontend**: React + Vite SPA served by Nginx (Port 3000)
- **Communication**: WebSocket connections for real-time chat
- **Container Orchestration**: Docker Compose

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v3.8+

## 🚀 Quick Start with Docker (Recommended)

### 1. Build and Run with Docker Compose

```bash
# Build and start both services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build
```

### 2. Access the Application

- **Frontend**: <http://localhost:3000>
- **Backend API**: <http://localhost:8000>
- **Health Check**: <http://localhost:8000/health>
- **Metrics**: <http://localhost:8000/metrics>

### 3. Stop the Services

```bash
# Stop and remove containers
docker-compose down

# Stop and remove containers, networks, and volumes
docker-compose down -v
```

## 🛠️ Development Setup (Without Docker)

### Backend Setup

```bash
cd backend

python -m venv venv

# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

pip install -r requirements.txt

python main.py
```

### Frontend Setup

```bash
cd frontend

npm install

npm run dev
```

## 📦 Docker Details

### Container Structure

- **Backend Container**: `chatroom-backend`
  - Base image: `python:3.12-slim`
  - Exposed port: 8000
  - Health check: `/health` endpoint

- **Frontend Container**: `chatroom-frontend`
  - Build stage: Node.js 20 Alpine
  - Runtime stage: Nginx Alpine
  - Exposed port: 80 (mapped to host 3000)
  - Serves static files and proxies WebSocket connections

### Docker Commands

```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# View backend logs only
docker-compose logs -f backend

# View frontend logs only
docker-compose logs -f frontend

# Rebuild a specific service
docker-compose up -d --build backend

# Execute commands in containers
docker-compose exec backend python -c "print('Hello from backend')"
docker-compose exec frontend sh

# Clean up everything
docker-compose down -v --rmi all
```

## 🌐 AWS Deployment Notes

### Preparing for AWS ECS/EKS

1. **Push images to ECR (Elastic Container Registry)**:

```bash
# Tag images
docker tag chatroom-backend:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-backend:latest
docker tag chatroom-frontend:latest <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-frontend:latest

# Push to ECR
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-backend:latest
docker push <aws-account-id>.dkr.ecr.<region>.amazonaws.com/chatroom-frontend:latest
```

2. **Environment Variables**: Update `VITE_BACKEND_URL` to point to your AWS load balancer or API Gateway URL

3. **CORS Configuration**: Update backend `main.py` to include your production domain

4. **Health Checks**: Both containers include health checks compatible with AWS ECS/EKS

## 🔧 Configuration

### Environment Variables

Copy `.env.example` to `.env` and customize:

```bash
cp .env.example .env
```

- `VITE_BACKEND_URL`: WebSocket backend URL (default: `ws://localhost:8000`)
- `HOSTNAME`: Backend server identifier for metrics

## 🏗️ Project Structure

```
.
├── backend/
│   ├── Dockerfile          # Backend container definition
│   ├── .dockerignore       # Files to exclude from backend image
│   ├── main.py             # FastAPI WebSocket server
│   └── requirement.txt     # Python dependencies
├── frontend/
│   ├── Dockerfile          # Frontend multi-stage build
│   ├── .dockerignore       # Files to exclude from frontend image
│   ├── nginx.conf          # Nginx configuration for production
│   ├── src/                # React source code
│   └── package.json        # Node dependencies
├── docker-compose.yml      # Container orchestration
└── .env.example            # Example environment configuration
```

## 🐛 Troubleshooting

### WebSocket Connection Issues

If WebSocket connections fail:

1. Ensure backend is running: `docker-compose logs backend`
2. Check CORS settings in `backend/main.py`
3. Verify network connectivity: `docker network inspect chatroom-microservice_chatroom-network`

### Container Build Fails

- **Backend**: Check Python version and package compatibility
- **Frontend**: Ensure `node_modules` is excluded by `.dockerignore`
- Clear Docker cache: `docker-compose build --no-cache`

### Port Already in Use

```bash
# Check what's using the port
netstat -ano | findstr :8000    # Windows
lsof -i :8000                   # Mac/Linux

# Stop and change port in docker-compose.yml
```

## 📝 Features

- Real-time WebSocket communication
- Multiple chat rooms (general, python, devops, random)
- User presence notifications
- Message history
- Health checks and metrics
- Container orchestration with Docker Compose
- Production-ready with Nginx
- AWS deployment ready

## 🤝 Contributing

1. Create a feature branch
2. Test with Docker: `docker-compose up --build`
3. Commit your changes
4. Submit a pull request

## 📄 License

MIT License
