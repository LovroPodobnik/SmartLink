# SmartLink - Intelligent Link Cloaking Platform

An intelligent link cloaking platform designed for content creators to bypass platform restrictions by detecting bots vs humans and routing them appropriately.

## Quick Start - Local Development

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
```bash
# Copy the example environment file
cp .env.example .env

# Edit .env with your configuration (optional for development)
# The default settings will work for local development
```

### 3. Run Local Development Server
```bash
# Option 1: Use the development script (recommended)
python run_local.py

# Option 2: Use Flask directly
python main.py
```

The application will be available at:
- **Main App**: http://localhost:5000
- **Dashboard**: http://localhost:5000/dashboard  
- **Login**: http://localhost:5000/login

### 4. Development Features
- **Auto-login**: Email not required in development mode
- **SQLite Database**: Automatically created as `smartlink_local.db`
- **Hot Reload**: Changes automatically reload the server

## Production Deployment

### 1. Generate Production Configuration
```bash
python setup_production.py
```

### 2. Deploy to Railway (Recommended - ~$10/month)
1. Connect your GitHub repository to Railway
2. Add environment variables from `.env.template`
3. Add PostgreSQL database service
4. Deploy automatically

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

## Key Features

- **Smart Bot Detection**: Automatically detects crawlers vs human users
- **Custom Domains**: Support for branded domains with SSL
- **Analytics Dashboard**: Track clicks, platforms, and performance
- **Magic Link Auth**: Passwordless authentication via email
- **Multi-Platform Ready**: Deploy to Railway, Heroku, Render, etc.

## How It Works

1. Create smart links pointing to your content (OnlyFans, etc.)
2. Share the short links on social media
3. Bots/crawlers see safe placeholder pages
4. Real users get redirected to your actual content
5. Track everything with built-in analytics

## Environment Variables

### Development (.env)
```env
FLASK_ENV=development
DATABASE_URL=sqlite:///smartlink_local.db
SESSION_SECRET=your-dev-secret
DEBUG=True
```

### Production
```env
FLASK_SECRET_KEY=your-production-secret-key
DATABASE_URL=postgresql://...
MAIL_SERVER=smtp.gmail.com
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
FLASK_ENV=production
```

## Support

- See [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
- Check the `/test` endpoint to verify domain routing
- Development mode includes detailed logging
