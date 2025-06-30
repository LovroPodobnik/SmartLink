#!/usr/bin/env python3
"""
Production setup script for SmartLink
Run this to generate required configuration files and secrets
"""

import secrets
import os

def generate_secret_key():
    """Generate a secure secret key for Flask"""
    return secrets.token_hex(32)

def create_env_template():
    """Create a .env template file with required variables"""
    secret_key = generate_secret_key()
    
    env_content = f"""# SmartLink Production Configuration
# Copy this to your deployment platform (Railway, Heroku, etc.)

# Required: Flask secret key (KEEP THIS SECRET!)
FLASK_SECRET_KEY={secret_key}
SESSION_SECRET={secret_key}

# Required: Database connection
DATABASE_URL=postgresql://username:password@host:port/database

# Required: Email configuration for magic links
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-gmail-app-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com

# Production settings
FLASK_ENV=production
DEBUG=False
"""
    
    with open('.env.template', 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env.template with secure secret key")
    print("📧 Remember to set up Gmail App Password for email sending")
    
def check_required_files():
    """Check if all required deployment files exist"""
    required_files = [
        'requirements.txt',
        'Procfile', 
        'runtime.txt',
        'railway.json',
        'main.py',
        'app.py'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {', '.join(missing_files)}")
        return False
    else:
        print("✅ All deployment files present")
        return True

def main():
    print("🚀 SmartLink Production Setup")
    print("=" * 40)
    
    # Generate environment template
    create_env_template()
    
    # Check required files
    check_required_files()
    
    print("\n📋 Next steps:")
    print("1. Copy variables from .env.template to your deployment platform")
    print("2. Set up Gmail App Password for MAIL_PASSWORD")
    print("3. Get PostgreSQL URL from your database provider")
    print("4. Deploy to Railway, Render, or similar platform")
    print("\n📖 See DEPLOYMENT.md for detailed instructions")

if __name__ == "__main__":
    main()