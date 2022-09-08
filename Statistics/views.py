from flask import Blueprint, render_template, request
from werkzeug.wrappers import response

from Statistics.logic.logic import get_line_status
from Statistics.logic.dataframes import CameraGraph
from config import LINES
from datetime import datetime
import json

site = Blueprint("site", __name__)


@site.route("/detailed_daily_report", methods=["GET", "POST"])
def detailed_daily_report():

    if request.method == "POST":
        lines_list = request.form.getlist("line_checkbox")
        calendar_date = datetime.strptime(request.form.get("calendar"), "%Y-%m-%d")
        new_response = CameraGraph(date_start=calendar_date, lines=lines_list)
        return json.dumps(new_response.graph())

    return render_template("detailed_daily_report.html", lines=LINES)


# домашняя страница
@site.route("/", methods=["GET", "POST"])
def index():
    """Главная страница"""

    lines_status = []
    if request.method == "POST":
        for line in LINES:
            lines_status.append(get_line_status(line))
        return json.dumps(dict(zip(LINES, lines_status)))

    lines_dict = dict(zip(LINES, lines_status))

    return render_template("index.html", LINES=LINES, lines_dict=lines_dict)


@site.route("/report", methods=["GET", "POST"])
def report():
    """Главная страница"""
    if request.method == "POST":
        date_from = datetime.strptime(request.form.get("calendar_from"), "%Y-%m-%d")
        date_to = datetime.strptime(request.form.get("calendar_to"), "%Y-%m-%d")
        data = CameraGraph(date_from, date_to)
        return data.summary_report()

    return render_template('report.html')

