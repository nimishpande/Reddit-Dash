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
from datetime import datetime, timedelta

# Load credentials from .env
load_dotenv()
REDDIT_CLIENT_ID = os.getenv('REDDIT_CLIENT_ID')
REDDIT_CLIENT_SECRET = os.getenv('REDDIT_CLIENT_SECRET')
REDDIT_USER_AGENT = 'packaging_discussion_analyzer/1.0 (by /u/your_username)'

# Directory structure
BASE_DIR = 'reddit_packaging_data'
JSON_DIR = os.path.join(BASE_DIR, 'json')
SKINCARE_DIR = os.path.join(JSON_DIR, 'skincare_packaging')
HAIRCARE_DIR = os.path.join(JSON_DIR, 'haircare_packaging')
CROSSOVER_DIR = os.path.join(JSON_DIR, 'crossover_packaging')

# Ensure directories exist
for d in [BASE_DIR, JSON_DIR, SKINCARE_DIR, HAIRCARE_DIR, CROSSOVER_DIR]:
    os.makedirs(d, exist_ok=True)

# Reddit API endpoints
REDDIT_TOKEN_URL = 'https://www.reddit.com/api/v1/access_token'
REDDIT_BASE_URL = 'https://oauth.reddit.com'

# Packaging search keywords
SKINCARE_KEYWORDS = [
    'skincare packaging', 'skincare bottle', 'skincare container', 'skincare design',
    'serum bottle', 'moisturizer jar', 'cleanser packaging', 'sunscreen tube',
    'toner bottle', 'essence packaging', 'face cream jar', 'eye cream container',
    'beautiful skincare', 'aesthetic skincare', 'luxury skincare packaging',
    'best skincare packaging', 'favorite skincare design', 'skincare branding',
    'skincare pump', 'skincare dropper', 'airless pump skincare'
]

HAIRCARE_KEYWORDS = [
    'haircare packaging', 'shampoo bottle', 'conditioner packaging', 'hair product design',
    'hair serum bottle', 'hair mask jar', 'styling product container',
    'hair oil bottle', 'hair treatment packaging', 'hair spray bottle',
    'beautiful haircare', 'aesthetic haircare', 'luxury haircare packaging',
    'best haircare packaging', 'favorite haircare design', 'haircare branding'
]

UNIVERSAL_DESIGN_KEYWORDS = [
    'packaging design', 'product design', 'bottle design', 'container design',
    'minimalist packaging', 'luxury packaging', 'eco friendly packaging',
    'sustainable packaging', 'aesthetic packaging', 'beautiful packaging',
    'clever packaging', 'innovative packaging', 'premium packaging'
]

# Target subreddits
SKINCARE_SUBREDDITS = [
    'SkincareAddiction', 'AsianBeauty', '30PlusSkinCare', 'SkincareAddicts',
    'ScientificSkincare', 'tretinoin', 'PanPorn'
]

HAIRCARE_SUBREDDITS = [
    'HaircareScience', 'curlyhair', 'FancyFollicles', 'haircare',
    'Hair', 'Wavyhair', 'naturalhair'
]

DESIGN_SUBREDDITS = [
    'design', 'ProductDesign', 'packaging', 'DesignPorn', 'crappydesign'
]

