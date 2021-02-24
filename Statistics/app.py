from datetime import date, datetime, timedelta

import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM, FC
from Statistics.data.table import make_table

app = Flask(__name__)

# тестовый клиент для тестов
client = app.test_client()

# создание подключения к базе EN-VM01 и EN-DB05
cam_engine = create_engine(
    f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}"
)
fc_engine = create_engine(
    f"postgresql+psycopg2://{FC['user']}:{FC['password']}@{FC['host']}/{FC['database']}"
)


session_cam = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=cam_engine)
)

session_fc = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=fc_engine)
)


Base_cam = declarative_base()
Base_fc = declarative_base()

Base_cam.query = session_cam.query_property()
Base_fc.query = session_fc.query_property()

# Импорт моделей
from Statistics.models import *

# Base.metadata.create_all(bind=cam_engine)
# Base.metadata.create_all(bind=fc_engine)

# добавление Blueprints
from .api.views import camera
from .site.views import site

# регистрация Blueprints
app.register_blueprint(camera)
app.register_blueprint(site)