from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo

from Statistics.models import User


class LoginForm(FlaskForm):
    username = StringField("Имя пользователя:", validators=[DataRequired()])
    password = PasswordField("Пароль:", validators=[DataRequired()])
    remember_me = BooleanField("Запомнить меня")
    submit = SubmitField("Войти")


class ResetPasswordRequestForm(FlaskForm):
    email = StringField("Email:", validators=[DataRequired(), Email()])
    submit = SubmitField("Сбросить пароль")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Пароль:", validators=[DataRequired()])
    password2 = PasswordField(
        "Повторите пароль:", validators=[DataRequired(), EqualTo("password")]
    )
    submit = SubmitField("Сбросить пароль")


class RegistrationForm(FlaskForm):
    username = StringField("Имя пользователя:", validators=[DataRequired()])
    email = StringField("Email:", validators=[DataRequired()])
    password = PasswordField("Пароль:", validators=[DataRequired()])
    password2 = PasswordField(
        "Повторите пароль:",
        validators=[
            DataRequired(),
            EqualTo("password", message="Пароли не совпадают"),
        ],
    )
    submit = SubmitField("Регистрация")

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError("Пожалуйста, выберите другое имя")

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError("Пожалуйста, выберите другой адрес почтового ящика")
        if "@silganmp.com" not in str(email.data).lower():
            raise ValidationError(
                "Адрес почтового ящика должен принадлежать домену silganmp.com"
            )
