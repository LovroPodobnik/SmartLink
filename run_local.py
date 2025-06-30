#!/usr/bin/env python3
"""
Local development server for SmartLink
Run this script to start the development server
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded environment variables from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed. Install with: pip install python-dotenv")
    print("⚠️  Using system environment variables only")

# Import the Flask app
try:
    from app import app
    print("✅ Successfully imported Flask app")
except ImportError as e:
    print(f"❌ Failed to import Flask app: {e}")
    print("💡 Make sure you've installed dependencies: pip install -r requirements.txt")
    sys.exit(1)

def main():
    print("🚀 Starting SmartLink Local Development Server")
    print("=" * 50)
    
    # Get configuration from environment
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() in ['true', '1', 'on']
    env = os.environ.get("FLASK_ENV", "development")
    
    print(f"📍 Environment: {env}")
    print(f"🌐 Port: {port}")
    print(f"🔧 Debug: {debug}")
    print(f"🗄️  Database: {os.environ.get('DATABASE_URL', 'sqlite:///smartlink.db')}")
    
    # Check if email is configured
    if os.environ.get('MAIL_USERNAME'):
        print(f"📧 Email: {os.environ.get('MAIL_USERNAME')} (configured)")
    else:
        print("📧 Email: Not configured (using development auto-login)")
    
    print("\n" + "=" * 50)
    print(f"🎯 SmartLink is running at: http://localhost:{port}")
    print("📊 Dashboard will be available at: http://localhost:{port}/dashboard")
    print("🔐 Login at: http://localhost:{port}/login")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 50)
    
    try:
        app.run(
            host='0.0.0.0',
            port=port,
            debug=debug,
            use_reloader=True,
            use_debugger=debug
        )
    except KeyboardInterrupt:
        print("\n👋 SmartLink development server stopped")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()