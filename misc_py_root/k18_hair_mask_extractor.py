#!/usr/bin/env python3
"""
K18 Hair Mask Reddit Data Extractor
Extracts all Reddit posts and comments related to K18 Hair Mask with sentiment analysis.
"""

import os
import json
import requests
import time
from typing import Dict, List, Optional, Tuple
import re
from datetime import datetime

# VADER Sentiment Analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
    print("✓ VADER Sentiment Analysis available")
except ImportError:
    VADER_AVAILABLE = False
    print("⚠ VADER Sentiment Analysis not available. Install with: pip install vaderSentiment")

# Initialize VADER analyzer
if VADER_AVAILABLE:
    vader_analyzer = SentimentIntensityAnalyzer()
else:
    vader_analyzer = None

# Reddit API Configuration
CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
USER_AGENT = 'IngredientAnalysis/1.0 (by /u/your_username)'

# Target ingredient
TARGET_INGREDIENT = "K18 Hair Mask"

def get_reddit_token() -> Optional[str]:
    """Get Reddit access token using client credentials flow."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Reddit API credentials not found in environment variables")
        return None
    
    auth_url = 'https://www.reddit.com/api/v1/access_token'
    auth_data = {
        'grant_type': 'client_credentials'
    }
    
    response = requests.post(
        auth_url,
        data=auth_data,
        auth=(CLIENT_ID, CLIENT_SECRET),
        headers={'User-Agent': USER_AGENT}
    )
    
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"❌ Failed to get access token: {response.status_code}")
        return None

def search_reddit_posts(access_token: str, query: str, subreddits: List[str] = None, limit: int = 100) -> List[Dict]:
    """Search Reddit posts for the given query."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': USER_AGENT
    }
    
    all_posts = []
    
    # If no specific subreddits, search across all of Reddit
    if not subreddits:
        search_url = f'https://oauth.reddit.com/search'
        params = {
            'q': query,
            'type': 'link',
            'limit': limit,
            'sort': 'relevance',
            't': 'all'
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            posts = data['data']['children']
            all_posts.extend([post['data'] for post in posts])
    else:
        # Search in specific subreddits
        for subreddit in subreddits:
            search_url = f'https://oauth.reddit.com/r/{subreddit}/search'
            params = {
                'q': query,
                'type': 'link',
                'limit': limit,
                'sort': 'relevance',
                't': 'all'
            }
            
            response = requests.get(search_url, headers=headers, params=params)
            if response.status_code == 200:
                data = response.json()
                posts = data['data']['children']
                all_posts.extend([post['data'] for post in posts])
            
            time.sleep(1)  # Rate limiting
    
    return all_posts

def fetch_post_comments(access_token: str, post_id: str, max_comments: int = 30, 
                       post_context: Dict = None, target_ingredient: str = None, 
                       min_sample_size: int = 385) -> Tuple[List, Dict, bool]:
    """Fetch comments for a specific post with sentiment analysis."""
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': USER_AGENT
    }
    
    # Get post comments
    comments_url = f'https://oauth.reddit.com/comments/{post_id}'
    params = {
        'limit': max_comments,
        'depth': 1  # Only top-level comments
    }
    
    response = requests.get(comments_url, headers=headers, params=params)
    if response.status_code != 200:
        return [], {}, False
    
    data = response.json()
    if len(data) < 2:
        return [], {}, False
    
    # Extract comments from the second element (first is the post, second is comments)
    comments_data = data[1]['data']['children']
    comments = []
    
    for comment in comments_data:
        if comment['kind'] == 't1':  # Comment type
            comment_data = comment['data']
            if comment_data.get('body') and comment_data['body'] != '[deleted]':
                # Analyze comment sentiment
                sentiment_analysis = analyze_comment_sentiment(
                    comment_data, post_context, target_ingredient
                )
                comment_data['sentiment_analysis'] = sentiment_analysis
                comments.append(comment_data)
    
    # Determine if post is significant (has at least 5 comments)
    is_significant = len(comments) >= 5
    
    if is_significant:
        # Analyze top 30 comments for significant posts
        top_comments = comments[:30]
        post_sentiment = aggregate_post_sentiment(post_context, top_comments, target_ingredient)
    else:
        # For insignificant posts, analyze post content only
        post_sentiment = analyze_post_only_sentiment(post_context, target_ingredient)
    
    return comments, post_sentiment, is_significant

