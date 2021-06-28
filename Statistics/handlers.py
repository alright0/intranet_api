from datetime import date, datetime, timedelta

import pandas as pd
import sqlalchemy as db
from config import *
from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user, login_required

# from Statistics.forms import LoginForm
from Statistics.logic.logic import *
from Statistics.models import Camera
from werkzeug.exceptions import HTTPException
import logging

error_handlers = Blueprint("handlers", __name__)


@error_handlers.route("/access_denied", methods=["get"])
def access_denied():
    """Редирект с контента с более высоким уровнем доступа"""

    error = {
        "code": "Доступ запрещен",
        "description": "Недостаточно прав для просмотра страницы",
    }

    return render_template("errors/error.html", error=error)


@error_handlers.app_errorhandler(HTTPException)
def default_errhandler(e):
    return render_template("errors/error.html", error=e), e.code
