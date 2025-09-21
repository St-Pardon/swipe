from flask import Flask
from flask_jwt_extended import JWTManager
from app.config import Config
from app.extensions import db, migrate, mail
from app.swagger import swagger_bp

# import Blueprint
from app.routes.base_route import base_bp
from app.routes.account import account_bp
from app.routes.auth import auth_bp
from app.routes.users import user_bp
from app.routes.card import card_bp
from app.routes.card_payments import card_payments_bp
from app.routes.transaction import transaction_bp
from app.routes.wallet import wallet_bp
from app.routes.webhooks import webhooks_bp
from app.routes.two_factor_auth import two_factor_bp
from app.routes.invoice import invoice_bp
from app.routes.invoice_payments import invoice_payments_bp

from app import models

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Init extensions
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    JWTManager(app)


    # Register Blueprint
    app.register_blueprint(base_bp)
    app.register_blueprint(swagger_bp)  # Swagger UI
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(account_bp, url_prefix="/api")
    app.register_blueprint(user_bp, url_prefix="/api")
    app.register_blueprint(card_bp, url_prefix="/api")
    app.register_blueprint(card_payments_bp, url_prefix="/api")
    app.register_blueprint(transaction_bp, url_prefix="/api")
    app.register_blueprint(wallet_bp, url_prefix="/api")
    app.register_blueprint(webhooks_bp, url_prefix="/api")
    app.register_blueprint(two_factor_bp, url_prefix="/api")
    app.register_blueprint(invoice_bp, url_prefix="/api")
    app.register_blueprint(invoice_payments_bp, url_prefix="/api")

    return app