def analyze_comment_sentiment(comment_data: Dict, post_context: Dict = None, 
                            target_ingredient: str = None) -> Dict:
    """Analyze sentiment of a single comment using VADER."""
    text = comment_data.get('body', '')
    if not text:
        return {'sentiment': 'neutral', 'confidence': 0.0}
    
    # Check if comment is ingredient-specific
    is_ingredient_specific = is_ingredient_specific_comment(text, post_context, target_ingredient)
    
    if VADER_AVAILABLE and vader_analyzer:
        # Use VADER for sentiment analysis
        vader_scores = vader_analyzer.polarity_scores(text)
        
        # Determine sentiment category
        compound = vader_scores['compound']
        if compound >= 0.05:
            sentiment_category = 'positive'
        elif compound <= -0.05:
            sentiment_category = 'negative'
        else:
            sentiment_category = 'neutral'
        
        # Calculate confidence based on compound score magnitude
        confidence = abs(compound)
        
        # Weighted score considering comment score
        comment_score = comment_data.get('score', 0)
        weighted_score = compound * (1 + comment_score / 100)  # Normalize score impact
        
        return {
            'vader_scores': vader_scores,
            'sentiment_category': sentiment_category,
            'confidence': confidence,
            'weighted_score': weighted_score,
            'ingredient_specific': is_ingredient_specific,
            'method': 'vader'
        }
    else:
        # Fallback to basic keyword analysis
        text = text.lower()
        positive_words = ['good', 'great', 'amazing', 'love', 'effective', 'works', 'helpful', 'recommend']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'ineffective', 'doesn\'t work', 'waste', 'avoid']
        
        positive_count = sum(1 for word in positive_words if word in text)
        negative_count = sum(1 for word in word in negative_words if word in text)
        
        if positive_count > negative_count:
            sentiment = 'positive'
            confidence = min(0.8, positive_count / 10)
        elif negative_count > positive_count:
            sentiment = 'negative'
            confidence = min(0.8, negative_count / 10)
        else:
            sentiment = 'neutral'
            confidence = 0.3
        
        return {
            'sentiment_category': sentiment,
            'confidence': confidence,
            'ingredient_specific': is_ingredient_specific,
            'method': 'keyword_fallback'
        }

def is_ingredient_specific_comment(comment_text: str, post_context: Dict = None, 
                                 target_ingredient: str = None) -> bool:
    """Determine if a comment is specifically about the target ingredient."""
    if not target_ingredient:
        return True
    
    # Check if ingredient is mentioned in comment
    ingredient_mentions = [
        'k18', 'k-18', 'k 18', 'hair mask', 'hair treatment'
    ]
    
    comment_lower = comment_text.lower()
    for mention in ingredient_mentions:
        if mention in comment_lower:
            return True
    
    # Check post context if available
    if post_context:
        post_title = post_context.get('title', '').lower()
        post_body = post_context.get('selftext', '').lower()
        
        for mention in ingredient_mentions:
            if mention in post_title or mention in post_body:
                return True
    
    return False

