import os
import requests
import json
import time
import base64
from dotenv import load_dotenv
import csv
import statistics
from collections import defaultdict, Counter
import sys
import re

# VADER Sentiment Analysis
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
    print("✓ VADER Sentiment Analysis available")
except ImportError:
    VADER_AVAILABLE = False
    print("⚠ VADER Sentiment Analysis not available. Install with: pip install vaderSentiment")

# Load credentials from .env
load_dotenv()
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'ingredient_cosmetics_analyzer/1.0 (by /u/your_username)'

# Directory structure
BASE_DIR = 'reddit_data'
JSON_DIR = os.path.join(BASE_DIR, 'json')
ALL_REDDIT_DIR = os.path.join(JSON_DIR, 'all_reddit')
SUBREDDITS_DIR = os.path.join(JSON_DIR, 'subreddits')
OR_DIR = os.path.join(ALL_REDDIT_DIR, 'or')
AND_DIR = os.path.join(ALL_REDDIT_DIR, 'and')
SECONDARY_ONLY_DIR = os.path.join(ALL_REDDIT_DIR, 'secondary_only')
SUB_OR_DIR = os.path.join(SUBREDDITS_DIR, 'or')
SUB_AND_DIR = os.path.join(SUBREDDITS_DIR, 'and')
SUB_SECONDARY_ONLY_DIR = os.path.join(SUBREDDITS_DIR, 'secondary_only')

# Ensure directories exist
for d in [BASE_DIR, JSON_DIR, ALL_REDDIT_DIR, SUBREDDITS_DIR, OR_DIR, AND_DIR, SECONDARY_ONLY_DIR, SUB_OR_DIR, SUB_AND_DIR, SUB_SECONDARY_ONLY_DIR]:
    os.makedirs(d, exist_ok=True)

# Debug: Check if credentials are loaded
print(f"Client ID loaded: {'Yes' if REDDIT_CLIENT_ID else 'No'}")
print(f"Client Secret loaded: {'Yes' if REDDIT_CLIENT_SECRET else 'No'}")

# Reddit API endpoints
REDDIT_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
REDDIT_BASE_URL = 'https://oauth.reddit.com'

# Initialize VADER analyzer
if VADER_AVAILABLE:
    vader_analyzer = SentimentIntensityAnalyzer()
else:
    vader_analyzer = None

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
        
        print(f"Response status: {response.status_code}")
        print(f"Response headers: {dict(response.headers)}")
        
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

def get_ingredient_variations(csv_path):
    """Read the 'inci_name' and 'search_keyword' columns from the ingredient search result CSV and return a list of unique values."""
    variations = set()
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            name = row.get('inci_name', '').strip()
            keyword = row.get('search_keyword', '').strip()
            if name:
                variations.add(name)
            if keyword:
                variations.add(keyword)
    return sorted(variations)

