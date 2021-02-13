# import psycopg2
import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from app1 import get_fig
from pgaccess import VM

app = Flask(__name__)

# тестовый клиент для тестов
client = app.test_client()

# создание подключения к базе EN-VM01
engine = create_engine(
    f"postgresql+psycopg2://{VM['user']}:{VM['password']}@{VM['host']}/{VM['database']}"
)
a = 1

session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))

Base = declarative_base()
Base.query = session.query_property()

from models import *

Base.metadata.create_all(bind=engine)

# Главная страница
@app.route("/", methods=["GET"])
def index():
    return render_template("base.html", plot=get_fig()), 200


# api-ответ, возвращающий json из EN-VM01.ibea_agregate
@app.route("/camera", methods=["GET"])
def get_camera_info():
    one = Camera.query.limit(5).all()

    serialized = []
    for cam in one:
        serialized.append(
            {
                "id": cam.id,
                "line": cam.line,
                "line_side": cam.line_side,
                "date_now": cam.date_now,
                "job": cam.job,
                "start_time": cam.start_time,
                "last_part": cam.last_part,
                "total": cam.total,
                "rejected": cam.rejected,
            }
        )
    return jsonify(serialized)


# обработчик 404
@app.errorhandler(404)
def page_not_found(e):

    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="127.0.0.1", port="5000", debug=True)
