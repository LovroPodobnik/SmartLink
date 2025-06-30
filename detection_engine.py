"""
Advanced Bot Detection Engine for SmartTicker
Sophisticated detection methods for TikTok, Instagram, and other platform bots
"""

import re
import time
import hashlib
import ipaddress
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from flask import request
# Platform IP ranges (avoiding circular import from utils)
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

# TikTok-specific patterns (avoiding circular import)
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

@dataclass
class DetectionResult:
    """Result of bot detection analysis"""
    is_bot: bool
    confidence_score: float  # 0.0 to 1.0
    platform: str
    detection_methods: List[str]
    risk_level: str  # 'low', 'medium', 'high', 'critical'
    
class AdvancedDetectionEngine:
    """Advanced bot detection with multiple analysis methods"""
    
    def __init__(self):
        self.detection_methods = {
            'user_agent': self._analyze_user_agent,
            'ip_analysis': self._analyze_ip_address,
            'header_fingerprint': self._analyze_headers,
            'timing_analysis': self._analyze_timing,
            'behavioral_patterns': self._analyze_behavior,
            'platform_specific': self._platform_specific_detection
        }
        
        # Enhanced TikTok bot signatures
        self.tiktok_bot_signatures = {
            'user_agents': [
                r'bytespider',
                r'tiktok.*crawler',
                r'bytedance.*bot',
                r'douyin.*spider',
                r'musicallybot',
                r'aweme.*crawler'
            ],
            'headers': {
                'required': ['Host'],
                'suspicious_absent': ['Accept-Language', 'Accept-Encoding', 'Connection'],
                'bot_indicators': {
                    'Accept': '*/*',
                    'Connection': 'close',
                    'User-Agent': lambda ua: len(ua) < 50 if ua else True
                }
            }
        }
        
        # Instagram/Facebook bot signatures - INCLUDING IN-APP BROWSERS
        self.instagram_bot_signatures = {
            'user_agents': [
                r'facebookexternalhit',
                r'facebookcatalog',
                r'instagrambot',
                r'meta.*external.*hit',
                r'whatsapp.*preview',
                # Instagram in-app browser patterns
                r'instagram\s+[\d\.]+',  # e.g., Instagram 303.0.0.11.109
                # Facebook in-app browser patterns
                r'\[FBAN/',               # Facebook App Network
                r'FBAV/',                  # Facebook App Version
                r'FBIOS',                  # Facebook iOS
                r'FBDV/',                  # Facebook Device
                r'\[FB',                  # Generic Facebook in-app pattern
            ],
            'referrer_patterns': [
                r'facebook\.com',
                r'instagram\.com',
                r'fb\.com',
                r'm\.facebook\.com'
            ]
        }
    
    def analyze_request(self, user_agent: str = None, ip_address: str = None, 
                       referrer: str = None, headers: Dict = None) -> DetectionResult:
        """Comprehensive request analysis"""
        
        # Get request data if not provided (handle cases outside request context)
        try:
            if not user_agent:
                user_agent = request.headers.get('User-Agent', '')
            if not ip_address:
                ip_address = request.remote_addr
            if not referrer:
                referrer = request.headers.get('Referer', '')
            if not headers:
                headers = dict(request.headers)
        except RuntimeError:
            # Outside of request context, use provided values or defaults
            user_agent = user_agent or ''
            ip_address = ip_address or ''
            referrer = referrer or ''
            headers = headers or {}
        
        detection_results = []
        confidence_scores = []
        detected_platforms = set()
        
        # Run all detection methods
        for method_name, method_func in self.detection_methods.items():
            try:
                result = method_func(user_agent, ip_address, referrer, headers)
                if result:
                    detection_results.append(method_name)
                    confidence_scores.append(result.get('confidence', 0.5))
                    if 'platform' in result:
                        detected_platforms.add(result['platform'])
            except Exception:
                # Continue if individual method fails
                pass
        
        # Calculate overall confidence with weighted scoring
        if confidence_scores:
            # Weight by method importance and take average of top scores
            high_confidence_scores = [score for score in confidence_scores if score > 0.7]
            if high_confidence_scores:
                overall_confidence = max(high_confidence_scores)
            else:
                overall_confidence = sum(confidence_scores) / len(confidence_scores)
        else:
            overall_confidence = 0.0
        
        # Determine if bot with more nuanced logic
        high_confidence_detections = len([score for score in confidence_scores if score > 0.8])
        is_bot = (overall_confidence > 0.8 or 
                 (overall_confidence > 0.6 and high_confidence_detections >= 1) or 
                 len(detection_results) >= 4)
        
        # Determine primary platform
        platform = self._determine_primary_platform(detected_platforms, user_agent, referrer)
        
        # Risk assessment
        risk_level = self._assess_risk_level(overall_confidence, detection_results)
        
        return DetectionResult(
            is_bot=is_bot,
            confidence_score=overall_confidence,
            platform=platform,
            detection_methods=detection_results,
            risk_level=risk_level
        )
    
    def _analyze_user_agent(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """Advanced user agent analysis"""
        if not user_agent:
            return {'confidence': 0.9, 'reason': 'missing_user_agent'}
        
        ua_lower = user_agent.lower()
        confidence = 0.0
        
        # Check for known bot patterns
        bot_patterns = [
            r'bot', r'crawler', r'spider', r'scraper',
            r'curl', r'wget', r'python', r'requests',
            r'headless', r'phantom', r'selenium', r'puppeteer'
        ]
        
        for pattern in bot_patterns:
            if re.search(pattern, ua_lower):
                confidence = max(confidence, 0.8)
        
        # TikTok specific checks
        for pattern in self.tiktok_bot_signatures['user_agents']:
            if re.search(pattern, ua_lower):
                confidence = max(confidence, 0.95)
                return {'confidence': confidence, 'platform': 'tiktok', 'reason': 'tiktok_bot_ua'}
        
        # Instagram/Facebook specific checks
        for pattern in self.instagram_bot_signatures['user_agents']:
            # Some patterns need case-sensitive matching (e.g., [FBAN/)
            if re.search(pattern, user_agent, re.IGNORECASE):
                confidence = max(confidence, 0.95)
                platform = 'facebook' if any(fb in pattern.lower() for fb in ['fban', 'fbav', 'fbios', 'fbdv', '\[fb']) else 'instagram'
                return {'confidence': confidence, 'platform': platform, 'reason': f'{platform}_bot_ua'}
        
        # Length and complexity analysis
        if len(user_agent) < 20:
            confidence = max(confidence, 0.7)
        
        # Check for legitimate browser indicators
        browser_indicators = ['chrome', 'firefox', 'safari', 'edge', 'opera']
        has_browser_indicator = any(indicator in ua_lower for indicator in browser_indicators)
        
        # Check for full browser user agent structure
        browser_structure_indicators = ['mozilla', 'webkit', 'gecko', 'applewebkit']
        has_browser_structure = any(indicator in ua_lower for indicator in browser_structure_indicators)
        
        # Reduce confidence if it looks like a legitimate browser
        if has_browser_indicator and has_browser_structure and len(user_agent) > 80:
            confidence = max(0.0, confidence - 0.4)  # Reduce bot confidence for real browsers
        elif not has_browser_indicator and confidence == 0.0:
            confidence = 0.6
        
        return {'confidence': confidence} if confidence > 0.3 else None
    
    def _analyze_ip_address(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """IP address analysis for platform detection"""
        if not ip:
            return None
        
        confidence = 0.0
        platform = None
        
        # Check against known platform IP ranges
        for platform_name, ip_ranges in PLATFORM_IP_RANGES.items():
            if self._ip_in_ranges(ip, ip_ranges):
                confidence = 0.9
                platform = platform_name
                break
        
        return {'confidence': confidence, 'platform': platform} if confidence > 0.0 else None
    
    def _analyze_headers(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """HTTP headers fingerprinting"""
        confidence = 0.0
        reasons = []
        
        # Check for missing headers that browsers typically send
        expected_headers = ['Accept', 'Accept-Language', 'Accept-Encoding', 'Connection']
        missing_headers = [h for h in expected_headers if h not in headers]
        
        if missing_headers:
            confidence += len(missing_headers) * 0.15
            reasons.append(f'missing_headers_{len(missing_headers)}')
        
        # Check for suspicious header values
        accept_header = headers.get('Accept', '')
        if accept_header in ['*/*', 'text/html', '']:
            confidence += 0.2
            reasons.append('suspicious_accept')
        
        # Check Connection header
        connection = headers.get('Connection', '').lower()
        if connection == 'close':
            confidence += 0.15
            reasons.append('connection_close')
        
        # Check for automation tool headers
        automation_headers = ['X-Requested-With', 'X-Automation', 'Selenium-Remote-Control']
        for header in automation_headers:
            if header in headers:
                confidence += 0.3
                reasons.append('automation_header')
        
        return {'confidence': min(confidence, 1.0), 'reasons': reasons} if confidence > 0.2 else None
    
    def _analyze_timing(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """Request timing analysis"""
        # This would typically track request patterns over time
        # For now, implement basic timing checks
        
        # Check if request seems too fast (less than 100ms after page load)
        # This would require session tracking in a real implementation
        
        return None  # Placeholder for timing analysis
    
    def _analyze_behavior(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """Behavioral pattern analysis"""
        confidence = 0.0
        
        # Check for lack of referrer (suspicious for social media traffic)
        if not referrer:
            confidence += 0.1
        
        # Check for direct access patterns that bots use
        if referrer and 'http' not in referrer:
            confidence += 0.2
        
        return {'confidence': confidence} if confidence > 0.15 else None
    
    def _platform_specific_detection(self, user_agent: str, ip: str, referrer: str, headers: Dict) -> Dict:
        """Platform-specific detection logic"""
        if not user_agent:
            return None
        
        ua_lower = user_agent.lower()
        ref_lower = referrer.lower() if referrer else ''
        
        # TikTok specific detection
        tiktok_indicators = 0
        if any(re.search(pattern, ua_lower) for pattern in TIKTOK_SPECIFIC_PATTERNS):
            tiktok_indicators += 3
        if 'tiktok.com' in ref_lower or 'musically.com' in ref_lower:
            tiktok_indicators += 2
        if self._ip_in_ranges(ip, PLATFORM_IP_RANGES.get('tiktok', [])):
            tiktok_indicators += 3
        
        if tiktok_indicators >= 2:
            return {
                'confidence': min(0.9, tiktok_indicators * 0.3),
                'platform': 'tiktok',
                'indicators': tiktok_indicators
            }
        
        # Instagram specific detection
        instagram_indicators = 0
        for pattern in self.instagram_bot_signatures['user_agents']:
            if re.search(pattern, ua_lower):
                instagram_indicators += 3
        
        for pattern in self.instagram_bot_signatures['referrer_patterns']:
            if re.search(pattern, ref_lower):
                instagram_indicators += 2
        
        if instagram_indicators >= 2:
            return {
                'confidence': min(0.9, instagram_indicators * 0.3),
                'platform': 'instagram',
                'indicators': instagram_indicators
            }
        
        return None
    
    def _ip_in_ranges(self, ip_address: str, ip_ranges: List[str]) -> bool:
        """Check if IP is in any of the given ranges"""
        if not ip_address or not ip_ranges:
            return False
        
        try:
            ip_obj = ipaddress.ip_address(ip_address)
            for cidr in ip_ranges:
                network = ipaddress.ip_network(cidr, strict=False)
                if ip_obj in network:
                    return True
        except (ValueError, ipaddress.AddressValueError):
            pass
        
        return False
    
    def _determine_primary_platform(self, platforms: set, user_agent: str, referrer: str) -> str:
        """Determine the primary platform from detected platforms"""
        if not platforms:
            # Fallback platform detection
            ua_lower = user_agent.lower() if user_agent else ''
            ref_lower = referrer.lower() if referrer else ''
            
            if any(keyword in ua_lower + ref_lower for keyword in ['tiktok', 'bytespider', 'douyin']):
                return 'tiktok'
            elif any(keyword in ua_lower + ref_lower for keyword in ['instagram', 'facebook']):
                return 'instagram'
            else:
                return 'unknown'
        
        # Priority order for platform detection
        priority_order = ['tiktok', 'instagram', 'facebook', 'twitter', 'google']
        for platform in priority_order:
            if platform in platforms:
                return platform
        
        return list(platforms)[0] if platforms else 'unknown'
    
    def _assess_risk_level(self, confidence: float, detection_methods: List[str]) -> str:
        """Assess the risk level based on confidence and detection methods"""
        if confidence >= 0.9 or len(detection_methods) >= 4:
            return 'critical'
        elif confidence >= 0.7 or len(detection_methods) >= 3:
            return 'high'
        elif confidence >= 0.5 or len(detection_methods) >= 2:
            return 'medium'
        else:
            return 'low'

# Singleton instance for use across the application
detection_engine = AdvancedDetectionEngine()

def enhanced_bot_detection(user_agent: str = None, ip_address: str = None) -> DetectionResult:
    """Enhanced bot detection function for easy import"""
    return detection_engine.analyze_request(user_agent, ip_address)

def is_sophisticated_tiktok_bot(user_agent: str = None, ip_address: str = None) -> bool:
    """Specific TikTok bot detection with high accuracy"""
    result = detection_engine.analyze_request(user_agent, ip_address)
    return result.platform == 'tiktok' and result.confidence_score >= 0.8