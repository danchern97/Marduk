import os, json
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    config = json.load("config.json")
    app = Flask(__name__)
    app.config["SECRET_KEY"] = config["SECRET_KEY"]

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/auth')

    return app
