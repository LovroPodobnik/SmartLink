# SmartLink MVP Deployment Guide

## Overview
This guide covers deploying SmartLink on Railway - a budget-friendly platform that provides everything you need: app hosting, PostgreSQL database, and custom domain support for under $20/month.

## Why Railway?
- **All-in-one platform**: App hosting + database + domains
- **Budget-friendly**: $5/month for app + $5/month for database
- **Simple deployment**: Git-based deployment
- **Custom domains**: Free SSL certificates included
- **PostgreSQL**: Fully managed database service

## Prerequisites
- Git repository with your SmartLink code
- Railway account (free signup)
- Domain name (optional, for custom domains)

## Step 1: Railway Setup

### 1.1 Create Railway Account
1. Go to [railway.app](https://railway.app)
2. Sign up with GitHub account
3. Verify email address

### 1.2 Install Railway CLI (Optional)
```bash
npm install -g @railway/cli
railway login
```

## Step 2: Deploy Application

### 2.1 Create New Project
1. Click "New Project" in Railway dashboard
2. Select "Deploy from GitHub repo"
3. Connect your SmartLink repository
4. Railway auto-detects it's a Python app

### 2.2 Environment Variables
In Railway dashboard, go to your app and add these variables:

```env
# Required
FLASK_SECRET_KEY=your-super-secret-key-here-make-it-long-and-random
DATABASE_URL=postgresql://username:password@host:port/database

# Email Configuration (for magic links)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Production Settings
FLASK_ENV=production
```

### 2.3 Generate Secret Key
```python
# Run this in Python to generate a secure secret key
import secrets
print(secrets.token_hex(32))
```

## Step 3: Database Setup

### 3.1 Add PostgreSQL to Project
1. In Railway dashboard, click "New Service"
2. Select "PostgreSQL"
3. Database provisions automatically
4. Copy the DATABASE_URL from database settings

### 3.2 Update App Environment
1. Go to your app service settings
2. Add the DATABASE_URL variable
3. Railway auto-connects services

## Step 4: Domain Configuration

### 4.1 Custom Domain for Dashboard
1. In Railway app settings, go to "Settings" > "Domains"
2. Add your domain (e.g., `smartlink.yourdomain.com`)
3. Update DNS: Add CNAME record pointing to Railway domain
4. SSL certificate auto-provisions

### 4.2 Email Setup
For Gmail SMTP:
1. Enable 2-factor authentication
2. Generate App Password in Google Account settings
3. Use app password in MAIL_PASSWORD variable

## Step 5: File Structure

Ensure your repository has these files:

### 5.1 requirements.txt
```txt
flask==3.0.0
flask-sqlalchemy==3.1.1
flask-wtf==1.2.1
flask-mail==0.9.1
flask-login==0.6.3
psycopg2-binary==2.9.9
gunicorn==21.2.0
wtforms==3.1.1
email-validator==2.1.0
dnspython==2.4.2
requests==2.31.0
```

### 5.2 Procfile
```
web: gunicorn --bind 0.0.0.0:$PORT main:app
```

### 5.3 runtime.txt
```
python-3.11.6
```

### 5.4 railway.json
```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "nixpacks"
  },
  "deploy": {
    "startCommand": "gunicorn --bind 0.0.0.0:$PORT main:app",
    "healthcheckPath": "/",
    "healthcheckTimeout": 100
  }
}
```

## Step 6: Production Configuration

### 6.1 Update main.py for Production
```python
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app = Flask(__name__)

# Production configuration
app.secret_key = os.environ.get("FLASK_SECRET_KEY")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20
}

# Email configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')

db.init_app(app)

with app.app_context():
    import models
    db.create_all()

# Import routes after app setup
import routes
```

## Step 7: Database Migration

### 7.1 Initial Setup
After deployment, the database tables are created automatically by `db.create_all()`.

### 7.2 Future Migrations
For schema changes, you can:
1. Connect to Railway database using provided credentials
2. Run SQL commands directly
3. Or use Flask-Migrate for managed migrations

## Step 8: Custom Domain Management

### 8.1 Customer Domain Setup
When customers want to use custom domains:

1. **Customer adds CNAME**:
   ```
   links.customer.com → your-app.railway.app
   ```

2. **Your app handles the domain**:
   - Railway automatically routes all domains to your app
   - Your Flask app detects the domain and serves appropriate content

### 8.2 SSL Certificates
Railway provides automatic SSL for:
- Your main domain
- Customer domains (when CNAME is properly configured)

## Step 9: Monitoring & Maintenance

### 9.1 Railway Dashboard
Monitor your app through Railway dashboard:
- Deployment logs
- Application metrics
- Database usage
- Domain status

### 9.2 Database Backups
Railway provides automatic backups for PostgreSQL:
- Daily backups retained for 7 days
- Point-in-time recovery available

## Step 10: Cost Breakdown

### Monthly Costs (Estimated):
- **Railway Starter Plan**: $5/month (app hosting)
- **PostgreSQL Database**: $5/month (512MB RAM, 1GB storage)
- **Custom Domain**: Free (SSL included)
- **Total**: ~$10/month for MVP

### Scaling Costs:
- **Pro Plan**: $20/month (more resources)
- **Database Upgrade**: $10/month (1GB RAM, 4GB storage)
- **Total**: ~$30/month for growing app

## Step 11: Going Live

### 11.1 Pre-Launch Checklist
- [ ] All environment variables set
- [ ] Database tables created
- [ ] Email sending working
- [ ] Custom domain pointing correctly
- [ ] SSL certificate active
- [ ] Test link creation and redirects

### 11.2 Launch Steps
1. Update DNS to point to Railway
2. Test all functionality
3. Monitor logs for any issues
4. Set up monitoring alerts

## Step 12: Alternative Budget Options

If Railway doesn't meet your needs:

### Render (Similar to Railway)
- Web service: $7/month
- PostgreSQL: $7/month
- Total: ~$14/month

### DigitalOcean App Platform
- Basic app: $5/month
- Managed database: $15/month
- Total: ~$20/month

### Heroku (More expensive but reliable)
- Dyno: $7/month
- PostgreSQL: $9/month
- Total: ~$16/month

## Troubleshooting

### Common Issues:
1. **Database connection errors**: Check DATABASE_URL format
2. **Email not sending**: Verify SMTP credentials
3. **Custom domains not working**: Check CNAME configuration
4. **App not starting**: Check Procfile and requirements.txt

### Debugging:
```bash
# View Railway logs
railway logs

# Connect to database
railway connect postgres
```

## Support

- **Railway Documentation**: [docs.railway.app](https://docs.railway.app)
- **Community**: Railway Discord server
- **Status**: [status.railway.app](https://status.railway.app)

---

This deployment setup gives you a production-ready SmartLink application for under $15/month, with room to scale as your user base grows.