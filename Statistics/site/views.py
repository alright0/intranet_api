from datetime import date, datetime, timedelta
import pandas as pd

import sqlalchemy as db
from flask import render_template, request, Blueprint, redirect, url_for
from flask_login import current_user, login_required
from config import *
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from Statistics.forms import LoginForm
from Statistics.logic.logic import *

site = Blueprint("site", __name__)


@site.route("/daily_report", methods=["GET"])
def daily_report():

    last_day_lines = up_puco_table(period="day", lines=["LL-01"])

    print(last_day_lines.__repr__())
    # df3 = last_day_lines.get_month_table()

    last_day_line_graph = last_day_lines.line_shift_report()

    return render_template("daily_report.html", lines=LINES)


# домашняя страница
@site.route("/", methods=["GET"])
def index():

    lines_status = []
    for line in LINES:
        lines_status.append(get_line_status(line))

    lines_dict = dict(zip(LINES, lines_status))
    now = datetime.strftime(datetime.now(), "%H:%M:%S")

    # print(lines_dict)

    return render_template("index.html", LINES=LINES, lines_dict=lines_dict, now=now)


# @login_required
@site.route("/test", methods=["get"])
def test():

    info = up_puco_table(lines=["LZ-1"])
    df = info.camera_table()

    # if current_user.accesslevel < 4:
    #    return redirect(url_for("site.access_denied"))
    return render_template("base.html")


@site.route("/production_plan_staff", methods=["GET"])
def production_plan_staff():

    info = up_puco_table()

    df = info.get_month_table()

    plot = info.subplots(df, style="mini")
    now = datetime.strftime(datetime.now(), "%H:%M:%S")

    return render_template(
        "production_plan_staff.html",
        plot=plot,
        now=now,
    )


# TODO: добавить возможность выбора периодов
@site.route("/production_plan", methods=["GET"])
def production_plan():

    info = up_puco_table()
    info.__repr__()

    print(info.date_start, info.date_end_with_hours)

    df = info.get_month_table()

    plot = info.subplots(df)
    table = info.date_table(df)
    table_average = info.date_table_average(df)

    return render_template(
        "production_plan.html",
        table=table,
        plot=plot,
        table_average=table_average,
    )


@site.route("/access_denied", methods=["get"])
def access_denied():
    return render_template("access_denied.html")


@site.errorhandler(404)
def page_not_found(e):

    return render_template("404.html"), 404