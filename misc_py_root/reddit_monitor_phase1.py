#!/usr/bin/env python3
"""
Reddit Monitor - Phase 1
Enhanced JSON structure with date-based folder organization
"""

import os
import requests
import json
import base64
from datetime import datetime, timezone
from dotenv import load_dotenv
import re

# Load environment variables
load_dotenv()

# Configuration
SUBREDDIT = 'skincareaddictsindia'
MIN_ENGAGEMENT_SCORE = 7
MIN_UPVOTES = 5
MIN_COMMENTS = 2
POSTS_LIMIT = 50
ANALYSIS_DIR = 'analysis'

# Subreddit color mapping
SUBREDDIT_COLORS = {
    'skincareaddictsindia': '#0079d3',
    'IndianSkincareAddicts': '#ff4500',
    'SkincareAddiction': '#7193ff',
    'HaircareScience': '#00c851',
    'curlyhair': '#ff6b35',
    'tressless': '#8e44ad',
    'Hair': '#e74c3c',
    'beauty': '#f39c12'
}

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
        'User-Agent': 'reddit_monitor_phase1/1.0',
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
        'User-Agent': 'reddit_monitor_phase1/1.0'
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

def generate_content_preview(content, max_length=150):
    """Generate content preview from post content"""
    if not content:
        return ""
    
    # Remove markdown formatting
    content = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', content)  # Remove links
    content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)  # Remove bold
    content = re.sub(r'\*([^*]+)\*', r'\1', content)  # Remove italic
    
    # Clean up whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    
    if len(content) <= max_length:
        return content
    
    # Truncate at word boundary
    truncated = content[:max_length]
    last_space = truncated.rfind(' ')
    if last_space > max_length * 0.8:  # If we can find a space in last 20%
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."

def calculate_age_human(created_utc):
    """Calculate human-readable age from UTC timestamp"""
    now = datetime.now(timezone.utc)
    created = datetime.fromtimestamp(created_utc, timezone.utc)
    diff = now - created
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return f"{int(seconds)}s ago"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        return f"{minutes}m ago"
    elif seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    else:
        days = int(seconds // 86400)
        return f"{days}d ago"

def create_enhanced_post_data(post):
    """Create enhanced post data with all required fields"""
    content = post.get('selftext', '')
    content_preview = generate_content_preview(content)
    
    created_utc = post.get('created_utc', 0)
    age_human = calculate_age_human(created_utc)
    
    subreddit = post.get('subreddit', '')
    subreddit_color = SUBREDDIT_COLORS.get(subreddit, '#0079d3')
    
    score = post.get('score', 0)
    comments = post.get('num_comments', 0)
    engagement_score = score + comments
    
    return {
        "id": post.get('id', ''),
        "title": post.get('title', 'No Title'),
        "content": content,
        "content_preview": content_preview,
        "content_length": len(content),
        "subreddit": subreddit,
        "subreddit_color": subreddit_color,
        "subreddit_display": f"r/{subreddit}",
        "url": f"https://reddit.com{post.get('permalink', '')}",
        "score": score,
        "comments": comments,
        "engagement_score": engagement_score,
        "created_utc": created_utc,
        "age_human": age_human,
        "age_seconds": int(datetime.now(timezone.utc).timestamp() - created_utc),
        "author": post.get('author', 'Unknown'),
        "has_images": bool(post.get('is_video') or post.get('is_gallery') or 
                          post.get('url', '').endswith(('.jpg', '.png', '.gif'))),
        "flair": post.get('link_flair_text'),
        "is_self": post.get('is_self', True),
        "permalink": post.get('permalink', '')
    }

def create_dashboard_data(posts, run_timestamp):
    """Create complete dashboard data structure"""
    today = run_timestamp.strftime('%Y-%m-%d')
    run_time = run_timestamp.strftime('%H_%M')
    run_id = f"{today}_{run_time}"
    
    # Count posts by subreddit
    subreddit_counts = {}
    for post in posts:
        subreddit = post['subreddit']
        subreddit_counts[subreddit] = subreddit_counts.get(subreddit, 0) + 1
    
    # Create subreddit info
    subreddits = {}
    for subreddit, count in subreddit_counts.items():
        subreddits[subreddit] = {
            "name": f"r/{subreddit}",
            "color": SUBREDDIT_COLORS.get(subreddit, '#0079d3'),
            "post_count": count
        }
    
    return {
        "dashboard_info": {
            "title": "Reddit Engagement Dashboard",
            "subtitle": "Skincare & Haircare Communities",
            "last_updated": run_timestamp.isoformat(),
            "total_posts": len(posts),
            "subreddits_count": len(subreddits),
            "refresh_interval": "4 hours",
            "run_id": run_id,
            "run_date": today,
            "run_time": run_time
        },
        "posts": posts,
        "subreddits": subreddits
    }

def save_json_data(data, run_timestamp):
    """Save JSON data to date-based folder structure"""
    today = run_timestamp.strftime('%Y-%m-%d')
    run_time = run_timestamp.strftime('%H_%M')
    
    # Create date folder
    date_folder = os.path.join(ANALYSIS_DIR, today)
    os.makedirs(date_folder, exist_ok=True)
    
    # Save timestamped file
    timestamped_file = os.path.join(date_folder, f"{run_time}_summary.json")
    with open(timestamped_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ JSON saved: {timestamped_file}")
    
    # Also save as latest.json for easy access
    latest_file = os.path.join(ANALYSIS_DIR, 'latest.json')
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Latest JSON updated: {latest_file}")
    
    return timestamped_file, latest_file

def main():
    """Main monitoring function"""
    print(f"🔍 Starting Reddit monitoring for r/{SUBREDDIT}")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create analysis directory
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    
    # Get Reddit access token
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get Reddit access token")
        return False
    
    print("✅ Reddit authentication successful")
    
    # Fetch posts
    print(f"📥 Fetching posts from r/{SUBREDDIT}...")
    posts = fetch_posts(access_token, SUBREDDIT, POSTS_LIMIT)
    
    if not posts:
        print("❌ No posts fetched")
        return False
    
    print(f"📊 Fetched {len(posts)} posts")
    
    # Filter engaging posts
    engaging_posts = filter_engaging_posts(posts)
    print(f"🎯 Found {len(engaging_posts)} engaging posts")
    
    if not engaging_posts:
        print("ℹ️ No engaging posts found")
        return False
    
    # Get run timestamp
    run_timestamp = datetime.now()
    
    # Create enhanced post data
    print("🔧 Creating enhanced post data...")
    enhanced_posts = [create_enhanced_post_data(post) for post in engaging_posts]
    
    # Create dashboard data
    print("📋 Creating dashboard data structure...")
    dashboard_data = create_dashboard_data(enhanced_posts, run_timestamp)
    
    # Save JSON files
    print("💾 Saving JSON data...")
    timestamped_file, latest_file = save_json_data(dashboard_data, run_timestamp)
    
    print(f"\n✅ Phase 1 monitoring complete!")
    print(f"📊 Engaging posts found: {len(enhanced_posts)}")
    print(f"📁 Files saved:")
    print(f"   - {timestamped_file}")
    print(f"   - {latest_file}")
    
    # Show top posts
    print(f"\n🏆 Top engaging posts:")
    for i, post in enumerate(enhanced_posts[:3], 1):
        title = post['title'][:60] + '...' if len(post['title']) > 60 else post['title']
        score = post['score']
        comments = post['comments']
        age = post['age_human']
        print(f"{i}. {title}")
        print(f"   Score: {score}, Comments: {comments}, Age: {age}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