# Comprehensive beauty brand database
COMMON_BEAUTY_BRANDS = {
    # Skincare Brands
    'cerave', 'neutrogena', 'olay', 'clinique', 'estee lauder', 'lancome',
    'drunk elephant', 'the ordinary', 'paula\'s choice', 'skinceuticals',
    'la roche posay', 'vichy', 'avene', 'eucerin', 'aveeno', 'cetaphil',
    'glossier', 'fenty beauty', 'rare beauty', 'charlotte tilbury',
    'kiehls', 'fresh', 'origins', 'clinique', 'biossance', 'tatcha',
    'sunday riley', 'murad', 'dermalogica', 'philosophy', 'clinique',
    'shiseido', 'sk-ii', 'laneige', 'innisfree', 'cosrx', 'the face shop',
    'etude house', 'missha', 'nature republic', 'tony moly', 'banila co',
    'belif', 'dr jart', 'klairs', 'purito', 'iunik', 'beauty of joseon',
    'round lab', 'torriden', 'anua', 'manyo', 'isntree', 'haruharu wonder',
    'goodal', 'pyunkang yul', 'hada labo', 'curel', 'ceramol', 'bioderma',
    'filorga', 'caudalie', 'nuxe', 'uriage', 'sanoflore', 'melvita',
    'weleda', 'dr hauschka', 'annemarie borlind', 'lavera', 'alverde',
    'balea', 'isana', 'dm', 'rossmann', 'muller', 'douglas',
    
    # Haircare Brands
    'tresemme', 'pantene', 'head shoulders', 'herbal essences', 'aussie',
    'garnier', 'loreal', 'schwarzkopf', 'matrix', 'redken', 'paul mitchell',
    'wella', 'toni guy', 'bed head', 'tigi', 'bumble and bumble',
    'living proof', 'olaplex', 'k18', 'briogeo', 'amika', 'moroccanoil',
    'it\'s a 10', 'kerastase', 'oribe', 'bumble and bumble', 'aveda',
    'joico', 'kenra', 'biolage', 'matrix', 'redken', 'paul mitchell',
    'wella', 'toni guy', 'bed head', 'tigi', 'bumble and bumble',
    'living proof', 'olaplex', 'k18', 'briogeo', 'amika', 'moroccanoil',
    'it\'s a 10', 'kerastase', 'oribe', 'bumble and bumble', 'aveda',
    'joico', 'kenra', 'biolage', 'matrix', 'redken', 'paul mitchell',
    
    # Luxury Brands
    'chanel', 'dior', 'ysl', 'guerlain', 'sisley', 'la mer', 'la prairie',
    'valmont', 'swiss perfection', 'cellcosmet', 'cellmen', 'juvena',
    'algenist', 'tatcha', 'sunday riley', 'drunk elephant', 'biossance',
    'fresh', 'origins', 'kiehls', 'clinique', 'estee lauder', 'lancome',
    'clarins', 'givenchy', 'hermes', 'tom ford', 'byredo', 'diptyque',
    'jo malone', 'penhaligons', 'creed', 'bond no 9', 'kilian',
    
    # Drugstore Brands
    'cerave', 'neutrogena', 'olay', 'aveeno', 'cetaphil', 'eucerin',
    'dove', 'dove men', 'nivea', 'vaseline', 'aquaphor', 'cerave',
    'neutrogena', 'olay', 'aveeno', 'cetaphil', 'eucerin', 'dove',
    'nivea', 'vaseline', 'aquaphor', 'cerave', 'neutrogena', 'olay',
    'aveeno', 'cetaphil', 'eucerin', 'dove', 'nivea', 'vaseline',
    
    # K-Beauty Brands
    'laneige', 'innisfree', 'cosrx', 'the face shop', 'etude house',
    'missha', 'nature republic', 'tony moly', 'banila co', 'belif',
    'dr jart', 'klairs', 'purito', 'iunik', 'beauty of joseon',
    'round lab', 'torriden', 'anua', 'manyo', 'isntree', 'haruharu wonder',
    'goodal', 'pyunkang yul', 'hada labo', 'curel', 'ceramol',
    
    # J-Beauty Brands
    'shiseido', 'sk-ii', 'hada labo', 'curel', 'ceramol', 'bioderma',
    'filorga', 'caudalie', 'nuxe', 'uriage', 'sanoflore', 'melvita',
    'weleda', 'dr hauschka', 'annemarie borlind', 'lavera', 'alverde',
    'balea', 'isana', 'dm', 'rossmann', 'muller', 'douglas'
}