def aggregate_post_sentiment(post_data: Dict, comments: List, target_ingredient: str = None) -> Dict:
    """Aggregate sentiment from comments for a post."""
    if not comments:
        return analyze_post_only_sentiment(post_data, target_ingredient)
    
    # Calculate overall sentiment
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    compound_scores = []
    ingredient_specific_scores = []
    
    for comment in comments:
        sentiment = comment.get('sentiment_analysis', {})
        category = sentiment.get('sentiment_category', 'neutral')
        sentiment_counts[category] += 1
        
        if 'vader_scores' in sentiment:
            compound_scores.append(sentiment['vader_scores']['compound'])
        
        if sentiment.get('ingredient_specific', False):
            if 'vader_scores' in sentiment:
                ingredient_specific_scores.append(sentiment['vader_scores']['compound'])
    
    # Determine overall sentiment
    total_comments = len(comments)
    if total_comments == 0:
        overall_sentiment = 'neutral'
    else:
        max_count = max(sentiment_counts.values())
        if sentiment_counts['positive'] == max_count:
            overall_sentiment = 'positive'
        elif sentiment_counts['negative'] == max_count:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
    
    # Calculate weighted average compound score
    weighted_avg_compound = 0.0
    if compound_scores:
        weighted_avg_compound = sum(compound_scores) / len(compound_scores)
    
    # Calculate ingredient-specific sentiment
    ingredient_specific_sentiment = 'neutral'
    if ingredient_specific_scores:
        avg_ingredient_score = sum(ingredient_specific_scores) / len(ingredient_specific_scores)
        if avg_ingredient_score >= 0.05:
            ingredient_specific_sentiment = 'positive'
        elif avg_ingredient_score <= -0.05:
            ingredient_specific_sentiment = 'negative'
    
    # Calculate confidence
    sentiment_confidence = max(sentiment_counts.values()) / total_comments if total_comments > 0 else 0.0
    
    # Get top sentiment comments
    top_sentiment_comments = sorted(
        comments, 
        key=lambda x: x.get('sentiment_analysis', {}).get('confidence', 0),
        reverse=True
    )[:3]
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_distribution': sentiment_counts,
        'weighted_average_compound': weighted_avg_compound,
        'ingredient_specific_sentiment': ingredient_specific_sentiment,
        'sentiment_confidence': sentiment_confidence,
        'top_sentiment_comments': [
            {
                'id': c.get('id'),
                'body': c.get('body', '')[:200] + '...' if len(c.get('body', '')) > 200 else c.get('body', ''),
                'sentiment': c.get('sentiment_analysis', {}).get('sentiment_category', 'neutral'),
                'confidence': c.get('sentiment_analysis', {}).get('confidence', 0.0)
            }
            for c in top_sentiment_comments
        ]
    }

def analyze_post_only_sentiment(post_data: Dict, target_ingredient: str = None) -> Dict:
    """Analyze sentiment based only on post content."""
    title = post_data.get('title', '')
    body = post_data.get('selftext', '')
    text = f"{title} {body}".strip()
    
    if not text:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 1},
            'weighted_average_compound': 0.0,
            'ingredient_specific_sentiment': 'neutral',
            'sentiment_confidence': 0.0,
            'top_sentiment_comments': []
        }
    
    # Analyze post sentiment
    if VADER_AVAILABLE and vader_analyzer:
        vader_scores = vader_analyzer.polarity_scores(text)
        compound = vader_scores['compound']
        
        if compound >= 0.05:
            sentiment = 'positive'
        elif compound <= -0.05:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'overall_sentiment': sentiment,
            'sentiment_distribution': {'positive': 1 if sentiment == 'positive' else 0, 
                                     'negative': 1 if sentiment == 'negative' else 0, 
                                     'neutral': 1 if sentiment == 'neutral' else 0},
            'weighted_average_compound': compound,
            'ingredient_specific_sentiment': sentiment,
            'sentiment_confidence': abs(compound),
            'top_sentiment_comments': []
        }
    else:
        # Basic keyword analysis
        text_lower = text.lower()
        positive_words = ['good', 'great', 'amazing', 'love', 'effective', 'works', 'helpful', 'recommend']
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'ineffective', 'doesn\'t work', 'waste', 'avoid']
        
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            sentiment = 'positive'
        elif negative_count > positive_count:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        return {
            'overall_sentiment': sentiment,
            'sentiment_distribution': {'positive': 1 if sentiment == 'positive' else 0, 
                                     'negative': 1 if sentiment == 'negative' else 0, 
                                     'neutral': 1 if sentiment == 'neutral' else 0},
            'weighted_average_compound': 0.0,
            'ingredient_specific_sentiment': sentiment,
            'sentiment_confidence': 0.5,
            'top_sentiment_comments': []
        }

