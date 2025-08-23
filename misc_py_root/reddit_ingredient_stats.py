import os
import requests
import json
import statistics
import time
import base64
import math
from dotenv import load_dotenv

# Add VADER sentiment analysis
try:
    from nltk.sentiment import SentimentIntensityAnalyzer
    import nltk
    nltk.data.find('sentiment/vader_lexicon.zip')
    vader_ready = True
except (ImportError, LookupError):
    vader_ready = False

def analyze_sentiment(text):
    if vader_ready:
        sia = SentimentIntensityAnalyzer()
        score = sia.polarity_scores(text)
        return score['compound']
    # fallback: rule-based
    text = text.lower()
    if any(word in text for word in ["good", "great", "love", "amazing", "best", "recommend", "safe"]):
        return 1
    if any(word in text for word in ["bad", "hate", "avoid", "dangerous", "toxic", "harmful", "worst"]):
        return -1
    return 0

def get_reddit_token():
    load_dotenv()
    client_id = os.getenv('REDDIT_CLIENT_ID')
    client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    user_agent = 'ingredient_cosmetics_analyzer/1.0 (by /u/your_username)'
    credentials = f"{client_id}:{client_secret}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'User-Agent': user_agent,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    data = {'grant_type': 'client_credentials'}
    response = requests.post('https://www.reddit.com/api/v1/access_token', headers=headers, data=data)
    response.raise_for_status()
    return response.json()['access_token'], user_agent

def search_reddit(access_token, user_agent, query, limit=100, time_filter='year', sort='top', search_type='link', max_results=300):
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': user_agent
    }
    url = 'https://oauth.reddit.com/search'
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
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json().get('data', {})
        children = data.get('children', [])
        all_results.extend(children)
        fetched += len(children)
        after = data.get('after')
        if not after or not children:
            break
        time.sleep(0.5)
    return all_results

def ingredient_stats(ingredient):
    if not vader_ready:
        print("VADER sentiment not available. Please run: python3 -m nltk.downloader vader_lexicon")
    access_token, user_agent = get_reddit_token()
    print(f"Searching Reddit for posts mentioning '{ingredient}'...")
    posts = search_reddit(access_token, user_agent, ingredient, limit=100, time_filter='year', sort='top', search_type='link', max_results=300)
    if not posts:
        print(f"No posts found for '{ingredient}'.")
        return
    upvotes = [p['data'].get('ups', 0) for p in posts]
    post_ids = [p['data']['id'] for p in posts if 'id' in p['data']]
    comment_count = sum(p['data'].get('num_comments', 0) for p in posts)
    sentiments = [analyze_sentiment(p['data'].get('title', '') + ' ' + p['data'].get('selftext', '')) for p in posts]
    comment_sentiments = []
    for pid in post_ids[:5]:  # Sample up to 5 posts for comments
        url = f"https://oauth.reddit.com/comments/{pid}"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'User-Agent': user_agent
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
        except Exception as e:
            print(f"Error fetching comments for post {pid}: {e}")
    all_sentiments = sentiments + comment_sentiments
    avg_sentiment = statistics.mean(all_sentiments) if all_sentiments else 0
    std_sentiment = statistics.stdev(all_sentiments) if len(all_sentiments) > 1 else 0
    n = len(all_sentiments)
    # 95% confidence interval for the mean (normal approx, large n)
    if n > 1:
        ci95 = 1.96 * std_sentiment / math.sqrt(n)
        ci = [avg_sentiment - ci95, avg_sentiment + ci95]
    else:
        ci = [avg_sentiment, avg_sentiment]
    stats = {
        'ingredient': ingredient,
        'post_count': len(posts),
        'avg_upvotes': statistics.mean(upvotes) if upvotes else 0,
        'comment_volume': comment_count,
        'avg_sentiment': avg_sentiment,
        'std_sentiment': std_sentiment,
        'sentiment_95ci': ci,
        'positive': avg_sentiment > 0,
        'negative': avg_sentiment < 0,
        'sentiment_method': 'vader' if vader_ready else 'rule-based'
    }
    print(json.dumps(stats, indent=2))
    with open(f'reddit_data/ingredient_stats_{ingredient}.json', 'w') as f:
        json.dump(stats, f, indent=2)
    print(f"Saved stats to reddit_data/ingredient_stats_{ingredient}.json")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        ingredient = sys.argv[1]
    else:
        ingredient = input("Enter ingredient name: ")
    ingredient_stats(ingredient) 