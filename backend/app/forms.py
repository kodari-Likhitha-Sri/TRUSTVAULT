import re
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User
from config import Config

def validate_strong_password(form, field):
    password = field.data or ''
    errors = []
    if len(password) < 12:
        errors.append('be at least 12 characters long')
    if not re.search(r'[A-Z]', password):
        errors.append('contain at least one uppercase letter')
    if not re.search(r'[a-z]', password):
        errors.append('contain at least one lowercase letter')
    if not re.search(r'[^A-Za-z0-9]', password):
        errors.append('contain at least one special character')

    if errors:
        raise ValidationError(f"Password must {', '.join(errors)}.")


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    role = SelectField('Account Role', choices=[
        ('Owner', 'Owner (Upload & Manage Documents)'),
        ('Viewer', 'Viewer (View & Download Shared Documents)'),
        ('Admin', 'Administrator (Full System Management)')
    ], default='Owner')
    password = PasswordField('Password', validators=[DataRequired(), validate_strong_password])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match')])
    submit = SubmitField('Create Account')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data.lower()).first()
        if user:
            raise ValidationError('An account with this email already exists.')


class LoginForm(FlaskForm):
    login_id = StringField('Email or Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Secure Login')


class DocumentUploadForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired(), Length(min=3, max=150)])
    category = SelectField('Category', choices=[(c, c) for c in Config.ALLOWED_CATEGORIES], validators=[DataRequired()])
    description = TextAreaField('Description / Notes', validators=[Length(max=500)])
    file = FileField('Upload File', validators=[
        DataRequired(message='Please select a document to upload'),
        FileAllowed(list(Config.ALLOWED_EXTENSIONS), f"Allowed formats: {', '.join(sorted(Config.ALLOWED_EXTENSIONS)).upper()}")
    ])
    submit = SubmitField('Upload Document')


class DocumentEditForm(FlaskForm):
    title = StringField('Document Title', validators=[DataRequired(), Length(min=3, max=150)])
    category = SelectField('Category', choices=[(c, c) for c in Config.ALLOWED_CATEGORIES], validators=[DataRequired()])
    description = TextAreaField('Description / Notes', validators=[Length(max=500)])
    submit = SubmitField('Save Changes')


class ShareDocumentForm(FlaskForm):
    user_id = SelectField('Select Recipient', coerce=int, validators=[DataRequired()])
    permission = SelectField('Access Permission', choices=[
        ('Read', 'Read Only (View and Download)'),
        ('Edit', 'Edit (View, Download, and Modify Details)')
    ], default='Read', validators=[DataRequired()])
    submit = SubmitField('Grant Access')


class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=30)])
    email = StringField('Email Address', validators=[DataRequired(), Email()])
    profile_pic = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (JPG, PNG, WEBP)')
    ])
    submit = SubmitField('Update Profile')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[DataRequired()])
    new_password = PasswordField('New Password', validators=[DataRequired(), validate_strong_password])
    confirm_new_password = PasswordField('Confirm New Password', validators=[DataRequired(), EqualTo('new_password', message='Passwords must match')])
    submit = SubmitField('Update Password')
