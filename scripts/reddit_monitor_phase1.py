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
ANALYSIS_DIR = 'data/analysis'  # Updated path for new repository structure

def load_subreddit_config():
    """Load subreddit configuration from JSON file"""
    config_path = 'config/subreddits.json'
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config
    except FileNotFoundError:
        print("⚠️ Subreddit config not found, using default settings")
        return {
            "subreddits": [{"name": "skincareaddictsindia", "enabled": True, "posts_limit": 25}],
            "settings": {"min_engagement_score": 7, "min_upvotes": 5, "min_comments": 2}
        }

def load_user_profile():
    """Load user profile configuration"""
    profile_path = 'config/user_profile.json'
    try:
        with open(profile_path, 'r', encoding='utf-8') as f:
            return json.load(f)['user_profile']
    except FileNotFoundError:
        print("⚠️ User profile not found, using default settings")
        return {
            "expertise_areas": ["skincare", "routine"],
            "interest_keywords": ["help", "recommendation"],
            "min_relevance_score": 10
        }

def calculate_relevance_score(post, user_profile):
    """Calculate how relevant a post is to user's expertise and interests"""
    title = post.get('title', '').lower()
    content = post.get('selftext', '').lower()
    flair = post.get('link_flair_text', '').lower() if post.get('link_flair_text') else ''
    
    # Combine all text for analysis
    full_text = f"{title} {content} {flair}"
    
    relevance_score = 0
    
    # Expertise area matching (high weight)
    expertise_matches = 0
    for expertise in user_profile.get('expertise_areas', []):
        if expertise.lower() in full_text:
            expertise_matches += 1
            relevance_score += 8  # High score for expertise match
    
    # Interest keyword matching (medium weight)
    interest_matches = 0
    for keyword in user_profile.get('interest_keywords', []):
        if keyword.lower() in full_text:
            interest_matches += 1
            relevance_score += 5  # Medium score for interest match
    
    # Question indicators (users asking for help = opportunity to engage)
    question_indicators = ['?', 'help', 'suggest', 'recommend', 'advice', 'how to', 'what should']
    question_score = sum(3 for indicator in question_indicators if indicator in full_text)
    relevance_score += min(question_score, 15)  # Cap at 15 points
    
    # Avoid certain content
    avoid_keywords = user_profile.get('avoid_keywords', [])
    for avoid in avoid_keywords:
        if avoid.lower() in full_text:
            relevance_score -= 10  # Penalty for avoided content
    
    # Bonus for specific post types
    if any(post_type in full_text for post_type in ['routine', 'beginner', 'help']):
        relevance_score += 5
    
    return max(0, relevance_score)  # Don't go below 0

def calculate_combined_score(post, user_profile):
    """Calculate combined engagement + relevance score"""
    # Your existing engagement score
    engagement_score = post.get('score', 0) + post.get('num_comments', 0)
    
    # New relevance score
    relevance_score = calculate_relevance_score(post, user_profile)
    
    # Competition penalty (more comments = harder to get noticed)
    competition_penalty = max(0, (post.get('num_comments', 0) - 15) * 0.5)
    
    # Timeliness boost (newer posts = better opportunity)
    hours_old = (datetime.now(timezone.utc).timestamp() - post.get('created_utc', 0)) / 3600
    timeliness_multiplier = max(0.5, 1 - (hours_old / 24))  # Decreases over 24 hours
    
    # Combined formula
    combined_score = (
        (engagement_score * 0.4) +  # 40% engagement weight
        (relevance_score * 0.6)     # 60% relevance weight
    ) * timeliness_multiplier - competition_penalty
    
    return max(0, combined_score)

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

def filter_engaging_posts(posts, user_profile):
    """Filter posts based on engagement AND relevance criteria"""
    engaging_posts = []
    
    for post in posts:
        # Calculate all scores
        engagement_score = post.get('score', 0) + post.get('num_comments', 0)
        relevance_score = calculate_relevance_score(post, user_profile)
        combined_score = calculate_combined_score(post, user_profile)
        
        # Filter criteria
        min_relevance = user_profile.get('min_relevance_score', 5)
        min_combined = 8
        
        if (relevance_score >= min_relevance and 
            combined_score >= min_combined and 
            post.get('selftext') not in ['[deleted]', '[removed]']):
            
            # Add scoring data to post
            post['relevance_score'] = relevance_score
            post['combined_score'] = combined_score
            post['engagement_score_original'] = engagement_score
            
            engaging_posts.append(post)
    
    # Sort by combined score (best opportunities first)
    engaging_posts.sort(key=lambda x: x['combined_score'], reverse=True)
    
    return engaging_posts

