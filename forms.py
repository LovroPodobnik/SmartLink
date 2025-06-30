from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, URLField
from wtforms.validators import DataRequired, Email, URL, Length

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class SmartLinkForm(FlaskForm):
    title = StringField('Link Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    target_url = URLField('Target URL (OnlyFans/Destination)', validators=[DataRequired(), URL()])
    safe_url = URLField('Safe Page URL (Optional)', validators=[URL(require_tld=False)])
    use_js_challenge = BooleanField('Use JavaScript Challenge', default=True)
    direct_from_tiktok = BooleanField('Direct from TikTok', default=True)
