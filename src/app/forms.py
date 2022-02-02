#
from flask_wtf import FlaskForm
from wtforms.fields import BooleanField, EmailField, PasswordField, StringField
from wtforms.validators import InputRequired, Email, Length, EqualTo

class LoginForm(FlaskForm):
    email = EmailField(
        'email',
        validators = [
            InputRequired("Email is required"),
            Email(message="Invalid email")
        ]
    )
    password = PasswordField(
        'password',
        validators=[InputRequired("Password is required")]
        )
    remember_me = BooleanField('Remember me', default=False)

class RegistrationForm(FlaskForm):
    email = EmailField(
        'email',
        validators = [InputRequired(), Email(message="Invalid email")]
        )
    password = PasswordField(
        'password',
        validators=[
            InputRequired(),
            Length(min=8, message='Password should contain at least 8 characters'),
            EqualTo('confirmpassword', message='Entered passwords don\'t match')
        ]
    )
    confirmpassword = PasswordField(
        'confirmpassword'
    )

class ResetForm(FlaskForm):
    email = EmailField(
        'email',
        validators = [InputRequired(), Email(message="Invalid email")]
        )

class NewProjectForm(FlaskForm):
    project_name = StringField(
        'project_name',
        validators = [InputRequired(), Length(min=1, message="Minimum project name length is 1")]
    )
