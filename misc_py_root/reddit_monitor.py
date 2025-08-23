import os
import requests
import json
import time
import base64
from dotenv import load_dotenv
from datetime import datetime, timedelta
import re
from pathlib import Path

# Load credentials from .env
load_dotenv()
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'skincare_monitor/1.0 (by /u/your_username)'

# Reddit API endpoints
REDDIT_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
REDDIT_BASE_URL = 'https://oauth.reddit.com'

# Configuration
SUBREDDIT = 'skincareaddictsindia'
MIN_ENGAGEMENT_SCORE = 7  # upvotes + comments
MIN_UPVOTES = 5
MIN_COMMENTS = 2
POSTS_LIMIT = 50  # Number of posts to fetch
MONITORING_DIR = 'reddit_monitoring'

def get_reddit_token():
    """Get Reddit OAuth access token"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("Error: Missing Reddit credentials in .env file")
        return None
    
    credentials = f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'User-Agent': REDDIT_USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
    try:
        response = requests.post(REDDIT_TOKEN_URL, headers=headers, data=data)
        if response.status_code == 200:
            token_data = response.json()
            return token_data['access_token']
        else:
            print(f"Error getting token: {response.text}")
            return None
    except Exception as e:
        print(f"Error getting Reddit token: {e}")
        return None

def fetch_subreddit_posts(access_token, subreddit, limit=50, sort='new'):
    """Fetch posts from subreddit"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    url = f"{REDDIT_BASE_URL}/r/{subreddit}/{sort}"
    params = {'limit': limit}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        posts = data['data']['children']
        
        return [post['data'] for post in posts]
        
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return []

def filter_engaging_posts(posts):
    """Filter posts based on engagement criteria"""
    engaging_posts = []
    
    for post in posts:
        score = post.get('score', 0)
        num_comments = post.get('num_comments', 0)
        engagement_score = score + num_comments
        
        # Check if post meets engagement criteria
        if (engagement_score >= MIN_ENGAGEMENT_SCORE or 
            score >= MIN_UPVOTES or 
            num_comments >= MIN_COMMENTS):
            
            # Skip deleted/removed posts
            if post.get('selftext') not in ['[deleted]', '[removed]']:
                engaging_posts.append(post)
    
    return engaging_posts

def extract_image_urls(post):
    """Extract image URLs from post"""
    image_urls = []
    
    # Check if post has images
    if post.get('is_video', False):
        return image_urls
    
    # Check preview images
    preview = post.get('preview', {})
    if preview and 'images' in preview:
        for image in preview['images']:
            if 'source' in image:
                image_urls.append(image['source']['url'])
    
    # Check thumbnail
    thumbnail = post.get('thumbnail')
    if thumbnail and thumbnail not in ['self', 'default', 'nsfw']:
        image_urls.append(thumbnail)
    
    # Check URL if it's an image
    url = post.get('url', '')
    if any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']):
        image_urls.append(url)
    
    return list(set(image_urls))  # Remove duplicates

def format_post_summary(post, index):
    """Format a single post for text output"""
    title = post.get('title', 'No Title')
    author = post.get('author', 'Unknown')
    score = post.get('score', 0)
    num_comments = post.get('num_comments', 0)
    created_utc = datetime.fromtimestamp(post.get('created_utc', 0))
    selftext = post.get('selftext', '')
    url = f"https://reddit.com{post.get('permalink', '')}"
    
    # Calculate engagement score
    engagement_score = score + num_comments
    
    # Extract image URLs
    image_urls = extract_image_urls(post)
    
    summary = f"""
{'='*80}
POST #{index+1}
{'='*80}
Title: {title}
Author: u/{author}
Posted: {created_utc.strftime('%Y-%m-%d %H:%M:%S')}
Score: {score} upvotes
Comments: {num_comments}
Engagement Score: {engagement_score}
URL: {url}

Content:
{selftext if selftext else '[No text content]'}

Images: {len(image_urls)} found
"""
    
    if image_urls:
        summary += "\nImage URLs:\n"
        for i, img_url in enumerate(image_urls, 1):
            summary += f"{i}. {img_url}\n"
    
    return summary

def get_last_run_timestamp():
    """Get timestamp of last run"""
    timestamp_file = os.path.join(MONITORING_DIR, 'last_run_timestamp.txt')
    
    if os.path.exists(timestamp_file):
        with open(timestamp_file, 'r') as f:
            timestamp_str = f.read().strip()
            try:
                return datetime.fromisoformat(timestamp_str)
            except:
                return None
    return None

def save_last_run_timestamp():
    """Save current timestamp"""
    timestamp_file = os.path.join(MONITORING_DIR, 'last_run_timestamp.txt')
    
    with open(timestamp_file, 'w') as f:
        f.write(datetime.now().isoformat())

