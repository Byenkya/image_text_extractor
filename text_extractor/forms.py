from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SubmitField
from text_extractor.config import Config
from wtforms import StringField, SubmitField, MultipleFileField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError, InputRequired
from wtforms import StringField, PasswordField, SubmitField, HiddenField
from .models import User 

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Login')

class UploadForm(FlaskForm):
    file = FileField(
        'Upload Image File', 
        validators=[FileAllowed(Config.ALLOWED_EXTENSIONS, 'Invalid file format.')])
    submit = SubmitField('Upload')


class ImageForm(FlaskForm):
    image_name = StringField('Image Name', validators=[DataRequired()])
    submit = SubmitField('Extract Text')

class ImageCaptureForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])
    image_data = HiddenField('Image Data', validators=[InputRequired()])

class UserCreationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Create User')

    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already exists. Please choose a different username.')
