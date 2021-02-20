from datetime import date, datetime, timedelta

import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM
from Statistics.data.table import make_table

app = Flask(__name__)

# тестовый клиент для тестов
client = app.test_client()

# создание подключения к базе EN-VM01
engine = create_engine(
    f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}"
)


session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = session.query_property()

# Импорт моделей
from Statistics.models import *

Base.metadata.create_all(bind=engine)

# добавление Blueprints
from .api.views import camera
from .site.views import site

# регистрация Blueprints
app.register_blueprint(camera)
app.register_blueprint(site)