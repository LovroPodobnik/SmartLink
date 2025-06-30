#!/usr/bin/env python3
"""
Test with actual platform user agents as they appear in the wild
"""
import requests
import time

TEST_URL = "https://links.lovropodobnik.si/RqlZ9d"

# Real user agents from actual platform crawlers
REAL_PLATFORM_AGENTS = {
    "TikTok In-App Browser iOS": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 BytedanceWebview/d8a21c6",
    
    "TikTok Crawler (ByteSpider)": "Mozilla/5.0 (Linux; Android 5.0) AppleWebKit/537.36 (KHTML, like Gecko) Mobile Safari/537.36 (compatible; Bytespider; spider-feedback@bytedance.com)",
    
    "Instagram In-App Browser": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Instagram 303.0.0.11.109 (iPhone13,2; iOS 16_6; en_US; en-US; scale=3.00; 1170x2532; 522098789)",
    
    "Facebook In-App Browser": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20G75 [FBAN/FBIOS;FBDV/iPhone13,2;FBMD/iPhone;FBSN/iOS;FBSV/16.6;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5;FBRV/522098789]",
    
    "Real Human - Chrome Mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/119.0.6045.169 Mobile/15E148 Safari/604.1",
    
    "Real Human - Safari Mobile": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1"
}

def test_platform(name, user_agent):
    """Test a single platform"""
    headers = {
        "User-Agent": user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive"
    }
    
    # Add platform-specific headers
    if "tiktok" in name.lower():
        headers["Referer"] = "https://www.tiktok.com/"
    elif "instagram" in name.lower():
        headers["Referer"] = "https://www.instagram.com/"
    elif "facebook" in name.lower():
        headers["Referer"] = "https://www.facebook.com/"
    
    try:
        response = requests.get(TEST_URL, headers=headers, allow_redirects=False, timeout=10)
        
        print(f"\n{'='*60}")
        print(f"Platform: {name}")
        print(f"Status: {response.status_code}")
        
        if response.status_code in [301, 302, 303, 307, 308]:
            location = response.headers.get('Location', 'Unknown')
            print(f"Redirected to: {location}")
            
            # Analyze redirect
            if '/safe/' in location:
                print("✅ Correctly detected as BOT - sent to safe page")
            elif '/challenge/' in location:
                print("🤔 Detected as suspicious - sent to challenge")
            elif 'onlyfans' in location or location == 'https://onlyfans.com/':
                print("❌ Incorrectly detected as HUMAN - sent to target")
            else:
                print(f"🎯 Redirected to: {location}")
                
        # Print partial user agent for reference
        print(f"User-Agent: {user_agent[:80]}...")
        
    except Exception as e:
        print(f"\nError testing {name}: {e}")

def main():
    print("🧪 Testing SmartTicker with Real Platform User Agents")
    print(f"📍 Test URL: {TEST_URL}")
    
    for name, ua in REAL_PLATFORM_AGENTS.items():
        test_platform(name, ua)
        time.sleep(0.5)
    
    print("\n\n📊 Summary:")
    print("The system should detect:")
    print("  - TikTok in-app browsers and crawlers as BOTS")
    print("  - Instagram in-app browsers as BOTS")
    print("  - Facebook in-app browsers as BOTS")
    print("  - Regular mobile browsers as HUMANS")

if __name__ == "__main__":
    main()