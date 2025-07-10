import os
import requests
import json
import time
import base64
from dotenv import load_dotenv
import csv
import statistics
from collections import defaultdict

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

def save_search_results(results, out_path, query_type, query, search_type, subreddit=None):
    # Only save if there are results
    if not results:
        print(f"No results for {query_type} query '{query}' ({search_type}) in {subreddit or 'all Reddit'}; not saving file.")
        return
    meta = {
        'query_type': query_type,
        'query': query,
        'search_type': search_type,
        'subreddit': subreddit,
        'result_count': len(results)
    }
    with open(out_path, 'w') as f:
        json.dump({'meta': meta, 'data': {'children': results}}, f, indent=2)
    print(f"✓ Saved results to {out_path}")

def analyze_sentiment(text):
    # Placeholder for sentiment analysis (simple rule-based for now)
    text = text.lower()
    if any(word in text for word in ["good", "great", "love", "amazing", "best", "recommend", "safe"]):
        return 1
    if any(word in text for word in ["bad", "hate", "avoid", "dangerous", "toxic", "harmful", "worst"]):
        return -1
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

def main():
    print("Testing Reddit API integration...")
    access_token = get_reddit_token()
    if not access_token:
        print("Failed to get access token")
        return
    print("✓ Successfully obtained Reddit access token")

    ingredient = 'cocamidopropyl'
    # Candidate subreddits for discovery (expand as needed)
    candidate_subreddits = [
        'SkincareAddiction', 'AsianBeauty', 'acne', 'HaircareScience', 'curlyhair', 'fancyfollicles',
        'beauty', 'MakeupAddiction', '30PlusSkinCare', 'CompulsiveSkinPicking', 'SebDerm', 'eczema',
        'rosacea', 'malegrooming', 'Naturalhair', 'wavyhair', 'longhair', 'HairDye', 'Hair', 'Shampoo',
        'Conditioner', 'ProductPorn', 'beautyproducts', 'beautyaddiction', 'ScaBeauty', 'SkincareScience'
    ]
    # Discovery phase
    discovery_stats = subreddit_discovery_phase(access_token, ingredient, candidate_subreddits)
    print("\n[Discovery Results]")
    for sub, stat in sorted(discovery_stats.items(), key=lambda x: -x[1]['post_count']):
        print(f"r/{sub}: posts={stat['post_count']}, avg_upvotes={stat['avg_upvotes']:.1f}, comments={stat['comment_volume']}, avg_sentiment={stat['avg_sentiment']:.2f}, positive={stat['positive']}, negative={stat['negative']}")
    # Curated mapping: only subreddits with at least 3 posts and nonzero comment volume
    curated = [sub for sub, stat in discovery_stats.items() if stat['post_count'] >= 3 and stat['comment_volume'] > 0]
    print(f"\n[Curated Subreddits for '{ingredient}']: {curated}")
    # Optionally, save this mapping to a file for future use
    with open(f'reddit_data/curated_subreddits_{ingredient}.json', 'w') as f:
        json.dump({'ingredient': ingredient, 'curated_subreddits': curated, 'stats': discovery_stats}, f, indent=2)
    # Stop here; do not run detailed searches until discovery is complete
    print("\nDiscovery phase complete. Run detailed searches only for curated subreddits.")

    # Use only the term 'cocamidopropyl' for all queries
    variations = ['cocamidopropyl']
    secondary_term = 'hair'

    # Build queries
    or_query = 'cocamidopropyl'
    and_query = f'cocamidopropyl {secondary_term}'
    secondary_only_query = secondary_term

    search_types = ['link', 'comment']  # posts and comments

    # All Reddit - OR, AND, and secondary only
    for s_type in search_types:
        # OR
        print(f"\nSearching all Reddit for 'cocamidopropyl' ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
        results = search_reddit(
            access_token,
            or_query,
            limit=100,
            time_filter='year',
            sort='top',
            search_type=s_type,
            max_results=300
        )
        out_name = f"reddit_cocamidopropyl_or_{'posts' if s_type=='link' else 'comments'}_top.json"
        out_path = os.path.join(OR_DIR, out_name)
        save_search_results(results, out_path, 'or', or_query, s_type)
        time.sleep(1)
        # AND
        print(f"\nSearching all Reddit for 'cocamidopropyl AND hair' ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
        results = search_reddit(
            access_token,
            and_query,
            limit=100,
            time_filter='year',
            sort='top',
            search_type=s_type,
            max_results=300
        )
        out_name = f"reddit_cocamidopropyl_and_{secondary_term}_{'posts' if s_type=='link' else 'comments'}_top.json"
        out_path = os.path.join(AND_DIR, out_name)
        save_search_results(results, out_path, 'and', and_query, s_type)
        time.sleep(1)
        # Secondary only
        print(f"\nSearching all Reddit for secondary term only ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
        results = search_reddit(
            access_token,
            secondary_only_query,
            limit=100,
            time_filter='year',
            sort='top',
            search_type=s_type,
            max_results=300
        )
        out_name = f"reddit_{secondary_term}_only_{'posts' if s_type=='link' else 'comments'}_top.json"
        out_path = os.path.join(SECONDARY_ONLY_DIR, out_name)
        save_search_results(results, out_path, 'secondary_only', secondary_only_query, s_type)
        time.sleep(1)

    # Subreddits - OR, AND, and secondary only
    for subreddit in curated: # Use curated subreddits for detailed searches
        for s_type in search_types:
            # OR
            print(f"\nSearching r/{subreddit} for 'cocamidopropyl' ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
            results = search_reddit(
                access_token,
                or_query,
                subreddit=subreddit,
                limit=100,
                time_filter='year',
                sort='top',
                search_type=s_type,
                max_results=300
            )
            out_name = f"reddit_{subreddit.lower()}_cocamidopropyl_or_{'posts' if s_type=='link' else 'comments'}_top.json"
            out_path = os.path.join(SUB_OR_DIR, out_name)
            save_search_results(results, out_path, 'or', or_query, s_type, subreddit)
            time.sleep(1)
            # AND
            print(f"\nSearching r/{subreddit} for 'cocamidopropyl AND hair' ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
            results = search_reddit(
                access_token,
                and_query,
                subreddit=subreddit,
                limit=100,
                time_filter='year',
                sort='top',
                search_type=s_type,
                max_results=300
            )
            out_name = f"reddit_{subreddit.lower()}_cocamidopropyl_and_{secondary_term}_{'posts' if s_type=='link' else 'comments'}_top.json"
            out_path = os.path.join(SUB_AND_DIR, out_name)
            save_search_results(results, out_path, 'and', and_query, s_type, subreddit)
            time.sleep(1)
            # Secondary only
            print(f"\nSearching r/{subreddit} for secondary term only ({'posts' if s_type=='link' else 'comments'}) sorted by top...")
            results = search_reddit(
                access_token,
                secondary_only_query,
                subreddit=subreddit,
                limit=100,
                time_filter='year',
                sort='top',
                search_type=s_type,
                max_results=300
            )
            out_name = f"reddit_{subreddit.lower()}_{secondary_term}_only_{'posts' if s_type=='link' else 'comments'}_top.json"
            out_path = os.path.join(SUB_SECONDARY_ONLY_DIR, out_name)
            save_search_results(results, out_path, 'secondary_only', secondary_only_query, s_type, subreddit)
            time.sleep(1)

if __name__ == "__main__":
    main() 