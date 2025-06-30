import re
import urllib.request
import urllib.error
import dns.resolver
import ipaddress
from flask import request
from flask_mail import Message
from app import mail

# Enhanced bot detection patterns with platform-specific detection
BOT_PATTERNS = [
    # TikTok crawlers (comprehensive coverage)
    r'bytespider',              # Main TikTok crawler
    r'tiktok',                  # Generic TikTok pattern
    r'musicallybot',            # Legacy Musical.ly bot
    r'bytedance',               # Parent company crawlers
    r'tiktok.*bot',             # TikTok variants
    r'douyin',                  # Chinese TikTok version
    
    # Meta/Facebook family
    r'facebookexternalhit',     # Facebook link preview
    r'facebookcatalog',         # Facebook catalog
    r'instagrambot',            # Instagram crawler
    r'meta.*bot',               # Meta variants
    
    # Twitter/X
    r'twitterbot',
    r'x.*bot',                  # New X branding
    
    # Other major platforms
    r'linkedinbot',
    r'whatsapp',
    r'telegrambot',
    r'snapchat.*bot',
    r'discordbot',
    r'slackbot',
    r'pinterestbot',
    r'redditbot',
    
    # Search engines
    r'googlebot',
    r'bingbot',
    r'applebot',
    r'baiduspider',
    r'yandexbot',
    
    # Generic patterns
    r'crawler',
    r'spider',
    r'scraper',
    r'bot/',
    r'headless',
    r'phantom',
    r'selenium',
    r'puppeteer'
]

# TikTok-specific user agent patterns for enhanced detection
TIKTOK_SPECIFIC_PATTERNS = [
    r'bytespider',
    r'tiktok',
    r'musically',
    r'bytedance',
    r'douyin',
    r'aweme',                   # TikTok internal name
    r'com\.zhiliaoapp\.musically',  # TikTok mobile app identifier
    r'musical_ly',
]

# Platform IP ranges (simplified - in production, use complete CIDR blocks)
PLATFORM_IP_RANGES = {
    'tiktok': [
        '103.216.0.0/16',       # TikTok Singapore
        '161.117.0.0/16',       # ByteDance US
        '49.51.0.0/16',         # TikTok Asia Pacific
    ],
    'facebook': [
        '31.13.0.0/16',         # Facebook main
        '66.220.0.0/16',        # Facebook crawlers
        '69.63.0.0/16',         # Facebook infrastructure
    ],
    'google': [
        '66.249.0.0/16',        # Googlebot
        '64.233.0.0/16',        # Google services
    ]
}

def is_bot_user_agent(user_agent):
    """Check if user agent matches known bot patterns"""
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    return False

def is_tiktok_bot(user_agent, ip_address=None):
    """Enhanced TikTok-specific bot detection"""
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    
    # Check TikTok-specific patterns
    for pattern in TIKTOK_SPECIFIC_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    
    # Check IP ranges if available
    if ip_address and is_platform_ip(ip_address, 'tiktok'):
        return True
    
    return False

def is_platform_ip(ip_address, platform):
    """Check if IP address belongs to a specific platform"""
    if not ip_address or platform not in PLATFORM_IP_RANGES:
        return False
    
    try:
        ip_obj = ipaddress.ip_address(ip_address)
        for cidr in PLATFORM_IP_RANGES[platform]:
            network = ipaddress.ip_network(cidr, strict=False)
            if ip_obj in network:
                return True
    except (ValueError, ipaddress.AddressValueError):
        pass
    
    return False

def detect_platform_from_request(user_agent=None, referrer=None, ip_address=None):
    """Comprehensive platform detection from request data"""
    if not user_agent:
        user_agent = request.headers.get('User-Agent', '')
    if not referrer:
        referrer = request.headers.get('Referer', '')
    if not ip_address:
        ip_address = request.remote_addr
    
    user_agent_lower = user_agent.lower()
    referrer_lower = referrer.lower() if referrer else ''
    
    # TikTok detection
    if (any(re.search(pattern, user_agent_lower) for pattern in TIKTOK_SPECIFIC_PATTERNS) or
        'tiktok.com' in referrer_lower or 'musically.com' in referrer_lower or
        is_platform_ip(ip_address, 'tiktok')):
        return 'tiktok'
    
    # Instagram/Facebook detection
    if ('instagram' in user_agent_lower or 'instagram.com' in referrer_lower or
        'facebook' in user_agent_lower or 'facebook.com' in referrer_lower or
        is_platform_ip(ip_address, 'facebook')):
        return 'instagram' if 'instagram' in (user_agent_lower + referrer_lower) else 'facebook'
    
    # Twitter/X detection
    if ('twitter' in user_agent_lower or 'twitter.com' in referrer_lower or
        'x.com' in referrer_lower):
        return 'twitter'
    
    # Fallback to referrer-based detection
    return get_platform_from_referrer(referrer)

