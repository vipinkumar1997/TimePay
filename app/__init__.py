from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import Config

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    from app import routes
    # Register blueprints or import routes directly if using simple structure
    # Since we are using a simple structure, we just import routes to register them with the app context
    # However, routes usually need 'app' or 'bp'. 
    # Let's use the app_context pattern in routes or just import routes at the end of this function if routes.py imports 'app' from here.
    # But circular imports are tricky.
    # Better approach: Define routes in a Blueprint or pass app to routes.
    # For simplicity in this single-module app, let's use the pattern where routes imports 'app' from a separate 'main' or we use `with app.app_context()` in run.py.
    
    # Actually, the standard simple flask pattern:
    # app/__init__.py creates 'app' variable.
    # But here I am using a factory.
    # Let's switch to the simple global 'app' object pattern for simplicity unless the user needs factory.
    # The user asked for a "complete modern web application". Factory is better practice.
    # So I will use Blueprints? Or just import routes and pass app?
    # Let's stick to the simplest robust way:
    # Create `routes.py` that takes `app` or uses `current_app`.
    # Actually, let's just use the global variable pattern for `app` in `__init__.py` to avoid complexity for the user, 
    # as they might be a beginner.
    
    return app

# Re-writing __init__.py to use global app instance for simplicity with routes
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)

from app import routes
