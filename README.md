# COMP4651 Chatroom Microservice

A production-ready, real-time chatroom application built with microservices architecture, designed for Kubernetes deployment with full authentication, distributed messaging, and horizontal scalability.

## 🏗️ Architecture

### Services
- **Frontend**: React + TypeScript SPA served by Nginx (Port 80/3000)
- **Backend (Chat Service)**: Python FastAPI WebSocket server (Port 8000)
  - Real-time messaging via WebSocket
  - Distributed message broadcasting with Redis Pub/Sub
  - Message persistence with MongoDB
- **Auth Service**: Flask authentication microservice (Port 5000)
  - JWT-based authentication
  - User registration and login
  - PostgreSQL database for user credentials
- **PostgreSQL**: User authentication database (Port 5432)
- **MongoDB**: Chat message and room persistence (Port 27017)
- **Redis**: Pub/Sub for cross-instance messaging (Port 6379)

### Key Features
- ✅ **Authentication**: JWT-based with guest mode support
- ✅ **Real-time Chat**: WebSocket connections with message broadcasting
- ✅ **Horizontal Scaling**: Redis Pub/Sub enables multiple backend instances
- ✅ **Persistence**: MongoDB stores messages, PostgreSQL stores users
- ✅ **Multiple Chat Rooms**: general, python, devops, random
- ✅ **Cloud-Native**: Kubernetes manifests included for production deployment

## 📋 Prerequisites

### For Local Development (Docker Compose)
- Docker Desktop (Windows/Mac) or Docker Engine (Linux)
- Docker Compose v2.0+

### For Production Deployment (Kubernetes)
- kubectl (Kubernetes CLI)
- A Kubernetes cluster (EKS, AKS, GKE, or local like minikube)
- eksctl (for AWS EKS deployment)

## 🚀 Quick Start

### Option 1: Kubernetes Deployment (Recommended for Production)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete Kubernetes setup instructions.

Quick deploy to existing cluster:
```bash
# Apply all Kubernetes manifests
kubectl apply -f kubernetes/

# Wait for pods to be ready
kubectl get pods --watch

# Get application URL
kubectl get ingress main-ingress
```

### Option 2: Docker Compose (Recommended for Local Development)

```bash
# Start all services
docker compose up -d

# Initialize sample users
curl http://localhost:5000/generate_db

# Access the application
# Frontend: http://localhost:3000
# Auth API: http://localhost:5000
# Chat API: http://localhost:8000
```

See **[QUICKSTART.md](QUICKSTART.md)** for detailed local development guide.

## 🧪 Testing

### Sample Users (After running `/generate_db`)
- Username: `alice` / Password: `pass123`
- Username: `bob` / Password: `qwerty123`
- Username: `charlie` / Password: `hello123`

### Load Testing
See **[LOAD-TESTING.md](LOAD-TESTING.md)** for comprehensive load testing guide using k6.

## 📦 Service Details

### Chat Backend
- **Technology**: Python FastAPI with WebSocket support
- **Database**: MongoDB (messages, rooms)
- **Cache/Pub-Sub**: Redis (distributed messaging)
- **Health Endpoint**: `/health`
- **WebSocket**: `/ws`

### Auth Service
- **Technology**: Flask with Flask-Bcrypt
- **Database**: PostgreSQL (users, passwords)
- **Security**: JWT tokens, bcrypt password hashing
- **Endpoints**: 
  - `POST /register` - Create new account
  - `POST /login` - Authenticate user
  - `POST /verify` - Verify JWT token
  - `GET /generate_db` - Initialize sample users

### Frontend
- **Technology**: React + TypeScript with Vite
- **Server**: Nginx (production)
- **Features**: 
  - Guest mode (instant access)
  - User authentication
  - Multiple chat rooms
  - Real-time message updates
  - User presence indicators

## 🐳 Docker Compose

For local development, all services run in Docker containers with health checks and automatic restarts.

```bash
# View logs
docker compose logs -f

# Rebuild specific service
docker compose up -d --build backend

# Execute commands in containers
docker compose exec backend python -c "print('Hello')"

# Clean up
docker compose down -v
```

See **[DOCKER.md](DOCKER.md)** for complete Docker reference.

## ☸️ Kubernetes Deployment

