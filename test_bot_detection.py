#!/usr/bin/env python3
"""
Test bot detection for SmartTicker links
Simulates different user agents and behaviors
"""
import requests
import time
from typing import Dict, List

# The link to test
TEST_URL = "https://links.lovropodobnik.si/RqlZ9d"

# Different user agents to test
USER_AGENTS = {
    "TikTok Bot": "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; https://zhanzhang.toutiao.com/)",
    
    "Instagram Bot": "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36 Instagram 166.1.0.42.245",
    
    "Facebook Bot": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
    
    "Twitter Bot": "Twitterbot/1.0",
    
    "Real Chrome Browser": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    
    "Real Safari Browser": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
    
    "Real Mobile Browser": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    
    "Googlebot": "Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    
    "Generic Bot": "Mozilla/5.0 (compatible; TestBot/1.0; +http://example.com/bot)",
    
    "Headless Chrome": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/120.0.0.0 Safari/537.36",
    
    "cURL": "curl/7.64.1",
    
    "Python Requests": "python-requests/2.31.0",
    
    "Empty User Agent": ""
}

# Different referrers to test
REFERRERS = {
    "Direct": None,
    "TikTok": "https://www.tiktok.com/",
    "Instagram": "https://www.instagram.com/",
    "Facebook": "https://www.facebook.com/",
    "Google": "https://www.google.com/",
}

def test_single_request(user_agent: str, referrer: str = None, label: str = "") -> Dict:
    """Test a single request with given parameters"""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Cache-Control": "max-age=0"
    }
    
    if referrer:
        headers["Referer"] = referrer
    
    try:
        # Don't follow redirects automatically
        response = requests.get(TEST_URL, headers=headers, allow_redirects=False, timeout=10)
        
        result = {
            "label": label,
            "user_agent": user_agent[:50] + "..." if len(user_agent) > 50 else user_agent,
            "referrer": referrer or "None",
            "status_code": response.status_code,
            "redirect_location": response.headers.get('Location', 'No redirect'),
            "detected_as": "Unknown"
        }
        
        # Analyze the redirect to determine detection
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location', '').lower()
            if 'safe' in location or 'bot' in location:
                result["detected_as"] = "🤖 BOT"
            elif 'challenge' in location:
                result["detected_as"] = "🤔 SUSPICIOUS"
            elif 'onlyfans' in location or location.startswith('http'):
                result["detected_as"] = "👤 HUMAN"
            else:
                result["detected_as"] = "❓ Unknown"
        
        return result
        
    except Exception as e:
        return {
            "label": label,
            "user_agent": user_agent[:50] + "...",
            "error": str(e)
        }

def run_all_tests():
    """Run all test combinations"""
    print("🧪 Testing SmartTicker Bot Detection")
    print(f"📍 Test URL: {TEST_URL}")
    print("=" * 80)
    
    results = []
    
    # Test different user agents
    print("\n📱 Testing Different User Agents...")
    for ua_name, ua_string in USER_AGENTS.items():
        result = test_single_request(ua_string, label=ua_name)
        results.append(result)
        print(f"\n{ua_name}:")
        print(f"  Status: {result['status_code']}")
        print(f"  Detected as: {result['detected_as']}")
        print(f"  Redirected to: {result['redirect_location']}")
        time.sleep(0.5)  # Be nice to the server
    
    # Test with different referrers
    print("\n\n🔗 Testing Different Referrers (with Chrome UA)...")
    chrome_ua = USER_AGENTS["Real Chrome Browser"]
    for ref_name, ref_url in REFERRERS.items():
        result = test_single_request(chrome_ua, referrer=ref_url, label=f"Chrome + {ref_name} referrer")
        print(f"\n{ref_name} referrer:")
        print(f"  Status: {result['status_code']}")
        print(f"  Detected as: {result['detected_as']}")
        print(f"  Redirected to: {result['redirect_location']}")
        time.sleep(0.5)
    
    # Summary
    print("\n\n📊 Detection Summary:")
    print("=" * 80)
    bot_count = sum(1 for r in results if r.get('detected_as') == '🤖 BOT')
    human_count = sum(1 for r in results if r.get('detected_as') == '👤 HUMAN')
    suspicious_count = sum(1 for r in results if r.get('detected_as') == '🤔 SUSPICIOUS')
    
    print(f"🤖 Detected as BOT: {bot_count}")
    print(f"👤 Detected as HUMAN: {human_count}")
    print(f"🤔 Detected as SUSPICIOUS: {suspicious_count}")
    print(f"❓ Unknown/Error: {len(results) - bot_count - human_count - suspicious_count}")
    
    return results

def test_rapid_requests():
    """Test rapid requests to check rate limiting or suspicious behavior detection"""
    print("\n\n⚡ Testing Rapid Requests...")
    print("Sending 5 requests in quick succession...")
    
    chrome_ua = USER_AGENTS["Real Chrome Browser"]
    for i in range(5):
        result = test_single_request(chrome_ua, label=f"Rapid request #{i+1}")
        print(f"  Request {i+1}: {result['detected_as']}")
        time.sleep(0.1)  # Very short delay

if __name__ == "__main__":
    # Run all tests
    results = run_all_tests()
    
    # Test rapid requests
    test_rapid_requests()
    
    print("\n\n✅ Testing complete!")
    print(f"🔗 Test URL: {TEST_URL}")
    print("\nNote: The bot detection is working if:")
    print("  - Known bots (TikTok, Instagram, etc.) are detected as BOT")
    print("  - Real browsers are detected as HUMAN")
    print("  - Suspicious patterns trigger challenges")