def analyze_request_fingerprint():
    """Analyze request characteristics for bot detection"""
    suspicion_score = 0
    
    # Check missing headers that real browsers typically send
    expected_headers = ['Accept', 'Accept-Language', 'Accept-Encoding', 'Connection']
    missing_headers = [h for h in expected_headers if not request.headers.get(h)]
    suspicion_score += len(missing_headers) * 10
    
    # Check for overly simple Accept header
    accept_header = request.headers.get('Accept', '')
    if accept_header in ['*/*', 'text/html', '']:
        suspicion_score += 15
    
    # Check for missing Accept-Language
    if not request.headers.get('Accept-Language'):
        suspicion_score += 20
    
    # Check for suspicious connection patterns
    connection = request.headers.get('Connection', '').lower()
    if connection in ['close', '']:
        suspicion_score += 10
    
    # Check User-Agent length and complexity
    user_agent = request.headers.get('User-Agent', '')
    if len(user_agent) < 50:  # Real browsers have longer user agents
        suspicion_score += 25
    
    # Check for common automation tool signatures
    automation_indicators = ['headless', 'phantom', 'selenium', 'puppeteer', 'playwright']
    if any(indicator in user_agent.lower() for indicator in automation_indicators):
        suspicion_score += 50
    
    return suspicion_score

def get_platform_from_referrer(referrer):
    """Detect platform from referrer"""
    if not referrer:
        return 'direct'
    
    referrer_lower = referrer.lower()
    if 'tiktok.com' in referrer_lower or 'musically.com' in referrer_lower:
        return 'tiktok'
    elif 'instagram.com' in referrer_lower:
        return 'instagram'
    elif 'facebook.com' in referrer_lower:
        return 'facebook'
    elif 'twitter.com' in referrer_lower or 'x.com' in referrer_lower:
        return 'twitter'
    else:
        return 'other'

def get_platform_from_user_agent(user_agent):
    """Detect platform from user agent"""
    if not user_agent:
        return 'unknown'
    
    user_agent_lower = user_agent.lower()
    if 'instagram' in user_agent_lower:
        return 'instagram'
    elif 'tiktok' in user_agent_lower:
        return 'tiktok'
    elif 'facebook' in user_agent_lower:
        return 'facebook'
    else:
        return 'unknown'

def is_suspicious_request():
    """Enhanced suspicious request detection using fingerprinting"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Very short or missing user agent
    if len(user_agent) < 20:
        return True
    
    # Check for common spoofing patterns
    suspicious_patterns = [
        r'curl',
        r'wget',
        r'python',
        r'requests',
        r'httpie',
        r'postman',
        r'scrapy',
        r'mechanize',
        r'urllib'
    ]
    
    user_agent_lower = user_agent.lower()
    for pattern in suspicious_patterns:
        if pattern in user_agent_lower:
            return True
    
    # Use advanced fingerprinting
    suspicion_score = analyze_request_fingerprint()
    
    # Consider suspicious if score is above threshold
    return suspicion_score >= 30

def send_magic_link_email(email, token):
    """Send magic link email for authentication"""
    subject = "Your SmartLink Login Link"
    
    # Use the current request context to build the magic link URL
    from flask import request, url_for
    if request:
        magic_link = url_for('verify_login', token=token, _external=True)
    else:
        # Fallback for testing or non-request contexts
        magic_link = f"http://localhost:5000/auth/verify/{token}"
    
    body = f"""
    Hi!
    
    Click the link below to sign in to your SmartLink dashboard:
    
    {magic_link}
    
    This link will expire in 15 minutes.
    
    If you didn't request this, you can safely ignore this email.
    
    Best regards,
    SmartLink Team
    """
    
    msg = Message(
        subject=subject,
        recipients=[email],
        body=body
    )
    
    try:
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def truncate_ip(ip_address):
    """Truncate IP for privacy (GDPR compliance)"""
    if not ip_address:
        return None
    
    if ':' in ip_address:  # IPv6
        parts = ip_address.split(':')
        return ':'.join(parts[:4]) + '::0'
    else:  # IPv4
        parts = ip_address.split('.')
        return '.'.join(parts[:3]) + '.0'

def verify_domain_ownership(domain, verification_token, method='dns'):
    """Verify domain ownership via DNS TXT record or file-based verification"""
    if method == 'dns':
        return verify_domain_dns(domain, verification_token)
    else:
        return verify_domain_file(domain, verification_token)

def verify_domain_dns(domain, verification_token):
    """Verify domain ownership via DNS TXT record on _smartlink-verify subdomain"""
    try:
        verification_subdomain = f"_smartlink-verify.{domain}"
        txt_records = dns.resolver.resolve(verification_subdomain, 'TXT')
        expected_record = verification_token
        
        for record in txt_records:
            txt_value = record.to_text().strip('"')
            if txt_value == expected_record:
                return True
        return False
    except Exception:
        return False

def verify_domain_file(domain, verification_token):
    """Verify domain ownership via file-based verification"""
    try:
        verification_url = f"http://{domain}/.well-known/smartlink-verification.txt"
        
        req = urllib.request.Request(verification_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            content = response.read().decode('utf-8').strip()
            return content == verification_token
    except (urllib.error.URLError, urllib.error.HTTPError, Exception):
        return False

def get_domain_from_request():
    """Get the domain from the current request"""
    return request.headers.get('Host', '').lower()

def is_custom_domain(domain):
    """Check if a domain is a custom domain (not the default SmartLink domain)"""
    default_domains = ['localhost:5000', '127.0.0.1:5000', 'smartlink.app', 'localhost', '127.0.0.1']
    return (domain not in default_domains and 
            not domain.endswith('.replit.app') and 
            not domain.endswith('.railway.app') and
            not domain.endswith('.herokuapp.com') and
            not domain.endswith('.render.com'))