def calculate_overall_ingredient_sentiment(all_posts: List, target_ingredient: str = None) -> Dict:
    """Calculate overall sentiment for the ingredient across all posts."""
    if not all_posts:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
            'average_compound_score': 0.0,
            'significant_posts_count': 0,
            'insignificant_posts_count': 0
        }
    
    significant_posts = [post for post in all_posts if post.get('is_significant_for_sentiment', False)]
    insignificant_posts = [post for post in all_posts if not post.get('is_significant_for_sentiment', False)]
    
    # Only use significant posts for overall sentiment calculation
    posts_for_sentiment = significant_posts
    
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    compound_scores = []
    
    for post in posts_for_sentiment:
        post_sentiment = post.get('post_sentiment_analysis', {})
        overall_sentiment = post_sentiment.get('overall_sentiment', 'neutral')
        sentiment_counts[overall_sentiment] += 1
        
        compound_score = post_sentiment.get('weighted_average_compound', 0.0)
        if compound_score != 0.0:
            compound_scores.append(compound_score)
    
    # Determine overall sentiment
    total_posts = len(posts_for_sentiment)
    if total_posts == 0:
        overall_sentiment = 'neutral'
    else:
        max_count = max(sentiment_counts.values())
        if sentiment_counts['positive'] == max_count:
            overall_sentiment = 'positive'
        elif sentiment_counts['negative'] == max_count:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
    
    # Calculate average compound score
    average_compound = sum(compound_scores) / len(compound_scores) if compound_scores else 0.0
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_distribution': sentiment_counts,
        'average_compound_score': average_compound,
        'significant_posts_count': len(significant_posts),
        'insignificant_posts_count': len(insignificant_posts)
    }

def calculate_sentiment_by_subreddit(all_posts: List) -> Dict:
    """Calculate sentiment breakdown by subreddit."""
    subreddit_sentiments = {}
    
    for post in all_posts:
        subreddit = post.get('subreddit', 'unknown')
        if subreddit not in subreddit_sentiments:
            subreddit_sentiments[subreddit] = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        post_sentiment = post.get('post_sentiment_analysis', {})
        sentiment = post_sentiment.get('overall_sentiment', 'neutral')
        subreddit_sentiments[subreddit][sentiment] += 1
    
    return subreddit_sentiments

def extract_effectiveness_sentiment(all_posts: List) -> Dict:
    """Extract sentiment related to effectiveness keywords."""
    effectiveness_keywords = ['effective', 'works', 'results', 'improvement', 'benefit', 'help', 'fix', 'solve']
    
    effectiveness_comments = []
    for post in all_posts:
        comments = post.get('comments', [])
        for comment in comments:
            comment_text = comment.get('body', '').lower()
            if any(keyword in comment_text for keyword in effectiveness_keywords):
                sentiment = comment.get('sentiment_analysis', {}).get('sentiment_category', 'neutral')
                effectiveness_comments.append({
                    'sentiment': sentiment,
                    'text': comment.get('body', '')[:100] + '...' if len(comment.get('body', '')) > 100 else comment.get('body', '')
                })
    
    # Count sentiments
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for comment in effectiveness_comments:
        sentiment_counts[comment['sentiment']] += 1
    
    return {
        'effectiveness_mentions': len(effectiveness_comments),
        'effectiveness_sentiment_distribution': sentiment_counts,
        'sample_effectiveness_comments': effectiveness_comments[:5]  # Top 5 examples
    }

def extract_safety_sentiment(all_posts: List) -> Dict:
    """Extract sentiment related to safety/side effect keywords."""
    safety_keywords = ['safe', 'side effect', 'irritation', 'allergic', 'burning', 'stinging', 'rash', 'reaction']
    
    safety_comments = []
    for post in all_posts:
        comments = post.get('comments', [])
        for comment in comments:
            comment_text = comment.get('body', '').lower()
            if any(keyword in comment_text for keyword in safety_keywords):
                sentiment = comment.get('sentiment_analysis', {}).get('sentiment_category', 'neutral')
                safety_comments.append({
                    'sentiment': sentiment,
                    'text': comment.get('body', '')[:100] + '...' if len(comment.get('body', '')) > 100 else comment.get('body', '')
                })
    
    # Count sentiments
    sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
    for comment in safety_comments:
        sentiment_counts[comment['sentiment']] += 1
    
    return {
        'safety_mentions': len(safety_comments),
        'safety_sentiment_distribution': sentiment_counts,
        'sample_safety_comments': safety_comments[:5]  # Top 5 examples
    }