def search_reddit(access_token, query, subreddit=None, limit=100, time_filter='year', sort='top', search_type='link', max_results=300):
    """
    Search Reddit for posts or comments with pagination.
    Args:
        access_token: OAuth access token
        query: Search query (e.g., "salicylic acid")
        subreddit: Specific subreddit to search (optional)
        limit: Number of results per call (max 100)
        time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        sort: 'relevance', 'hot', 'top', 'new', 'comments'
        search_type: 'link' for posts, 'comment' for comments
        max_results: Maximum total results to fetch
    Returns:
        List of all results (children)
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    if subreddit:
        search_url = f"{REDDIT_BASE_URL}/r/{subreddit}/search"
    else:
        search_url = f"{REDDIT_BASE_URL}/search"
    
    params = {
        'q': query,
        'limit': min(limit, 100),
        't': time_filter,
        'sort': sort,
        'type': search_type
    }
    
    all_results = []
    after = None
    fetched = 0
    while fetched < max_results:
        if after:
            params['after'] = after
        else:
            params.pop('after', None)
        try:
            response = requests.get(search_url, headers=headers, params=params)
            print(f"[DEBUG] URL: {response.url}")
            print(f"[DEBUG] Status: {response.status_code}")
            if response.status_code != 200:
                print(f"[DEBUG] Response text: {response.text}")
            response.raise_for_status()
            data = response.json().get('data', {})
            children = data.get('children', [])
            if not children:
                print(f"[DEBUG] No results for query: {query}")
                print(f"[DEBUG] Raw response: {response.text}")
            all_results.extend(children)
            fetched += len(children)
            after = data.get('after')
            if not after or not children:
                break
        except Exception as e:
            print(f"Error searching Reddit: {e}")
            break
    return all_results

def save_search_results(results, out_path, query_type, query, search_type, subreddit=None, ingredient_name=None):
    # Only save if there are results
    if not results:
        print(f"No results for {query_type} query '{query}' ({search_type}) in {subreddit or 'all Reddit'}; not saving file.")
        return
    # New format: {"ingredient": <ingredient name>, "results": [ ... ]}
    output = {
        "ingredient": ingredient_name or query,
        "results": [r['data'] for r in results if 'data' in r]
    }
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    print(f"✓ Saved results to {out_path}")

def analyze_comment_sentiment(comment_data: dict, post_context: dict = None, target_ingredient: str = None) -> dict:
    """
    Analyze sentiment for individual comment with VADER.
    
    Args:
        comment_data: Comment dict with 'body', 'score', 'author', etc.
        post_context: Optional post context for better analysis
        target_ingredient: Target ingredient name for specific analysis
    
    Returns:
        Dict with sentiment scores and analysis
    """
    if not VADER_AVAILABLE:
        # Fallback to basic analysis
        text = comment_data.get('body', '').lower()
        if any(word in text for word in ["good", "great", "love", "amazing", "best", "recommend", "safe"]):
            return {
                'vader_scores': {'pos': 0.5, 'neg': 0, 'neu': 0.5, 'compound': 0.5},
                'sentiment_category': 'positive',
                'confidence': 0.5,
                'weighted_score': 0.5 * max(comment_data.get('score', 1), 1),
                'ingredient_specific': False,
                'fallback_analysis': True
            }
        if any(word in text for word in ["bad", "hate", "avoid", "dangerous", "toxic", "harmful", "worst"]):
            return {
                'vader_scores': {'pos': 0, 'neg': 0.5, 'neu': 0.5, 'compound': -0.5},
                'sentiment_category': 'negative',
                'confidence': 0.5,
                'weighted_score': -0.5 * max(comment_data.get('score', 1), 1),
                'ingredient_specific': False,
                'fallback_analysis': True
            }
        return {
            'vader_scores': {'pos': 0, 'neg': 0, 'neu': 1, 'compound': 0},
            'sentiment_category': 'neutral',
            'confidence': 0,
            'weighted_score': 0,
            'ingredient_specific': False,
            'fallback_analysis': True
        }
    
    # Get comment text
    comment_text = comment_data.get('body', '')
    if not comment_text or comment_text in ['[deleted]', '[removed]']:
        return {
            'vader_scores': {'pos': 0, 'neg': 0, 'neu': 1, 'compound': 0},
            'sentiment_category': 'neutral',
            'confidence': 0,
            'weighted_score': 0,
            'ingredient_specific': False
        }
    
    # Get VADER scores
    scores = vader_analyzer.polarity_scores(comment_text)
    
    # Determine sentiment category
    compound = scores['compound']
    if compound >= 0.05:
        sentiment_category = 'positive'
    elif compound <= -0.05:
        sentiment_category = 'negative'
    else:
        sentiment_category = 'neutral'
    
    # Calculate weighted score (VADER compound * comment score)
    comment_score = comment_data.get('score', 0)
    weighted_score = compound * max(comment_score, 1)  # Avoid zero multiplication
    
    # Check if comment is ingredient-specific
    ingredient_specific = is_ingredient_specific_comment(comment_text, post_context, target_ingredient)
    
    return {
        'vader_scores': scores,
        'sentiment_category': sentiment_category,
        'confidence': abs(compound),  # Higher absolute value = higher confidence
        'weighted_score': weighted_score,
        'ingredient_specific': ingredient_specific,
        'comment_length': len(comment_text),
        'has_ingredient_mention': ingredient_specific
    }

def is_ingredient_specific_comment(comment_text: str, post_context: dict = None, target_ingredient: str = None) -> bool:
    """
    Check if a comment is specifically about the target ingredient.
    
    Args:
        comment_text: The comment text to analyze
        post_context: Post context (title, body, etc.)
        target_ingredient: Target ingredient name
    
    Returns:
        True if comment is ingredient-specific, False otherwise
    """
    if not target_ingredient:
        return False
    
    # Clean ingredient name for regex matching
    ingredient_pattern = target_ingredient.lower().replace("_", r"\s*").replace(" ", r"\s*")
    
    # Check for ingredient mentions
    if re.search(rf'\b{ingredient_pattern}\b', comment_text.lower()):
        return True
    
    # Check for ingredient-related keywords in context
    if post_context:
        post_text = f"{post_context.get('title', '')} {post_context.get('body', '')}".lower()
        if re.search(rf'\b{ingredient_pattern}\b', post_text):
            return True
    
    return False

def analyze_post_only_sentiment(post_data: dict, target_ingredient: str = None) -> dict:
    """
    Analyze sentiment for post content only (when post has <5 comments).
    
    Args:
        post_data: Post data dict with title and body
        target_ingredient: Target ingredient name
    
    Returns:
        Dict with post-only sentiment analysis
    """
    # Combine title and body for analysis
    post_text = f"{post_data.get('title', '')} {post_data.get('body', '')}".strip()
    
    if not post_text:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 1},
            'weighted_average_compound': 0,
            'ingredient_specific_sentiment': {'positive': 0, 'negative': 0, 'neutral': 0},
            'sentiment_confidence': 0,
            'top_sentiment_comments': [],
            'total_comments_analyzed': 0,
            'ingredient_specific_comments': 0,
            'post_sentiment_analysis': {
                'vader_scores': {'pos': 0, 'neg': 0, 'neu': 1, 'compound': 0},
                'sentiment_category': 'neutral',
                'confidence': 0,
                'ingredient_specific': False
            }
        }
    
    # Analyze post sentiment
    post_sentiment = analyze_comment_sentiment(
        {'body': post_text, 'score': post_data.get('score', 0)}, 
        post_data, 
        target_ingredient
    )
    
    # Determine overall sentiment from post
    compound = post_sentiment['vader_scores']['compound']
    if compound >= 0.05:
        overall_sentiment = 'positive'
    elif compound <= -0.05:
        overall_sentiment = 'negative'
    else:
        overall_sentiment = 'neutral'
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_distribution': {
            'positive': 1 if overall_sentiment == 'positive' else 0,
            'negative': 1 if overall_sentiment == 'negative' else 0,
            'neutral': 1 if overall_sentiment == 'neutral' else 0
        },
        'weighted_average_compound': compound,
        'ingredient_specific_sentiment': {
            'positive': 1 if post_sentiment.get('ingredient_specific', False) and overall_sentiment == 'positive' else 0,
            'negative': 1 if post_sentiment.get('ingredient_specific', False) and overall_sentiment == 'negative' else 0,
            'neutral': 1 if post_sentiment.get('ingredient_specific', False) and overall_sentiment == 'neutral' else 0
        },
        'sentiment_confidence': abs(compound),
        'top_sentiment_comments': [],
        'total_comments_analyzed': 0,
        'ingredient_specific_comments': 1 if post_sentiment.get('ingredient_specific', False) else 0,
        'post_sentiment_analysis': post_sentiment
    }

def aggregate_post_sentiment(post_data: dict, comments: list, target_ingredient: str = None) -> dict:
    """
    Aggregate sentiment across all comments in a post.
    
    Args:
        post_data: Post data dict
        comments: List of comment dicts with sentiment analysis
        target_ingredient: Target ingredient name
    
    Returns:
        Dict with aggregated sentiment data
    """
    if not comments:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 1},
            'weighted_average_compound': 0,
            'ingredient_specific_sentiment': {'positive': 0, 'negative': 0, 'neutral': 0},
            'sentiment_confidence': 0,
            'top_sentiment_comments': [],
            'total_comments_analyzed': 0,
            'ingredient_specific_comments': 0
        }
    
    # Analyze each comment if not already analyzed
    comment_sentiments = []
    ingredient_specific_sentiments = []
    
    for comment in comments:
        if 'sentiment_analysis' not in comment:
            sentiment_data = analyze_comment_sentiment(comment, post_data, target_ingredient)
            comment['sentiment_analysis'] = sentiment_data
        else:
            sentiment_data = comment['sentiment_analysis']
        
        comment_sentiments.append(sentiment_data)
        
        if sentiment_data.get('ingredient_specific', False):
            ingredient_specific_sentiments.append(sentiment_data)
    
    # Calculate distributions
    sentiment_categories = [s['sentiment_category'] for s in comment_sentiments]
    sentiment_distribution = {
        'positive': sentiment_categories.count('positive'),
        'negative': sentiment_categories.count('negative'),
        'neutral': sentiment_categories.count('neutral')
    }
    
    # Calculate weighted average compound score
    total_weight = sum(s['weighted_score'] for s in comment_sentiments)
    total_comments = len(comment_sentiments)
    weighted_avg_compound = total_weight / total_comments if total_comments > 0 else 0
    
    # Determine overall sentiment
    if weighted_avg_compound >= 0.05:
        overall_sentiment = 'positive'
    elif weighted_avg_compound <= -0.05:
        overall_sentiment = 'negative'
    else:
        overall_sentiment = 'neutral'
    
    # Get top sentiment comments (most impactful)
    top_comments = sorted(comment_sentiments, key=lambda x: abs(x['weighted_score']), reverse=True)[:3]
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_distribution': sentiment_distribution,
        'weighted_average_compound': weighted_avg_compound,
        'ingredient_specific_sentiment': {
            'positive': len([s for s in ingredient_specific_sentiments if s['sentiment_category'] == 'positive']),
            'negative': len([s for s in ingredient_specific_sentiments if s['sentiment_category'] == 'negative']),
            'neutral': len([s for s in ingredient_specific_sentiments if s['sentiment_category'] == 'neutral'])
        },
        'sentiment_confidence': abs(weighted_avg_compound),
        'top_sentiment_comments': top_comments,
        'total_comments_analyzed': len(comment_sentiments),
        'ingredient_specific_comments': len(ingredient_specific_sentiments)
    }

def analyze_sentiment(text):
    """
    Legacy function for backward compatibility.
    Now uses VADER-based analysis.
    """
    if not VADER_AVAILABLE:
        # Fallback to basic analysis
        text = text.lower()
        if any(word in text for word in ["good", "great", "love", "amazing", "best", "recommend", "safe"]):
            return 1
        if any(word in text for word in ["bad", "hate", "avoid", "dangerous", "toxic", "harmful", "worst"]):
            return -1
        return 0
    
    # Use VADER for better analysis
    scores = vader_analyzer.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        return 1
    elif compound <= -0.05:
        return -1
    else:
        return 0

def subreddit_discovery_phase(access_token, ingredient, candidate_subreddits, limit=50, time_filter='year'):
    """
    For a given ingredient, search across candidate subreddits and collect:
    - Number of posts mentioning the ingredient
    - Average upvotes
    - Comment volume and sentiment
    - Whether the ingredient is mentioned positively or negatively
    Returns a mapping of subreddit to stats.
    """
    stats = {}
    for subreddit in candidate_subreddits:
        print(f"[Discovery] Searching r/{subreddit} for '{ingredient}'...")
        posts = search_reddit(
            access_token,
            ingredient,
            subreddit=subreddit,
            limit=limit,
            time_filter=time_filter,
            sort='top',
            search_type='link',
            max_results=limit
        )
        if not posts:
            continue
        upvotes = [p['data'].get('ups', 0) for p in posts]
        post_ids = [p['data']['id'] for p in posts if 'id' in p['data']]
        comment_count = sum(p['data'].get('num_comments', 0) for p in posts)
        # Sentiment on post titles and selftext
        sentiments = [analyze_sentiment(p['data'].get('title', '') + ' ' + p['data'].get('selftext', '')) for p in posts]
        # Fetch comments for each post (limited for speed)
        comment_sentiments = []
        for pid in post_ids[:5]:  # Only sample up to 5 posts for comments
            url = f"{REDDIT_BASE_URL}/r/{subreddit}/comments/{pid}"
            headers = {
                'Authorization': f'Bearer {access_token}',
                'User-Agent': REDDIT_USER_AGENT
            }
            try:
                resp = requests.get(url, headers=headers, params={'limit': 20})
                if resp.status_code == 200:
                    data = resp.json()
                    if isinstance(data, list) and len(data) > 1:
                        comments = data[1].get('data', {}).get('children', [])
                        for c in comments:
                            body = c.get('data', {}).get('body', '')
                            if body:
                                comment_sentiments.append(analyze_sentiment(body))
                else:
                    print(f"[Discovery] Failed to fetch comments for post {pid} in r/{subreddit}")
            except Exception as e:
                print(f"[Discovery] Error fetching comments: {e}")
        all_sentiments = sentiments + comment_sentiments
        avg_sentiment = statistics.mean(all_sentiments) if all_sentiments else 0
        stats[subreddit] = {
            'post_count': len(posts),
            'avg_upvotes': statistics.mean(upvotes) if upvotes else 0,
            'comment_volume': comment_count,
            'avg_sentiment': avg_sentiment,
            'positive': avg_sentiment > 0,
            'negative': avg_sentiment < 0
        }
    return stats

def fetch_post_comments(access_token, post_id, max_comments=30, post_context=None, target_ingredient=None, min_sample_size=385):
    """
    Fetch and analyze comments for a given post using Reddit API.
    
    Args:
        access_token: Reddit OAuth token
        post_id: Reddit post ID
        max_comments: Maximum number of comments to fetch
        post_context: Post context for sentiment analysis
        target_ingredient: Target ingredient for specific analysis
        min_sample_size: Minimum sample size for statistical significance
    
    Returns:
        Tuple of (comment_list, post_sentiment_analysis, is_significant)
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    url = f"{REDDIT_BASE_URL}/comments/{post_id}"
    try:
        resp = requests.get(url, headers=headers, params={'limit': max_comments})
        resp.raise_for_status()
        data = resp.json()
        # Comments are in the second item of the returned list
        if isinstance(data, list) and len(data) > 1:
            comments = data[1].get('data', {}).get('children', [])
            comment_list = []
            for c in comments:
                cdata = c.get('data', {})
                if c.get('kind') == 't1' and cdata.get('body') and cdata.get('author'):
                    comment_data = {
                        'author': cdata.get('author'),
                        'body': cdata.get('body').strip(),
                        'score': cdata.get('score', 0),
                        'is_top_level': cdata.get('parent_id', '').startswith('t3_'),
                        'created_utc': cdata.get('created_utc'),
                        'id': cdata.get('id')
                    }
                    
                    comment_list.append(comment_data)
            
            # Sort by score, take top 30 comments for analysis
            comment_list.sort(key=lambda x: x['score'], reverse=True)
            top_comments = comment_list[:30]
            
            # Determine if post is significant for sentiment analysis
            total_comments = len(comment_list)
            is_significant = total_comments >= 5
            
            if is_significant:
                # Analyze top 30 comments for significant posts
                for comment_data in top_comments:
                    comment_data['sentiment_analysis'] = analyze_comment_sentiment(
                        comment_data, post_context, target_ingredient
                    )
                
                # Aggregate post-level sentiment using top 30 comments
                post_sentiment = aggregate_post_sentiment(post_context or {}, top_comments, target_ingredient)
                post_sentiment['analysis_scope'] = 'top_30_comments'
                post_sentiment['total_comments_available'] = total_comments
                post_sentiment['comments_analyzed'] = len(top_comments)
                post_sentiment['is_statistically_significant'] = total_comments >= min_sample_size
            else:
                # For posts with <5 comments, only analyze the post itself
                post_sentiment = analyze_post_only_sentiment(post_context or {}, target_ingredient)
                post_sentiment['analysis_scope'] = 'post_only'
                post_sentiment['total_comments_available'] = total_comments
                post_sentiment['comments_analyzed'] = 0
                post_sentiment['is_statistically_significant'] = False
            
            return comment_list, post_sentiment, is_significant
    except Exception as e:
        print(f"[WARN] Could not fetch comments for post {post_id}: {e}")
    
    # Return empty results if failed
    empty_sentiment = analyze_post_only_sentiment(post_context or {}, target_ingredient)
    empty_sentiment['analysis_scope'] = 'failed_fetch'
    empty_sentiment['total_comments_available'] = 0
    empty_sentiment['comments_analyzed'] = 0
    empty_sentiment['is_statistically_significant'] = False
    return [], empty_sentiment, False

