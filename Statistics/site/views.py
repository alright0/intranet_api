from datetime import date, datetime, timedelta
import pandas as pd

import sqlalchemy as db
from flask import Flask, jsonify, redirect, render_template, request, url_for, Blueprint
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import scoped_session, sessionmaker

from Statistics.app import *
from Statistics.config import *
from Statistics.data.table import make_table
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from Statistics.logic.logic import *

site = Blueprint("site", __name__)


@site.route("/daily/<line>", methods=["GET", "POST"])
def daily_report(line):

    return render_template("daily_report")


@site.route("/production_plan", methods=["GET"])
def production_plan():

    df = up_puco_table().get_month_table()

    """df = up_puco_table(
        date=datetime(2021, 3, 1), period="day", delta=3, lines=["LL-01", "LL-02"]
    ).get_month_table()"""

    plot = up_puco_table().subplots(df)
    table = up_puco_table().date_table(df)
    table_average = up_puco_table().date_table_average(df)

    return render_template(
        "production_plan.html",
        table=table,
        plot=plot,
        table_average=table_average,
    )


# домашняя страница
@site.route("/", methods=["GET"])
def index():

    lines_status = []

    for line in LINES:
        lines_status.append(get_line_status(line))

    lines_dict = dict(zip(LINES, lines_status))

    # print(lines_dict)

    return render_template("index.html", LINES=LINES, lines_dict=lines_dict)


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
        return render_template("camera_report.html", dt="Выберите дату"), 200


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