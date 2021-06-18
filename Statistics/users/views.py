from datetime import date, datetime, timedelta
import pandas as pd

from flask import render_template, Blueprint, flash, redirect, url_for, request
from werkzeug.urls import url_parse
from flask_login import current_user, login_user, logout_user


from Statistics import *
from config import *
from Statistics.models import User
from Statistics.mail import send_email, send_password_reset_email
from Statistics.forms import (
    LoginForm,
    RegistrationForm,
    ResetPasswordRequestForm,
    ResetPasswordForm,
)
from Statistics.logic.logic import *

users = Blueprint("users", __name__)


@users.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if current_user.is_authenticated:
        return redirect(url_for("site.index"))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=str(form.email.data).lower()).first()
        if user:
            send_password_reset_email(user)
        flash(
            "На указанный адрес электронной почты отправлено сообщение с инструкцией по сбросу пароля"
        )
        return redirect(url_for("users.login"))
    return render_template("forgot_password.html", title="Сброс пароля", form=form)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for("site.index"))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for("site.index"))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        print(user.password)

        user.set_password(form.password.data)

        session_cam().commit()

        flash("Ваш пароль сброшен!")
        return redirect(url_for("users.login"))
    return render_template("reset_password.html", form=form)


@users.route("/login", methods=["GET", "POST"])
def login():

    if current_user.is_authenticated:
        return redirect(url_for("index"))

    # передача формы из forms(flask_wtf)
    form = LoginForm()

    if form.validate_on_submit():

        user = User.query.filter_by(username=str(form.username.data).lower()).first()

        # Если пользователь не найден или пароль не подошел, то вернуть сообщение
        if user is None or not user.check_password(form.password.data):
            flash("Неверный пользователь или пароль")
            return redirect(url_for("users.login"))

        login_user(user, remember=form.remember_me.data)

        # возврат на страницу, с которой был перевод на авторизацию или на index.html
        next_page = request.args.get("next")
        if not next_page or url_parse(next_page).netloc != "":
            next_page = url_for("site.index")
        return redirect(next_page)

    return render_template("login.html", title="Sign In", form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("site.index"))


@users.route("/register", methods=["GET", "POST"])
def register():

    # Если пользователь авторизован - редирект на index.html
    if current_user.is_authenticated:
        return redirect(url_for("site.index"))

    # Передача формы из forms(flask_wtf)
    form = RegistrationForm()

    if form.validate_on_submit():

        user = User(
            username=str(form.username.data).lower(), email=str(form.email.data).lower()
        )
        user.set_password(form.password.data)

        # добавление в базу
        session.add(user)
        session.commit()

        flash("Вы зарегистрированы!")

        return redirect(url_for("users.login"))

    return render_template("registration.html", title="Register", form=form)
