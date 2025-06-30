from app import db
from datetime import datetime, timedelta
import secrets
import string
import os

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    smart_links = db.relationship('SmartLink', backref='user', lazy=True)
    login_tokens = db.relationship('LoginToken', backref='user', lazy=True)
    custom_domains = db.relationship('CustomDomain', backref='user', lazy=True)

class LoginToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    used = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id):
        self.user_id = user_id
        self.token = self.generate_token()
        self.expires_at = datetime.utcnow() + timedelta(minutes=15)
    
    @staticmethod
    def generate_token():
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))

class SmartLink(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    custom_domain_id = db.Column(db.Integer, db.ForeignKey('custom_domain.id'), nullable=True)
    short_code = db.Column(db.String(10), unique=True, nullable=False)
    target_url = db.Column(db.String(500), nullable=False)  # OnlyFans or target URL
    safe_url = db.Column(db.String(500), nullable=True)     # Safe page URL (optional)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Settings
    use_js_challenge = db.Column(db.Boolean, default=True)
    direct_from_tiktok = db.Column(db.Boolean, default=True)
    
    # Relationships
    clicks = db.relationship('Click', backref='smart_link', lazy=True)
    custom_domain = db.relationship('CustomDomain', backref='smart_links', lazy=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.short_code:
            self.short_code = self.generate_short_code()
    
    @staticmethod
    def generate_short_code():
        while True:
            code = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(6))
            if not SmartLink.query.filter_by(short_code=code).first():
                return code
    
    def get_full_url(self, request_host=None):
        """Get the full URL for this smart link"""
        if self.custom_domain and self.custom_domain.is_verified and self.custom_domain.is_active:
            # Use custom domain
            protocol = 'https' if self.custom_domain.ssl_enabled else 'http'
            return f"{protocol}://{self.custom_domain.domain}/{self.short_code}"
        else:
            # Use default domain from request or fallback
            host = request_host or 'smartlink.app'
            return f"https://{host}/{self.short_code}"

class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    smart_link_id = db.Column(db.Integer, db.ForeignKey('smart_link.id'), nullable=False)
    ip_address = db.Column(db.String(45))  # Support IPv6
    user_agent = db.Column(db.Text)
    referrer = db.Column(db.String(500))
    click_type = db.Column(db.String(20))  # 'human', 'bot', 'suspect'
    target_reached = db.Column(db.String(20))  # 'target', 'safe', 'challenge'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Enhanced platform tracking
    platform = db.Column(db.String(20))  # 'tiktok', 'instagram', 'facebook', 'twitter', 'other'
    country = db.Column(db.String(2))
    
    # Advanced detection analytics
    confidence_score = db.Column(db.Float)  # Bot detection confidence (0.0-1.0)
    risk_level = db.Column(db.String(10))   # 'low', 'medium', 'high', 'critical'
    detection_methods = db.Column(db.Text)  # JSON array of detection methods used

class CustomDomain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    domain = db.Column(db.String(255), unique=True, nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(64), nullable=False)
    ssl_enabled = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)
    verification_method = db.Column(db.String(20), default='dns')  # 'dns' or 'file'
    # railway_domain_id = db.Column(db.String(64), nullable=True)  # TODO: Add after database migration
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.verification_token:
            self.verification_token = self.generate_verification_token()
    
    @staticmethod
    def generate_verification_token():
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
    
    def get_verification_txt_record(self):
        """Get the TXT record value for domain verification"""
        return self.verification_token
    
    def get_verification_txt_subdomain(self):
        """Get the subdomain name for TXT record verification"""
        return f"_smartlink-verify.{self.domain}"
    
    def get_cname_record_value(self):
        """Get the CNAME record value for routing"""
        # Use Railway's provided environment variables in order of preference
        return (os.environ.get('RAILWAY_PUBLIC_DOMAIN') or 
                os.environ.get('RAILWAY_STATIC_URL') or
                os.environ.get('APP_DOMAIN') or
                'web-production-b9e4.up.railway.app')
    
    def get_verification_file_content(self):
        """Get the verification file content for file-based verification"""
        return self.verification_token