def calculate_overall_ingredient_sentiment(all_posts: list, target_ingredient: str = None) -> dict:
    """
    Calculate overall sentiment summary for an ingredient across significant posts only.
    
    Args:
        all_posts: List of post dicts with sentiment analysis
        target_ingredient: Target ingredient name
    
    Returns:
        Dict with overall sentiment summary
    """
    if not all_posts:
        return {
            'overall_sentiment': 'neutral',
            'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
            'weighted_average_compound': 0,
            'total_posts_analyzed': 0,
            'total_comments_analyzed': 0,
            'ingredient_specific_comments': 0,
            'sentiment_confidence': 0,
            'significant_posts_count': 0,
            'insignificant_posts_count': 0
        }
    
    # Separate significant and insignificant posts
    significant_posts = [post for post in all_posts if post.get('is_significant_for_sentiment', False)]
    insignificant_posts = [post for post in all_posts if not post.get('is_significant_for_sentiment', False)]
    
    # Collect sentiment data from significant posts only
    post_sentiments = []
    all_comment_sentiments = []
    ingredient_specific_sentiments = []
    
    for post in significant_posts:
        if 'post_sentiment' in post:
            post_sentiments.append(post['post_sentiment'])
        
        comments = post.get('comments', [])
        for comment in comments:
            if 'sentiment_analysis' in comment:
                all_comment_sentiments.append(comment['sentiment_analysis'])
                if comment['sentiment_analysis'].get('ingredient_specific', False):
                    ingredient_specific_sentiments.append(comment['sentiment_analysis'])
    
    # Calculate overall sentiment from significant posts only
    if post_sentiments:
        overall_sentiments = [ps['overall_sentiment'] for ps in post_sentiments]
        sentiment_distribution = {
            'positive': overall_sentiments.count('positive'),
            'negative': overall_sentiments.count('negative'),
            'neutral': overall_sentiments.count('neutral')
        }
        
        # Determine dominant sentiment
        if sentiment_distribution['positive'] > sentiment_distribution['negative']:
            overall_sentiment = 'positive'
        elif sentiment_distribution['negative'] > sentiment_distribution['positive']:
            overall_sentiment = 'negative'
        else:
            overall_sentiment = 'neutral'
        
        # Calculate weighted average compound score
        weighted_compounds = [ps['weighted_average_compound'] for ps in post_sentiments]
        avg_compound = sum(weighted_compounds) / len(weighted_compounds) if weighted_compounds else 0
    else:
        overall_sentiment = 'neutral'
        sentiment_distribution = {'positive': 0, 'negative': 0, 'neutral': 0}
        avg_compound = 0
    
    return {
        'overall_sentiment': overall_sentiment,
        'sentiment_distribution': sentiment_distribution,
        'weighted_average_compound': avg_compound,
        'total_posts_analyzed': len(post_sentiments),
        'total_comments_analyzed': len(all_comment_sentiments),
        'ingredient_specific_comments': len(ingredient_specific_sentiments),
        'sentiment_confidence': abs(avg_compound),
        'significant_posts_count': len(significant_posts),
        'insignificant_posts_count': len(insignificant_posts),
        'analysis_notes': f"Sentiment analysis based on {len(significant_posts)} significant posts (≥5 comments) out of {len(all_posts)} total posts"
    }

