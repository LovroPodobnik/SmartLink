import re
from flask import request
from flask_mail import Message
from app import mail

# Known bot user agents
BOT_PATTERNS = [
    r'facebookexternalhit',
    r'bytespider',
    r'twitterbot',
    r'linkedinbot',
    r'whatsapp',
    r'telegrambot',
    r'applebot',
    r'googlebot',
    r'bingbot',
    r'slackbot',
    r'discordbot',
    r'crawler',
    r'spider',
    r'scraper',
    r'bot/'
]

def is_bot_user_agent(user_agent):
    """Check if user agent matches known bot patterns"""
    if not user_agent:
        return True
    
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    return False

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
    """Check if request appears suspicious"""
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
        r'postman'
    ]
    
    user_agent_lower = user_agent.lower()
    for pattern in suspicious_patterns:
        if pattern in user_agent_lower:
            return True
    
    return False

def send_magic_link_email(email, token):
    """Send magic link email for authentication"""
    subject = "Your SmartLink Login Link"
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
