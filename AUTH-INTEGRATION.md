# Authentication System Documentation

This document describes the authentication architecture and implementation of the chatroom application.

## 🏗️ Architecture Overview

The authentication system is implemented as a separate microservice using Flask, with PostgreSQL for user data storage. It integrates seamlessly with the chat backend and frontend, supporting both authenticated users and guest mode.

### Components

1. **Auth Service** (Flask microservice)
   - User registration and login
   - JWT token generation and verification
   - Password hashing with bcrypt
   - Input validation and sanitization
   - PostgreSQL database integration

2. **PostgreSQL Database**
   - User credentials storage
   - Bcrypt password hashing
   - Unique username constraints
   - Sample user data for testing

3. **Frontend Integration** (React)
   - Guest mode with auto-generated usernames
   - Login/Register modal UI
   - JWT token management via localStorage
   - Automatic token verification on load
   - Seamless guest-to-user transition

4. **Chat Backend Integration** (FastAPI)
   - No direct auth logic
   - Accepts any username from client
   - Frontend handles authentication state
   - Token validation done by auth service

## 🚀 Deployment Options

### Docker Compose (Local Development)

All services run locally:
- **Frontend**: http://localhost:3000
- **Chat Backend**: http://localhost:8000
- **Auth Service**: http://localhost:5000
- **PostgreSQL**: localhost:5432

```bash
# Start all services
docker compose up -d

# Initialize sample users
curl http://localhost:5000/generate_db
```

### Kubernetes (Production)

Services deployed to cluster with:
- NGINX Ingress Controller for routing
- PersistentVolume for PostgreSQL data
- Internal service-to-service communication
- Single external endpoint via Ingress

```bash
# Deploy to Kubernetes
kubectl apply -f kubernetes/

# Access via Ingress URL
kubectl get ingress main-ingress
```

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed Kubernetes setup.

## 🔐 API Endpoints

### POST `/register`
Register a new user account.

**Request Body**:
```json
{
  "username": "alice",
  "password": "pass123"
}
```

**Validations**:
- Username: 3-20 characters, alphanumeric + underscore only
- Password: minimum 6 characters
- Weak passwords rejected (password, 123456, etc.)
- Username uniqueness enforced

**Response** (Success - 201):
```json
{
  "message": "User registered successfully",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "alice"
}
```

**Response** (Error - 400):
```json
{
  "error": "Username already exists"
}
```

### POST `/login`
Authenticate an existing user.

**Request Body**:
```json
{
  "username": "alice",
  "password": "pass123"
}
```

**Response** (Success - 200):
```json
{
  "message": "Login successful",
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "username": "alice"
}
```

**Response** (Error - 401):
```json
{
  "error": "Invalid username or password"
}
```

### POST `/verify`
Verify a JWT token.

**Request Body**:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** (Valid - 200):
```json
{
  "valid": true,
  "username": "alice"
}
```

**Response** (Invalid - 401):
```json
{
  "valid": false,
  "error": "Token has expired"
}
```

### GET `/generate_db`
Initialize database with sample users (development only).

**Response** (200):
```json
{
  "message": "Database initialized successfully",
  "users_created": 5
}
```

**Sample Users Created**:
- `alice` / `pass123`
- `bob` / `qwerty123`
- `charlie` / `hello123`
- `dave` / `abc123def`
- `emma` / `secret123`

### GET `/health`
Health check endpoint.

**Response** (200):
```json
{
  "service": "auth-service",
  "status": "running",
  "health": "healthy"
}
```

## 🎮 User Experience Flow

### First-Time Visitor (Guest Mode)
1. App loads → automatically assigned random guest username (e.g., `guest4523`)
2. Can chat immediately in any room without registration
3. Sees banner: "You're browsing as a guest. Login or Register to save your username!"
4. Guest badge (yellow dot) shown next to username
5. Guest username persists in localStorage across page reloads

### Registering from Guest Mode
1. User clicks "Login / Register" button in header
2. Modal opens with login/register tabs
3. User switches to "Register" tab
4. Enters desired username and password
5. Real-time validation shows errors immediately
6. Clicks "Register" button
7. → Backend validates and creates account
8. → Frontend receives JWT token
9. → Token saved to localStorage
10. → Username updated from guest to registered username
11. → Guest badge removed, green dot appears
12. → User continues chatting with new username
13. → Banner disappears