def calculate_sentiment_by_subreddit(all_posts: list) -> dict:
    """
    Calculate sentiment breakdown by subreddit.
    
    Args:
        all_posts: List of post dicts with sentiment analysis
    
    Returns:
        Dict with sentiment data by subreddit
    """
    subreddit_sentiments = defaultdict(lambda: {
        'posts': 0,
        'comments': 0,
        'positive_posts': 0,
        'negative_posts': 0,
        'neutral_posts': 0,
        'avg_compound': 0,
        'weighted_avg_compound': 0
    })
    
    for post in all_posts:
        subreddit = post.get('subreddit', 'unknown')
        post_sentiment = post.get('post_sentiment', {})
        
        subreddit_sentiments[subreddit]['posts'] += 1
        subreddit_sentiments[subreddit]['comments'] += len(post.get('comments', []))
        
        overall_sentiment = post_sentiment.get('overall_sentiment', 'neutral')
        if overall_sentiment == 'positive':
            subreddit_sentiments[subreddit]['positive_posts'] += 1
        elif overall_sentiment == 'negative':
            subreddit_sentiments[subreddit]['negative_posts'] += 1
        else:
            subreddit_sentiments[subreddit]['neutral_posts'] += 1
        
        subreddit_sentiments[subreddit]['avg_compound'] += post_sentiment.get('weighted_average_compound', 0)
    
    # Calculate averages
    for subreddit, data in subreddit_sentiments.items():
        if data['posts'] > 0:
            data['avg_compound'] /= data['posts']
            data['weighted_avg_compound'] = data['avg_compound']  # Could be weighted by post score
    
    return dict(subreddit_sentiments)

