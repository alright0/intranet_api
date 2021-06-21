import logging
from datetime import date, datetime, timedelta

import pandas as pd
import sqlalchemy as db
from config import *
from flask import Blueprint, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required
from Statistics.forms import LoginForm
from Statistics.handlers import access_denied, default_errhandler
from Statistics.logic.logic import *
from Statistics.models import Camera, up_puco_export
from werkzeug.exceptions import HTTPException
from random import random

site = Blueprint("site", __name__)


@site.route("/order_info", methods=["GET", "POST"])
def order_info():

    if request.method == "POST":
        pass

    return render_template("order_info.html", lines=LINES)


@site.route("/detailed_daily_report", methods=["GET", "POST"])
def detailed_daily_report():

    if request.method == "POST":
        lines_list = request.form.getlist("line_checkbox")
        calendar_date = get_date_from_html_input(
            request.form.get("calendar"), "%Y-%m-%d"
        )
        new_response = up_puco_table(date=calendar_date, lines=lines_list, period="day")
        return json.dumps(new_response.stops_trace_graph())

    table = "line_report.camera_defrate_table()"
    return render_template("detailed_daily_report.html", table=table, lines=LINES)


@site.route("/daily_report", methods=["GET"])
def daily_report():
    """отчет за указанные сутки"""

    return render_template("daily_report.html", lines=LINES)


# домашняя страница
@site.route("/", methods=["GET", "POST"])
def index():
    """Главная страница"""

    if request.method == "POST":
        lines_status = []

        for line in LINES:
            lines_status.append(get_line_status(line))

        return json.dumps(dict(zip(LINES, lines_status)))

    lines_status = []
    for line in LINES:
        lines_status.append(
            dict(
                status="",
                operator="",
                input=0,
                output=0,
                order={"order": "", "description": ""},
                camera={},
            )
        )

    lines_dict = dict(zip(LINES, lines_status))

    return render_template("index.html", LINES=LINES, lines_dict=lines_dict)


@site.route("/production_plan_staff", methods=["GET", "POST"])
def production_plan_staff():
    """Страница с графиком выработки для персонала"""

    def _update_table():
        return up_puco_table().subplots(style="mini")

    if request.method == "POST":
        return _update_table()

    return render_template("production_plan_staff.html", plot=_update_table())


# TODO: добавить возможность выбора периодов
@site.route("/production_plan", methods=["GET", "POST"])
def production_plan():
    """План производства с подробным графиком.
    Всегда показывает текущий месяц, если не указано другое"""

    if request.method == "POST":

        calendar_date = get_date_from_html_input(
            request.form.get("calendar_date"), "%Y-%m"
        )
        new_response = up_puco_table(date=calendar_date)
        return json.dumps(
            {
                "table": new_response.date_table(),
                "plot": new_response.subplots(),
                "average": new_response.date_table_average(),
            }
        )
    start_response = up_puco_table()
    return render_template(
        "production_plan.html",
        table=start_response.date_table(),
        plot=start_response.subplots(),
        table_average=start_response.date_table_average(),
    )