### Logging In
1. User clicks "Login / Register" button
2. Modal opens on "Login" tab by default
3. Enters username and password
4. Clicks "Login" button
5. → Backend validates credentials
6. → Frontend receives JWT token
7. → Token saved to localStorage
8. → Green dot indicator appears
9. → User is authenticated

### Returning User (Auto-Login)
1. User visits site with token in localStorage
2. Frontend automatically calls `/verify` endpoint
3. If token valid → user logged in automatically
4. If token expired → user becomes guest with stored guest username
5. No re-login required for valid tokens

### Logging Out
1. User clicks "Logout" button
2. Token removed from localStorage
3. Username changes back to stored guest username
4. Green dot changes to yellow (guest indicator)
5. Guest banner reappears
6. Can continue chatting as guest

## 🔒 Security Implementation

### Password Security
- **Hashing**: bcrypt with automatic salt generation
- **Strength**: Minimum 6 characters required
- **Weak Password Detection**: Rejects common passwords (password, 123456, qwerty, etc.)
- **No Plain Text**: Passwords never stored or logged in plain text

### JWT Token Security
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 1 hour from generation
- **Secret**: Configurable via `JWT_SECRET` environment variable
- **Claims**: Contains username and expiration time
- **Verification**: Signature and expiration checked on every `/verify` call

### Input Validation
- **Username**: Regex validation (`^[a-zA-Z0-9_]{3,20}$`)
- **SQL Injection**: PostgreSQL parameterized queries
- **XSS Protection**: Input sanitization on backend
- **CSRF**: Not applicable (API-only, no cookies)

### Database Security
- **Unique Constraints**: Username uniqueness enforced at DB level
- **Connection String**: Configurable via environment variable
- **Credentials**: Stored in Kubernetes secrets or environment variables
- **Prepared Statements**: All queries use parameterized statements
- **CORS Configuration**: Proper origin restrictions

## 📊 Architecture

```
┌─────────────┐
│   Frontend  │  (React + Vite + Nginx)
│  Port 3000  │
└──────┬──────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌──────────┐  ┌──────────────┐
│ Backend  │  │ Auth Service │  (Flask)
│Port 8000 │  │  Port 5000   │
└──────────┘  └──────┬───────┘
                     │
                     ▼
              ┌──────────────┐
              │  PostgreSQL  │
              │  Port 5432   │
              └──────────────┘
```

## 🛠️ Commands

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f auth-service
docker compose logs -f frontend

# Stop services
docker compose down

# Rebuild after code changes
docker compose up --build -d

# Initialize database
curl http://localhost:5000/generate_db

# Check service health
curl http://localhost:5000/health
curl http://localhost:8000/health
```

## 📝 API Endpoints

### Auth Service (Port 5000)

**POST /register**
```json
{
  "username": "myusername",
  "password": "mypassword"
}
```
Response: `{ "access_token": "...", "username": "...", "message": "..." }`

**POST /login**
```json
{
  "username": "myusername",
  "password": "mypassword"
}
```
Response: `{ "access_token": "...", "username": "..." }`

**POST /verify**
```json
{
  "token": "your-jwt-token"
}
```
Response: `{ "valid": true, "user_id": 1, "username": "..." }`

**GET /health**
## 🎨 Frontend Implementation

### UI Components

**AuthForm Component** (`src/components/AuthForm.tsx`)
- Login/Register toggle tabs
- Real-time form validation
- Error message display
- Loading states during API calls
- "Continue as Guest" option

**User Presence Indicators**
- 🟢 **Green dot**: Authenticated user
- 🟡 **Yellow dot**: Guest user
- Shown next to username in chat header

**Guest Banner**
- Informative message for guest users
- Call-to-action to register
- Automatically hidden for authenticated users

### State Management

**localStorage Keys**:
- `authToken`: JWT token for authenticated users
- `username`: Current username (guest or authenticated)
- `guestUsername`: Persisted guest username

**React State**:
- `isAuthenticated`: Boolean authentication status
- `username`: Current display name
- `isLoading`: Loading state during API calls

**Token Lifecycle**:
1. On app load → Check localStorage for token
2. If token exists → Verify with `/verify` endpoint
3. If valid → Set authenticated state
4. If invalid/expired → Clear token, use guest mode
5. On logout → Clear token, revert to guest username

### API Service (`src/services/authService.ts`)

```typescript
// Register new user
authService.register(username, password)
  .then(({ token, username }) => {
    localStorage.setItem('authToken', token);
    localStorage.setItem('username', username);
  });