def extract_effectiveness_sentiment(all_posts: list) -> dict:
    """
    Extract sentiment specifically related to effectiveness.
    
    Args:
        all_posts: List of post dicts with sentiment analysis
    
    Returns:
        Dict with effectiveness-related sentiment
    """
    effectiveness_keywords = [
        'work', 'works', 'working', 'effective', 'effectiveness', 'results', 'improved', 
        'better', 'helped', 'helped with', 'fixed', 'solved', 'cured', 'healed',
        'growth', 'grew', 'increased', 'decreased', 'reduced', 'eliminated'
    ]
    
    effectiveness_comments = []
    
    for post in all_posts:
        comments = post.get('comments', [])
        for comment in comments:
            comment_text = comment.get('body', '').lower()
            if any(keyword in comment_text for keyword in effectiveness_keywords):
                if 'sentiment_analysis' in comment:
                    effectiveness_comments.append(comment['sentiment_analysis'])
    
    if not effectiveness_comments:
        return {
            'effectiveness_sentiment': 'neutral',
            'positive_effectiveness': 0,
            'negative_effectiveness': 0,
            'neutral_effectiveness': 0,
            'total_effectiveness_comments': 0
        }
    
    positive_count = sum(1 for c in effectiveness_comments if c['sentiment_category'] == 'positive')
    negative_count = sum(1 for c in effectiveness_comments if c['sentiment_category'] == 'negative')
    neutral_count = sum(1 for c in effectiveness_comments if c['sentiment_category'] == 'neutral')
    
    if positive_count > negative_count:
        effectiveness_sentiment = 'positive'
    elif negative_count > positive_count:
        effectiveness_sentiment = 'negative'
    else:
        effectiveness_sentiment = 'neutral'
    
    return {
        'effectiveness_sentiment': effectiveness_sentiment,
        'positive_effectiveness': positive_count,
        'negative_effectiveness': negative_count,
        'neutral_effectiveness': neutral_count,
        'total_effectiveness_comments': len(effectiveness_comments)
    }

