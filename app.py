import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Load environment variables from .env file for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available in production, skip
    pass

# Configure logging based on environment
env = os.environ.get('FLASK_ENV', 'production')
if env == 'development':
    logging.basicConfig(level=logging.DEBUG)
else:
    logging.basicConfig(level=logging.INFO)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
mail = Mail()

# Create the app
app = Flask(__name__)

# Configuration based on environment
app.secret_key = os.environ.get("SESSION_SECRET") or os.environ.get("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
app.config['ENV'] = env
if env == 'production':
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
database_url = os.environ.get("DATABASE_URL", "sqlite:///smartlink.db")

# Fix Railway/Heroku/Supabase postgres URL format for SQLAlchemy 2.0+
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

# For Vercel, ensure we're not using local SQLite in production
if os.environ.get('VERCEL_ENV') and database_url.startswith("sqlite"):
    raise ValueError("SQLite cannot be used on Vercel. Please configure DATABASE_URL with PostgreSQL.")

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Debug logging for database configuration
if env == 'development':
    app.logger.info(f"Database URL: {database_url}")
else:
    # Don't log full URL in production for security, just the type
    db_type = database_url.split("://")[0] if "://" in database_url else "unknown"
    app.logger.info(f"Database type: {db_type}")

# Database engine options - different for SQLite vs PostgreSQL
if database_url.startswith("sqlite"):
    # SQLite configuration
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_pre_ping": True,
    }
else:
    # PostgreSQL configuration for production
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }

# Mail configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USE_SSL'] = os.environ.get('MAIL_USE_SSL', 'false').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@smartlink.app')

# Initialize extensions
db.init_app(app)
mail.init_app(app)

# Import models and routes
import models
import routes
import health_check

# Initialize database tables only if not on Vercel
# Vercel serverless functions shouldn't create tables on every request
if not os.environ.get('VERCEL_ENV'):
    with app.app_context():
        try:
            db.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Database initialization failed: {e}")
            if env == 'development':
                raise
            else:
                # In production, continue without crashing but log the error
                app.logger.error("Continuing without database initialization")
