from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, URLField, SelectField
from wtforms.validators import DataRequired, Email, URL, Length, Regexp

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])

class SmartLinkForm(FlaskForm):
    title = StringField('Link Title', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    target_url = URLField('Target URL (OnlyFans/Destination)', validators=[DataRequired(), URL()])
    safe_url = URLField('Safe Page URL (Optional)', validators=[URL(require_tld=False)])
    custom_domain_id = SelectField('Domain', coerce=int, validators=[])
    use_js_challenge = BooleanField('Use JavaScript Challenge', default=True)
    direct_from_tiktok = BooleanField('Direct from TikTok', default=True)

class CustomDomainForm(FlaskForm):
    domain = StringField('Domain Name', 
                        validators=[
                            DataRequired(), 
                            Length(max=255),
                            Regexp(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]*\.([a-zA-Z]{2,}\.?)*[a-zA-Z]{2,}$', 
                                  message="Please enter a valid domain name (e.g., links.yoursite.com)")
                        ])