def extract_safety_sentiment(all_posts: list) -> dict:
    """
    Extract sentiment specifically related to safety and side effects.
    
    Args:
        all_posts: List of post dicts with sentiment analysis
    
    Returns:
        Dict with safety-related sentiment
    """
    safety_keywords = [
        'safe', 'safety', 'side effect', 'side effects', 'adverse', 'reaction', 
        'allergic', 'irritation', 'irritated', 'burning', 'stinging', 'redness',
        'swelling', 'rash', 'breakout', 'acne', 'cystic', 'pimples', 'harmful',
        'dangerous', 'toxic', 'poisonous', 'cancer', 'carcinogenic'
    ]
    
    safety_comments = []
    
    for post in all_posts:
        comments = post.get('comments', [])
        for comment in comments:
            comment_text = comment.get('body', '').lower()
            if any(keyword in comment_text for keyword in safety_keywords):
                if 'sentiment_analysis' in comment:
                    safety_comments.append(comment['sentiment_analysis'])
    
    if not safety_comments:
        return {
            'safety_sentiment': 'neutral',
            'positive_safety': 0,
            'negative_safety': 0,
            'neutral_safety': 0,
            'total_safety_comments': 0
        }
    
    positive_count = sum(1 for c in safety_comments if c['sentiment_category'] == 'positive')
    negative_count = sum(1 for c in safety_comments if c['sentiment_category'] == 'negative')
    neutral_count = sum(1 for c in safety_comments if c['sentiment_category'] == 'neutral')
    
    if positive_count > negative_count:
        safety_sentiment = 'positive'
    elif negative_count > positive_count:
        safety_sentiment = 'negative'
    else:
        safety_sentiment = 'neutral'
    
    return {
        'safety_sentiment': safety_sentiment,
        'positive_safety': positive_count,
        'negative_safety': negative_count,
        'neutral_safety': neutral_count,
        'total_safety_comments': len(safety_comments)
    }

