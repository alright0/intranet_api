From flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired

class LoginForm(FlaskForm):
    username = StringField('Username', Validators=[DataRequired[]])
    password = PasswordField('Password', validators=[DataRequired[]])
    remember_me = BooleanField('Remember me')
    submit = SubmitField('Sign In')

    