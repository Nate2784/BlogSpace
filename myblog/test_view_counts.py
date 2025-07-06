#!/usr/bin/env python3
"""
Test script to verify view count functionality
"""

import requests
import time
import json

BASE_URL = "http://localhost:8000"

def get_view_count(post_id):
    """Extract view count from post page"""
    try:
        response = requests.get(f"{BASE_URL}/post/{post_id}/")
        if response.status_code == 200:
            # Extract view count from HTML
            import re
            match = re.search(r'(\d+) views', response.text)
            if match:
                return int(match.group(1))
        return None
    except Exception as e:
        print(f"Error getting view count: {e}")
        return None

def simulate_different_ips(post_id, num_requests=3):
    """Simulate requests from different IP addresses"""
    print(f"\n🧪 Testing view counts for post {post_id}")
    
    # Get initial view count
    initial_count = get_view_count(post_id)
    print(f"📊 Initial view count: {initial_count}")
    
    # Simulate requests with different headers to mimic different users
    headers_list = [
        {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
        {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"},
    ]
    
    for i, headers in enumerate(headers_list[:num_requests]):
        print(f"\n🔄 Request {i+1} with different User-Agent...")
        
        try:
            response = requests.get(f"{BASE_URL}/post/{post_id}/", headers=headers)
            if response.status_code == 200:
                new_count = get_view_count(post_id)
                print(f"📈 View count after request {i+1}: {new_count}")
                
                if new_count and initial_count:
                    change = new_count - initial_count
                    print(f"📊 Change: +{change}")
                
                # Wait a bit between requests
                time.sleep(2)
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error in request {i+1}: {e}")

def test_throttling(post_id):
    """Test that rapid requests from same source are throttled"""
    print(f"\n🕐 Testing throttling for post {post_id}")
    
    initial_count = get_view_count(post_id)
    print(f"📊 Initial view count: {initial_count}")
    
    # Make multiple rapid requests
    for i in range(3):
        print(f"\n⚡ Rapid request {i+1}...")
        response = requests.get(f"{BASE_URL}/post/{post_id}/")
        
        if response.status_code == 200:
            new_count = get_view_count(post_id)
            print(f"📈 View count: {new_count}")
            
            if new_count and initial_count:
                change = new_count - initial_count
                if change == 0 and i > 0:
                    print("✅ Throttling working - no additional views counted")
                elif change > 0 and i == 0:
                    print("✅ First view counted successfully")
        
        time.sleep(1)  # Short delay

def main():
    """Run all tests"""
    print("🚀 Starting BlogSpace View Count Tests")
    print("=" * 50)
    
    # Test posts (adjust IDs based on your data)
    test_posts = [19, 20, 21]  # Common post IDs
    
    for post_id in test_posts:
        try:
            # Test 1: Different user simulation
            simulate_different_ips(post_id, 2)
            
            # Wait between tests
            time.sleep(5)
            
            # Test 2: Throttling test
            test_throttling(post_id)
            
            print("\n" + "="*50)
            
        except Exception as e:
            print(f"❌ Error testing post {post_id}: {e}")
            continue
    
    print("🎉 View count testing completed!")

if __name__ == "__main__":
    main()
