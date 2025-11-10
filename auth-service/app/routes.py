from flask import request,jsonify
from app.database import get_database
from flask_bcrypt import Bcrypt
from app.utils import generate_jwt
def register_routes(app):

    @app.route("/")
    def home():
        return "root"

    @app.route('/login',methods=['POST'])
    def login():
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        bcrypt = Bcrypt(app)

        sql = "SELECT id,password_hash FROM users WHERE username = %s"

        db = get_database()
        cursor = db.cursor()
        cursor.execute(sql,(username,))    
        res = cursor.fetchone()
        if not res:
            return jsonify({"error":"user not found"}),404
        elif bcrypt.check_password_hash(res[1],password):
            token = generate_jwt(res[0])
            return jsonify({"access_token":token}),200
        else:
            return jsonify({"error":"crentials not valid"}),401
    
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
            ("bob", "qwerty"),
            ("charlie", "hello123"),
            ("dave", "abc123"),
            ("emma", "secret1"),
            ("frank", "test123"),
            ("grace", "password1"),
            ("henry", "letmein"),
            ("isabella", "monkey1"),
            ("jack", "simple123")
        ]
        for u,p in users:
            hash = bcrypt.generate_password_hash(p).decode("utf-8")
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (%s, %s)", (u,hash)
            )
        db.commit()
        return "ok"