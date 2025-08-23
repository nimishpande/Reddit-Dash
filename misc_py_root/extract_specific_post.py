import os
import requests
import json
import time
import base64
from dotenv import load_dotenv
import re
from datetime import datetime

# Load credentials from .env
load_dotenv()
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'ingredient_cosmetics_analyzer/1.0 (by /u/your_username)'

# Reddit API endpoints
REDDIT_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
REDDIT_BASE_URL = 'https://oauth.reddit.com'

def get_reddit_token():
    """Get Reddit OAuth access token using client credentials flow"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("Error: Missing Reddit credentials in .env file")
        return None
    
    # Create Basic Auth header
    credentials = f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'User-Agent': REDDIT_USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {
        'grant_type': 'client_credentials'
    }
    
    try:
        print("Requesting Reddit access token...")
        response = requests.post(REDDIT_TOKEN_URL, headers=headers, data=data)
        
        if response.status_code == 200:
            token_data = response.json()
            print("✓ Successfully obtained access token")
            return token_data['access_token']
        else:
            print(f"Error response: {response.text}")
            return None
            
    except Exception as e:
        print(f"Error getting Reddit token: {e}")
        return None

def extract_post_id_from_url(url):
    """Extract post ID from Reddit URL"""
    # Pattern to match Reddit post URLs
    patterns = [
        r'/comments/([a-zA-Z0-9]+)/',
        r'/comments/([a-zA-Z0-9]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def fetch_post_data(access_token, post_id):
    """Fetch post data and all comments with pagination"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    url = f"{REDDIT_BASE_URL}/comments/{post_id}"
    
    try:
        print(f"Fetching data for post {post_id}...")
        
        # First, get the post data and initial comments
        response = requests.get(url, headers=headers, params={'limit': 1000})
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, list) or len(data) < 2:
            print("Invalid response format")
            return None
        
        # First item is the post, second item is comments
        post_data = data[0]['data']['children'][0]['data']
        comments_data = data[1]['data']['children']
        
        # Get the total number of comments from the post
        total_comments = post_data.get('num_comments', 0)
        print(f"Post reports {total_comments} total comments")
        
        # If we have fewer comments than reported, try to get more
        if len(comments_data) < total_comments:
            print(f"Initial fetch got {len(comments_data)} comments, trying to get more...")
            
            # Try different sorting methods to get more comments
            sort_methods = ['confidence', 'top', 'new', 'controversial', 'old', 'qa']
            
            for sort_method in sort_methods:
                if len(comments_data) >= total_comments:
                    break
                    
                print(f"Trying sort method: {sort_method}")
                params = {
                    'limit': 1000,
                    'sort': sort_method
                }
                
                response = requests.get(url, headers=headers, params=params)
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list) and len(data) > 1:
                        new_comments = data[1]['data']['children']
                        
                        # Merge comments, avoiding duplicates
                        existing_ids = {comment['data']['id'] for comment in comments_data if 'data' in comment and 'id' in comment['data']}
                        for comment in new_comments:
                            if 'data' in comment and 'id' in comment['data'] and comment['data']['id'] not in existing_ids:
                                comments_data.append(comment)
                                existing_ids.add(comment['data']['id'])
                        
                        print(f"After {sort_method} sort: {len(comments_data)} comments")
                
                time.sleep(1)  # Rate limiting
        
        print(f"Final comment count: {len(comments_data)}")
        return post_data, comments_data
        
    except Exception as e:
        print(f"Error fetching post data: {e}")
        return None

def extract_comments_recursive(comments_data, depth=0):
    """Recursively extract all comments and replies"""
    comments = []
    
    for comment in comments_data:
        if comment['kind'] == 't1':  # Comment
            comment_data = comment['data']
            
            # Skip deleted/removed comments
            if comment_data.get('body') in ['[deleted]', '[removed]']:
                continue
            
            comment_info = {
                'id': comment_data.get('id'),
                'author': comment_data.get('author'),
                'body': comment_data.get('body'),
                'score': comment_data.get('score', 0),
                'upvote_ratio': comment_data.get('upvote_ratio', 1.0),
                'created_utc': comment_data.get('created_utc'),
                'depth': depth,
                'parent_id': comment_data.get('parent_id'),
                'is_submitter': comment_data.get('is_submitter', False),
                'distinguished': comment_data.get('distinguished'),
                'edited': comment_data.get('edited'),
                'gilded': comment_data.get('gilded', 0),
                'controversiality': comment_data.get('controversiality', 0),
                'permalink': comment_data.get('permalink'),
                'stickied': comment_data.get('stickied', False),
                'replies': []
            }
            
            # Extract replies if they exist
            if 'replies' in comment_data and comment_data['replies']:
                replies_data = comment_data['replies']['data']['children']
                comment_info['replies'] = extract_comments_recursive(replies_data, depth + 1)
            
            comments.append(comment_info)
    
    return comments

