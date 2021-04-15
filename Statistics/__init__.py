from datetime import date, datetime, timedelta

import sqlalchemy as db
from flask import Flask
from flask_login import LoginManager, UserMixin
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker
from pathlib import Path


from config import VM, FC, Config

app = Flask(__name__)
app.config.from_object(Config)

login = LoginManager(app)
login.login_view = "users.login"
login.login_message = "Вы должны авторизоваться, чтобы получить доступ к данной странице"  # flash сообщение при редиректре на login_required

# тестовый клиент для тестов
client = app.test_client()

path = Path(__file__).parents[0]

# для демонстрации
if 0:
    # создание подключения к базе EN-VM01
    cam_engine = create_engine(
        f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}",
    )

    # создание подключения к базе EN-DB05
    fc_engine = create_engine(
        f"postgresql+psycopg2://{FC['user']}:{FC['password']}@{FC['host']}/{FC['database']}",
    )

else:

    # создание подключения к базе EN-VM01
    cam_engine = create_engine(
        f"sqlite:///{path}/Demo/VM.db",
    )

    # создание подключения к базе EN-DB05
    fc_engine = create_engine(
        f"sqlite:///{path}/Demo/FC.db",
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
from .api.views import camera
from .site.views import site
from .users.views import users

# регистрация Blueprints
app.register_blueprint(camera)
app.register_blueprint(site)
app.register_blueprint(users)