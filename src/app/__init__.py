import os
import json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    config = json.load(open("app/config.json"))
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config["SECRET_KEY"]
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///db/{DB_NAME}'
    # app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth/')

    from .models import User, Project, File

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    if not os.path.exists('db/' + DB_NAME):
        with app.app_context():
            db.create_all()
        print('Created Database!')