def main():
    """Main function to extract K18 Hair Mask data."""
    print(f"🔍 Starting K18 Hair Mask Reddit data extraction...")
    
    # Calculate minimum sample size for statistical significance
    # For 95% confidence level, 5% margin of error, p=0.5
    min_sample_size = int(1.96**2 * 0.5 * (1-0.5) / 0.05**2)
    print(f"📊 Minimum sample size for significance: {min_sample_size}")
    
    # Get Reddit access token
    print("🔑 Requesting Reddit access token...")
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get Reddit access token")
        return
    
    print("✅ Reddit access token obtained")
    
    # Define subreddits to search
    subreddits = [
        'HaircareScience', 'Hair', 'curlyhair', 'longhair', 'haircarescience',
        'SkincareAddiction', 'beauty', 'makeup', 'hair', 'haircare'
    ]
    
    # Search for posts
    print(f"🔍 Searching for posts about '{TARGET_INGREDIENT}'...")
    posts = search_reddit_posts(access_token, TARGET_INGREDIENT, subreddits, limit=100)
    
    if not posts:
        print("❌ No posts found")
        return
    
    print(f"✅ Found {len(posts)} posts")
    
    # Process each post
    all_posts_data = []
    total_comments = 0
    
    for i, post in enumerate(posts, 1):
        print(f"📝 Processing post {i}/{len(posts)}: {post.get('title', 'No title')[:50]}...")
        
        # Fetch comments for this post
        comments, post_sentiment, is_significant = fetch_post_comments(
            access_token, post['id'], max_comments=30, 
            post_context=post, target_ingredient=TARGET_INGREDIENT,
            min_sample_size=min_sample_size
        )
        
        # Add sentiment analysis to post data
        post['comments'] = comments
        post['post_sentiment_analysis'] = post_sentiment
        post['is_significant_for_sentiment'] = is_significant
        
        all_posts_data.append(post)
        total_comments += len(comments)
        
        # Rate limiting
        time.sleep(1)
    
    # Calculate overall sentiment
    print("📊 Calculating overall sentiment...")
    overall_sentiment = calculate_overall_ingredient_sentiment(all_posts_data, TARGET_INGREDIENT)
    subreddit_sentiment = calculate_sentiment_by_subreddit(all_posts_data)
    effectiveness_sentiment = extract_effectiveness_sentiment(all_posts_data)
    safety_sentiment = extract_safety_sentiment(all_posts_data)
    
    # Create comprehensive sentiment summary
    sentiment_summary = {
        'overall': overall_sentiment,
        'by_subreddit': subreddit_sentiment,
        'effectiveness': effectiveness_sentiment,
        'safety': safety_sentiment,
        'analysis_timestamp': datetime.now().isoformat()
    }
    
    # Prepare final output
    output_data = {
        'ingredient': TARGET_INGREDIENT,
        'post_count': len(all_posts_data),
        'comment_count': total_comments,
        'sentiment_summary': sentiment_summary,
        'results': all_posts_data
    }
    
    # Write output file
    out_dir = '/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/raw data'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{TARGET_INGREDIENT.replace(' ', '_')}_all_comments.json")
    
    print(f"💾 Saving data to {out_path}...")
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print(f"\n🎉 K18 Hair Mask extraction completed!")
    print(f"📊 Posts processed: {len(all_posts_data)}")
    print(f"💬 Total comments: {total_comments}")
    print(f"📈 Overall sentiment: {overall_sentiment['overall_sentiment']}")
    print(f"📁 Output file: {out_path}")
    
    # File size info
    file_size = os.path.getsize(out_path)
    file_size_mb = file_size / (1024 * 1024)
    print(f"📏 File size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    main() 