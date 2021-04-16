from datetime import date, datetime, timedelta

import pandas as pd
import sqlalchemy as db
from config import *
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from Statistics.forms import LoginForm
from Statistics.logic.logic import *
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from werkzeug.exceptions import HTTPException
import logging

site = Blueprint("site", __name__)


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

    info = up_puco_table(date(2021, 3, 3))

    plot = info.subplots(style="mini")
    now = datetime.strftime(datetime.now(), "%H:%M:%S")

    return render_template(
        "production_plan_staff.html",
        plot=plot,
        now=now,
    )


# TODO: добавить возможность выбора периодов
@site.route("/production_plan", methods=["GET"])
def production_plan():
    """План производства с подробным графиком.
    Всегда показывает текущий месяц, если не указано другое"""

    info = up_puco_table(date(2021, 3, 3))

    # df = info.get_month_table()

    plot = info.subplots()
    table = info.date_table()
    table_average = info.date_table_average()

    return render_template(
        "production_plan.html",
        table=table,
        plot=plot,
        table_average=table_average,
    )


@site.route("/access_denied", methods=["get"])
def access_denied():
    """Редирект с контента с более высоким уровнем доступа"""

    error = {
        "code": "Доступ запрещен",
        "description": "Недостаточно прав для просмотра страницы",
    }

    return render_template("error.html", error=error)


@site.app_errorhandler(HTTPException)
def default_errhandler(e):
    return render_template("error.html", error=e), e.code
