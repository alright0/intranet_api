from datetime import date, datetime, timedelta


import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for, Blueprint
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.config import VM
from Statistics.data.table import make_table
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from Statistics.logic.logic import get_camera_now, makedate, camera_json_deserialize

site = Blueprint("site", __name__)

IBEA_ADDRESS = [
    "LZ-1 A",
    "LZ-1 B",
    "LZ-2 A",
    "LZ-2 B",
    "LZ-3",
    "LZ-4",
    "123" "LZ-5 A",
    "LZ-5 B",
    "LZ-1 ST",
    "LZ-2 ST",
]


# домашняя страница
@site.route("/", methods=["GET"])
def index():
    return render_template("base.html")


# страница с ежедневным отчетом
@site.route("/daily_camera_report", methods=["GET", "POST"])
def camera2():

    if request.method == "POST":
        dt = request.form.get("dt")
        dt = makedate(dt)

        return render_template(
            "camera_report.html", dt=(dt[0], dt[1]), table=make_table()
        )

    else:
        return render_template("camera_report.html", dt="Выберите дату")


# страница с текущим положением дел по камерам
@site.route("/now_camera_report", methods=["GET"])
def camera_now():

    line_info = []

    for line in IBEA_ADDRESS:
        line_info.append(camera_json_deserialize(get_camera_now(line)))

    return render_template(
        "camera_report_cont.html",
        lines=line_info,
    )


# страница с ежедневным отчетом
@site.route("/daily_camera_report", methods=["GET", "POST"])
def camera():

    if request.method == "POST":
        dt = request.form.get("dt")
        dt = makedate(dt)

        return render_template(
            "camera_report.html", dt=(dt[0], dt[1]), table=make_table()
        )

    else:
        return render_template("camera_report.html", dt="Выберите дату")


# обработчик 404
@site.errorhandler(404)
def page_not_found(e):

    return render_template("404.html"), 404