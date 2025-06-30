#!/usr/bin/env python3
"""Test bot detection patterns standalone"""
import re

# Copy of patterns from utils.py
BOT_PATTERNS = [
    # Instagram patterns
    r'instagram\s+\d+',        # Instagram in-app browser (e.g., Instagram 303.0.0.11.109)
    # Facebook patterns
    r'FBAN',                    # Facebook App identifier
    r'FBAV',                    # Facebook App version
    r'FBIOS',                   # Facebook iOS app
    r'FBDV',                    # Facebook device
    r'\[FB',                    # Facebook in-app browser pattern
]

# Test cases
test_cases = {
    "Instagram In-App": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 303.0.0.11.109 (iPhone13,2; iOS 16_6; en_US; en-US; scale=3.00; 1170x2532; 522098789)",
    "Facebook In-App": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 [FBAN/FBIOS;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/522098789]",
}

print("Testing Bot Patterns:")
print("=" * 60)

for name, ua in test_cases.items():
    print(f"\n{name}:")
    print(f"User-Agent: {ua[:80]}...")
    
    # Test each pattern
    matches = []
    for pattern in BOT_PATTERNS:
        try:
            if re.search(pattern, ua, re.IGNORECASE):
                matches.append(pattern)
        except Exception as e:
            print(f"  Error with pattern {pattern}: {e}")
    
    print(f"Matched patterns: {matches}")
    print(f"Is bot: {len(matches) > 0}")

# Test the detection_engine patterns
print("\n\nTesting detection_engine.py patterns:")
print("=" * 60)

# From detection_engine.py
instagram_patterns = [
    r'instagram\s+[\d\.]+',  # e.g., Instagram 303.0.0.11.109
    r'\[FBAN/',               # Facebook App Network
    r'FBAV/',                  # Facebook App Version
    r'FBIOS',                  # Facebook iOS
    r'FBDV/',                  # Facebook Device
    r'\[FB',                  # Generic Facebook in-app pattern
]

for name, ua in test_cases.items():
    print(f"\n{name}:")
    ua_lower = ua.lower()
    
    matches = []
    for pattern in instagram_patterns:
        try:
            if re.search(pattern, ua_lower):
                matches.append(pattern)
        except Exception as e:
            print(f"  Error with pattern {pattern}: {e}")
    
    print(f"Matched patterns: {matches}")
    print(f"Is bot: {len(matches) > 0}")