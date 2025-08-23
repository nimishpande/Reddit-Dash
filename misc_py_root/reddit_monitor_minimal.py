#!/usr/bin/env python3
"""
Minimal Reddit Monitor
Ultra-simple version with maximum error handling
"""

import os
import sys
import requests
import json
import base64
from datetime import datetime
from dotenv import load_dotenv

def main():
    """Main function with comprehensive error handling"""
    try:
        print("🚀 Starting minimal Reddit monitor...")
        
        # Load environment
        load_dotenv()
        print("✅ Environment loaded")
        
        # Check credentials
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("❌ Missing Reddit credentials")
            return False
            
        print("✅ Credentials found")
        
        # Get token
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'User-Agent': 'minimal_monitor/1.0',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        print("🔑 Getting Reddit token...")
        response = requests.post('https://www.reddit.com/api/v1/access_token', 
                               headers=headers, data=data, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Token request failed: {response.status_code}")
            return False
            
        token_data = response.json()
        access_token = token_data['access_token']
        print("✅ Token obtained")
        
        # Fetch posts
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': 'minimal_monitor/1.0'
        }
        
        print("📥 Fetching posts...")
        response = requests.get('https://oauth.reddit.com/r/skincareaddictsindia/new', 
                              headers=headers, params={'limit': 25}, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Posts request failed: {response.status_code}")
            return False
            
        data = response.json()
        posts = data['data']['children']
        post_data = [post['data'] for post in posts]
        
        print(f"✅ Fetched {len(post_data)} posts")
        
        # Create output directory
        os.makedirs('reddit_monitoring', exist_ok=True)
        
        # Save simple summary
        today = datetime.now().strftime('%Y-%m-%d')
        summary_file = f'reddit_monitoring/minimal_summary_{today}.txt'
        
        with open(summary_file, 'w') as f:
            f.write(f"Minimal Reddit Monitor - {today}\n")
            f.write("=" * 50 + "\n\n")
            
            for i, post in enumerate(post_data[:10], 1):
                f.write(f"{i}. {post.get('title', 'No Title')}\n")
                f.write(f"   Score: {post.get('score', 0)}, Comments: {post.get('num_comments', 0)}\n\n")
        
        print(f"✅ Summary saved: {summary_file}")
        
        # Save timestamp
        with open('reddit_monitoring/last_run.txt', 'w') as f:
            f.write(datetime.now().isoformat())
        
        print("✅ Timestamp saved")
        print("🎉 Minimal monitor completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error in minimal monitor: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
