"""Validated WTForms used by account and community routes. Sole creator, developer, and author: Ezra Kidanu."""
from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, SelectChoice, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length


class SignupForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=80)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=12, max=128)])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo("password")])
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=254)])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember me on this device", default=True)
    submit = SubmitField("Log in")


class PostForm(FlaskForm):
    category = SelectField(
        "Category",
        choices=[SelectChoice(category, category) for category in ("Academics", "Clubs", "Sports", "General")],
        validators=[DataRequired()],
    )
    title = StringField("Title", validators=[DataRequired(), Length(min=3, max=120)])
    content = TextAreaField("What's the update?", validators=[DataRequired(), Length(min=10, max=3000)])
    submit = SubmitField("Publish")


class CommentForm(FlaskForm):
    content = TextAreaField("Comment", validators=[DataRequired(), Length(min=1, max=500)])
    submit = SubmitField("Comment")


class LogoutForm(FlaskForm):
    submit = SubmitField("Log out")
