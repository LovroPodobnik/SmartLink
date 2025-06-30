# SmartLink - Intelligent Link Cloaking Platform

## Overview

SmartLink is a Flask-based web application designed for content creators who need to bypass platform restrictions when sharing links to their content (primarily OnlyFans). The system intelligently detects bots/crawlers and redirects them to safe pages while sending real human users directly to the target destination.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLAlchemy ORM with SQLite (default) or PostgreSQL support
- **Authentication**: Magic link authentication via email (no passwords)
- **Email Service**: Flask-Mail with SMTP configuration
- **Session Management**: Flask sessions with secure secret keys

### Frontend Architecture
- **Templates**: Jinja2 templating engine
- **Styling**: Bootstrap 5.3.0 with custom CSS
- **JavaScript**: Vanilla JS with Chart.js for analytics
- **Icons**: Font Awesome 6.4.0
- **Responsive Design**: Mobile-first approach optimized for TikTok/Instagram

### Database Schema
- **Users**: Email-based user accounts with creation timestamps
- **LoginTokens**: Time-limited magic link tokens for authentication
- **SmartLinks**: Core link entities with cloaking configuration
- **Clicks**: Analytics tracking for each link interaction
- **CustomDomains**: User-owned domains for branded smart links with verification system

## Key Components

### Authentication System
- **Magic Link Login**: Password-less authentication via email tokens
- **Token Expiration**: 15-minute token validity for security
- **Session Management**: Flask session-based user state

### Smart Link Engine
- **Bot Detection**: User-agent pattern matching for known crawlers
- **Platform Detection**: Referrer-based platform identification (TikTok, Instagram, etc.)
- **Conditional Routing**: Humans → target URL, Bots → safe page
- **JavaScript Challenge**: Optional additional bot verification

### Analytics System
- **Click Tracking**: Separate counting for human vs bot interactions
- **Platform Analytics**: Traffic source identification
- **Real-time Metrics**: Dashboard with visual charts
- **IP Truncation**: Privacy-conscious analytics (truncated IPs)

### Link Management
- **Short Code Generation**: Unique alphanumeric identifiers
- **Dual URL System**: Target URL (OnlyFans) + Optional safe page URL
- **Configuration Options**: JS challenge toggle, TikTok direct routing
- **Link Lifecycle**: Active/inactive status management

## Data Flow

### Human User Flow
1. User clicks SmartLink in social media bio
2. System detects human user-agent and referrer
3. Direct 302 redirect to target URL (OnlyFans)
4. Click recorded as "human" in analytics

### Bot/Crawler Flow
1. Platform crawler accesses SmartLink
2. System identifies bot via user-agent patterns
3. 302 redirect to safe page with generic content
4. Click recorded as "bot" in analytics

### Authentication Flow
1. User enters email address
2. System generates time-limited token
3. Magic link sent via email
4. Token verification creates session
5. User gains access to dashboard

## External Dependencies

### Email Service
- **SMTP Configuration**: Gmail or custom SMTP server
- **Environment Variables**: MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD
- **Fallback**: Local development uses debug mode

### Database
- **Development**: SQLite for local development
- **Production**: PostgreSQL via DATABASE_URL environment variable
- **Connection Pooling**: Configured for production reliability

### CDN Resources
- **Bootstrap**: External CSS/JS framework
- **Font Awesome**: Icon library
- **Chart.js**: Analytics visualization
- **No critical dependencies**: All external resources have fallbacks

## Deployment Strategy

### Environment Configuration
- **Development**: Local SQLite with debug mode
- **Production**: Environment variables for all sensitive data
- **Security**: ProxyFix middleware for proper header handling

### Scalability Considerations
- **Database**: Easy migration from SQLite to PostgreSQL
- **Session Storage**: Can be moved to Redis for horizontal scaling
- **CDN**: Static assets ready for CDN deployment

### Security Features
- **CSRF Protection**: Flask-WTF forms with CSRF tokens
- **SQL Injection**: SQLAlchemy ORM prevents injection attacks
- **Session Security**: Secure session keys and HTTPS-ready
- **Rate Limiting**: Ready for implementation with Flask-Limiter

## Changelog

```
Changelog:
- June 30, 2025. Initial setup
- June 30, 2025. Added custom domain functionality with verification system
```

## User Preferences

```
Preferred communication style: Simple, everyday language.
```