def get_subreddit_info(access_token, subreddit):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    url = f"{REDDIT_BASE_URL}/r/{subreddit}/about"
    try:
        resp = requests.get(url, headers=headers)
        resp.raise_for_status()
        data = resp.json().get('data', {})
        return {
            'subscribers': data.get('subscribers'),
            'score': data.get('score')  # Not always present
        }
    except Exception as e:
        print(f"[WARN] Could not fetch info for subreddit {subreddit}: {e}")
        return {'subscribers': None, 'score': None}

def main():
    print("Testing Reddit API integration with enhanced sentiment analysis...")
    access_token = get_reddit_token()
    if not access_token:
        print("Failed to get access token")
        return
    print("✓ Successfully obtained Reddit access token")

    # Calculate statistically significant sample size (for 95% confidence, 5% margin, p=0.5)
    # n = (Z^2 * p * (1-p)) / e^2, Z=1.96, p=0.5, e=0.05
    import math
    Z = 1.96
    p = 0.5
    e = 0.05
    min_sample_size = math.ceil((Z**2 * p * (1-p)) / (e**2))  # ~385

    # Allow ingredient to be set via command-line argument
    ingredient = sys.argv[1] if len(sys.argv) > 1 else 'cocamidopropyl'
    search_types = ['link', 'comment']  # posts and comments
    all_posts = []
    
    print(f"\n🔍 Starting sentiment analysis for ingredient: {ingredient}")
    
    for s_type in search_types:
        print(f"\nSearching all Reddit for '{ingredient}' ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
        results = search_reddit(
            access_token,
            ingredient,
            limit=100,
            time_filter='year',
            sort='top',
            search_type=s_type,
            max_results=300
        )
        for r in results:
            if 'data' in r:
                post = r['data']
                post_id = post.get('id')
                
                # Create post context for sentiment analysis
                post_context = {
                    'title': post.get('title', ''),
                    'body': post.get('body', ''),
                    'subreddit': post.get('subreddit', ''),
                    'score': post.get('score', 0),
                    'id': post_id
                }
                
                # Fetch comments with enhanced sentiment analysis for this post
                if post_id:
                    comments, post_sentiment, is_significant = fetch_post_comments(
                        access_token, 
                        post_id, 
                        max_comments=30, 
                        post_context=post_context, 
                        target_ingredient=ingredient,
                        min_sample_size=min_sample_size
                    )
                    post['comments'] = comments
                    post['post_sentiment'] = post_sentiment
                    post['is_significant_for_sentiment'] = is_significant
                    post['comment_breakdown'] = {
                        'total_collected': len(comments),
                        'top_level': len(comments),
                        'nested_replies': 0,
                        'is_significant': is_significant,
                        'analysis_scope': post_sentiment.get('analysis_scope', 'unknown')
                    }
                else:
                    post['comments'] = []
                    post['post_sentiment'] = analyze_post_only_sentiment(post_context, ingredient)
                    post['is_significant_for_sentiment'] = False
                    post['comment_breakdown'] = {
                        'total_collected': 0,
                        'top_level': 0,
                        'nested_replies': 0,
                        'is_significant': False,
                        'analysis_scope': 'post_only'
                    }
                
                all_posts.append(post)
        time.sleep(1)
    
    # Write a single file per ingredient, as a dict with 'ingredient', 'post_count', 'comment_count', and 'results' keys
    out_dir = '/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/raw data'
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{ingredient}_all_comments.json")
    
    # Calculate summary statistics
    non_deleted_posts = [p for p in all_posts if p.get('body') not in ['[deleted]', '[removed]']]
    deleted_posts_count = len(all_posts) - len(non_deleted_posts)
    post_count = len(non_deleted_posts)
    
    # Comments
    all_comments = []
    deleted_comments_count = 0
    for post in non_deleted_posts:
        comments = post.get('comments', [])
        filtered_comments = [c for c in comments if c.get('body') not in ['[deleted]', '[removed]']]
        deleted_comments_count += len(comments) - len(filtered_comments)
        all_comments.extend(filtered_comments)
        post['comments'] = filtered_comments  # Overwrite with filtered
    comment_count = len(all_comments)

    # Weighted average comments per post (by upvotes)
    if post_count > 0:
        weights = [max(post.get('score', 1), 1) for post in non_deleted_posts]
        comments_per_post = [len(post.get('comments', [])) for post in non_deleted_posts]
        weighted_avg_comments = sum(c * w for c, w in zip(comments_per_post, weights)) / sum(weights)
        avg_upvotes_per_post = sum(weights) / post_count
    else:
        weighted_avg_comments = 0
        avg_upvotes_per_post = 0

    # Average upvotes per comment
    if comment_count > 0:
        avg_upvotes_per_comment = sum(c.get('score', 0) for c in all_comments) / comment_count
    else:
        avg_upvotes_per_comment = 0

    # Top subreddits with extra info
    subreddit_counts = Counter(post.get('subreddit') for post in non_deleted_posts)
    top_subreddit_names = [s for s, _ in subreddit_counts.most_common(5)]
    top_subreddits = []
    for sub in top_subreddit_names:
        # Get all posts for this subreddit
        posts_in_sub = [p for p in non_deleted_posts if p.get('subreddit') == sub]
        avg_post_score = sum(p.get('score', 0) for p in posts_in_sub) / len(posts_in_sub) if posts_in_sub else 0
        # Get all comments for this subreddit
        comments_in_sub = []
        for p in posts_in_sub:
            comments_in_sub.extend(p.get('comments', []))
        # Top 3 authors by comment count, excluding '[deleted]' and '[removed]'
        author_counts = Counter(
            c.get('author') for c in comments_in_sub if c.get('author') not in ['[deleted]', '[removed]', None]
        )
        top_authors = [a for a, _ in author_counts.most_common(3)]
        # Fetch subreddit info
        sub_info = get_subreddit_info(access_token, sub)
        top_subreddits.append({
            'subreddit': sub,
            'subscriber_count': sub_info['subscribers'],
            'avg_post_score': avg_post_score,
            'top_authors': top_authors
        })

    # NEW: Enhanced Sentiment Analysis Summary
    print(f"\n📊 Calculating comprehensive sentiment analysis for {ingredient}...")
    
    sentiment_summary = {
        "overall_ingredient_sentiment": calculate_overall_ingredient_sentiment(non_deleted_posts, ingredient),
        "sentiment_by_subreddit": calculate_sentiment_by_subreddit(non_deleted_posts),
        "effectiveness_sentiment": extract_effectiveness_sentiment(non_deleted_posts),
        "safety_sentiment": extract_safety_sentiment(non_deleted_posts)
    }
    
    # Print enhanced sentiment summary
    overall_sentiment = sentiment_summary["overall_ingredient_sentiment"]
    print(f"\n🎯 Enhanced Sentiment Analysis for {ingredient}:")
    print(f"   Overall Sentiment: {overall_sentiment['overall_sentiment'].upper()}")
    print(f"   Sentiment Distribution: {overall_sentiment['sentiment_distribution']}")
    print(f"   Weighted Average Compound: {overall_sentiment['weighted_average_compound']:.3f}")
    print(f"   Significant Posts: {overall_sentiment['significant_posts_count']} (≥5 comments)")
    print(f"   Insignificant Posts: {overall_sentiment['insignificant_posts_count']} (<5 comments)")
    print(f"   Posts Analyzed for Sentiment: {overall_sentiment['total_posts_analyzed']}")
    print(f"   Comments Analyzed: {overall_sentiment['total_comments_analyzed']}")
    print(f"   Ingredient-Specific Comments: {overall_sentiment['ingredient_specific_comments']}")
    print(f"   Analysis Notes: {overall_sentiment.get('analysis_notes', 'N/A')}")
    
    effectiveness = sentiment_summary["effectiveness_sentiment"]
    print(f"\n💪 Effectiveness Sentiment:")
    print(f"   Overall: {effectiveness['effectiveness_sentiment'].upper()}")
    print(f"   Positive: {effectiveness['positive_effectiveness']}, Negative: {effectiveness['negative_effectiveness']}, Neutral: {effectiveness['neutral_effectiveness']}")
    
    safety = sentiment_summary["safety_sentiment"]
    print(f"\n🛡️ Safety Sentiment:")
    print(f"   Overall: {safety['safety_sentiment'].upper()}")
    print(f"   Positive: {safety['positive_safety']}, Negative: {safety['negative_safety']}, Neutral: {safety['neutral_safety']}")

    output = {
        "ingredient": ingredient,
        "post_count": post_count,
        "comment_count": comment_count,
        "deleted_post_count": deleted_posts_count,
        "deleted_comment_count": deleted_comments_count,
        "weighted_avg_comments_per_post": weighted_avg_comments,
        "avg_upvotes_per_post": avg_upvotes_per_post,
        "avg_upvotes_per_comment": avg_upvotes_per_comment,
        "top_subreddits": top_subreddits,
        "min_sample_size_for_significance": min_sample_size,
        
        # NEW: Enhanced Sentiment Analysis Data
        "sentiment_summary": sentiment_summary,
        
        "results": non_deleted_posts
    }
    
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Enhanced results saved to {out_path}")
    print(f"   📊 Posts: {post_count}, Comments: {comment_count}")
    print(f"   🗑️ Deleted Posts: {deleted_posts_count}, Deleted Comments: {deleted_comments_count}")
    print(f"   🎯 Sentiment Analysis: Complete with VADER-based analysis")
    print(f"   📈 Data includes: Comment-level sentiment, Post-level aggregation, Ingredient-specific analysis")

if __name__ == "__main__":
    main() 