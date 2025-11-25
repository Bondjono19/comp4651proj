# Quick Start Guide - Authenticated Chatroom

## 🚀 Start the Application

```bash
# Start all services (PostgreSQL, Auth, Backend, Frontend)
docker compose up -d

# Initialize database with sample users
curl http://localhost:5000/generate_db

# View logs
docker compose logs -f
```

## 🌐 Access the Application

Open http://localhost:3000 in your browser

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
docker compose down
```

## 🔄 Rebuild After Changes

```bash
docker compose down
docker compose up --build -d
```

## 📊 Check Status

```bash
# View running containers
docker compose ps

# Check auth service
curl http://localhost:5000/health

# Check backend
curl http://localhost:8000/health
```

## 🐛 Troubleshooting

**Container won't start?**
```bash
docker compose logs [service-name]
# Examples: frontend, backend, auth-service, postgres
```

**Database not initialized?**
```bash
curl http://localhost:5000/generate_db
```

**Port already in use?**
```bash
# Stop existing containers
docker compose down

# Or change ports in docker-compose.yml
```

**Frontend not loading?**
```bash
# Rebuild frontend
docker compose up --build -d frontend
```

## 💡 Tips

- Guest usernames persist across page reloads
- Authenticated users stay logged in automatically
- Switch between rooms anytime
- Logout returns you to guest mode
- Register to save your username permanently

That's it! Enjoy your chatroom! 🎉