# Common words to exclude from brand detection
EXCLUDED_WORDS = {
    'this', 'that', 'what', 'when', 'where', 'how', 'why', 'the', 'and', 'but', 'for',
    'with', 'from', 'into', 'during', 'including', 'until', 'against', 'among',
    'throughout', 'despite', 'towards', 'upon', 'concerning', 'regarding',
    'about', 'above', 'across', 'after', 'along', 'amid', 'around', 'at',
    'before', 'behind', 'below', 'beneath', 'beside', 'between', 'beyond',
    'by', 'down', 'except', 'for', 'from', 'in', 'inside', 'into', 'like',
    'near', 'of', 'off', 'on', 'onto', 'out', 'outside', 'over', 'past',
    'since', 'through', 'throughout', 'to', 'toward', 'under', 'underneath',
    'until', 'up', 'upon', 'with', 'within', 'without',
    'first', 'second', 'third', 'fourth', 'fifth', 'sixth', 'seventh',
    'eighth', 'ninth', 'tenth', 'eleventh', 'twelfth', 'thirteenth',
    'fourteenth', 'fifteenth', 'sixteenth', 'seventeenth', 'eighteenth',
    'nineteenth', 'twentieth',
    'january', 'february', 'march', 'april', 'may', 'june', 'july',
    'august', 'september', 'october', 'november', 'december',
    'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'
}

