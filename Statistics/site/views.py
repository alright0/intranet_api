import logging
from datetime import date, datetime, timedelta

import pandas as pd
import sqlalchemy as db
from config import *
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from Statistics.forms import LoginForm
from Statistics.handlers import access_denied, default_errhandler
from Statistics.logic.logic import *
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from werkzeug.exceptions import HTTPException

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

        # экземпляр ответа
        new_response = up_puco_table(date=calendar_date, lines=lines_list, period="day")

        return json.dumps(new_response.stops_trace_graph())

        """l_dict = {line: {1: {"data": 1, "layout": 2}, 2: "xyz"} for line in lines_list}
        print(l_dict)
        return json.dumps(l_dict)"""

    # line_report = up_puco_table(period="day", lines=["LZ-02"])
    table = "line_report.camera_defrate_table()"

    stops_plot = {"1": " 1", "2": " 2"}  # line_report.stops_trace_graph()

    return render_template(
        "detailed_daily_report.html", table=table, stops_plot=stops_plot, lines=LINES
    )


"""@site.route("/detailed_daily_report", methods=["GET", "POST"])
def detailed_daily_report():

    if request.method == "POST":
        print(request.form.get("123"))

    line_report = up_puco_table(period="day", lines=["LZ-02"])
    table = line_report.camera_defrate_table()

    stops_plot = line_report.stops_trace_graph()

    return render_template(
        "detailed_daily_report.html", table=table, stops_plot=stops_plot, lines=LINES
    )"""


@site.route("/daily_report", methods=["GET"])
def daily_report():
    """Здесь будет страница отчета за последние сутки(или за указанные)"""

    return render_template("daily_report.html", lines=LINES)


# домашняя страница
@site.route("/", methods=["GET"])
def index():
    """Главная страница, содержащая табло работы линий в реальном времени"""

    logging.info("я сообщение лога")

    lines_status = []
    for line in LINES:
        lines_status.append(get_line_status(line))

    lines_dict = dict(zip(LINES, lines_status))
    now = datetime.strftime(datetime.now(), "%H:%M:%S")

    return render_template("index.html", LINES=LINES, lines_dict=lines_dict, now=now)


@site.route("/production_plan_staff", methods=["GET"])
def production_plan_staff():
    """Страница с графиком выработки для персонала"""

    info = up_puco_table()

    plot = info.subplots(style="mini")
    now = datetime.strftime(datetime.now(), "%H:%M:%S")

    return render_template(
        "production_plan_staff.html",
        plot=plot,
        now=now,
    )


# TODO: добавить возможность выбора периодов
@site.route("/production_plan", methods=["GET", "POST"])
def production_plan():
    """План производства с подробным графиком.
    Всегда показывает текущий месяц, если не указано другое"""

    if request.method == "POST":

        calendar_date = get_date_from_html_input(
            request.form.get("calendar_date"), "%Y-%m"
        )

        # экземпляр ответа
        new_response = up_puco_table(date=calendar_date)

        return json.dumps(
            {
                "table": new_response.date_table(),
                "plot": new_response.subplots(),
                "average": new_response.date_table_average(),
            }
        )

    # Экземпляр для начальных условий
    start_response = up_puco_table()

    return render_template(
        "production_plan.html",
        table=start_response.date_table(),
        plot=start_response.subplots(),
        table_average=start_response.date_table_average(),
    )
