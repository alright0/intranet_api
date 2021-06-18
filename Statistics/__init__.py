import os
import logging
from pathlib import Path
import sqlalchemy as db
import pandas as pd

from datetime import date, datetime, timedelta
from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager, UserMixin
from flask_mail import Mail
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from pathlib import Path
from logging.handlers import SMTPHandler, RotatingFileHandler

from config import VM, FC, Config


path = Path(__file__).parents[1]

app = Flask(__name__)
app.config.from_object(Config)

login = LoginManager(app)
login.login_view = "users.login"
login.login_message = (
    "Вы должны авторизоваться, чтобы получить доступ к данной странице"
)

client = app.test_client()

mail = Mail(app)
cache = Cache(app)


# создание подключения к базе EN-VM01
cam_engine = create_engine(
    f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}",
)

# создание подключения к базе EN-DB05
fc_engine = create_engine(
    f"postgresql+psycopg2://{FC['user']}:{FC['password']}@{FC['host']}/{FC['database']}"
)


session_cam = scoped_session(
    sessionmaker(
        autocommit=False, autoflush=False, bind=cam_engine, expire_on_commit=False
    )
)

session_fc = scoped_session(
    sessionmaker(
        autocommit=False, autoflush=False, bind=fc_engine, expire_on_commit=False
    )
)

session = session_cam()

Base_cam = declarative_base()
Base_fc = declarative_base()

Base_cam.query = session_cam.query_property()
Base_fc.query = session_fc.query_property()

# Импорт моделей
from Statistics.models import *

# добавление Blueprints
from .site.views import site
from .users.views import users
from Statistics.handlers import error_handlers

# регистрация Blueprints
app.register_blueprint(site)
app.register_blueprint(users)
app.register_blueprint(error_handlers)


if not app.debug:

    if not Path.exists(path / "logs"):
        Path.mkdir(path / "logs")
    file_handler = RotatingFileHandler(
        path / "logs/statistcs.log", maxBytes=10240, backupCount=10
    )

    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )

    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)

# отключение предупреждения chained_assignment
pd.options.mode.chained_assignment = None
