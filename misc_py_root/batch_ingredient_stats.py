import os
import json
import time
from reddit_ingredient_stats import get_reddit_token, search_reddit, analyze_sentiment, vader_ready
import statistics
import requests

def batch_ingredient_stats(ingredient_list, out_path):
    access_token, user_agent = get_reddit_token()
    all_stats = []
    for idx, ingredient in enumerate(ingredient_list):
        print(f"[{idx+1}/{len(ingredient_list)}] Processing: {ingredient}")
        try:
            posts = search_reddit(access_token, user_agent, ingredient, limit=100, time_filter='year', sort='top', search_type='link', max_results=300)
            if not posts:
                print(f"No posts found for '{ingredient}'.")
                stats = {
                    'ingredient': ingredient,
                    'post_count': 0,
                    'avg_upvotes': 0,
                    'comment_volume': 0,
                    'avg_sentiment': 0,
                    'std_sentiment': 0,
                    'sentiment_95ci': [0, 0],
                    'positive': False,
                    'negative': False,
                    'sentiment_method': 'vader' if vader_ready else 'rule-based'
                }
            else:
                upvotes = [p['data'].get('ups', 0) for p in posts]
                post_ids = [p['data']['id'] for p in posts if 'id' in p['data']]
                comment_count = sum(p['data'].get('num_comments', 0) for p in posts)
                sentiments = [analyze_sentiment(p['data'].get('title', '') + ' ' + p['data'].get('selftext', '')) for p in posts]
                comment_sentiments = []
                for pid in post_ids[:5]:
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
                if n > 1:
                    ci95 = 1.96 * std_sentiment / (n ** 0.5)
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
            all_stats.append(stats)
            time.sleep(1)  # Be nice to Reddit API
        except Exception as e:
            print(f"Error processing {ingredient}: {e}")
    with open(out_path, 'w') as f:
        json.dump(all_stats, f, indent=2)
    print(f"Saved all stats to {out_path}")

def read_ingredient_list(path):
    with open(path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    return lines

if __name__ == "__main__":
    ingredient_list = read_ingredient_list('ingredient.txt')
    batch_ingredient_stats(ingredient_list, 'reddit_data/all_ingredient_stats.json') 