import os

from dotenv import load_dotenv

from flask import Flask
from flask_cors import CORS

def create_app(test_config=None):

    load_dotenv()

    app = Flask(__name__,instance_relative_config=True)
    
    # Configure CORS
    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://localhost",
                "http://frontend",
                "http://frontend:80"
            ],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    app.config.from_mapping(
        DATABASE_URL=os.getenv("DATABASE_URL"),
        JWT_SECRET=os.getenv("JWT_SECRET")
    )

    if test_config is None:
        app.config.from_pyfile('config.py',silent=True)
    else:
        app.config.from_mapping(test_config)
    
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from . import routes

    routes.register_routes(app)

    return app