#!/usr/bin/env python3
"""Test bot detection patterns locally"""
import re
from utils import BOT_PATTERNS, is_bot_user_agent, is_social_media_bot

# Test user agents
test_cases = {
    "Instagram In-App": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 303.0.0.11.109 (iPhone13,2; iOS 16_6; en_US; en-US; scale=3.00; 1170x2532; 522098789)",
    "Facebook In-App": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 [FBAN/FBIOS;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/522098789]",
    "TikTok In-App": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 BytedanceWebview/d8a21c6",
    "Regular Chrome": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.169 Mobile/15E148 Safari/604.1"
}

print("Testing BOT_PATTERNS:")
print("=" * 60)

for name, ua in test_cases.items():
    ua_lower = ua.lower()
    matches = []
    
    for pattern in BOT_PATTERNS:
        if re.search(pattern, ua_lower):
            matches.append(pattern)
    
    print(f"\n{name}:")
    print(f"  User-Agent: {ua[:60]}...")
    print(f"  Matches: {matches if matches else 'None'}")
    print(f"  is_bot_user_agent: {is_bot_user_agent(ua)}")
    
    if hasattr(is_social_media_bot, '__call__'):
        print(f"  is_social_media_bot: {is_social_media_bot(ua)}")

# Test specific patterns
print("\n\nTesting specific patterns:")
print("=" * 60)

fb_pattern = r'\[FBAN/'
fb_ua = "[FBAN/FBIOS"
print(f"Pattern: {fb_pattern}")
print(f"Test string: {fb_ua}")
print(f"Match: {bool(re.search(fb_pattern, fb_ua))}")

# Test Instagram pattern
ig_pattern = r'instagram\s+[\d\.]+'
ig_ua = "instagram 303.0.0.11.109"
print(f"\nPattern: {ig_pattern}")
print(f"Test string: {ig_ua}")
print(f"Match: {bool(re.search(ig_pattern, ig_ua))}")