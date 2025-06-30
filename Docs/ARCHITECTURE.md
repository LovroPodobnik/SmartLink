# SmartTicker Architecture Documentation

## Table of Contents
1. [Project Overview](#project-overview)
2. [Core Problem & Solution](#core-problem--solution)
3. [Architecture Components](#architecture-components)
4. [Custom Domain Management System](#custom-domain-management-system)
5. [DNS Verification Innovation](#dns-verification-innovation)
6. [Railway API Automation](#railway-api-automation)
7. [Smart Routing Logic](#smart-routing-logic)
8. [Database Schema](#database-schema)
9. [API Endpoints](#api-endpoints)
10. [Deployment Pipeline](#deployment-pipeline)
11. [Security Considerations](#security-considerations)
12. [Scalability & Performance](#scalability--performance)

---

## Project Overview

**SmartTicker** is a SaaS platform that provides intelligent link cloaking services for content creators. The platform enables creators to bypass social media platform restrictions by using smart bot detection to route crawlers and human users differently.

### Key Value Proposition
- **Problem**: Social media platforms (TikTok, Instagram) block or restrict links to adult content sites
- **Solution**: Smart links that show "safe" content to platform crawlers but redirect real users to intended destinations
- **Benefit**: Creators can share links without being flagged, increasing conversion rates by ~25%

---

## Core Problem & Solution

### The Platform Restriction Challenge
Content creators face a fundamental problem when promoting their work on social media:

```
Creator posts link → Platform crawler detects → Link gets flagged → Post restricted/banned
```

### SmartTicker's Solution
```
Creator posts SmartLink → Bot sees safe page → Human users reach target → Analytics tracked
```

### Technical Implementation
1. **Bot Detection**: User-agent analysis, behavioral patterns, IP filtering
2. **Smart Routing**: Bots → safe placeholder pages, Humans → actual content
3. **Analytics**: Track conversion rates, platform sources, click patterns
4. **Custom Domains**: White-label experience for enterprise clients

---

## Architecture Components

### Technology Stack
- **Backend**: Flask (Python 3.11)
- **Database**: PostgreSQL (production), SQLite (development)
- **Hosting**: Railway (auto-scaling, SSL, domain management)
- **Frontend**: Bootstrap 5, HTML5, JavaScript
- **DNS**: Custom domain verification system
- **API**: Railway GraphQL API integration

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Social Media  │    │   SmartTicker   │    │   Target Site   │
│   Platform Bot  │───▶│   Smart Router  │───▶│   (OnlyFans)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Safe Landing  │
                       │      Page       │
                       └─────────────────┘
```

### Core Services
1. **SmartLink Generator**: Creates short codes and manages redirects
2. **Bot Detection Engine**: Identifies crawlers vs human users
3. **Custom Domain Manager**: Handles white-label domain setup
4. **Analytics Tracker**: Records click data and conversion metrics
5. **Railway API Client**: Automates domain provisioning

---

## Custom Domain Management System

### Business Context
SmartTicker operates as a **SaaS platform** where customers can use their own branded domains instead of the default SmartTicker domain.

**Example Customer Flow:**
1. Customer signs up for SmartTicker
2. Customer wants to use `links.customer.com` instead of `smartticker.app/customer`
3. Customer adds domain in dashboard
4. System automatically provisions domain with SSL
5. Customer creates branded SmartLinks: `https://links.customer.com/abc123`

### Technical Challenge
The fundamental challenge was **automating domain provisioning** for a multi-tenant SaaS platform:

- ❌ **Manual approach**: Admin manually adds each customer domain to Railway → doesn't scale
- ✅ **Automated approach**: Customer verifies domain → System automatically provisions → Zero manual work

### Solution Architecture

#### 1. Domain Verification Flow
```
Customer adds domain → DNS verification → Automatic Railway provisioning → SSL activation
```

#### 2. Multi-Tenant Routing
```python
@app.route('/')
def index():
    current_domain = get_domain_from_request()
    
    if is_custom_domain(current_domain):
        # Customer's branded domain - show their landing page
        custom_domain = CustomDomain.query.filter_by(domain=current_domain).first()
        return render_template('custom_domain_index.html', domain=custom_domain)
    
    # Main SmartTicker domain - show platform homepage
    return render_template('index.html')
```

#### 3. Smart Link Resolution
```python
@app.route('/<short_code>')
def smart_redirect(short_code):
    smart_link = SmartLink.query.filter_by(short_code=short_code).first()
    
    # Bot detection logic
    if is_bot_user_agent(request.headers.get('User-Agent')):
        return redirect(smart_link.safe_url)  # Show safe page to bots
    
    # Human users get real content
    return redirect(smart_link.target_url)
```

---

## DNS Verification Innovation

### The DNS Conflict Problem
Traditional domain verification systems have a fundamental flaw when using Railway (or similar platforms):

```
❌ PROBLEMATIC APPROACH:
TXT Record: customer.com = "verification-token"
CNAME Record: customer.com = "railway.app" 

Result: DNS conflict - same domain can't have both TXT and CNAME records
```

### Our Solution: Subdomain Verification
We developed a **DNS standards-compliant verification system**:

```
✅ SMARTTICKER APPROACH:
TXT Record: _smartlink-verify.customer.com = "verification-token"  
CNAME Record: customer.com = "railway.app"

Result: No conflicts - TXT uses subdomain, CNAME uses main domain
```

### Implementation Details

#### Models (models.py)
```python
class CustomDomain(db.Model):
    domain = db.Column(db.String(255), unique=True, nullable=False)
    verification_token = db.Column(db.String(64), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    
    def get_verification_txt_subdomain(self):
        return f"_smartlink-verify.{self.domain}"
    
    def get_verification_txt_record(self):
        return self.verification_token  # Just the token, no prefix
```

#### Verification Logic (utils.py)
```python
def verify_domain_dns(domain, verification_token):
    verification_subdomain = f"_smartlink-verify.{domain}"
    txt_records = dns.resolver.resolve(verification_subdomain, 'TXT')
    
    for record in txt_records:
        if record.to_text().strip('"') == verification_token:
            return True
    return False
```

#### Customer Instructions
The system automatically generates correct DNS instructions:
```
Add these DNS records:
1. TXT: _smartlink-verify.links.customer.com = abc123xyz
2. CNAME: links.customer.com = smartticker-production.railway.app
```

---

## Railway API Automation

### The Scalability Challenge
Manual domain management doesn't scale for SaaS platforms:
- **Problem**: Each customer domain requires manual addition to Railway dashboard
- **Impact**: Operational bottleneck, delayed customer onboarding
- **Solution**: Automate domain provisioning via Railway's GraphQL API

### Railway API Integration

#### API Client (railway_api.py)
```python
class RailwayDomainManager:
    def __init__(self):
        self.endpoint = "https://backboard.railway.com/graphql/v2"
        self.api_token = os.environ.get('RAILWAY_API_TOKEN')
    
    def add_custom_domain(self, domain):
        mutation = """
        mutation CustomDomainCreate($input: CustomDomainCreateInput!) {
            customDomainCreate(input: $input) {
                id
                domain
                status
            }
        }
        """
        
        variables = {
            "input": {
                "projectId": self.project_id,
                "serviceId": self.service_id,
                "environmentId": self.environment_id,
                "domain": domain
            }
        }
        
        return self._make_request(mutation, variables)
```

#### Automated Workflow (routes.py)
```python
@app.route('/domains/<int:domain_id>/check', methods=['POST'])
def check_domain_verification(domain_id):
    domain = CustomDomain.query.get(domain_id)
    
    # Step 1: Verify DNS ownership
    if verify_domain_ownership(domain.domain, domain.verification_token):
        domain.is_verified = True
        
        # Step 2: Auto-add to Railway
        try:
            railway_manager = get_railway_manager()
            railway_result = railway_manager.add_custom_domain(domain.domain)
            
            if railway_result:
                domain.ssl_enabled = True  # Railway auto-provisions SSL
                flash(f'Domain {domain.domain} verified and activated!', 'success')
                
        except Exception as e:
            flash(f'Domain verified but setup failed: {str(e)}', 'warning')
```

### Customer Experience Flow
```
1. Customer adds domain in dashboard
2. Customer sets DNS records as instructed
3. Customer clicks "Verify Domain"
4. System automatically:
   ✅ Verifies DNS ownership
   ✅ Adds domain to Railway via API
   ✅ Enables SSL automatically
   ✅ Activates domain for SmartLink creation
5. Customer immediately uses: https://links.customer.com/abc123
```

### Environment Configuration
```bash
# Required Railway API variables
RAILWAY_API_TOKEN=your_graphql_api_token
RAILWAY_PROJECT_ID=project_uuid
RAILWAY_SERVICE_ID=service_uuid  
RAILWAY_ENVIRONMENT_ID=environment_uuid
```

---

## Smart Routing Logic

### Bot Detection Engine
The core intelligence of SmartTicker lies in distinguishing between automated crawlers and human users:

#### User-Agent Analysis
```python
BOT_PATTERNS = [
    r'facebookexternalhit',  # Facebook crawler
    r'bytespider',           # TikTok crawler
    r'twitterbot',           # Twitter crawler
    r'linkedinbot',          # LinkedIn crawler
    r'whatsapp',             # WhatsApp preview
    r'googlebot',            # Google crawler
    r'crawler', r'spider', r'scraper', r'bot/'
]

def is_bot_user_agent(user_agent):
    if not user_agent:
        return True  # No user-agent = likely bot
    
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    return False
```

#### Behavioral Analysis
```python
def is_suspicious_request(user_agent):
    suspicious_patterns = [
        r'curl', r'wget', r'python', r'requests', 
        r'httpie', r'postman'
    ]
    # Additional checks for automated tools
```

#### Platform Detection
```python
def get_platform_from_referrer(referrer):
    if 'tiktok.com' in referrer.lower():
        return 'tiktok'
    elif 'instagram.com' in referrer.lower():
        return 'instagram'
    # ... other platforms
```

### Redirect Logic
```python
@app.route('/<short_code>')
def smart_redirect(short_code):
    smart_link = SmartLink.query.filter_by(short_code=short_code).first()
    
    # Analytics tracking
    click = Click(
        smart_link_id=smart_link.id,
        ip_address=truncate_ip(request.remote_addr),
        user_agent=request.headers.get('User-Agent'),
        referrer=request.headers.get('Referer'),
        platform=get_platform_from_referrer(request.headers.get('Referer'))
    )
    
    # Smart routing decision
    if is_bot_user_agent(request.headers.get('User-Agent')):
        click.click_type = 'bot'
        click.target_reached = 'safe'
        db.session.add(click)
        db.session.commit()
        
        # Redirect bots to safe page
        safe_url = smart_link.safe_url or url_for('index')
        return redirect(safe_url)
    
    # Human users get real content
    click.click_type = 'human'
    click.target_reached = 'target'
    db.session.add(click)
    db.session.commit()
    
    return redirect(smart_link.target_url)
```

---

## Database Schema

### Core Tables

#### Users
```sql
CREATE TABLE user (
    id SERIAL PRIMARY KEY,
    email VARCHAR(120) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE
);
```

#### Smart Links
```sql
CREATE TABLE smart_link (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    custom_domain_id INTEGER REFERENCES custom_domain(id),
    short_code VARCHAR(10) UNIQUE NOT NULL,
    target_url VARCHAR(500) NOT NULL,  -- Real destination (e.g., OnlyFans)
    safe_url VARCHAR(500),             -- Safe page for bots
    title VARCHAR(100) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Settings
    use_js_challenge BOOLEAN DEFAULT TRUE,
    direct_from_tiktok BOOLEAN DEFAULT TRUE
);
```

#### Custom Domains
```sql
CREATE TABLE custom_domain (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    domain VARCHAR(255) UNIQUE NOT NULL,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(64) NOT NULL,
    ssl_enabled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMP,
    verification_method VARCHAR(20) DEFAULT 'dns'
);
```

#### Click Analytics
```sql
CREATE TABLE click (
    id SERIAL PRIMARY KEY,
    smart_link_id INTEGER REFERENCES smart_link(id),
    ip_address VARCHAR(45),           -- Truncated for GDPR compliance
    user_agent TEXT,
    referrer VARCHAR(500),
    click_type VARCHAR(20),           -- 'human', 'bot', 'suspect'
    target_reached VARCHAR(20),       -- 'target', 'safe', 'challenge'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Analytics fields
    country VARCHAR(2),
    platform VARCHAR(20)              -- 'tiktok', 'instagram', 'other'
);
```

#### Login Tokens (Magic Link Auth)
```sql
CREATE TABLE login_token (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user(id),
    token VARCHAR(64) UNIQUE NOT NULL,
    expires_at TIMESTAMP NOT NULL,
    used BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Key Relationships
- One user can have multiple domains
- One domain can have multiple smart links
- Each smart link tracks multiple clicks
- Users authenticate via magic link tokens

---

## API Endpoints

### Authentication Endpoints
```python
# Magic link authentication
POST /login                    # Send magic link to email
GET  /auth/verify/<token>      # Verify magic link token
GET  /logout                   # Clear session
```

### Smart Link Management
```python
# Core SmartLink operations
GET  /dashboard               # User dashboard with analytics
GET  /create                  # Create new SmartLink form
POST /create                  # Create SmartLink
GET  /links/<int:link_id>     # View/edit specific link
POST /links/<int:link_id>/delete  # Delete link

# Public redirect endpoint
GET  /<short_code>            # Smart redirect logic
```

### Domain Management
```python
# Custom domain operations
GET  /domains                 # List user domains
GET  /domains/add             # Add domain form
POST /domains/add             # Create domain
GET  /domains/<int:id>/verify # Domain verification page
POST /domains/<int:id>/check  # Verify domain (triggers Railway API)
POST /domains/<int:id>/delete # Delete domain
```

### Analytics & Utilities
```python
# Analytics and tools
GET  /analytics/<int:link_id> # Link analytics dashboard
GET  /test                    # Test domain routing
GET  /                        # Landing page (domain-aware routing)
```

### Domain-Aware Routing
All endpoints automatically detect the requesting domain and adjust behavior:

```python
def get_domain_from_request():
    return request.headers.get('Host', '').lower()

def is_custom_domain(domain):
    default_domains = ['localhost:5000', 'smartlink.app']
    return (domain not in default_domains and 
            not domain.endswith('.railway.app'))
```

---

## Deployment Pipeline

### Development Environment
```bash
# Local development setup
python run_local.py           # Development server with auto-login
DATABASE_URL=sqlite:///smartlink_local.db
FLASK_ENV=development
DEBUG=True
```

### Production Deployment (Railway)

#### Infrastructure as Code
```json
// railway.json
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

#### Environment Variables
```bash
# Production configuration
FLASK_SECRET_KEY=production_secret_key
DATABASE_URL=postgresql://user:pass@host:port/db
MAIL_SERVER=smtp.provider.com
MAIL_USERNAME=noreply@smartticker.com
MAIL_PASSWORD=app_password
FLASK_ENV=production

# Railway API automation
RAILWAY_API_TOKEN=graphql_api_token
RAILWAY_PROJECT_ID=project_uuid
RAILWAY_SERVICE_ID=service_uuid
RAILWAY_ENVIRONMENT_ID=environment_uuid
```

#### Deployment Flow
```
Git push → Railway detects changes → Build → Deploy → Health check → Live
```

#### Database Migrations
```python
# Database initialization on startup
with app.app_context():
    import models
    db.create_all()  # Creates tables if they don't exist
```

### CI/CD Pipeline
```
1. Code push to main branch
2. Railway automatic deployment
3. Build Docker container with nixpacks
4. Run database migrations
5. Health check on /
6. Update service domains
7. SSL certificate provisioning
```

---

## Security Considerations

### Input Validation & Sanitization
```python
# Domain validation
DOMAIN_REGEX = re.compile(
    r'^[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?'
    r'(\.[a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?)*$'
)

class CustomDomainForm(FlaskForm):
    domain = StringField('Domain', validators=[
        DataRequired(),
        Regexp(DOMAIN_REGEX, message="Invalid domain format")
    ])
```

### Privacy Protection (GDPR Compliance)
```python
def truncate_ip(ip_address):
    """Truncate IP for privacy compliance"""
    if ':' in ip_address:  # IPv6
        parts = ip_address.split(':')
        return ':'.join(parts[:4]) + '::0'
    else:  # IPv4
        parts = ip_address.split('.')
        return '.'.join(parts[:3]) + '.0'
```

### Authentication Security
```python
# Secure token generation
def generate_verification_token():
    return ''.join(secrets.choice(string.ascii_letters + string.digits) 
                   for _ in range(32))

# Magic link token expiration
class LoginToken(db.Model):
    expires_at = db.Column(db.DateTime, nullable=False)
    
    def __init__(self, user_id):
        self.expires_at = datetime.utcnow() + timedelta(minutes=15)
```

### SQL Injection Prevention
- Uses SQLAlchemy ORM with parameterized queries
- All database interactions through ORM models
- No raw SQL execution with user input

### XSS Protection
- Flask-WTF CSRF protection enabled
- Template auto-escaping enabled
- User input sanitized in templates

### SSL/TLS Security
- Railway auto-provisions SSL certificates
- HTTPS enforced in production
- Secure headers configured

---

## Scalability & Performance

### Performance Optimizations

#### Database Connection Pooling
```python
# PostgreSQL connection optimization
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
    "pool_size": 10,
    "max_overflow": 20
}
```

#### Caching Strategy
```python
# IP address truncation caching
@lru_cache(maxsize=1000)
def truncate_ip(ip_address):
    # Cached IP truncation for performance
```

#### Efficient Redirects
- <50ms redirect time target
- Minimal database queries per redirect
- Optimized bot detection patterns

### Scalability Considerations

#### Horizontal Scaling
- Stateless application design
- External PostgreSQL database
- Railway auto-scaling capabilities

#### Database Scaling
```sql
-- Indexes for performance
CREATE INDEX idx_smart_link_short_code ON smart_link(short_code);
CREATE INDEX idx_custom_domain_domain ON custom_domain(domain);
CREATE INDEX idx_click_smart_link_id ON click(smart_link_id);
CREATE INDEX idx_click_created_at ON click(created_at);
```

#### Rate Limiting
- Railway provides built-in DDoS protection
- Application-level rate limiting for API endpoints
- Bot detection helps reduce malicious traffic

#### Cost Optimization
```
Railway Costs:
- Starter Plan: $5/month (app hosting)
- PostgreSQL: $5/month (managed database)
- Custom Domains: Free (SSL included)
Total: ~$10/month for MVP

Scaling Path:
- Pro Plan: $20/month (higher resources)
- Database Upgrade: $10/month (more storage/memory)
- CDN: Optional for global performance
```

### Monitoring & Observability

#### Application Logging
```python
import logging

# Structured logging for Railway
app.logger.info(f"Domain {domain.domain} added to Railway with ID {railway_id}")
app.logger.warning(f"Domain {domain.domain} verified but Railway setup failed")
app.logger.error(f"Railway API error for domain {domain.domain}: {str(e)}")
```

#### Analytics Tracking
- Click-through rates by platform
- Bot vs human traffic analysis
- Domain performance metrics
- User engagement tracking

#### Health Monitoring
```python
@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
```

---

## Conclusion

SmartTicker represents a sophisticated SaaS platform that solves real-world problems for content creators while implementing cutting-edge automation technologies. The combination of intelligent bot detection, automated domain provisioning, and DNS innovation creates a scalable, user-friendly solution.

### Key Innovations
1. **DNS Verification Innovation**: Solved the TXT/CNAME conflict with subdomain verification
2. **Railway API Automation**: Zero-touch domain provisioning for SaaS customers
3. **Smart Routing**: Intelligent bot detection and content routing
4. **Multi-Tenant Architecture**: Proper domain isolation and branding

### Technical Excellence
- **Scalable Architecture**: Designed for growth from day one
- **Security First**: GDPR compliance, secure authentication, input validation
- **Performance Optimized**: <50ms redirects, efficient database design
- **Developer Friendly**: Clear code organization, comprehensive documentation

### Business Impact
- **Customer Experience**: Zero-friction domain setup and management
- **Operational Efficiency**: Fully automated domain provisioning
- **Scalability**: Can handle thousands of custom domains automatically
- **Revenue Enablement**: Removes technical barriers to customer onboarding

This architecture serves as a blueprint for building modern SaaS platforms that require automated infrastructure provisioning and intelligent content routing.