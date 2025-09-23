#!/usr/bin/env python3
"""
Reddit Account Analyzer
Analyzes user's Reddit activity to build comprehensive account profiles
"""

import praw
import json
import os
from datetime import datetime, timezone
from collections import Counter, defaultdict
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class RedditAccountAnalyzer:
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Reddit Account Analyzer v1.0')
        )
        print("✅ Reddit API connection established")
    
    def fetch_user_comment_history(self, username, limit=1000):
        """Fetch user's recent comments with metadata"""
        print(f"🔍 Fetching comment history for u/{username}...")
        
        try:
            user = self.reddit.redditor(username)
            comments = []
            
            for comment in user.comments.new(limit=limit):
                comment_data = {
                    'id': comment.id,
                    'subreddit': str(comment.subreddit),
                    'subreddit_display': comment.subreddit.display_name,
                    'post_title': comment.submission.title if hasattr(comment, 'submission') else 'Unknown',
                    'comment_text': comment.body,
                    'comment_length': len(comment.body),
                    'score': comment.score,
                    'created_utc': comment.created_utc,
                    'created_human': datetime.fromtimestamp(comment.created_utc, tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'),
                    'permalink': f"https://reddit.com{comment.permalink}",
                    'is_submitter': comment.is_submitter,
                    'controversiality': comment.controversiality,
                    'gilded': comment.gilded
                }
                comments.append(comment_data)
            
            print(f"✅ Fetched {len(comments)} comments")
            return comments
            
        except Exception as e:
            print(f"❌ Error fetching comments for u/{username}: {e}")
            return []
    
    def analyze_subreddit_patterns(self, comments):
        """Identify which subreddits user is most active in"""
        print("📊 Analyzing subreddit participation patterns...")
        
        subreddit_activity = Counter()
        subreddit_karma = defaultdict(int)
        subreddit_engagement = defaultdict(list)
        
        for comment in comments:
            subreddit = comment['subreddit']
            subreddit_activity[subreddit] += 1
            subreddit_karma[subreddit] += comment['score']
            subreddit_engagement[subreddit].append(comment['score'])
        
        # Calculate engagement metrics
        subreddit_stats = {}
        for subreddit, scores in subreddit_engagement.items():
            subreddit_stats[subreddit] = {
                'comment_count': subreddit_activity[subreddit],
                'total_karma': subreddit_karma[subreddit],
                'avg_score': sum(scores) / len(scores) if scores else 0,
                'max_score': max(scores) if scores else 0,
                'engagement_rate': len([s for s in scores if s > 0]) / len(scores) if scores else 0
            }
        
        return {
            'top_subreddits': subreddit_activity.most_common(20),
            'subreddit_stats': subreddit_stats,
            'total_unique_subreddits': len(subreddit_activity)
        }
    
    def extract_expertise_themes(self, comments):
        """Use keyword analysis to identify recurring topics user discusses"""
        print("🧠 Extracting expertise themes...")
        
        # Define expertise categories and keywords
        expertise_categories = {
            'skincare': [
                'routine', 'cleanser', 'moisturizer', 'serum', 'acne', 'pimples', 'blackheads',
                'dry skin', 'oily skin', 'combination skin', 'sensitive skin', 'exfoliation',
                'retinol', 'vitamin c', 'niacinamide', 'hyaluronic acid', 'sunscreen', 'spf'
            ],
            'haircare': [
                'hair', 'shampoo', 'conditioner', 'curly hair', 'straight hair', 'hair loss',
                'dandruff', 'scalp', 'hair growth', 'hair care', 'styling', 'products'
            ],
            'ingredients': [
                'ingredient', 'active', 'chemical', 'natural', 'organic', 'synthetic',
                'formulation', 'compound', 'molecule', 'extract', 'oil', 'acid'
            ],
            'products': [
                'brand', 'product', 'recommendation', 'review', 'rating', 'price',
                'affordable', 'budget', 'expensive', 'luxury', 'drugstore', 'high-end'
            ],
            'problems': [
                'problem', 'issue', 'trouble', 'help', 'advice', 'solution', 'fix',
                'treat', 'cure', 'heal', 'improve', 'better', 'worse'
            ],
            'routine': [
                'morning', 'evening', 'night', 'daily', 'weekly', 'step', 'order',
                'sequence', 'timing', 'schedule', 'habit', 'consistency'
            ]
        }
        
        # Analyze comment text for expertise themes
        theme_scores = defaultdict(int)
        theme_mentions = defaultdict(list)
        
        for comment in comments:
            comment_text = comment['comment_text'].lower()
            comment_score = comment['score']
            
            for category, keywords in expertise_categories.items():
                matches = [keyword for keyword in keywords if keyword in comment_text]
                if matches:
                    theme_scores[category] += len(matches) * (1 + comment_score * 0.1)
                    theme_mentions[category].extend(matches)
        
        # Calculate confidence scores
        total_theme_score = sum(theme_scores.values())
        expertise_confidence = {}
        
        for category, score in theme_scores.items():
            confidence = (score / total_theme_score) * 100 if total_theme_score > 0 else 0
            expertise_confidence[category] = {
                'confidence_score': round(confidence, 2),
                'mentions': len(set(theme_mentions[category])),
                'unique_keywords': list(set(theme_mentions[category]))
            }
        
        return expertise_confidence
    
    def analyze_engagement_success(self, comments):
        """Find patterns in highly-upvoted comments"""
        print("📈 Analyzing engagement success patterns...")
        
        # Categorize comments by score
        high_score_comments = [c for c in comments if c['score'] >= 5]
        medium_score_comments = [c for c in comments if 2 <= c['score'] < 5]
        low_score_comments = [c for c in comments if c['score'] < 2]
        
        # Analyze patterns in successful comments
        success_patterns = {
            'high_score_characteristics': self._analyze_comment_characteristics(high_score_comments),
            'medium_score_characteristics': self._analyze_comment_characteristics(medium_score_comments),
            'low_score_characteristics': self._analyze_comment_characteristics(low_score_comments),
            'success_metrics': {
                'high_score_count': len(high_score_comments),
                'medium_score_count': len(medium_score_comments),
                'low_score_count': len(low_score_comments),
                'avg_score': sum(c['score'] for c in comments) / len(comments) if comments else 0,
                'success_rate': len(high_score_comments) / len(comments) if comments else 0
            }
        }
        
        return success_patterns
    
    def _analyze_comment_characteristics(self, comments):
        """Analyze characteristics of a group of comments"""
        if not comments:
            return {}
        
        # Analyze comment length patterns
        lengths = [c['comment_length'] for c in comments]
        avg_length = sum(lengths) / len(lengths)
        
        # Analyze subreddit patterns
        subreddits = [c['subreddit'] for c in comments]
        subreddit_counts = Counter(subreddits)
        
        # Analyze time patterns
        hours = [datetime.fromtimestamp(c['created_utc'], tz=timezone.utc).hour for c in comments]
        hour_counts = Counter(hours)
        
        return {
            'avg_comment_length': round(avg_length, 2),
            'top_subreddits': subreddit_counts.most_common(5),
            'peak_hours': hour_counts.most_common(3),
            'comment_count': len(comments)
        }
    
    def detect_user_tone(self, comments):
        """Analyze writing style and tone patterns"""
        print("🎭 Analyzing user tone and writing style...")
        
        # Analyze comment length patterns
        lengths = [c['comment_length'] for c in comments]
        avg_length = sum(lengths) / len(lengths) if lengths else 0
        
        # Analyze writing style indicators
        style_indicators = {
            'average_comment_length': avg_length,
            'long_comments_ratio': len([c for c in comments if c['comment_length'] > 200]) / len(comments) if comments else 0,
            'short_comments_ratio': len([c for c in comments if c['comment_length'] < 50]) / len(comments) if comments else 0,
            'question_ratio': len([c for c in comments if '?' in c['comment_text']]) / len(comments) if comments else 0,
            'exclamation_ratio': len([c for c in comments if '!' in c['comment_text']]) / len(comments) if comments else 0,
            'emoji_usage': len([c for c in comments if any(ord(char) > 127 for char in c['comment_text'])]) / len(comments) if comments else 0
        }
        
        # Determine tone characteristics
        tone_profile = {
            'writing_style': 'detailed' if avg_length > 100 else 'concise' if avg_length < 50 else 'balanced',
            'engagement_style': 'questioning' if style_indicators['question_ratio'] > 0.3 else 'informative',
            'formality': 'casual' if style_indicators['emoji_usage'] > 0.1 else 'professional',
            'verbosity': 'verbose' if style_indicators['long_comments_ratio'] > 0.3 else 'succinct'
        }
        
        return {
            'style_indicators': style_indicators,
            'tone_profile': tone_profile
        }
    
    def generate_account_profile(self, username, comments_limit=1000):
        """Generate comprehensive account profile"""
        print(f"🚀 Starting comprehensive analysis for u/{username}")
        print(f"📊 Analyzing {comments_limit} recent comments...")
        
        # Fetch comment history
        comments = self.fetch_user_comment_history(username, comments_limit)
        
        if not comments:
            print(f"❌ No comments found for u/{username}")
            return None
        
        # Run all analyses
        subreddit_analysis = self.analyze_subreddit_patterns(comments)
        expertise_analysis = self.extract_expertise_themes(comments)
        engagement_analysis = self.analyze_engagement_success(comments)
        tone_analysis = self.detect_user_tone(comments)
        
        # Generate comprehensive profile
        account_profile = {
            'account_info': {
                'username': username,
                'analysis_date': datetime.now(timezone.utc).isoformat(),
                'comments_analyzed': len(comments),
                'analysis_period': f"Last {comments_limit} comments"
            },
            'subreddit_activity': subreddit_analysis,
            'expertise_areas': expertise_analysis,
            'engagement_patterns': engagement_analysis,
            'tone_profile': tone_analysis,
            'recommendations': self._generate_recommendations(
                subreddit_analysis, expertise_analysis, engagement_analysis, tone_analysis
            )
        }
        
        print(f"✅ Account analysis complete for u/{username}")
        return account_profile
    
    def _generate_recommendations(self, subreddit_analysis, expertise_analysis, engagement_analysis, tone_analysis):
        """Generate personalized recommendations based on analysis"""
        recommendations = {
            'focus_subreddits': [sub[0] for sub in subreddit_analysis['top_subreddits'][:5]],
            'expertise_strengths': [area for area, data in expertise_analysis.items() if data['confidence_score'] > 20],
            'engagement_tips': [],
            'content_suggestions': []
        }
        
        # Generate engagement tips based on success patterns
        success_rate = engagement_analysis['success_metrics']['success_rate']
        if success_rate < 0.3:
            recommendations['engagement_tips'].append("Focus on providing detailed, helpful responses")
        elif success_rate > 0.7:
            recommendations['engagement_tips'].append("Continue your current successful engagement strategy")
        
        # Generate content suggestions based on expertise
        top_expertise = sorted(expertise_analysis.items(), key=lambda x: x[1]['confidence_score'], reverse=True)[:3]
        for area, data in top_expertise:
            if data['confidence_score'] > 15:
                recommendations['content_suggestions'].append(f"Share more insights about {area}")
        
        return recommendations
    
    def save_account_profile(self, profile, username):
        """Save account profile to file"""
        # Create accounts directory if it doesn't exist
        os.makedirs('config/accounts', exist_ok=True)
        
        filename = f"config/accounts/{username}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Account profile saved to: {filename}")
        return filename

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python account_analyzer.py <username> [comments_limit]")
        print("Example: python account_analyzer.py dotconsistent3677 1000")
        sys.exit(1)
    
    username = sys.argv[1]
    comments_limit = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    
    try:
        analyzer = RedditAccountAnalyzer()
        profile = analyzer.generate_account_profile(username, comments_limit)
        
        if profile:
            analyzer.save_account_profile(profile, username)
            print(f"\n🎉 Analysis complete! Profile saved for u/{username}")
        else:
            print(f"❌ Failed to generate profile for u/{username}")
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        raise

if __name__ == "__main__":
    main()
