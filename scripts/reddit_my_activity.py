#!/usr/bin/env python3
"""
My Reddit Activity Tracker
Simple script to track where you've commented and which subreddits you follow
"""

import praw
import json
import os
from datetime import datetime, timezone
from collections import Counter
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def connect_to_reddit():
    """Connect to Reddit API"""
    try:
        reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'My Reddit Activity Tracker v1.0')
        )
        
        # Test connection by getting a user
        username = os.getenv('REDDIT_USERNAME')
        if not username:
            print("❌ REDDIT_USERNAME not found in .env file")
            exit(1)
            
        user = reddit.redditor(username)
        print(f"✅ Connected to Reddit API")
        print(f"👤 Analyzing user: {username}")
        return reddit, user
    except Exception as e:
        print(f"❌ Failed to connect to Reddit: {e}")
        print("💡 Make sure your .env file has the correct Reddit credentials")
        exit(1)

def get_my_comments(reddit, user, limit=500):
    """Get your recent comments and analyze subreddit activity"""
    print(f"🔍 Analyzing your last {limit} comments...")
    
    comment_subreddits = []
    comment_details = []
    
    for comment in user.comments.new(limit=limit):
        subreddit_name = str(comment.subreddit)
        comment_subreddits.append(subreddit_name)
        
        comment_details.append({
            'subreddit': subreddit_name,
            'subreddit_display': comment.subreddit.display_name,
            'post_title': comment.submission.title if hasattr(comment, 'submission') else 'Unknown',
            'comment_text': comment.body[:100] + '...' if len(comment.body) > 100 else comment.body,
            'score': comment.score,
            'created': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M'),
            'url': f"https://reddit.com{comment.permalink}"
        })
    
    # Count subreddit activity
    subreddit_counts = Counter(comment_subreddits)
    
    return comment_details, subreddit_counts

def get_my_subreddits(reddit, user):
    """Get subreddits you're subscribed to (limited without auth)"""
    print("📋 Note: Cannot fetch subscribed subreddits without authentication")
    print("   This would require your Reddit password for full access")
    
    # Return empty list since we can't access subscriptions without auth
    return []

def print_activity_summary(comment_details, subreddit_counts, subscribed_subreddits):
    """Print a nice summary of your activity"""
    print("\n" + "="*70)
    print("📊 YOUR REDDIT ACTIVITY SUMMARY")
    print("="*70)
    
    # Basic stats
    total_comments = len(comment_details)
    unique_subreddits_commented = len(subreddit_counts)
    total_subscribed = len(subscribed_subreddits)
    
    print(f"💬 Total Comments Analyzed: {total_comments:,}")
    print(f"🏠 Unique Subreddits You've Commented In: {unique_subreddits_commented:,}")
    print(f"📋 Subreddits You're Subscribed To: {total_subscribed:,}")
    
    # Top subreddits by comment count
    print(f"\n🏆 TOP SUBREDDITS BY COMMENT ACTIVITY:")
    for i, (subreddit, count) in enumerate(subreddit_counts.most_common(10), 1):
        print(f"  {i:2d}. r/{subreddit} - {count} comments")
    
    # Recent activity
    print(f"\n⏰ RECENT COMMENTS (Last 5):")
    for comment in comment_details[:5]:
        print(f"  • r/{comment['subreddit']} - {comment['created']}")
        print(f"    Post: {comment['post_title'][:60]}...")
        print(f"    Comment: {comment['comment_text']}")
        print(f"    Score: {comment['score']} | URL: {comment['url']}")
        print()
    
    # Subscribed subreddits
    print(f"📋 YOUR SUBSCRIBED SUBREDDITS (First 15):")
    for i, sub in enumerate(subscribed_subreddits[:15], 1):
        print(f"  {i:2d}. r/{sub['display_name']} ({sub['subscribers']:,} subscribers)")
        if sub['description']:
            print(f"      {sub['description']}")
        print()
    
    if len(subscribed_subreddits) > 15:
        print(f"     ... and {len(subscribed_subreddits) - 15} more subreddits")

def save_activity_data(comment_details, subreddit_counts, subscribed_subreddits):
    """Save activity data to JSON file"""
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    # Create output directory
    os.makedirs('data/my_activity', exist_ok=True)
    
    # Prepare data for saving
    activity_data = {
        'analysis_date': datetime.now(timezone.utc).isoformat(),
        'total_comments': len(comment_details),
        'unique_subreddits_commented': len(subreddit_counts),
        'total_subscribed_subreddits': len(subscribed_subreddits),
        'comment_activity_by_subreddit': dict(subreddit_counts),
        'recent_comments': comment_details[:50],  # Last 50 comments
        'subscribed_subreddits': subscribed_subreddits
    }
    
    # Save to file
    filename = f"data/my_activity/my_reddit_activity_{timestamp}.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(activity_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Activity data saved to: {filename}")
    return filename

def main():
    """Main function"""
    print("🚀 Starting Reddit Activity Analysis...")
    print("This will analyze your commenting history and subscribed subreddits")
    print()
    
    try:
        # Connect to Reddit
        reddit, user = connect_to_reddit()
        
        # Get your comments
        comment_details, subreddit_counts = get_my_comments(reddit, user, limit=1000)
        
        # Get subscribed subreddits
        subscribed_subreddits = get_my_subreddits(reddit, user)
        
        # Print summary
        print_activity_summary(comment_details, subreddit_counts, subscribed_subreddits)
        
        # Save data
        filename = save_activity_data(comment_details, subreddit_counts, subscribed_subreddits)
        
        print(f"\n✅ Analysis complete! Data saved to: {filename}")
        print("💡 You can now see exactly where you've been commenting and which subreddits you follow!")
        
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        print("💡 Make sure your Reddit API credentials are correct in the .env file")

if __name__ == "__main__":
    main()