// Login existing user
authService.login(username, password)
  .then(({ token, username }) => {
    localStorage.setItem('authToken', token);
    localStorage.setItem('username', username);
  });

// Verify token
authService.verifyToken(token)
  .then(({ valid, username }) => {
    if (valid) {
      setIsAuthenticated(true);
    }
  });
```

## 🐳 Docker Configuration

### Environment Variables

**Auth Service**:
```yaml
environment:
  - DATABASE_URL=postgresql://chatuser:chatpass@postgres:5432/chatroom
  - JWT_SECRET=your-secret-key-change-in-production
  - FLASK_APP=app
```

**Frontend** (build-time):
```yaml
environment:
  - VITE_AUTH_URL=http://localhost:5000
  - VITE_BACKEND_URL=ws://localhost:8000
```

### Health Checks

All services include health checks:
```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## ☸️ Kubernetes Configuration

### Service Routing (Ingress)

```yaml
# Auth endpoints routed through Ingress
- path: /register
  backend: service-auth:5000
- path: /login
  backend: service-auth:5000
- path: /verify
  backend: service-auth:5000
- path: /generate_db
  backend: service-auth:5000
```

### Secrets

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
data:
  postgres-password: <base64-encoded>
  jwt-secret: <base64-encoded>
```

### Environment Variables

```yaml
env:
  - name: DATABASE_URL
    value: postgresql://chatuser:$(POSTGRES_PASSWORD)@service-db:5432/chatroom
  - name: JWT_SECRET
    valueFrom:
      secretKeyRef:
        name: app-secrets
        key: jwt-secret
```

## 🧪 Testing

### Manual Testing
```bash
# Register a new user
curl -X POST http://localhost:5000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# Login
curl -X POST http://localhost:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"test123"}'

# Verify token
curl -X POST http://localhost:5000/verify \
  -H "Content-Type: application/json" \
  -d '{"token":"<your-jwt-token>"}'

# Initialize sample users
curl http://localhost:5000/generate_db
```

### Expected Behaviors
- ✅ Registration creates user and returns JWT
- ✅ Login validates credentials and returns JWT
- ✅ Duplicate usernames are rejected
- ✅ Weak passwords are rejected
- ✅ Invalid tokens fail verification
- ✅ Expired tokens (>1 hour) fail verification
- ✅ Guest mode works without authentication

## 🔧 Production Recommendations

### Security Enhancements
- [ ] Use strong JWT secret (32+ characters, random)
- [ ] Enable HTTPS/TLS for all endpoints
- [ ] Implement rate limiting on auth endpoints
- [ ] Add CAPTCHA for registration
- [ ] Enable audit logging for authentication events
- [ ] Implement account lockout after failed login attempts
- [ ] Add email verification for new accounts
- [ ] Implement refresh tokens for longer sessions

### Database Enhancements
- [ ] Use managed PostgreSQL (RDS, Cloud SQL)
- [ ] Enable automated backups
- [ ] Set up read replicas for scaling
- [ ] Implement connection pooling
- [ ] Add database indexes on username column

### Monitoring
- [ ] Log all authentication attempts
- [ ] Monitor failed login rates
- [ ] Track token verification failures
- [ ] Alert on unusual authentication patterns
- [ ] Monitor database query performance

## 🎯 Optional Enhancements

Future features to consider:
- Password reset via email
- OAuth providers (Google, GitHub, etc.)
- Two-factor authentication (2FA)
- User profile pages with avatars
- Admin panel for user management
- Password change functionality
- Session management (view/revoke active sessions)
- Private messaging between users
- User-specific message history
- Username change functionality

---

**For deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**  
**For local development, see [QUICKSTART.md](QUICKSTART.md)**
