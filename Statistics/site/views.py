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


@site.route("/test", methods=["get"])
@login_required
def test():

    if current_user.accesslevel < 4:
        return redirect(url_for("site.access_denied"))
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