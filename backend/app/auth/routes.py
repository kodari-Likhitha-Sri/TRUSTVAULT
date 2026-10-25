from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import current_user, login_required
from app.forms import RegistrationForm, LoginForm
from app.auth.service import AuthService

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
    form = LoginForm()
    return render_template('index.html', form=form)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        success, result = AuthService.register_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data,
            role=form.role.data,
            req=request
        )
        if success:
            flash('Your account has been created successfully! You can now log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result, 'danger')

    return render_template('register.html', form=form)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        success, result = AuthService.authenticate_user(
            login_id=form.login_id.data,
            password=form.password.data,
            remember=form.remember.data,
            req=request
        )
        if success:
            flash(f'Welcome back, {result.username}!', 'success')
            next_page = request.args.get('next')
            if next_page and next_page.startswith('/'):
                return redirect(next_page)
            return redirect(url_for('dashboard.index'))
        else:
            flash(result, 'danger')

    return render_template('login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    AuthService.logout_current_user(current_user, req=request)
    flash('You have been logged out securely.', 'info')
    return redirect(url_for('auth.login'))
