#!/usr/bin/env python3
"""
Direct test for Facebook in-app browser detection
"""
import requests

# Facebook in-app browser user agent
fb_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 [FBAN/FBIOS;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/522098789]"

headers = {
    "User-Agent": fb_ua,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Referer": "https://www.facebook.com/"
}

# Test the link
response = requests.get("https://links.lovropodobnik.si/RqlZ9d", headers=headers, allow_redirects=False)

print(f"Status: {response.status_code}")
print(f"Location: {response.headers.get('Location', 'No redirect')}")

# Analyze
location = response.headers.get('Location', '').lower()
if '/safe/' in location:
    print("✅ Correctly detected as BOT")
elif 'onlyfans' in location:
    print("❌ Incorrectly detected as HUMAN")
else:
    print(f"🎯 Redirected to: {response.headers.get('Location')}")

# Show the user agent for verification
print(f"\nUser-Agent tested: {fb_ua[:80]}...")
print(f"Contains [FBAN/: {'[FBAN/' in fb_ua}")