from flask import request
from flask_wtf import FlaskForm
from wtforms import (BooleanField, DateField,
                     PasswordField, SelectField, StringField, SubmitField,
                     TextAreaField)
from wtforms.validators import (DataRequired, Email, EqualTo,
                                Length, Regexp, URL, ValidationError)

from models import User

def email_exists(form, field):
    if User.select().where(User.email==field.data).exists():
        raise ValidationError("That email has already been used.")


class RegisterForm(FlaskForm):
    email = StringField(
        'Email',
        validators=[
            DataRequired(),
            Email(),
            email_exists
        ]
    )
    password = PasswordField(
        'Password',
        validators=[
            DataRequired(),
            Length(min=7),
            EqualTo('password2', message="Passwords must match.")
        ]
    )
    password2 = PasswordField(
        'Confirm Password',
        validators=[DataRequired()]
    )


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class WishlistForm(FlaskForm):
    title = StringField(
        "Enter a new list title.",
        validators=[DataRequired()]
    )


class ItemForm(FlaskForm):
    name = StringField(
        "Enter a new list item.",
        validators=[DataRequired()]
    )
    link = StringField(
        "Enter a URL.",
        validators=[URL(require_tld=True)]
    )


class SearchForm(FlaskForm):
    choices = [('User', 'User')]
    select = SelectField(choices=choices)
    search = StringField(validators=[DataRequired()])


class EditItem(FlaskForm):
    name = StringField(validators=[DataRequired()])
    link = StringField(validators=[URL(require_tld=True)])


class EditListName(FlaskForm):
    title = StringField(validators=[DataRequired()])
