import logging
from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from .models import User
from .utils import send_email
from . import db
from .forms import LoginForm, RegistrationForm, ResetForm

auth = Blueprint("auth", __name__)

@auth.route('/login', methods=['POST', 'GET'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.data['email']
        password = form.data['password']
        remember = form.data['remember_me']

        user = User.query.filter_by(email=email).first()
        # app.logger.debug(f"Logged in: {user}")

        if user:
            if check_password_hash(user.password, password):
                flash('Logged in successfully!', category='success')
                login_user(user, remember=True)
                return redirect(url_for('views.home'))
            else:
                flash('Incorrect password, try again.', category='error')
        else:
            flash('User does not exist.', category='error')

    return render_template("index.html", user=current_user, form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth.route('/reset', methods=['GET', 'POST'])
def reset():
    form = ResetForm()
    if form.validate_on_submit():
        email = form.data.get('email')
        user = User.query.filter_by(email=email).first()
        if user:
            send_email(email)
            flush(f"To reset your password, follow instructions sent to {email}!")
            return redirect(url_for('auth.login'))
    return render_template('reset.html', user=current_user, form=form)


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.data.get('email')
        password = form.data.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already exists.', category='error')
        else:
            new_user = User(email=email, password=generate_password_hash(
                password, method='sha256'))
            db.session.add(new_user)
            db.session.commit()
            login_user(new_user, remember=True)
            flash('Account created!', category='success')
            return redirect(url_for('views.home'))

    return render_template("register.html", user=current_user, form=form)