def calculate_comment_stats(comments):
    """Calculate statistics for comments"""
    total_comments = len(comments)
    total_upvotes = sum(c['score'] for c in comments)
    avg_upvotes = total_upvotes / total_comments if total_comments > 0 else 0
    
    # Count by depth
    depth_counts = {}
    for comment in comments:
        depth = comment['depth']
        depth_counts[depth] = depth_counts.get(depth, 0) + 1
    
    # Top comments by score
    top_comments = sorted(comments, key=lambda x: x['score'], reverse=True)[:10]
    
    return {
        'total_comments': total_comments,
        'total_upvotes': total_upvotes,
        'average_upvotes': avg_upvotes,
        'depth_distribution': depth_counts,
        'top_comments': top_comments
    }

def main():
    # The Reddit post URL
    post_url = "https://www.reddit.com/r/IndianBeautyTalks/comments/1mvhudo/my_boyfriend_and_i_are_planning_to_launch_a/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button"
    
    print("🔍 Extracting data from Reddit post...")
    print(f"URL: {post_url}")
    
    # Get access token
    access_token = get_reddit_token()
    if not access_token:
        print("Failed to get access token")
        return
    
    # Extract post ID from URL
    post_id = extract_post_id_from_url(post_url)
    if not post_id:
        print("Could not extract post ID from URL")
        return
    
    print(f"Post ID: {post_id}")
    
    # Fetch post data
    result = fetch_post_data(access_token, post_id)
    if not result:
        print("Failed to fetch post data")
        return
    
    post_data, comments_data = result
    
    # Extract all comments recursively
    print("Extracting comments...")
    all_comments = extract_comments_recursive(comments_data)
    
    # Calculate statistics
    stats = calculate_comment_stats(all_comments)
    
    # Create output structure
    output = {
        "extraction_info": {
            "source_url": post_url,
            "post_id": post_id,
            "extraction_timestamp": datetime.now().isoformat(),
            "total_comments_extracted": len(all_comments)
        },
        "post_data": {
            "id": post_data.get('id'),
            "title": post_data.get('title'),
            "author": post_data.get('author'),
            "score": post_data.get('score', 0),
            "upvote_ratio": post_data.get('upvote_ratio', 1.0),
            "num_comments": post_data.get('num_comments', 0),
            "created_utc": post_data.get('created_utc'),
            "selftext": post_data.get('selftext'),
            "subreddit": post_data.get('subreddit'),
            "permalink": post_data.get('permalink'),
            "url": post_data.get('url'),
            "is_self": post_data.get('is_self', False),
            "is_video": post_data.get('is_video', False),
            "over_18": post_data.get('over_18', False),
            "spoiler": post_data.get('spoiler', False),
            "stickied": post_data.get('stickied', False),
            "edited": post_data.get('edited'),
            "gilded": post_data.get('gilded', 0),
            "distinguished": post_data.get('distinguished'),
            "locked": post_data.get('locked', False),
            "archived": post_data.get('archived', False),
            "contest_mode": post_data.get('contest_mode', False),
            "subreddit_subscribers": post_data.get('subreddit_subscribers'),
            "domain": post_data.get('domain'),
            "thumbnail": post_data.get('thumbnail'),
            "preview": post_data.get('preview')
        },
        "comment_statistics": stats,
        "comments": all_comments
    }
    
    # Save to file
    output_dir = "reddit_data/json/specific_posts"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"indian_beauty_talks_launch_post_{post_id}.json"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Data extracted successfully!")
    print(f"📁 Saved to: {output_path}")
    print(f"📊 Post Score: {post_data.get('score', 0)}")
    print(f"💬 Total Comments: {len(all_comments)}")
    print(f"⬆️ Total Upvotes: {stats['total_upvotes']}")
    print(f"📈 Average Upvotes per Comment: {stats['average_upvotes']:.2f}")
    print(f"📊 Comment Depth Distribution: {stats['depth_distribution']}")

if __name__ == "__main__":
    main()
