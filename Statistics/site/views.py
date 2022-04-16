from flask import Blueprint, render_template, request
from Statistics.logic.logic import *
from config import LINES

site = Blueprint("site", __name__)

@site.route("/detailed_daily_report", methods=["GET", "POST"])
def detailed_daily_report():

    if request.method == "POST":
        lines_list = request.form.getlist("line_checkbox")
        calendar_date = datetime.strptime(request.form.get("calendar"), "%Y-%m-%d")
        new_response = up_puco_table(date=calendar_date, lines=lines_list)
        return json.dumps(new_response.graph())

    table = "line_report.camera_defrate_table()"
    return render_template("detailed_daily_report.html", table=table, lines=LINES)

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