def extract_image_urls(post):
    """Extract image URLs from Reddit post data"""
    image_urls = []
    
    # Handle gallery posts (multiple images)
    if post.get('is_gallery'):
        gallery_data = post.get('gallery_data', {}).get('items', [])
        media_metadata = post.get('media_metadata', {})
        
        for item in gallery_data:
            media_id = item.get('media_id')
            if media_id in media_metadata:
                # Get the highest resolution image (source)
                source_url = media_metadata[media_id].get('s', {}).get('u')
                if source_url:
                    # Clean up the URL (remove HTML entities)
                    clean_url = source_url.replace('&amp;', '&')
                    image_urls.append({
                        'url': clean_url,
                        'width': media_metadata[media_id].get('s', {}).get('x'),
                        'height': media_metadata[media_id].get('s', {}).get('y'),
                        'type': 'gallery'
                    })
    
    # Handle single image posts
    elif post.get('preview', {}).get('images'):
        for image in post['preview']['images']:
            source_url = image.get('source', {}).get('url')
            if source_url:
                # Clean up the URL (remove HTML entities)
                clean_url = source_url.replace('&amp;', '&')
                image_urls.append({
                    'url': clean_url,
                    'width': image.get('source', {}).get('width'),
                    'height': image.get('source', {}).get('height'),
                    'type': 'preview'
                })
    
    # Handle direct image URLs
    elif post.get('url', '').endswith(('.jpg', '.jpeg', '.png', '.gif')):
        image_urls.append({
            'url': post.get('url'),
            'width': None,
            'height': None,
            'type': 'direct'
        })
    
    # Handle thumbnail
    elif post.get('thumbnail') and post.get('thumbnail') != 'self':
        image_urls.append({
            'url': post.get('thumbnail'),
            'width': post.get('thumbnail_width'),
            'height': post.get('thumbnail_height'),
            'type': 'thumbnail'
        })
    
    return image_urls

def create_enhanced_post_data(post):
    """Create enhanced post data with additional fields"""
    # Calculate age
    created_utc = post.get('created_utc', 0)
    current_time = datetime.now(timezone.utc).timestamp()
    age_seconds = current_time - created_utc
    
    # Convert to human readable age
    if age_seconds < 60:
        age_human = f"{int(age_seconds)}s ago"
    elif age_seconds < 3600:
        age_human = f"{int(age_seconds // 60)}m ago"
    elif age_seconds < 86400:
        age_human = f"{int(age_seconds // 3600)}h ago"
    else:
        age_human = f"{int(age_seconds // 86400)}d ago"
    
    # Get subreddit info
    subreddit = post.get('subreddit', '')
    subreddit_display = f"r/{subreddit}"
    # Load subreddit config for color
    subreddit_config = load_subreddit_config()
    subreddit_info = next((s for s in subreddit_config['subreddits'] if s['name'] == subreddit), None)
    subreddit_color = subreddit_info.get('color', '#0079d3') if subreddit_info else '#0079d3'
    
    # Content preview
    content = post.get('selftext', '')
    content_length = len(content)
    content_preview = content[:150] + '...' if len(content) > 150 else content
    
    # Extract image URLs
    image_urls = extract_image_urls(post)
    has_images = len(image_urls) > 0
    
    # Engagement score
    score = post.get('score', 0)
    comments = post.get('num_comments', 0)
    engagement_score = score + comments
    
    return {
        'id': post.get('id', ''),
        'title': post.get('title', ''),
        'content': content,
        'content_preview': content_preview,
        'content_length': content_length,
        'subreddit': subreddit,
        'subreddit_color': subreddit_color,
        'subreddit_display': subreddit_display,
        'url': f"https://reddit.com{post.get('permalink', '')}",
        'score': score,
        'comments': comments,
        'engagement_score': engagement_score,
        'created_utc': created_utc,
        'age_human': age_human,
        'age_seconds': age_seconds,
        'author': post.get('author', ''),
        'has_images': has_images,
        'image_urls': image_urls,
        'image_count': len(image_urls),
        'flair': post.get('link_flair_text', ''),
        'is_self': post.get('is_self', False),
        'permalink': post.get('permalink', ''),
        'relevance_score': post.get('relevance_score', 0),
        'combined_score': post.get('combined_score', 0),
        'engagement_score_original': post.get('engagement_score_original', 0),
        'opportunity_rating': "high" if post.get('combined_score', 0) > 30 else 
                             "medium" if post.get('combined_score', 0) > 20 else "low"
    }

