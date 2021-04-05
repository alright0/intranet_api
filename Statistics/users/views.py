from datetime import date, datetime, timedelta
import pandas as pd

from flask import render_template, Blueprint, flash, redirect, url_for


from Statistics import *
from config import *
from Statistics.models import Camera
from Statistics.schemas import CameraSchema
from Statistics.forms import LoginForm
from Statistics.logic.logic import *

users = Blueprint("users", __name__)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        flash(
            "Login requested for user {}, remember_me={}".format(
                form.username.data, form.remember_me.data
            )
        )
        return redirect(url_for("login"))
    return render_template("login.html", title="Sign In", form=form)
