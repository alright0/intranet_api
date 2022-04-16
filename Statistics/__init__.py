import pandas as pd

from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from config import VM, Config

app = Flask(__name__)
app.config.from_object(Config)

# создание подключения к базе EN-VM01
engine = create_engine(f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}")
session_cam = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False))
session = session_cam()
Base_cam = declarative_base()
Base_cam.query = session_cam.query_property()

from Statistics.models import *

from Statistics.site.views import site
from Statistics.handlers import error_handlers

# регистрация Blueprints
app.register_blueprint(site)
app.register_blueprint(error_handlers)

# отключение предупреждения chained_assignment
pd.options.mode.chained_assignment = None
