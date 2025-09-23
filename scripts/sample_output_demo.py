#!/usr/bin/env python3
"""
Sample Output Demo for Reddit Activity Analysis
Shows what the output will look like without requiring Reddit API access
"""

import json
import os
from datetime import datetime, timezone

def create_sample_output():
    """Create a sample output to show what the analysis will look like"""
    
    # Sample data structure
    sample_data = {
        'analysis_date': datetime.now(timezone.utc).isoformat(),
        'total_comments': 247,
        'unique_subreddits_commented': 23,
        'total_subscribed_subreddits': 45,
        'comment_activity_by_subreddit': {
            'SkincareAddiction': 89,
            'curlyhair': 67,
            'IndianSkincareAddicts': 34,
            'skincareaddictsindia': 28,
            'Hair': 15,
            'SkincareAddicts': 8,
            'beauty': 3,
            'MakeupAddiction': 2
        },
        'recent_comments': [
            {
                'subreddit': 'SkincareAddiction',
                'subreddit_display': 'SkincareAddiction',
                'post_title': 'Routine Help: I\'m at a total loss of what is destroying my skin',
                'comment_text': 'Have you tried switching to a gentler cleanser? Sometimes harsh products can cause more damage...',
                'score': 12,
                'created': '2025-09-23 05:30',
                'url': 'https://reddit.com/r/SkincareAddiction/comments/1nnnecy/routine_help/abc123/'
            },
            {
                'subreddit': 'curlyhair',
                'subreddit_display': 'curlyhair',
                'post_title': 'I love my curls 🩷',
                'comment_text': 'Your curls look amazing! What products are you using? I\'m struggling with frizz...',
                'score': 8,
                'created': '2025-09-23 04:15',
                'url': 'https://reddit.com/r/curlyhair/comments/1nnnecy/i_love_my_curls/def456/'
            },
            {
                'subreddit': 'IndianSkincareAddicts',
                'subreddit_display': 'IndianSkincareAddicts',
                'post_title': 'Need budget skincare recs for tiny bumps',
                'comment_text': 'Try The Ordinary Niacinamide 10% + Zinc 1%. It\'s affordable and works great for texture issues.',
                'score': 15,
                'created': '2025-09-23 03:45',
                'url': 'https://reddit.com/r/IndianSkincareAddicts/comments/1nnpf0f/budget_skincare/ghi789/'
            }
        ],
        'subscribed_subreddits': [
            {
                'name': 'SkincareAddiction',
                'display_name': 'SkincareAddiction',
                'subscribers': 4500000,
                'description': 'Skincare advice, product reviews, and routine help for all skin types',
                'type': 'public',
                'over18': False
            },
            {
                'name': 'curlyhair',
                'display_name': 'curlyhair',
                'subscribers': 1200000,
                'description': 'A community for people with curly, wavy, and coily hair to share tips and support',
                'type': 'public',
                'over18': False
            },
            {
                'name': 'IndianSkincareAddicts',
                'display_name': 'IndianSkincareAddicts',
                'subscribers': 89000,
                'description': 'Skincare community focused on Indian beauty products and routines',
                'type': 'public',
                'over18': False
            }
        ]
    }
    
    return sample_data

def show_data_storage_structure():
    """Show where data will be stored"""
    print("📁 DATA STORAGE STRUCTURE")
    print("="*50)
    print()
    print("The Reddit activity analysis will store data in:")
    print()
    print("📂 data/my_activity/")
    print("   ├── my_reddit_activity_YYYYMMDD_HHMMSS.json")
    print("   ├── my_reddit_activity_YYYYMMDD_HHMMSS.json")
    print("   └── ... (timestamped files for each analysis)")
    print()
    print("📂 data/activity_analysis/")
    print("   ├── reddit_activity_report_YYYYMMDD_HHMMSS.json")
    print("   ├── reddit_activity_report_YYYYMMDD_HHMMSS.json")
    print("   └── ... (comprehensive reports)")
    print()
    print("Each file contains:")
    print("• Your comment history")
    print("• Subreddit activity counts")
    print("• Subscribed subreddits list")
    print("• Activity timeline")
    print("• Karma statistics")

def show_sample_output():
    """Show what the output will look like"""
    print("\n" + "="*70)
    print("📊 SAMPLE REDDIT ACTIVITY OUTPUT")
    print("="*70)
    
    sample_data = create_sample_output()
    
    print(f"💬 Total Comments Analyzed: {sample_data['total_comments']:,}")
    print(f"🏠 Unique Subreddits You've Commented In: {sample_data['unique_subreddits_commented']:,}")
    print(f"📋 Subreddits You're Subscribed To: {sample_data['total_subscribed_subreddits']:,}")
    
    print(f"\n🏆 TOP SUBREDDITS BY COMMENT ACTIVITY:")
    for i, (subreddit, count) in enumerate(sample_data['comment_activity_by_subreddit'].items(), 1):
        print(f"  {i:2d}. r/{subreddit} - {count} comments")
    
    print(f"\n⏰ RECENT COMMENTS (Last 3):")
    for comment in sample_data['recent_comments']:
        print(f"  • r/{comment['subreddit']} - {comment['created']}")
        print(f"    Post: {comment['post_title']}")
        print(f"    Comment: {comment['comment_text']}")
        print(f"    Score: {comment['score']} | URL: {comment['url']}")
        print()
    
    print(f"📋 YOUR SUBSCRIBED SUBREDDITS (First 3):")
    for i, sub in enumerate(sample_data['subscribed_subreddits'], 1):
        print(f"  {i:2d}. r/{sub['display_name']} ({sub['subscribers']:,} subscribers)")
        print(f"      {sub['description']}")
        print()

def show_json_structure():
    """Show the JSON structure of the output"""
    print("\n" + "="*70)
    print("📄 JSON OUTPUT STRUCTURE")
    print("="*70)
    
    sample_data = create_sample_output()
    
    print("The analysis creates JSON files with this structure:")
    print()
    print(json.dumps(sample_data, indent=2)[:1000] + "...")
    print()
    print("Key fields:")
    print("• analysis_date: When the analysis was run")
    print("• total_comments: Number of comments analyzed")
    print("• comment_activity_by_subreddit: Count of comments per subreddit")
    print("• recent_comments: Array of recent comment details")
    print("• subscribed_subreddits: Array of subreddits you follow")

def main():
    """Main demo function"""
    print("🔍 REDDIT ACTIVITY ANALYSIS - DATA STORAGE & OUTPUT DEMO")
    print("="*70)
    
    show_data_storage_structure()
    show_sample_output()
    show_json_structure()
    
    print("\n" + "="*70)
    print("🚀 TO RUN THE ACTUAL ANALYSIS:")
    print("="*70)
    print("1. Set up Reddit API credentials:")
    print("   python scripts/setup_reddit_analysis.py")
    print()
    print("2. Run the analysis:")
    print("   python scripts/reddit_my_activity.py")
    print()
    print("3. Check the output files in:")
    print("   data/my_activity/")
    print()
    print("💡 The analysis will show you exactly where you've commented")
    print("   and which subreddits you're subscribed to!")

if __name__ == "__main__":
    main()
