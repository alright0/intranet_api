import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from config import VM

from data.table import make_table

# from ibea import ibea_date
from datetime import date, datetime, timedelta

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

from models import *

Base.metadata.create_all(bind=engine)

IBEA_ADDRESS = [
    "LZ-1 A",
    "LZ-1 B",
    "LZ-2 A",
    "LZ-2 B",
    "LZ-3",
    "LZ-4",
    "TO-1",
    "LZ-5 A",
    "LZ-5 B",
    "LZ-1 ST",
    "LZ-2 ST",
]


def get_camera_now(line):

    try:
        cam = (
            Camera.query.filter(Camera.line_side == line)
            .order_by(Camera.date_now.desc())
            .first()
        )

        serialized = {
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

    except:
        return {"message": "data not found"}

    return jsonify(serialized)


def makedate(dt):

    dt = datetime.strptime(dt[:10], "%Y-%m-%d")

    dt2 = dt + timedelta(days=1)

    return dt, dt2


# домашняя страница
@app.route("/", methods=["GET"])
def index():
    return render_template("base.html")


# страница с ежедневным отчетом
@app.route("/daily_camera_report", methods=["GET", "POST"])
def camera2():

    if request.method == "POST":
        dt = request.form.get("dt")
        dt = makedate(dt)

        return render_template(
            "camera_report.html", dt=(dt[0], dt[1]), table=make_table()
        )

    else:
        return render_template("camera_report.html", dt="Выберите дату")


@app.route("/now_camera_report", methods=["GET"])
def camera_now():

    line_info = []

    for line in IBEA_ADDRESS:
        line_info.append(get_camera_now(line))

    return render_template(
        "camera_report_cont.html",
        lines=line_info,
    )


# страница с ежедневным отчетом
@app.route("/daily_camera_report", methods=["GET", "POST"])
def camera():

    if request.method == "POST":
        dt = request.form.get("dt")
        dt = makedate(dt)

        return render_template(
            "camera_report.html", dt=(dt[0], dt[1]), table=make_table()
        )

    else:
        return render_template("camera_report.html", dt="Выберите дату")


# api-ответ, возвращающий json из EN-VM01.ibea_agregate
@app.route("/camera/<line>", methods=["GET"])
def get_camera_info(line):

    one = Camera.query.filter(Camera.line == line).limit(5)

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

    if not serialized:
        return {"message": "data not found"}

    return jsonify(serialized)


# api-ответ Нахождение последней записи в базе
@app.route("/camera/last/<line>", methods=["GET"])
def get_camera_info_last(line):
    return get_camera_now(line)


# обработчик 404
@app.errorhandler(404)
def page_not_found(e):

    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="5000", debug=True)
