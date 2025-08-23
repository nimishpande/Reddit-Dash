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
    patterns = [
        r'/comments/([a-zA-Z0-9]+)/',
        r'/comments/([a-zA-Z0-9]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def fetch_all_comments(access_token, post_id):
    """Fetch all comments using multiple strategies"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    url = f"{REDDIT_BASE_URL}/comments/{post_id}"
    
    all_comments = []
    comment_ids = set()
    
    # Strategy 1: Try different sorting methods
    sort_methods = ['confidence', 'top', 'new', 'controversial', 'old', 'qa', 'best']
    
    for sort_method in sort_methods:
        print(f"Trying sort method: {sort_method}")
        
        params = {
            'limit': 1000,
            'sort': sort_method,
            'depth': 10  # Get deeper comment threads
        }
        
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    comments = data[1]['data']['children']
                    
                    # Add new comments
                    new_count = 0
                    for comment in comments:
                        if 'data' in comment and 'id' in comment['data']:
                            comment_id = comment['data']['id']
                            if comment_id not in comment_ids:
                                all_comments.append(comment)
                                comment_ids.add(comment_id)
                                new_count += 1
                    
                    print(f"  Added {new_count} new comments (total: {len(all_comments)})")
            
            time.sleep(1)  # Rate limiting
            
        except Exception as e:
            print(f"  Error with {sort_method}: {e}")
    
    # Strategy 2: Try with different parameters
    print("Trying additional parameters...")
    
    additional_params = [
        {'limit': 1000, 'show': 'all'},  # Show all comments including hidden
        {'limit': 1000, 'sr_detail': True},  # Include subreddit details
        {'limit': 1000, 'raw_json': 1},  # Raw JSON format
    ]
    
    for params in additional_params:
        try:
            response = requests.get(url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and len(data) > 1:
                    comments = data[1]['data']['children']
                    
                    new_count = 0
                    for comment in comments:
                        if 'data' in comment and 'id' in comment['data']:
                            comment_id = comment['data']['id']
                            if comment_id not in comment_ids:
                                all_comments.append(comment)
                                comment_ids.add(comment_id)
                                new_count += 1
                    
                    print(f"  Added {new_count} new comments (total: {len(all_comments)})")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error with additional params: {e}")
    
    return all_comments

def fetch_post_data_complete(access_token, post_id):
    """Fetch post data and all comments with comprehensive approach"""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    url = f"{REDDIT_BASE_URL}/comments/{post_id}"
    
    try:
        print(f"Fetching post data for {post_id}...")
        
        # Get post data
        response = requests.get(url, headers=headers, params={'limit': 1})
        response.raise_for_status()
        
        data = response.json()
        
        if not isinstance(data, list) or len(data) < 1:
            print("Invalid response format")
            return None
        
        post_data = data[0]['data']['children'][0]['data']
        total_comments = post_data.get('num_comments', 0)
        
        print(f"Post reports {total_comments} total comments")
        
        # Get all comments using comprehensive strategy
        all_comments = fetch_all_comments(access_token, post_id)
        
        print(f"Final comment count: {len(all_comments)}")
        print(f"Missing comments: {total_comments - len(all_comments)}")
        
        return post_data, all_comments
        
    except Exception as e:
        print(f"Error fetching post data: {e}")
        return None

def extract_comments_recursive(comments_data, depth=0):
    """Recursively extract all comments and replies"""
    comments = []
    
    for comment in comments_data:
        if comment['kind'] == 't1':  # Comment
            comment_data = comment['data']
            
            # Include deleted/removed comments for analysis
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
                'is_deleted': comment_data.get('body') in ['[deleted]', '[removed]'],
                'is_hidden': comment_data.get('score', 0) < 0,  # Comments with negative scores
                'replies': []
            }
            
            # Extract replies if they exist
            if 'replies' in comment_data and comment_data['replies']:
                replies_data = comment_data['replies']['data']['children']
                comment_info['replies'] = extract_comments_recursive(replies_data, depth + 1)
            
            comments.append(comment_info)
    
    return comments

def analyze_missing_comments(post_data, extracted_comments):
    """Analyze why some comments might be missing"""
    total_reported = post_data.get('num_comments', 0)
    total_extracted = len(extracted_comments)
    missing_count = total_reported - total_extracted
    
    print(f"\n🔍 MISSING COMMENTS ANALYSIS:")
    print(f"   Reported by Reddit: {total_reported}")
    print(f"   Successfully extracted: {total_extracted}")
    print(f"   Missing: {missing_count}")
    
    if missing_count > 0:
        print(f"\n   Possible reasons for missing comments:")
        print(f"   • Deleted/removed comments: {missing_count} comments may have been deleted by users or removed by moderators")
        print(f"   • Hidden comments: Comments with very low scores might be hidden by Reddit")
        print(f"   • API limitations: Reddit's API may not return all comments due to rate limiting or other restrictions")
        print(f"   • Spam/automod removal: Comments caught by Reddit's spam filters")
        print(f"   • Shadow-banned users: Comments from shadow-banned users may not appear")
    
    # Count deleted/removed comments
    deleted_count = sum(1 for comment in extracted_comments if comment.get('is_deleted', False))
    hidden_count = sum(1 for comment in extracted_comments if comment.get('is_hidden', False))
    
    print(f"\n   Extracted comment breakdown:")
    print(f"   • Valid comments: {total_extracted - deleted_count}")
    print(f"   • Deleted/removed: {deleted_count}")
    print(f"   • Hidden (negative score): {hidden_count}")

def main():
    # The Reddit post URL
    post_url = "https://www.reddit.com/r/IndianBeautyTalks/comments/1mvhudo/my_boyfriend_and_i_are_planning_to_launch_a/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button"
    
    print("🔍 COMPREHENSIVE REDDIT POST EXTRACTION")
    print("=" * 50)
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
    
    # Fetch post data with comprehensive comment extraction
    result = fetch_post_data_complete(access_token, post_id)
    if not result:
        print("Failed to fetch post data")
        return
    
    post_data, comments_data = result
    
    # Extract all comments recursively
    print("\nExtracting comments...")
    all_comments = extract_comments_recursive(comments_data)
    
    # Analyze missing comments
    analyze_missing_comments(post_data, all_comments)
    
    # Calculate statistics
    valid_comments = [c for c in all_comments if not c.get('is_deleted', False)]
    stats = {
        'total_comments': len(valid_comments),
        'total_upvotes': sum(c['score'] for c in valid_comments),
        'average_upvotes': sum(c['score'] for c in valid_comments) / len(valid_comments) if valid_comments else 0,
        'depth_distribution': {},
        'top_comments': sorted(valid_comments, key=lambda x: x['score'], reverse=True)[:10]
    }
    
    # Calculate depth distribution
    for comment in valid_comments:
        depth = comment['depth']
        stats['depth_distribution'][depth] = stats['depth_distribution'].get(depth, 0) + 1
    
    # Create output structure
    output = {
        "extraction_info": {
            "source_url": post_url,
            "post_id": post_id,
            "extraction_timestamp": datetime.now().isoformat(),
            "total_comments_extracted": len(valid_comments),
            "total_comments_reported": post_data.get('num_comments', 0),
            "missing_comments": post_data.get('num_comments', 0) - len(valid_comments),
            "deleted_comments": len([c for c in all_comments if c.get('is_deleted', False)]),
            "hidden_comments": len([c for c in all_comments if c.get('is_hidden', False)])
        },
        "post_data": post_data,
        "comment_statistics": stats,
        "comments": valid_comments,
        "all_comments_including_deleted": all_comments
    }
    
    # Save to file
    output_dir = "reddit_data/json/specific_posts"
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f"indian_beauty_talks_launch_post_{post_id}_complete.json"
    output_path = os.path.join(output_dir, filename)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Complete data extracted successfully!")
    print(f"📁 Saved to: {output_path}")
    print(f"📊 Post Score: {post_data.get('score', 0)}")
    print(f"💬 Valid Comments: {len(valid_comments)}")
    print(f"🗑️ Deleted/Removed: {len([c for c in all_comments if c.get('is_deleted', False)])}")
    print(f"⬆️ Total Upvotes: {stats['total_upvotes']}")
    print(f"📈 Average Upvotes per Comment: {stats['average_upvotes']:.2f}")

if __name__ == "__main__":
    main()
