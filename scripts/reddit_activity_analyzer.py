#!/usr/bin/env python3
"""
Reddit Activity Analyzer
Analyzes your Reddit commenting history and subreddit activity
"""

import praw
import json
import os
from datetime import datetime, timezone
from collections import defaultdict, Counter
import argparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditActivityAnalyzer:
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Reddit Activity Analyzer v1.0'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD')
        )
        
        # Verify connection
        try:
            self.user = self.reddit.user.me()
            print(f"✅ Connected as: {self.user.name}")
        except Exception as e:
            print(f"❌ Failed to connect to Reddit: {e}")
            exit(1)
    
    def analyze_comments(self, limit=1000):
        """Analyze your comment history"""
        print(f"🔍 Analyzing your last {limit} comments...")
        
        comments_data = []
        subreddit_activity = defaultdict(int)
        comment_karma_by_subreddit = defaultdict(int)
        comment_timeline = []
        
        for comment in self.user.comments.new(limit=limit):
            comment_data = {
                'id': comment.id,
                'subreddit': str(comment.subreddit),
                'subreddit_display_name': comment.subreddit.display_name,
                'post_title': comment.submission.title if hasattr(comment, 'submission') else 'Unknown',
                'post_url': f"https://reddit.com{comment.permalink}",
                'comment_text': comment.body[:200] + '...' if len(comment.body) > 200 else comment.body,
                'score': comment.score,
                'created_utc': comment.created_utc,
                'created_human': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'is_submitter': comment.is_submitter,
                'controversiality': comment.controversiality,
                'gilded': comment.gilded
            }
            
            comments_data.append(comment_data)
            
            # Track subreddit activity
            subreddit_activity[str(comment.subreddit)] += 1
            comment_karma_by_subreddit[str(comment.subreddit)] += comment.score
            
            # Track timeline
            comment_timeline.append({
                'date': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d'),
                'subreddit': str(comment.subreddit),
                'score': comment.score
            })
        
        return {
            'comments': comments_data,
            'subreddit_activity': dict(subreddit_activity),
            'comment_karma_by_subreddit': dict(comment_karma_by_subreddit),
            'timeline': comment_timeline
        }
    
    def analyze_submissions(self, limit=500):
        """Analyze your submission history"""
        print(f"📝 Analyzing your last {limit} submissions...")
        
        submissions_data = []
        subreddit_submissions = defaultdict(int)
        
        for submission in self.user.submissions.new(limit=limit):
            submission_data = {
                'id': submission.id,
                'subreddit': str(submission.subreddit),
                'subreddit_display_name': submission.subreddit.display_name,
                'title': submission.title,
                'url': submission.url,
                'selftext': submission.selftext[:200] + '...' if len(submission.selftext) > 200 else submission.selftext,
                'score': submission.score,
                'num_comments': submission.num_comments,
                'created_utc': submission.created_utc,
                'created_human': datetime.fromtimestamp(submission.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                'is_self': submission.is_self,
                'over_18': submission.over_18,
                'gilded': submission.gilded
            }
            
            submissions_data.append(submission_data)
            subreddit_submissions[str(submission.subreddit)] += 1
        
        return {
            'submissions': submissions_data,
            'subreddit_submissions': dict(subreddit_submissions)
        }
    
    def get_subscribed_subreddits(self):
        """Get list of subreddits you're subscribed to"""
        print("📋 Fetching subscribed subreddits...")
        
        subscribed_subreddits = []
        for subreddit in self.user.subreddits.new(limit=None):
            subreddit_info = {
                'name': str(subreddit),
                'display_name': subreddit.display_name,
                'subscribers': subreddit.subscribers,
                'description': subreddit.description[:100] + '...' if len(subreddit.description) > 100 else subreddit.description,
                'public_description': subreddit.public_description[:100] + '...' if len(subreddit.public_description) > 100 else subreddit.public_description,
                'over18': subreddit.over18,
                'subreddit_type': subreddit.subreddit_type
            }
            subscribed_subreddits.append(subreddit_info)
        
        return subscribed_subreddits
    
    def generate_activity_report(self, comments_limit=1000, submissions_limit=500):
        """Generate comprehensive activity report"""
        print("🚀 Starting Reddit Activity Analysis...")
        print(f"📊 Analyzing {comments_limit} comments and {submissions_limit} submissions")
        
        # Analyze comments
        comments_analysis = self.analyze_comments(comments_limit)
        
        # Analyze submissions
        submissions_analysis = self.analyze_submissions(submissions_limit)
        
        # Get subscribed subreddits
        subscribed_subreddits = self.get_subscribed_subreddits()
        
        # Generate summary statistics
        total_comments = len(comments_analysis['comments'])
        total_submissions = len(submissions_analysis['submissions'])
        total_subscribed = len(subscribed_subreddits)
        
        # Top subreddits by activity
        top_comment_subreddits = Counter(comments_analysis['subreddit_activity']).most_common(10)
        top_submission_subreddits = Counter(submissions_analysis['subreddit_submissions']).most_common(10)
        
        # Karma analysis
        total_comment_karma = sum(comment['score'] for comment in comments_analysis['comments'])
        total_submission_karma = sum(submission['score'] for submission in submissions_analysis['submissions'])
        
        # Create comprehensive report
        report = {
            'analysis_metadata': {
                'analyzed_at': datetime.now(timezone.utc).isoformat(),
                'reddit_username': self.user.name,
                'comments_analyzed': total_comments,
                'submissions_analyzed': total_submissions,
                'subreddits_subscribed': total_subscribed
            },
            'summary_stats': {
                'total_comments': total_comments,
                'total_submissions': total_submissions,
                'total_subscribed_subreddits': total_subscribed,
                'total_comment_karma': total_comment_karma,
                'total_submission_karma': total_submission_karma,
                'total_karma': total_comment_karma + total_submission_karma
            },
            'top_comment_subreddits': [
                {'subreddit': sub, 'comment_count': count} 
                for sub, count in top_comment_subreddits
            ],
            'top_submission_subreddits': [
                {'subreddit': sub, 'submission_count': count} 
                for sub, count in top_submission_subreddits
            ],
            'comment_karma_by_subreddit': comments_analysis['comment_karma_by_subreddit'],
            'recent_comments': comments_analysis['comments'][:20],  # Last 20 comments
            'recent_submissions': submissions_analysis['submissions'][:20],  # Last 20 submissions
            'subscribed_subreddits': subscribed_subreddits,
            'activity_timeline': comments_analysis['timeline'][-30:]  # Last 30 days
        }
        
        return report
    
    def save_report(self, report, filename=None):
        """Save report to JSON file"""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"reddit_activity_report_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs('data/activity_analysis', exist_ok=True)
        filepath = f"data/activity_analysis/{filename}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Report saved to: {filepath}")
        return filepath
    
    def print_summary(self, report):
        """Print a summary of the analysis"""
        print("\n" + "="*60)
        print("📊 REDDIT ACTIVITY SUMMARY")
        print("="*60)
        
        stats = report['summary_stats']
        print(f"👤 Username: {report['analysis_metadata']['reddit_username']}")
        print(f"💬 Total Comments: {stats['total_comments']:,}")
        print(f"📝 Total Submissions: {stats['total_submissions']:,}")
        print(f"📋 Subscribed Subreddits: {stats['total_subscribed_subreddits']:,}")
        print(f"⬆️  Total Karma: {stats['total_karma']:,}")
        print(f"💬 Comment Karma: {stats['total_comment_karma']:,}")
        print(f"📝 Submission Karma: {stats['total_submission_karma']:,}")
        
        print("\n🏆 TOP COMMENT SUBREDDITS:")
        for i, item in enumerate(report['top_comment_subreddits'][:5], 1):
            print(f"  {i}. r/{item['subreddit']} - {item['comment_count']} comments")
        
        print("\n📝 TOP SUBMISSION SUBREDDITS:")
        for i, item in enumerate(report['top_submission_subreddits'][:5], 1):
            print(f"  {i}. r/{item['subreddit']} - {item['submission_count']} submissions")
        
        print("\n📋 RECENTLY SUBSCRIBED SUBREDDITS:")
        for sub in report['subscribed_subreddits'][:10]:
            print(f"  • r/{sub['display_name']} ({sub['subscribers']:,} subscribers)")
        
        print("\n" + "="*60)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Analyze Reddit activity and subreddit subscriptions')
    parser.add_argument('--comments-limit', type=int, default=1000, 
                       help='Number of recent comments to analyze (default: 1000)')
    parser.add_argument('--submissions-limit', type=int, default=500,
                       help='Number of recent submissions to analyze (default: 500)')
    parser.add_argument('--output', type=str, default=None,
                       help='Output filename (default: auto-generated)')
    parser.add_argument('--no-save', action='store_true',
                       help='Don\'t save report to file, just print summary')
    
    args = parser.parse_args()
    
    try:
        # Initialize analyzer
        analyzer = RedditActivityAnalyzer()
        
        # Generate report
        report = analyzer.generate_activity_report(
            comments_limit=args.comments_limit,
            submissions_limit=args.submissions_limit
        )
        
        # Print summary
        analyzer.print_summary(report)
        
        # Save report if requested
        if not args.no_save:
            filepath = analyzer.save_report(report, args.output)
            print(f"\n✅ Analysis complete! Report saved to: {filepath}")
        else:
            print("\n✅ Analysis complete!")
            
    except KeyboardInterrupt:
        print("\n⏹️  Analysis interrupted by user")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