def create_dashboard_data(posts, run_timestamp):
    """Create the complete dashboard data structure"""
    # Get unique subreddits
    subreddits = list(set(post['subreddit'] for post in posts))
    
    # Create dashboard info
    dashboard_info = {
        'title': 'Reddit Engagement Dashboard',
        'subtitle': 'Skincare & Haircare Communities',
        'last_updated': run_timestamp.isoformat(),
        'total_posts': len(posts),
        'subreddits_count': len(subreddits),
        'refresh_interval': '20 minutes',
        'run_id': run_timestamp.strftime('%Y-%m-%d_%H_%M'),
        'run_date': run_timestamp.strftime('%Y-%m-%d'),
        'run_time': run_timestamp.strftime('%H_%M')
    }
    
    return {
        'dashboard_info': dashboard_info,
        'posts': posts,
        'subreddits': subreddits
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
    
    # Copy to docs folder for dashboard access
    docs_data_file = os.path.join('docs', 'data.json')
    with open(docs_data_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Dashboard data updated: {docs_data_file}")
    
    return timestamped_file, latest_file

def main():
    """Main monitoring function"""
    # Load configurations
    subreddit_config = load_subreddit_config()
    user_profile = load_user_profile()
    
    # Get enabled subreddits
    enabled_subreddits = [s for s in subreddit_config['subreddits'] if s.get('enabled', True)]
    settings = subreddit_config.get('settings', {})
    
    print(f"🔍 Starting Reddit monitoring for {len(enabled_subreddits)} subreddits")
    print(f"⏰ Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 User profile loaded: {len(user_profile.get('expertise_areas', []))} expertise areas")
    
    # Create analysis directory
    os.makedirs(ANALYSIS_DIR, exist_ok=True)
    os.makedirs('config', exist_ok=True)  # Ensure config directory exists
    
    # Get Reddit access token
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get Reddit access token")
        return False
    
    print("✅ Reddit authentication successful")
    
    # Fetch posts from all enabled subreddits
    all_posts = []
    for subreddit_info in enabled_subreddits:
        subreddit_name = subreddit_info['name']
        posts_limit = subreddit_info.get('posts_limit', 25)
        
        print(f"📥 Fetching posts from r/{subreddit_name} (limit: {posts_limit})...")
        posts = fetch_posts(access_token, subreddit_name, posts_limit)
        if posts:
            all_posts.extend(posts)
            print(f"   ✅ Found {len(posts)} posts from r/{subreddit_name}")
        else:
            print(f"   ⚠️ No posts found in r/{subreddit_name}")
    
    if not all_posts:
        print("❌ No posts fetched from any subreddit")
        return False
    
    print(f"📊 Total posts fetched: {len(all_posts)} from {len(enabled_subreddits)} subreddits")
    
    # Filter engaging posts (now with relevance scoring)
    engaging_posts = filter_engaging_posts(all_posts, user_profile)
    print(f"🎯 Found {len(engaging_posts)} relevant posts")
    
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
    
    # Copy latest data to docs folder for dashboard
    print("📋 Copying data to dashboard...")
    try:
        import shutil
        docs_dir = 'docs'
        os.makedirs(docs_dir, exist_ok=True)
        shutil.copy2(latest_file, os.path.join(docs_dir, 'data.json'))
        print("✅ Data copied to docs/data.json")
    except Exception as e:
        print(f"⚠️ Failed to copy data to docs: {e}")
    
    print(f"\n✅ Phase 1 monitoring complete!")
    print(f"📊 Engaging posts found: {len(enhanced_posts)}")
    print(f"📁 Files saved:")
    print(f"   - {timestamped_file}")
    print(f"   - {latest_file}")
    
    # Show top posts with relevance info
    print(f"\n🏆 Top relevant posts:")
    for i, post in enumerate(enhanced_posts[:5], 1):
        title = post['title'][:60] + '...' if len(post['title']) > 60 else post['title']
        relevance = post.get('relevance_score', 0)
        combined = post.get('combined_score', 0)
        age = post.get('age_human', 'Unknown')
        print(f"{i}. {title}")
        print(f"   Relevance: {relevance:.1f}, Combined: {combined:.1f}, Age: {age}")
    
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