def get_reddit_token():
    """Get Reddit OAuth access token using client credentials flow"""
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        print("Error: Missing Reddit credentials in .env file")
        return None
    
    credentials = f"{REDDIT_CLIENT_ID}:{REDDIT_CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    
    headers = {
        'Authorization': f'Basic {encoded_credentials}',
        'User-Agent': REDDIT_USER_AGENT,
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    data = {'grant_type': 'client_credentials'}
    
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

def search_reddit_packaging(access_token, query, subreddit=None, limit=100, time_filter='year', sort='top', search_type='link', max_results=25):
    """
    Search Reddit for packaging-related posts with 2-year timeframe.
    Returns top 25 posts sorted by score (upvotes).
    """
    headers = {
        'Authorization': f'Bearer {access_token}',
        'User-Agent': REDDIT_USER_AGENT
    }
    
    if subreddit:
        search_url = f"{REDDIT_BASE_URL}/r/{subreddit}/search"
    else:
        search_url = f"{REDDIT_BASE_URL}/search"
    
    # Use 2-year timeframe
    params = {
        'q': query,
        'limit': min(limit, 100),
        't': 'year',  # Will search past year, we'll filter for 2 years in post-processing
        'sort': 'top',  # Always sort by top voted
        'type': search_type
    }
    
    all_results = []
    after = None
    fetched = 0
    
    while fetched < max_results * 2:  # Fetch more to account for filtering
        if after:
            params['after'] = after
        else:
            params.pop('after', None)
            
        try:
            response = requests.get(search_url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json().get('data', {})
            children = data.get('children', [])
            
            if not children:
                break
                
            # Filter for posts from last 2 years
            two_years_ago = datetime.now().timestamp() - (2 * 365 * 24 * 60 * 60)
            filtered_children = []
            
            for child in children:
                post_time = child.get('data', {}).get('created_utc', 0)
                if post_time >= two_years_ago:
                    filtered_children.append(child)
            
            all_results.extend(filtered_children)
            fetched += len(children)
            after = data.get('after')
            
            if not after or not children:
                break
                
        except Exception as e:
            print(f"Error searching Reddit: {e}")
            break
            
        time.sleep(0.5)  # Rate limiting
    
    # Sort by score (upvotes) and return top 25
    sorted_results = sorted(all_results, key=lambda x: x.get('data', {}).get('score', 0), reverse=True)
    return sorted_results[:max_results]

def detect_image_links(text):
    """
    Detect if post contains image links.
    Returns score: 2 for direct images, 1 for image hosts, 0 for none
    """
    if not text:
        return 0
    
    image_patterns = [
        r'imgur\.com',
        r'i\.redd\.it',
        r'i\.imgur\.com',
        r'reddit\.com/gallery',
        r'redgifs\.com',
        r'\.jpg',
        r'\.jpeg',
        r'\.png',
        r'\.gif',
        r'instagram\.com',
        r'pinterest\.com'
    ]
    
    score = 0
    text_lower = text.lower()
    
    for pattern in image_patterns:
        if re.search(pattern, text_lower):
            if any(ext in pattern for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                score = 2  # Direct image link
                break
            else:
                score = max(score, 1)  # Image hosting platform
    
    return score

def extract_brand_mentions(text, existing_brands=None):
    """
    Extract ONLY verified brand mentions from text.
    Only returns brands that are in our verified beauty brand database.
    """
    if not text:
        return []
    
    mentioned_brands = []
    text_lower = text.lower()
    
    # ONLY check against our comprehensive beauty brand database
    for brand in COMMON_BEAUTY_BRANDS:
        brand_lower = brand.lower()
        # Use word boundary matching to avoid partial matches
        if re.search(r'\b' + re.escape(brand_lower) + r'\b', text_lower):
            mentioned_brands.append(brand)
    
    return list(set(mentioned_brands))

def analyze_packaging_relevance(post_data, comments=None):
    """
    Analyze how relevant a post is to packaging discussions.
    Returns relevance score and category classification.
    """
    title = post_data.get('title', '').lower()
    body = post_data.get('selftext', '').lower()
    post_text = f"{title} {body}"
    
    # STRICT beauty/packaging context validation
    beauty_context_terms = [
        'skincare', 'skin care', 'haircare', 'hair care', 'beauty', 'cosmetics',
        'serum', 'moisturizer', 'cleanser', 'shampoo', 'conditioner', 'makeup',
        'product', 'brand', 'routine', 'skincare routine', 'hair routine'
    ]
    
    # Check if post has ANY beauty context
    has_beauty_context = any(term in post_text for term in beauty_context_terms)
    
    if not has_beauty_context:
        return {
            'relevance_score': 0,
            'design_terms_count': 0,
            'ux_terms_count': 0,
            'recommendation_terms_count': 0,
            'post_type': 'irrelevant',
            'rejected_reason': 'no_beauty_context'
        }
    
    # Design terminology scoring
    design_terms = [
        'packaging', 'bottle', 'container', 'jar', 'tube', 'pump', 'dropper',
        'design', 'aesthetic', 'beautiful', 'gorgeous', 'sleek', 'minimalist',
        'luxury', 'premium', 'elegant', 'chic', 'stylish', 'branding',
        'label', 'logo', 'color', 'frosted', 'clear', 'matte', 'glossy'
    ]
    
    design_score = sum(1 for term in design_terms if term in post_text)
    
    # User experience terms
    ux_terms = [
        'easy to use', 'hard to use', 'convenient', 'messy', 'waste',
        'pump works', 'pump broken', 'dropper', 'squeeze', 'dispenser'
    ]
    
    ux_score = sum(1 for term in ux_terms if term in post_text)
    
    # Question/recommendation indicators
    rec_terms = [
        'favorite', 'best', 'recommend', 'suggestions', 'opinions',
        'thoughts', 'what do you think', 'help me choose', 'looking for'
    ]
    
    rec_score = sum(1 for term in rec_terms if term in post_text)
    
    # Calculate total relevance score
    relevance_score = (design_score * 2) + ux_score + rec_score
    
    # Classify post type
    post_type = 'discussion'
    if any(term in post_text for term in ['favorite', 'best', 'recommend', 'suggestions']):
        post_type = 'recommendation_request'
    elif any(term in post_text for term in ['review', 'thoughts on', 'using']):
        post_type = 'review_showcase'
    
    return {
        'relevance_score': relevance_score,
        'design_terms_count': design_score,
        'ux_terms_count': ux_score,
        'recommendation_terms_count': rec_score,
        'post_type': post_type,
        'has_beauty_context': has_beauty_context
    }

def classify_packaging_category(post_data, comments=None):
    """
    Classify post into skincare, haircare, or crossover category.
    """
    title = post_data.get('title', '').lower()
    body = post_data.get('selftext', '').lower()
    post_text = f"{title} {body}"
    
    # Add comments to analysis
    if comments:
        comment_text = ' '.join([c.get('body', '') for c in comments[:10]])  # Top 10 comments
        post_text += f" {comment_text.lower()}"
    
    # Skincare indicators
    skincare_terms = [
        'skincare', 'skin care', 'serum', 'moisturizer', 'cleanser', 'toner',
        'essence', 'face cream', 'eye cream', 'sunscreen', 'retinol', 'vitamin c',
        'hyaluronic acid', 'niacinamide', 'salicylic acid', 'glycolic acid'
    ]
    
    # Haircare indicators
    haircare_terms = [
        'haircare', 'hair care', 'shampoo', 'conditioner', 'hair mask', 'hair oil',
        'hair serum', 'styling', 'hair product', 'scalp', 'hair treatment',
        'leave in', 'curl cream', 'hair gel', 'mousse', 'hair spray'
    ]
    
    skincare_count = sum(1 for term in skincare_terms if term in post_text)
    haircare_count = sum(1 for term in haircare_terms if term in post_text)
    
    if skincare_count > 0 and haircare_count > 0:
        return 'crossover'
    elif skincare_count > haircare_count:
        return 'skincare'
    elif haircare_count > skincare_count:
        return 'haircare'
    else:
        # Default classification based on subreddit
        subreddit = post_data.get('subreddit', '').lower()
        if any(sub in subreddit for sub in ['skincare', 'asianbeauty', 'tretinoin']):
            return 'skincare'
        elif any(sub in subreddit for sub in ['hair', 'curly']):
            return 'haircare'
        else:
            return 'general'

def calculate_engagement_score(post_data, image_bonus=0, relevance_data=None):
    """
    Calculate engagement score for ranking posts.
    Formula: (upvotes × 0.3) + (comments × 0.4) + (image_bonus × 0.2) + (relevance × 0.1)
    """
    upvotes = max(post_data.get('score', 0), 0)
    comments = max(post_data.get('num_comments', 0), 0)
    relevance = relevance_data.get('relevance_score', 0) if relevance_data else 0
    
    engagement_score = (upvotes * 0.3) + (comments * 0.4) + (image_bonus * 0.2) + (relevance * 0.1)
    
    return engagement_score

def fetch_post_comments_packaging(access_token, post_id, max_comments=50):
    """
    Fetch comments for packaging analysis.
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
        
        if isinstance(data, list) and len(data) > 1:
            comments = data[1].get('data', {}).get('children', [])
            comment_list = []
            
            for c in comments:
                cdata = c.get('data', {})
                author = cdata.get('author', '').lower()
                
                # Skip AutoModerator and other bot comments
                if author in ['automoderator', 'moderator', 'bot', 'reddit']:
                    continue
                    
                if c.get('kind') == 't1' and cdata.get('body') and cdata.get('author'):
                    comment_data = {
                        'author': cdata.get('author'),
                        'body': cdata.get('body').strip(),
                        'score': cdata.get('score', 0),
                        'created_utc': cdata.get('created_utc'),
                        'id': cdata.get('id')
                    }
                    comment_list.append(comment_data)
            
            return comment_list
            
    except Exception as e:
        print(f"[WARN] Could not fetch comments for post {post_id}: {e}")
    
    return []

def search_packaging_discussions(access_token):
    """
    Main function to search for packaging discussions across Reddit.
    """
    print("🔍 Starting comprehensive packaging discussion search...")
    
    all_posts = {
        'skincare': [],
        'haircare': [],
        'crossover': []
    }
    
    discovered_brands = set(COMMON_BEAUTY_BRANDS)
    rejected_posts = []  # Track rejected posts for debugging
    
    # Phase 1: Broad Reddit search with packaging keywords
    print("\n📡 Phase 1: Broad Reddit search...")
    
    all_keywords = SKINCARE_KEYWORDS + HAIRCARE_KEYWORDS + UNIVERSAL_DESIGN_KEYWORDS
    
    for i, keyword in enumerate(all_keywords[:15]):  # Limit to first 15 to avoid rate limits
        print(f"Searching for: '{keyword}' ({i+1}/{min(15, len(all_keywords))}) - Top 25 posts")
        
        results = search_reddit_packaging(
            access_token,
            keyword,
            limit=50,
            time_filter='year',
            sort='top',
            search_type='link',
            max_results=25
        )
        
        print(f"   Found {len(results)} posts, filtering by engagement and beauty context...")
        processed_count = 0
        rejected_count = 0
        
        for result in results:
            post_data = result.get('data', {})
            
            # Check minimum engagement requirements
            upvotes = post_data.get('score', 0)
            num_comments = post_data.get('num_comments', 0)
            
            if upvotes < 10 or num_comments < 5:
                rejected_count += 1
                rejected_posts.append({
                    'title': post_data.get('title', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'reason': 'low_engagement',
                    'upvotes': upvotes,
                    'comments': num_comments
                })
                continue
            
            # Analyze packaging relevance with strict beauty context validation
            relevance_data = analyze_packaging_relevance(post_data)
            
            # Reject posts without beauty context
            if not relevance_data.get('has_beauty_context', False):
                rejected_count += 1
                rejected_posts.append({
                    'title': post_data.get('title', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'reason': 'no_beauty_context',
                    'upvotes': upvotes,
                    'comments': num_comments
                })
                continue
                
            # Reject posts with very low relevance scores
            if relevance_data['relevance_score'] < 2:
                rejected_count += 1
                rejected_posts.append({
                    'title': post_data.get('title', ''),
                    'subreddit': post_data.get('subreddit', ''),
                    'reason': 'low_relevance',
                    'relevance_score': relevance_data['relevance_score'],
                    'upvotes': upvotes,
                    'comments': num_comments
                })
                continue
            
            # Detect images
            post_text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
            image_bonus = detect_image_links(post_text)
            
            # Extract brands
            brands = extract_brand_mentions(post_text, discovered_brands)
            discovered_brands.update(brands)
            
            # Fetch comments
            post_id = post_data.get('id')
            comments = []
            if post_id:
                comments = fetch_post_comments_packaging(access_token, post_id, max_comments=30)
            
            # Classify category
            category = classify_packaging_category(post_data, comments)
            
            if category in ['skincare', 'haircare', 'crossover']:
                # Calculate engagement score
                engagement_score = calculate_engagement_score(post_data, image_bonus, relevance_data)
                
                post_entry = {
                    'post_data': post_data,
                    'comments': comments,
                    'category': category,
                    'relevance_data': relevance_data,
                    'image_score': image_bonus,
                    'brands_mentioned': brands,
                    'engagement_score': engagement_score,
                    'search_keyword': keyword
                }
                
                all_posts[category].append(post_entry)
                processed_count += 1
        
        print(f"   ✓ Processed {processed_count} qualifying posts")
        time.sleep(1)  # Rate limiting
    
    # Phase 2: Targeted subreddit search
    print(f"\n🎯 Phase 2: Targeted subreddit search...")
    print(f"Discovered {len(discovered_brands)} brands so far")
    
    all_subreddits = SKINCARE_SUBREDDITS + HAIRCARE_SUBREDDITS + DESIGN_SUBREDDITS
    
    for subreddit in all_subreddits[:10]:  # Limit subreddits to avoid rate limits
        print(f"Searching r/{subreddit}...")
        
        # Search with top packaging terms
        top_terms = ['packaging', 'bottle design', 'aesthetic', 'beautiful products']
        
        for term in top_terms:
            results = search_reddit_packaging(
                access_token,
                term,
                subreddit=subreddit,
                limit=25,
                sort='top',
                max_results=25
            )
            
            for result in results:
                post_data = result.get('data', {})
                
                # Check minimum engagement
                if post_data.get('score', 0) < 10 or post_data.get('num_comments', 0) < 5:
                    continue
                
                # Check if we already have this post
                post_id = post_data.get('id')
                already_exists = False
                for category in all_posts:
                    for existing_post in all_posts[category]:
                        if existing_post['post_data'].get('id') == post_id:
                            already_exists = True
                            break
                    if already_exists:
                        break
                
                if already_exists:
                    continue
                
                # Process similar to Phase 1
                relevance_data = analyze_packaging_relevance(post_data)
                if relevance_data['relevance_score'] < 1:
                    continue
                
                post_text = f"{post_data.get('title', '')} {post_data.get('selftext', '')}"
                image_bonus = detect_image_links(post_text)
                brands = extract_brand_mentions(post_text, discovered_brands)
                
                comments = []
                if post_id:
                    comments = fetch_post_comments_packaging(access_token, post_id, max_comments=30)
                
                category = classify_packaging_category(post_data, comments)
                
                if category in ['skincare', 'haircare', 'crossover']:
                    engagement_score = calculate_engagement_score(post_data, image_bonus, relevance_data)
                    
                    post_entry = {
                        'post_data': post_data,
                        'comments': comments,
                        'category': category,
                        'relevance_data': relevance_data,
                        'image_score': image_bonus,
                        'brands_mentioned': brands,
                        'engagement_score': engagement_score,
                        'search_keyword': term,
                        'source_subreddit': subreddit
                    }
                    
                    all_posts[category].append(post_entry)
            
            time.sleep(0.5)
    
    # Show examples of rejected posts for debugging
    if rejected_posts:
        print(f"\n🚫 Examples of rejected posts:")
        print(f"   Total rejected: {len(rejected_posts)}")
        
        # Group by reason
        by_reason = {}
        for post in rejected_posts:
            reason = post['reason']
            if reason not in by_reason:
                by_reason[reason] = []
            by_reason[reason].append(post)
        
        for reason, posts in by_reason.items():
            print(f"\n   {reason.replace('_', ' ').title()} ({len(posts)} posts):")
            for post in posts[:3]:  # Show first 3 examples
                print(f"      • r/{post['subreddit']}: {post['title'][:80]}...")
    
    return all_posts, discovered_brands

def validate_brand_extraction(discovered_brands):
    """
    Validate and report on brand extraction quality.
    ONLY return verified beauty brands.
    """
    print(f"\n🔍 Brand Extraction Validation:")
    print(f"   Total brands discovered: {len(discovered_brands)}")
    
    # ONLY keep verified beauty brands
    verified_brands = []
    rejected_brands = []
    
    for brand in discovered_brands:
        if brand.lower() in [b.lower() for b in COMMON_BEAUTY_BRANDS]:
            verified_brands.append(brand)
        else:
            rejected_brands.append(brand)
    
    print(f"   ✓ Verified beauty brands: {len(verified_brands)}")
    print(f"   ❌ Rejected non-beauty brands: {len(rejected_brands)}")
    
    if rejected_brands:
        print(f"\n   Examples of rejected brands:")
        for brand in rejected_brands[:5]:  # Show first 5
            print(f"      • {brand}")
        if len(rejected_brands) > 5:
            print(f"      ... and {len(rejected_brands) - 5} more")
    
    # Return ONLY verified brands
    return verified_brands, []

def save_packaging_results(all_posts, discovered_brands):
    """
    Save results to separate JSON files for each category.
    """
    print(f"\n💾 Saving results...")
    
    # Validate brand extraction
    verified_brands, potential_new_brands = validate_brand_extraction(discovered_brands)
    
    for category, posts in all_posts.items():
        if not posts:
            print(f"No posts found for {category} category")
            continue
        
        # Sort by engagement score and take top 25
        sorted_posts = sorted(posts, key=lambda x: x['engagement_score'], reverse=True)[:25]
        
        # Prepare output data
        output_data = {
            'category': category,
            'search_timestamp': datetime.now().isoformat(),
            'total_posts_found': len(posts),
            'top_posts_selected': len(sorted_posts),
            'posts_per_search_term': 25,
            'verified_brands': sorted(verified_brands),
            'total_brands_discovered': len(verified_brands),
            'selection_criteria': {
                'min_upvotes': 10,
                'min_comments': 5,
                'min_relevance_score': 1,
                'ranking_formula': '(upvotes × 0.3) + (comments × 0.4) + (image_bonus × 0.2) + (relevance × 0.1)'
            },
            'posts': []
        }
        
        for post_entry in sorted_posts:
            post_summary = {
                'reddit_id': post_entry['post_data'].get('id'),
                'title': post_entry['post_data'].get('title'),
                'subreddit': post_entry['post_data'].get('subreddit'),
                'author': post_entry['post_data'].get('author'),
                'score': post_entry['post_data'].get('score'),
                'num_comments': post_entry['post_data'].get('num_comments'),
                'created_utc': post_entry['post_data'].get('created_utc'),
                'selftext': post_entry['post_data'].get('selftext', '')[:500] + '...' if len(post_entry['post_data'].get('selftext', '')) > 500 else post_entry['post_data'].get('selftext', ''),
                'url': post_entry['post_data'].get('url'),
                'permalink': f"https://reddit.com{post_entry['post_data'].get('permalink', '')}",
                'engagement_score': round(post_entry['engagement_score'], 2),
                'relevance_score': post_entry['relevance_data']['relevance_score'],
                'post_type': post_entry['relevance_data']['post_type'],
                'has_images': post_entry['image_score'] > 0,
                'image_score': post_entry['image_score'],
                'brands_mentioned': post_entry['brands_mentioned'],
                'search_source': post_entry.get('search_keyword', 'unknown'),
                'comments_sample': [
                    {
                        'author': c.get('author'),
                        'body': c.get('body', '')[:200] + '...' if len(c.get('body', '')) > 200 else c.get('body', ''),
                        'score': c.get('score')
                    }
                    for c in post_entry['comments'][:5]  # Top 5 comments
                ]
            }
            output_data['posts'].append(post_summary)
        
        # Save to appropriate directory
        if category == 'skincare':
            output_file = os.path.join(SKINCARE_DIR, 'skincare_packaging_discussions.json')
        elif category == 'haircare':
            output_file = os.path.join(HAIRCARE_DIR, 'haircare_packaging_discussions.json')
        else:  # crossover
            output_file = os.path.join(CROSSOVER_DIR, 'crossover_packaging_discussions.json')
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Saved {len(sorted_posts)} {category} posts to {output_file}")

def main():
    """
    Main execution function.
    """
    print("🚀 Reddit Packaging Discussion Analyzer")
    print("=" * 50)
    print("📊 Search Configuration:")
    print("   • Top 25 posts per search term")
    print("   • Sorted by upvotes (top voted first)")
    print("   • Minimum 10 upvotes + 5 comments")
    print("   • 2-year timeframe")
    print("=" * 50)
    
    # Get Reddit access token
    access_token = get_reddit_token()
    if not access_token:
        print("❌ Failed to get Reddit access token")
        return
    
    # Search for packaging discussions
    all_posts, discovered_brands = search_packaging_discussions(access_token)
    
    # Print summary
    print(f"\n📊 Search Summary:")
    print(f"   Skincare posts: {len(all_posts['skincare'])}")
    print(f"   Haircare posts: {len(all_posts['haircare'])}")
    print(f"   Crossover posts: {len(all_posts['crossover'])}")
    
    # Validate brands before saving
    verified_brands, _ = validate_brand_extraction(discovered_brands)
    print(f"   ✓ Verified beauty brands: {len(verified_brands)}")
    
    # Save results
    save_packaging_results(all_posts, discovered_brands)
    
    print(f"\n🎉 Analysis complete! Check the output directories:")
    print(f"   📁 {SKINCARE_DIR}")
    print(f"   📁 {HAIRCARE_DIR}")
    print(f"   📁 {CROSSOVER_DIR}")

if __name__ == "__main__":
    main()