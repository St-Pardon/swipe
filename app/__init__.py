from flask import Flask
from app.config import Config
from app.extensions import db, migrate

# import Blueprint
from app.routes.base_route import base_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)

    # Register Blueprint
    app.register_blueprint(base_bp)

    return app
