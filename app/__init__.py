from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate

db = SQLAlchemy()
jwt = JWTManager()
migrate = Migrate()


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///social_network.db'
    app.config['JWT_SECRET_KEY'] = 'your-secret-key'

    db.init_app(app)
    jwt.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    from .auth import auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .views import post_blueprint
    app.register_blueprint(post_blueprint)

    return app