def create_daily_summary(posts, run_timestamp):
    """Create daily summary text file"""
    today = datetime.now().strftime('%Y-%m-%d')
    summary_file = os.path.join(MONITORING_DIR, f'daily_summary_{today}.txt')
    
    # Check if file exists and append mode
    mode = 'a' if os.path.exists(summary_file) else 'w'
    
    with open(summary_file, mode, encoding='utf-8') as f:
        if mode == 'w':
            f.write(f"REDDIT MONITORING SUMMARY - r/{SUBREDDIT}\n")
            f.write(f"Date: {today}\n")
            f.write(f"Monitoring started: {run_timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*80 + "\n\n")
        
        f.write(f"\n{'='*60}\n")
        f.write(f"RUN AT: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"POSTS FOUND: {len(posts)}\n")
        f.write(f"{'='*60}\n")
        
        if not posts:
            f.write("\nNo engaging posts found in this run.\n")
        else:
            for i, post in enumerate(posts):
                f.write(format_post_summary(post, i))
                f.write("\n")
        
        f.write(f"\n{'='*60}\n")
        f.write(f"END OF RUN\n")
        f.write(f"{'='*60}\n\n")

def save_posts_json(posts, run_timestamp):
    """Save posts data as JSON backup"""
    today = datetime.now().strftime('%Y-%m-%d')
    json_file = os.path.join(MONITORING_DIR, f'posts_{today}.json')
    
    data = {
        'monitoring_info': {
            'subreddit': SUBREDDIT,
            'run_timestamp': run_timestamp.isoformat(),
            'posts_found': len(posts),
            'engagement_criteria': {
                'min_engagement_score': MIN_ENGAGEMENT_SCORE,
                'min_upvotes': MIN_UPVOTES,
                'min_comments': MIN_COMMENTS
            }
        },
        'posts': posts
    }
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    """Main monitoring function"""
    print(f"🔍 Starting Reddit monitoring for r/{SUBREDDIT}")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Create monitoring directory
    os.makedirs(MONITORING_DIR, exist_ok=True)
    
    # Get access token
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get access token")
        return
    
    print("✅ Successfully obtained access token")
    
    # Fetch posts
    print(f"📥 Fetching posts from r/{SUBREDDIT}...")
    posts = fetch_subreddit_posts(access_token, SUBREDDIT, POSTS_LIMIT, 'new')
    
    if not posts:
        print("❌ No posts fetched")
        return
    
    print(f"📊 Fetched {len(posts)} posts")
    
    # Filter engaging posts
    engaging_posts = filter_engaging_posts(posts)
    print(f"🎯 Found {len(engaging_posts)} engaging posts")
    
    # Get run timestamp
    run_timestamp = datetime.now()
    
    # Create summary
    print("📝 Creating daily summary...")
    create_daily_summary(engaging_posts, run_timestamp)
    
    # Save JSON backup
    print("💾 Saving JSON backup...")
    save_posts_json(engaging_posts, run_timestamp)
    
    # Save timestamp
    save_last_run_timestamp()
    
    # Upload to GitHub Releases (optional)
    try:
        from github_storage import upload_to_github
        print("\n☁️ Uploading to GitHub Releases...")
        upload_success = upload_to_github()
        if upload_success:
            print("✅ Files uploaded to GitHub Releases!")
        else:
            print("⚠️ GitHub upload failed (files still saved locally)")
    except ImportError:
        print("ℹ️ GitHub storage not available (files saved locally only)")
    except Exception as e:
        print(f"⚠️ GitHub upload error: {e}")
    
    # Upload to Google Drive (optional - fallback)
    try:
        from google_drive_uploader import upload_monitoring_files
        print("\n☁️ Uploading to Google Drive...")
        upload_success = upload_monitoring_files()
        if upload_success:
            print("✅ Files uploaded to Google Drive!")
        else:
            print("⚠️ Google Drive upload failed (files still saved locally)")
    except ImportError:
        print("ℹ️ Google Drive uploader not available (files saved locally only)")
    except Exception as e:
        print(f"⚠️ Google Drive upload error: {e}")
    
    # Print summary to console
    print(f"\n✅ Monitoring complete!")
    print(f"📁 Summary saved to: {MONITORING_DIR}/daily_summary_{datetime.now().strftime('%Y-%m-%d')}.txt")
    print(f"📊 Engaging posts found: {len(engaging_posts)}")
    
    if engaging_posts:
        print(f"\n🏆 Top engaging posts:")
        for i, post in enumerate(engaging_posts[:3], 1):
            title = post.get('title', 'No Title')[:60] + '...' if len(post.get('title', '')) > 60 else post.get('title', 'No Title')
            score = post.get('score', 0)
            comments = post.get('num_comments', 0)
            print(f"{i}. {title}")
            print(f"   Score: {score}, Comments: {comments}")

if __name__ == "__main__":
    main()