The application is designed for Kubernetes-first deployment with:
- Deployment manifests for all services
- Service definitions with proper networking
- PersistentVolumeClaims for databases
- NGINX Ingress Controller configuration
- Secret management
- Health checks and readiness probes

### Quick Kubernetes Deploy
```bash
# Apply all manifests
kubectl apply -f kubernetes/

# Check status
kubectl get all

# Access via Ingress
kubectl get ingress main-ingress
```

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for step-by-step Kubernetes deployment guide.

## 🏗️ Project Structure

```
.
├── backend/                    # Chat WebSocket service
│   ├── main.py                # FastAPI WebSocket server
│   ├── mongodb_manager.py     # MongoDB connection & queries
│   ├── redis_manager.py       # Redis Pub/Sub manager
│   ├── requirement.txt        # Python dependencies
│   └── Dockerfile
├── auth-service/              # Authentication service
│   ├── app/
│   │   ├── routes.py         # Auth endpoints
│   │   ├── database.py       # PostgreSQL connection
│   │   └── utils.py          # JWT utilities
│   ├── db.sql                # Database schema
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                  # React web application
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── services/         # API service clients
│   │   └── hooks/            # Custom React hooks
│   ├── nginx.conf            # Production web server config
│   ├── package.json
│   └── Dockerfile
├── kubernetes/                # Kubernetes manifests
│   ├── deploy-*.yaml         # Deployment definitions
│   ├── service-*.yaml        # Service definitions
│   ├── volume-*.yaml         # PersistentVolumes
│   ├── secret.yaml           # Secrets configuration
│   └── deploy-ingress.yaml   # Ingress routing
├── docker-compose.yml         # Local development orchestration
├── load-test-scenarios.js     # k6 load testing scenarios
├── README.md                  # This file
├── QUICKSTART.md             # Local development guide
├── DEPLOYMENT.md             # Kubernetes deployment guide
├── DOCKER.md                 # Docker reference
├── AUTH-INTEGRATION.md       # Authentication details
└── LOAD-TESTING.md           # Load testing guide
```

## 🔧 Configuration

### Environment Variables

**Backend (Chat Service)**
- `REDIS_URL`: Redis connection string (default: `redis://redis:6379`)
- `MONGO_URL`: MongoDB connection string (default: `mongodb://mongodb:27017/chatroom`)
- `HOSTNAME`: Pod/instance identifier for debugging

**Auth Service**
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret key for JWT signing (change in production!)
- `FLASK_APP`: Flask application module

**Frontend**
- `VITE_BACKEND_URL`: WebSocket URL for chat backend
- `VITE_AUTH_URL`: HTTP URL for auth service

## 🐛 Troubleshooting

### WebSocket Connection Issues
```bash
# Check backend logs
docker compose logs -f backend
# or in Kubernetes
kubectl logs -l app=chat

# Verify Redis connection
docker compose exec redis redis-cli ping
```

### Authentication Issues
```bash
# Check auth service logs
docker compose logs -f auth-service
# or in Kubernetes
kubectl logs -l app=auth

# Verify database initialized
curl http://localhost:5000/generate_db
```

### Database Connection Issues
```bash
# Check PostgreSQL
docker compose exec postgres pg_isready -U chatuser

# Check MongoDB
docker compose exec mongodb mongosh --eval "db.adminCommand('ping')"

# Check Redis
docker compose exec redis redis-cli ping
```

### Port Already in Use
```powershell
# Windows: Find process using port
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or change ports in docker-compose.yml
```

## 📝 Features

- ✅ Real-time WebSocket communication with Redis Pub/Sub
- ✅ Multiple chat rooms (general, python, devops, random)
- ✅ User authentication with JWT tokens
- ✅ Guest mode for instant access
- ✅ Message persistence in MongoDB
- ✅ User presence notifications
- ✅ Horizontal scaling support
- ✅ Kubernetes-ready with health checks
- ✅ Load balancing and ingress routing

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Test locally with Docker Compose: `docker compose up --build`
4. Commit your changes
5. Submit a pull request

## 📄 License

This project is part of COMP4651 coursework at HKUST.

## 🔗 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [React Documentation](https://react.dev/)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Redis Pub/Sub Guide](https://redis.io/docs/manual/pubsub/)
- [MongoDB Documentation](https://www.mongodb.com/docs/)
- [JWT Authentication](https://jwt.io/introduction)
