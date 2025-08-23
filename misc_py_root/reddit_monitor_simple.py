#!/usr/bin/env python3
"""
Simplified Reddit Monitor
Clean, reliable version built from scratch
"""

import os
import requests
import json
import base64
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Configuration
SUBREDDIT = 'skincareaddictsindia'
MIN_ENGAGEMENT_SCORE = 7
MIN_UPVOTES = 5
MIN_COMMENTS = 2
POSTS_LIMIT = 50
MONITORING_DIR = 'reddit_monitoring'

def get_reddit_token():
    """Get Reddit OAuth access token"""
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Missing Reddit credentials")
        return None
    
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'User-Agent': 'skincare_monitor/1.0',
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post('https://www.reddit.com/api/v1/access_token', 
                               headers=headers, data=data, timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            return token_data['access_token']
        else:
            print(f"❌ Reddit API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Reddit API connection failed: {e}")
        return None

def fetch_posts(access_token, subreddit, limit=50):
    """Fetch posts from subreddit"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': 'skincare_monitor/1.0'
    }
    
    url = f"https://oauth.reddit.com/r/{subreddit}/new"
    params = {'limit': limit}
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        posts = data['data']['children']
        return [post['data'] for post in posts]
        
    except Exception as e:
        print(f"❌ Failed to fetch posts: {e}")
        return []

def filter_engaging_posts(posts):
    """Filter posts based on engagement criteria"""
    engaging_posts = []
    
    for post in posts:
        score = post.get('score', 0)
        num_comments = post.get('num_comments', 0)
        engagement_score = score + num_comments
        
        if (engagement_score >= MIN_ENGAGEMENT_SCORE or 
            score >= MIN_UPVOTES or 
            num_comments >= MIN_COMMENTS):
            
            if post.get('selftext') not in ['[deleted]', '[removed]']:
                engaging_posts.append(post)
    
    return engaging_posts

def create_summary(posts, timestamp):
    """Create daily summary file"""
    today = datetime.now().strftime('%Y-%m-%d')
    summary_file = os.path.join(MONITORING_DIR, f'daily_summary_{today}.txt')
    
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"REDDIT MONITORING SUMMARY - r/{SUBREDDIT}\n")
        f.write(f"Date: {today}\n")
        f.write(f"Monitoring started: {timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 80 + "\n\n")
        
        for i, post in enumerate(posts, 1):
            f.write("=" * 80 + "\n")
            f.write(f"POST #{i}\n")
            f.write("=" * 80 + "\n")
            f.write(f"Title: {post.get('title', 'No Title')}\n")
            f.write(f"Author: u/{post.get('author', 'Unknown')}\n")
            f.write(f"Posted: {datetime.fromtimestamp(post.get('created_utc', 0)).strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Score: {post.get('score', 0)} upvotes\n")
            f.write(f"Comments: {post.get('num_comments', 0)}\n")
            f.write(f"Engagement Score: {post.get('score', 0) + post.get('num_comments', 0)}\n")
            f.write(f"URL: https://reddit.com{post.get('permalink', '')}\n\n")
            
            content = post.get('selftext', 'No content')
            f.write(f"Content:\n{content}\n\n")
            
            # Check for images
            if post.get('is_video') or post.get('is_gallery') or post.get('url', '').endswith(('.jpg', '.png', '.gif')):
                f.write("Images: Found\n\n")
            else:
                f.write("Images: None\n\n")
    
    print(f"✅ Summary saved: {summary_file}")

def save_json_backup(posts, timestamp):
    """Save posts as JSON backup"""
    today = datetime.now().strftime('%Y-%m-%d')
    json_file = os.path.join(MONITORING_DIR, f'posts_{today}.json')
    
    data = {
        'monitoring_info': {
            'subreddit': SUBREDDIT,
            'timestamp': timestamp.isoformat(),
            'posts_found': len(posts),
            'criteria': {
                'min_engagement': MIN_ENGAGEMENT_SCORE,
                'min_upvotes': MIN_UPVOTES,
                'min_comments': MIN_COMMENTS
            }
        },
        'posts': posts
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON backup saved: {json_file}")

def save_timestamp():
    """Save last run timestamp"""
    timestamp_file = os.path.join(MONITORING_DIR, 'last_run_timestamp.txt')
    with open(timestamp_file, 'w') as f:
        f.write(datetime.now().isoformat())
    print(f"✅ Timestamp saved: {timestamp_file}")

def main():
    """Main monitoring function"""
    print(f"🔍 Starting Reddit monitoring for r/{SUBREDDIT}")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create monitoring directory
    os.makedirs(MONITORING_DIR, exist_ok=True)
    
    # Get Reddit access token
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get Reddit access token")
        return
    
    print("✅ Reddit authentication successful")
    
    # Fetch posts
    print(f"📥 Fetching posts from r/{SUBREDDIT}...")
    posts = fetch_posts(access_token, SUBREDDIT, POSTS_LIMIT)
    
    if not posts:
        print("❌ No posts fetched")
        return
    
    print(f"📊 Fetched {len(posts)} posts")
    
    # Filter engaging posts
    engaging_posts = filter_engaging_posts(posts)
    print(f"🎯 Found {len(engaging_posts)} engaging posts")
    
    if not engaging_posts:
        print("ℹ️ No engaging posts found")
        return
    
    # Get timestamp
    run_timestamp = datetime.now()
    
    # Create files
    create_summary(engaging_posts, run_timestamp)
    save_json_backup(engaging_posts, run_timestamp)
    save_timestamp()
    
    print(f"\n✅ Monitoring complete!")
    print(f"📊 Engaging posts found: {len(engaging_posts)}")
    
    # Show top posts
    print(f"\n🏆 Top engaging posts:")
    for i, post in enumerate(engaging_posts[:3], 1):
        title = post.get('title', 'No Title')[:60] + '...' if len(post.get('title', '')) > 60 else post.get('title', 'No Title')
        score = post.get('score', 0)
        comments = post.get('num_comments', 0)
        print(f"{i}. {title}")
        print(f"   Score: {score}, Comments: {comments}")

if __name__ == "__main__":
    main()
