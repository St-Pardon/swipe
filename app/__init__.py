from flask import Flask
from flask_jwt_extended import JWTManager
from app.config import Config
from app.extensions import db, migrate

# import Blueprint
from app.routes.base_route import base_bp
from app.routes.account import account_bp
from app.routes.auth import auth_bp
from app.routes.users import user_bp
from app.routes.card import card_bp
from app.routes.payment import payment_bp
from app.routes.transaction import transaction_bp


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    JWTManager(app)


    # Register Blueprint
    app.register_blueprint(base_bp)
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(account_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(card_bp, url_prefix="/api")
    app.register_blueprint(payment_bp, url_prefix="/api")
    app.register_blueprint(transaction_bp, url_prefix="/api")

    return app
