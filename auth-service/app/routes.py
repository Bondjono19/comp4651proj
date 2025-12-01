from flask import request, jsonify
from app.database import get_database
from flask_bcrypt import Bcrypt
from app.utils import generate_jwt
import re
import os

POD_NAME = os.getenv("POD_NAME","unknown")

def register_routes(app):

    @app.route("/")
    def home():
        print(f"User connected to endpoint: '/loadbalancetest' in Pod:{POD_NAME}")
        return jsonify({"service": "auth-service", "status": "running","pod_instance":POD_NAME})
    
    @app.route('/health')
    def health():
        print(f"User connected to endpoint: '/health' in Pod:{POD_NAME}")
        return jsonify({"service": "auth-service", "status": "running","health":"healthy","pod_instance":POD_NAME})

    @app.route('/register', methods=['POST'])
    def register():
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')

        # Validation
        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400
        
        # Username validation: 3-20 chars, alphanumeric and underscore only
        if not re.match(r'^[a-zA-Z0-9_]{3,20}$', username):
            return jsonify({"error": "Username must be 3-20 characters, alphanumeric and underscore only"}), 400
        
        # Password validation: minimum 6 characters
        if len(password) < 6:
            return jsonify({"error": "Password must be at least 6 characters"}), 400
        
        # Check for common weak passwords
        weak_passwords = ['password', '123456', 'password123', 'qwerty', 'abc123']
        if password.lower() in weak_passwords:
            return jsonify({"error": "Password is too weak, please choose a stronger password"}), 400

        bcrypt = Bcrypt(app)
        db = get_database()
        cursor = db.cursor()

        # Check if username already exists
        cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            return jsonify({"error": "Username already exists"}), 409
        
        # Create new user
        try:
            password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id",
                (username, password_hash)
            )
            user_id = cursor.fetchone()[0]
            db.commit()
            
            # Generate JWT token for immediate login
            token = generate_jwt(user_id)
            
            return jsonify({
                "message": "User registered successfully",
                "access_token": token,
                "username": username
            }), 201
        except Exception as e:
            db.rollback()
            return jsonify({"error": "Registration failed", "details": str(e)}), 500

    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return jsonify({"error": "Username and password are required"}), 400

        bcrypt = Bcrypt(app)

        sql = "SELECT id,password_hash FROM users WHERE username = %s"

        db = get_database()
        cursor = db.cursor()
        cursor.execute(sql,(username,))    
        res = cursor.fetchone()
        if not res:
            return jsonify({"error":"User not found"}), 404
        elif bcrypt.check_password_hash(res[1], password):
            token = generate_jwt(res[0])
            return jsonify({
                "access_token": token,
                "username": username
            }), 200
        else:
            return jsonify({"error":"Invalid credentials"}), 401
    
    @app.route('/verify', methods=['POST'])
    def verify():
        """Verify JWT token and return user info"""
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({"error": "Token is required"}), 400
        
        try:
            import jwt
            from flask import current_app
            payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
            user_id = payload['sub']
            
            db = get_database()
            cursor = db.cursor()
            cursor.execute("SELECT username FROM users WHERE id = %s", (user_id,))
            result = cursor.fetchone()
            
            if result:
                return jsonify({
                    "valid": True,
                    "user_id": user_id,
                    "username": result[0]
                }), 200
            else:
                return jsonify({"error": "User not found"}), 404
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token has expired"}), 401
        except jwt.InvalidTokenError:
            return jsonify({"error": "Invalid token"}), 401
    
    @app.route('/generate_db')
    def generate_db():
        bcrypt = Bcrypt(app)
        db = get_database()
        cursor = db.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id BIGSERIAL PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        );
        """)
        db.commit()
        users = [
            ("alice", "pass123"),
            ("bob", "qwerty123"),
            ("charlie", "hello123"),
            ("dave", "abc123def"),
            ("emma", "secret123")
        ]
        for u,p in users:
            hash = bcrypt.generate_password_hash(p).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s) ON CONFLICT (username) DO NOTHING", 
                (u, hash)
            )
        db.commit()
        return jsonify({"message": "Database initialized successfully"})