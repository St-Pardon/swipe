from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_marshmallow import Marshmallow
from flask_mail import Mail

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()
mail = Mail()
BLOCKLIST = set()