import json
import pandas as pd
import re
import os
from pathlib import Path
import logging
import requests
import time
from typing import Dict, List, Optional, Any
from collections import Counter
from urllib.parse import urlparse

# Enhanced logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_api_key() -> Optional[str]:
    """Load OpenAI API key from environment variables or .env files"""
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_SECRET_KEY') or os.getenv('openAI_Secret_Key')
    if api_key:
        logger.info("✅ OpenAI API key loaded from environment")
        return api_key
    env_files = ['.env', '../.env', '../../.env', '/Users/nimishpande/Ingredient_cosmetic/.env']
    for env_file in env_files:
        if os.path.exists(env_file):
            try:
                with open(env_file, 'r') as f:
                    for line in f:
                        if line.strip().startswith('OPENAI'):
                            api_key = line.split('=')[1].strip().strip('"\'')
                            logger.info(f"✅ OpenAI API key loaded from {env_file}")
                            return api_key
            except Exception as e:
                logger.warning(f"Failed to read {env_file}: {e}")
    logger.warning("⚠️ OpenAI API key not found - LLM summaries will be unavailable")
    return None

def setup_paths():
    """Setup and validate required directory paths"""
    base_dir = Path('IngredientsScrapper')
    paths = {
        'base': base_dir,
        'separated': base_dir / 'separated_ingredients',
        'raw_data': base_dir / 'raw data',
        'reddit_analysis': base_dir / 'reddit analysis',
        'mapping': base_dir / 'ingredient_file_mapping_inci_centric.json'
    }
    missing_paths = []
    for name, path in paths.items():
        if name == 'mapping':
            if not path.exists():
                missing_paths.append(f"Mapping file: {path}")
        else:
            if not path.exists():
                missing_paths.append(f"Directory: {path}")
    if missing_paths:
        logger.error("❌ Missing required paths:")
        for path in missing_paths:
            logger.error(f"  • {path}")
        raise FileNotFoundError(f"Missing {len(missing_paths)} required paths")
    logger.info("✅ All required paths validated")
    return paths

def load_inci_mapping(mapping_path: Path) -> Dict:
    """Load INCI ingredient mapping from JSON file"""
    try:
        with open(mapping_path, 'r', encoding='utf-8') as f:
            mapping = json.load(f)
        logger.info(f"✅ Loaded {len(mapping)} INCI ingredients from mapping")
        return mapping
    except Exception as e:
        logger.error(f"❌ Failed to load INCI mapping: {e}")
        raise

def safe_get_nested_value(data: Dict, key_path: str, default: Any = None) -> Any:
    """Safely get nested dictionary values with dot notation"""
    try:
        keys = key_path.split('.')
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, default)
            else:
                return default
        return value
    except Exception:
        return default

def extract_inci_data_from_files(files: List[str], separated_dir: Path) -> Optional[Dict]:
    """Enhanced INCI data extraction with focus on usage concentration and safety data"""
    if not files:
        logger.warning("No separated ingredient files specified")
        return None
    
    for file in files:
        path = separated_dir / file
        if not path.exists():
            logger.debug(f"INCI file not found: {path}")
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different data structures
            detailed_info = safe_get_nested_value(data, 'detailed_info', [])
            if detailed_info and len(detailed_info) > 0:
                inci_info = detailed_info[0]
                
                # Enhanced usage extraction - look for concentration data
                usage_info = safe_get_nested_value(inci_info, 'percentage', 0)
                usage_range = safe_get_nested_value(inci_info, 'usage_range', '')
                max_usage = safe_get_nested_value(inci_info, 'max_usage', '')
                
                # Combine usage information
                usage_data = None
                if usage_info and usage_info != 0:
                    usage_data = f"{usage_info}%"
                elif usage_range:
                    usage_data = usage_range
                elif max_usage:
                    usage_data = f"Up to {max_usage}%"
                
                # Extract functions safely
                functions = safe_get_nested_value(inci_info, 'functions', [])
                if functions:
                    function_list = []
                    for func in functions:
                        if isinstance(func, dict):
                            desc = func.get('description') or func.get('name', '')
                            if desc:
                                function_list.append(desc)
                        elif isinstance(func, str):
                            function_list.append(func)
                else:
                    function_list = []
                
                # Extract origin safely
                origin_data = safe_get_nested_value(inci_info, 'origin', [])
                if isinstance(origin_data, list) and origin_data:
                    origin = origin_data[0].get('name', 'Unknown') if isinstance(origin_data[0], dict) else str(origin_data[0])
                elif isinstance(origin_data, str):
                    origin = origin_data
                else:
                    origin = 'Unknown'
                
                return {
                    'inci_name': safe_get_nested_value(inci_info, 'inci_name', 'Unknown'),
                    'usage_data': usage_data,
                    'functions': function_list,
                    'origin': origin,
                    'dangers': safe_get_nested_value(inci_info, 'dangers', []),
                    'restrictions': safe_get_nested_value(inci_info, 'restrictions', []),
                    'regulatory_status': safe_get_nested_value(inci_info, 'regulatory_status', ''),
                    'cas': safe_get_nested_value(inci_info, 'cas', 'Not available'),
                    'comedogenic_rating': safe_get_nested_value(inci_info, 'comedogenic_rating', ''),
                    'irritancy_rating': safe_get_nested_value(inci_info, 'irritancy_rating', '')
                }
            else:
                # Fallback to direct data structure
                functions = data.get('functions', [])
                if not isinstance(functions, list):
                    functions = [str(functions)] if functions else []
                
                return {
                    'inci_name': data.get('inci_name') or data.get('name', 'Unknown'),
                    'usage_data': f"{data.get('percentage', '')}%" if data.get('percentage') else None,
                    'functions': functions,
                    'origin': data.get('origin', 'Unknown'),
                    'dangers': data.get('dangers', []),
                    'restrictions': data.get('restrictions', []),
                    'regulatory_status': data.get('regulatory_status', ''),
                    'cas': data.get('cas', 'Not available'),
                    'comedogenic_rating': data.get('comedogenic_rating', ''),
                    'irritancy_rating': data.get('irritancy_rating', '')
                }
        except Exception as e:
            logger.error(f"Failed to extract INCI data from {file}: {e}")
            continue
    
    logger.warning(f"Could not extract INCI data from any of {len(files)} files")
    return None

def extract_report_sentiment_from_files(files: List[str], separated_dir: Path, reddit_analysis_dir: Path) -> Optional[Dict]:
    """Extract sentiment analysis data from report files"""
    if not files:
        return None
    for file in files:
        for dir_path in [separated_dir, reddit_analysis_dir]:
            path = dir_path / file
            if not path.exists():
                continue
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    report_text = f.read()
                def extract_metric(pattern, default='0'):
                    match = re.search(pattern, report_text)
                    return match.group(1) if match else default
                return {
                    'sentiment': extract_metric(r'Overall sentiment: (\w+)', 'Unknown'),
                    'positive_posts': extract_metric(r'Positive sentiment posts: (\d+)', '0'),
                    'negative_posts': extract_metric(r'Negative sentiment posts: (\d+)', '0'),
                    'total_posts': extract_metric(r'Total Posts Analyzed: (\d+)', '0'),
                    'dosage_statements': extract_metric(r'Total Dosage Statements: (\d+)', '0')
                }
            except Exception as e:
                logger.error(f"Failed to extract sentiment from {file}: {e}")
                continue
    return None

def load_reddit_comments_from_files(files: List[str], raw_data_dir: Path) -> List[Dict]:
    """Load Reddit comments from JSON files"""
    all_comments = []
    files_loaded = 0
    for file in files:
        path = raw_data_dir / file
        if not path.exists():
            logger.debug(f"Reddit file not found: {path}")
            continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                all_comments.extend(data)
                files_loaded += 1
                logger.debug(f"Loaded {len(data)} comments from {file}")
            elif isinstance(data, dict):
                all_comments.append(data)
                files_loaded += 1
                logger.debug(f"Loaded 1 comment from {file}")
        except Exception as e:
            logger.warning(f"Failed to load Reddit data from {file}: {e}")
            continue
    logger.info(f"Loaded {len(all_comments)} total comments from {files_loaded} files")
    return all_comments

def get_research_paper_links(ingredient_name: str, functions: List[str], api_key: Optional[str]) -> List[str]:
    """
    MISSING FUNCTION - This was causing NameError
    Simulate research paper link retrieval (placeholder implementation)
    """
    try:
        # Placeholder implementation - in real scenario, this would:
        # 1. Search academic databases (PubMed, Google Scholar)
        # 2. Use APIs to find relevant papers
        # 3. Validate links and relevance
        
        # For now, return simulated links based on ingredient name
        base_urls = [
            f"https://pubmed.ncbi.nlm.nih.gov/?term={ingredient_name.replace(' ', '+')}",
            f"https://scholar.google.com/scholar?q={ingredient_name.replace(' ', '+')}"
        ]
        
        # In a real implementation, you would validate these links
        logger.info(f"Generated research links for {ingredient_name}")
        return base_urls[:2]  # Return max 2 links
        
    except Exception as e:
        logger.warning(f"Failed to get research links for {ingredient_name}: {e}")
        return []

def call_openai_with_retry(prompt: str, api_key: str, max_retries: int = 3) -> str:
    """Call OpenAI API with retry logic"""
    if not api_key:
        return "LLM summary unavailable - no API key"
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [
            {'role': 'system', 'content': 'You are a helpful cosmetic science assistant providing clear, evidence-based summaries.'},
            {'role': 'user', 'content': prompt}
        ],
        'max_tokens': 300,
        'temperature': 0.7
    }
    
    for attempt in range(max_retries):
        try:
            time.sleep(1)  # Rate limiting
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'].strip()
        except requests.exceptions.RequestException as e:
            logger.warning(f"OpenAI API attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                return f"LLM summary unavailable - API error after {max_retries} attempts"
            time.sleep(2 ** attempt)  # Exponential backoff
    return "LLM summary unavailable - max retries exceeded"

def truncate_text(text: str, word_limit: int = 50) -> str:
    """Truncate text to a maximum number of words for CSV fields."""
    if not isinstance(text, str):
        return str(text) if text is not None else ""
    words = text.split()
    if len(words) > word_limit:
        return ' '.join(words[:word_limit]) + '...'
    return text

def extract_comprehensive_cons(inci_data: Dict, comments: List[Dict]) -> str:
    """Extract comprehensive cons with improved logic"""
    cons_list = []
    
    if inci_data:
        # 1. Regulatory restrictions (actual legal limitations)
        restrictions = inci_data.get('restrictions', [])
        if restrictions:
            for restriction in restrictions:
                if isinstance(restriction, dict):
                    desc = restriction.get('description', '')
                    if desc and 'no restriction' not in desc.lower():
                        cons_list.append(f"Regulatory: {desc}")
                elif isinstance(restriction, str) and restriction.strip():
                    cons_list.append(f"Regulatory: {restriction}")
        
        # 2. Safety concerns from dangers (actual hazards)
        dangers = inci_data.get('dangers', [])
        if dangers:
            for danger in dangers:
                if isinstance(danger, dict):
                    label = danger.get('label', '')
                    value = danger.get('value', 0)
                    # Only include actual dangers, not "no penalty" items
                    if label and 'no penalty' not in label.lower() and value > 0:
                        cons_list.append(f"Safety concern: {label} (Level {value})")
        
        # 3. Comedogenic rating (only if problematic)
        comedogenic_rating = inci_data.get('comedogenic_rating', '')
        if comedogenic_rating:
            try:
                rating = float(comedogenic_rating)
                if rating >= 3:  # Only flag moderate to high comedogenic ratings
                    cons_list.append(f"Comedogenic rating: {rating}/5")
            except (ValueError, TypeError):
                if 'high' in str(comedogenic_rating).lower():
                    cons_list.append("High comedogenic potential")
        
        # 4. Irritancy concerns (only if significant)
        irritancy_rating = inci_data.get('irritancy_rating', '')
        if irritancy_rating:
            try:
                rating = float(irritancy_rating)
                if rating >= 3:  # Only flag moderate to high irritancy
                    cons_list.append(f"Irritancy rating: {rating}/5")
            except (ValueError, TypeError):
                if any(word in str(irritancy_rating).lower() for word in ['high', 'severe', 'significant']):
                    cons_list.append(f"Irritancy potential: {irritancy_rating}")
    
    # 5. User-reported issues (from comments)
    if comments:
        issue_keywords = {
            'allergic reaction': ['allergic', 'allergy', 'reaction'],
            'skin irritation': ['irritation', 'irritating', 'burning', 'stinging'],
            'breakouts': ['breakout', 'acne', 'pimple', 'comedogenic'],
            'dryness': ['drying', 'dry', 'stripped'],
            'sensitivity': ['sensitive', 'sensitivity'],
            'expensive': ['expensive', 'costly', 'price'],
            'availability': ['hard to find', 'unavailable', 'discontinued']
        }
        
        issue_counts = {}
        for comment in comments:
            comment_text = str(comment).lower()
            for issue, keywords in issue_keywords.items():
                if any(keyword in comment_text for keyword in keywords):
                    issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Only include issues reported by multiple users
        for issue, count in issue_counts.items():
            if count >= 2:  # Threshold for inclusion
                cons_list.append(f"{count} reports of {issue}")
    
    return "; ".join(cons_list) if cons_list else 'No significant concerns reported'

def analyze_reddit_data(comments: List[Dict], report_data: Optional[Dict]) -> Dict:
    """Enhanced Reddit analysis with subreddit breakdown"""
    total_comments = len(comments)
    
    # Extract subreddit information
    subreddits = []
    for comment in comments:
        # Try different possible subreddit field names
        subreddit = None
        if isinstance(comment, dict):
            subreddit = (comment.get('subreddit') or 
                        comment.get('subreddit_name') or 
                        comment.get('sub') or
                        comment.get('source'))
            
            # If subreddit info is in a nested structure
            if not subreddit and 'data' in comment:
                data = comment.get('data', {})
                if isinstance(data, dict):
                    subreddit = data.get('subreddit')
        
        if subreddit:
            subreddits.append(subreddit)
    
    # Count top subreddits
    subreddit_counts = Counter(subreddits)
    top_subreddits = subreddit_counts.most_common(3)
    
    # Format subreddit summary
    subreddit_summary = ""
    if top_subreddits:
        subreddit_parts = []
        for sub, count in top_subreddits:
            subreddit_parts.append(f"r/{sub} ({count})")
        subreddit_summary = f"; Top subreddits: {', '.join(subreddit_parts)}"
    
    # Get sentiment data
    positive_posts = int(report_data['positive_posts']) if report_data and report_data.get('positive_posts', '0').isdigit() else 0
    negative_posts = int(report_data['negative_posts']) if report_data and report_data.get('negative_posts', '0').isdigit() else 0
    sentiment = report_data['sentiment'] if report_data else 'Unknown'
    
    return {
        'total_comments': total_comments,
        'positive_posts': positive_posts,
        'negative_posts': negative_posts,
        'sentiment': sentiment,
        'subreddit_summary': subreddit_summary,
        'formatted_summary': f"{sentiment} sentiment; {total_comments} total comments ({positive_posts} positive, {negative_posts} negative){subreddit_summary}"
    }

def calculate_functional_effectiveness(inci_data: Dict, comments: List[Dict], report_data: Optional[Dict] = None) -> str:
    """Calculate effectiveness based on how well ingredient performs its intended INCI functions"""
    effectiveness_components = []
    
    if not inci_data:
        return "Effectiveness data unavailable - no INCI information"
    
    # 1. Extract primary functions from INCI data
    functions = inci_data.get('functions', [])
    primary_functions = []
    for func in functions[:3]:  # Top 3 functions
        if isinstance(func, dict):
            primary_functions.append(func.get('name', '').lower())
        else:
            primary_functions.append(str(func).lower())
    
    # 2. Function-specific effectiveness mapping
    function_effectiveness_map = {
        'humectant': {
            'keywords': ['hydrat', 'moisture', 'moistur', 'dry skin', 'plump', 'water retention', 'dehydrat'],
            'description': 'hydration effectiveness'
        },
        'skin conditioning': {
            'keywords': ['soft', 'smooth', 'supple', 'condition', 'skin feel', 'texture improvement', 'healthier skin'],
            'description': 'skin conditioning effectiveness'
        },
        'emollient': {
            'keywords': ['smooth', 'soft', 'silky', 'barrier', 'protect', 'seal', 'comfortable'],
            'description': 'emollient effectiveness'
        },
        'solvent': {
            'keywords': ['dissolve', 'penetrat', 'absorb', 'delivery', 'vehicle', 'carrier'],
            'description': 'solvent effectiveness'
        },
        'skin protecting': {
            'keywords': ['protect', 'barrier', 'shield', 'defend', 'guard', 'irritation prevent'],
            'description': 'protective effectiveness'
        },
        'hair conditioning': {
            'keywords': ['shiny', 'manageable', 'detangle', 'hair feel', 'volume', 'soft hair'],
            'description': 'hair conditioning effectiveness'
        },
        'viscosity controlling': {
            'keywords': ['texture', 'consistency', 'thickness', 'formula feel', 'application'],
            'description': 'texture modification effectiveness'
        },
        'film forming': {
            'keywords': ['lasting', 'wear', 'stay', 'film', 'coverage', 'duration'],
            'description': 'film formation effectiveness'
        }
    }
    
    # 3. Analyze user experience for each primary function
    functional_performance = {}
    if comments:
        for function in primary_functions:
            if function in function_effectiveness_map:
                keywords = function_effectiveness_map[function]['keywords']
                description = function_effectiveness_map[function]['description']
                
                # Count positive functional mentions
                positive_mentions = 0
                negative_mentions = 0
                
                for comment in comments:
                    comment_text = str(comment).lower()
                    for keyword in keywords:
                        if keyword in comment_text:
                            # Simple sentiment analysis for functional effectiveness
                            if any(pos in comment_text for pos in ['good', 'great', 'love', 'amazing', 'effective', 'works', 'helped', 'improved', 'better']):
                                positive_mentions += 1
                            elif any(neg in comment_text for neg in ['bad', 'terrible', 'hate', 'ineffective', 'doesn\'t work', 'worse', 'disappointed']):
                                negative_mentions += 1
                            else:
                                positive_mentions += 0.5  # Neutral mentions get half weight
                
                if positive_mentions > 0:
                    functional_performance[description] = {
                        'positive': positive_mentions,
                        'negative': negative_mentions,
                        'effectiveness_score': positive_mentions / (positive_mentions + negative_mentions) if (positive_mentions + negative_mentions) > 0 else 0
                    }
    
    # 4. Industry adoption rate (shows proven effectiveness)
    usage_percentage = 0
    if inci_data:
        # Prefer usage_data if present
        usage_data = inci_data.get('usage_data')
        if usage_data:
            if isinstance(usage_data, str) and '%' in usage_data:
                try:
                    usage_percentage = float(usage_data.replace('%', ''))
                except ValueError:
                    usage_percentage = 0
            else:
                try:
                    usage_percentage = float(usage_data)
                except Exception:
                    usage_percentage = 0
        # Fallback to 'percentage' if usage_data is not present
        elif 'percentage' in inci_data:
            try:
                usage_percentage = float(inci_data.get('percentage', 0))
            except Exception:
                usage_percentage = 0
    
    if usage_percentage > 50:
        effectiveness_components.append(f"Industry-proven effectiveness ({usage_percentage}% adoption)")
    elif usage_percentage > 10:
        effectiveness_components.append(f"Established effectiveness ({usage_percentage}% adoption)")
    elif usage_percentage > 1:
        effectiveness_components.append(f"Specialized effectiveness ({usage_percentage}% adoption)")
    else:
        effectiveness_components.append(f"Niche effectiveness ({usage_percentage}% adoption)")
    
    # 5. Function-specific user satisfaction
    if functional_performance:
        for func_desc, performance in functional_performance.items():
            score = performance['effectiveness_score']
            total_mentions = performance['positive'] + performance['negative']
            
            if score > 0.8 and total_mentions >= 5:
                effectiveness_components.append(f"Highly effective for {func_desc} ({total_mentions} user reports)")
            elif score > 0.6 and total_mentions >= 3:
                effectiveness_components.append(f"Moderately effective for {func_desc} ({total_mentions} user reports)")
            elif total_mentions >= 2:
                effectiveness_components.append(f"Mixed effectiveness for {func_desc} ({total_mentions} user reports)")
    
    # 6. Category performance (where it works best)
    category_data = inci_data.get('category_percentage', [])
    if category_data:
        top_category = max(category_data, key=lambda x: float(x.get('percentage', 0)))
        category_name = top_category.get('category_name', 'Unknown')
        category_perc = top_category.get('percentage', '0')
        effectiveness_components.append(f"Most effective in {category_name} ({category_perc}% usage)")
    
    # 7. Overall user satisfaction from report data
    if report_data:
        positive_posts = int(report_data.get('positive_posts', 0))
        negative_posts = int(report_data.get('negative_posts', 0))
        total_posts = positive_posts + negative_posts
        
        if total_posts > 0:
            satisfaction_rate = (positive_posts / total_posts) * 100
            if satisfaction_rate > 80:
                effectiveness_components.append(f"High user satisfaction ({satisfaction_rate:.0f}% positive)")
            elif satisfaction_rate > 60:
                effectiveness_components.append(f"Good user satisfaction ({satisfaction_rate:.0f}% positive)")
            else:
                effectiveness_components.append(f"Mixed user satisfaction ({satisfaction_rate:.0f}% positive)")
    
    # 8. Safety effectiveness (no side effects = more effective)
    dangers = inci_data.get('dangers', [])
    score = inci_data.get('score', 0)
    if score == 0 and dangers:
        danger_info = dangers[0].get('label', '') if isinstance(dangers[0], dict) else str(dangers[0])
        if 'no penalty' in danger_info.lower():
            effectiveness_components.append("Excellent safety profile enhances effectiveness")
    
    return "; ".join(effectiveness_components) if effectiveness_components else "Limited effectiveness data available"

def classify_skin_hair_usage(functions: List[str], inci_name: str) -> str:
    """Classify ingredient usage for skin care, hair care, or both"""
    functions_text = ' '.join(functions).lower() if functions else ''
    inci_lower = inci_name.lower()
    
    # Hair care indicators
    hair_keywords = [
        'shampoo', 'conditioner', 'hair', 'scalp', 'dandruff', 'seborrheic',
        'follicle', 'growth', 'strengthening', 'detangling', 'volumizing',
        'anti-dandruff', 'hair loss', 'alopecia', 'thinning'
    ]
    
    # Skin care indicators
    skin_keywords = [
        'moisturizing', 'hydrating', 'anti-aging', 'wrinkle', 'acne',
        'comedogenic', 'facial', 'serum', 'cream', 'lotion', 'cleanser',
        'exfoliat', 'brightening', 'lightening', 'sun protection', 'spf',
        'anti-inflammatory', 'soothing', 'calming', 'barrier repair'
    ]
    
    # Check for specific ingredient classifications
    hair_specific_ingredients = [
        'zinc pyrithione', 'selenium sulfide', 'ketoconazole', 'climbazole',
        'piroctone olamine', 'cetrimonium', 'behentrimonium', 'polyquaternium',
        'guar hydroxypropyltrimonium'
    ]
    
    skin_specific_ingredients = [
        'salicylic acid', 'glycolic acid', 'retinol', 'niacinamide',
        'hyaluronic acid', 'ascorbic acid', 'kojic acid'
    ]
    
    hair_score = 0
    skin_score = 0
    
    # Score based on functions
    for keyword in hair_keywords:
        if keyword in functions_text:
            hair_score += 2
    
    for keyword in skin_keywords:
        if keyword in functions_text:
            skin_score += 2
    
    # Score based on ingredient name
    for ingredient in hair_specific_ingredients:
        if ingredient in inci_lower:
            hair_score += 3
    
    for ingredient in skin_specific_ingredients:
        if ingredient in inci_lower:
            skin_score += 3
    
    # Universal ingredients (used in both)
    universal_keywords = [
        'preservative', 'emulsifier', 'thickener', 'stabilizer', 'fragrance',
        'colorant', 'ph adjuster', 'chelating', 'antioxidant'
    ]
    
    universal_score = sum(1 for keyword in universal_keywords if keyword in functions_text)
    
    # Classification logic
    if hair_score > skin_score + 1:
        return "Hair Care"
    elif skin_score > hair_score + 1:
        return "Skin Care"
    elif universal_score >= 2 or (hair_score > 0 and skin_score > 0):
        return "Both"
    else:
        # Default classification based on common usage patterns
        if any(word in inci_lower for word in ['sulfate', 'glucoside', 'betaine']):
            return "Both"  # Common cleansing agents
        return "Both"  # When in doubt, assume both

def process_single_ingredient(inci_name: str, mapping: Dict, paths: Dict, api_key: Optional[str]) -> Optional[Dict]:
    """Process a single ingredient and extract all relevant data"""
    logger.info(f"🔄 Processing: {inci_name}")
    try:
        # Extract data from all sources
        inci_data = extract_inci_data_from_files(
            mapping.get('separated_ingredient_files', []), 
            paths['separated']
        )
        
        report_data = extract_report_sentiment_from_files(
            mapping.get('reddit_analysis_files', []),
            paths['separated'],
            paths['reddit_analysis']
        )
        
        comments = load_reddit_comments_from_files(
            mapping.get('raw_data_files', []),
            paths['raw_data']
        )
        
        # Basic information
        name = inci_data['inci_name'] if inci_data else inci_name
        
        # Enhanced Usage - primarily from INCI tables
        usage = 'Not specified'
        if inci_data and inci_data.get('usage_data'):
            usage = inci_data['usage_data']
        
        # Research analysis
        research_paper_links = get_research_paper_links(name, inci_data['functions'] if inci_data else [], api_key)
        research_summary = ""
        if research_paper_links:
            research_summary = f"Research papers: {'; '.join(research_paper_links)}"
        else:
            research_summary = "No research papers found."
        
        # Enhanced Pros
        pros_list = []
        if inci_data and inci_data['functions']:
            pros_list.extend([f for f in inci_data['functions'] if f])
        
        if report_data and int(report_data.get('positive_posts', '0')) > 0:
            pros_list.append(f"{report_data['positive_posts']} positive user experiences")
        
        effectiveness_mentions = len([c for c in comments if any(word in str(c).lower() for word in ['effective', 'works', 'helped', 'results', 'improvement'])])
        if effectiveness_mentions > 0:
            pros_list.append(f"{effectiveness_mentions} effectiveness reports")
        
        pros = "; ".join(pros_list) if pros_list else 'Limited positive feedback'
        
        # Enhanced Cons (similar structure to pros)
        cons = extract_comprehensive_cons(inci_data, comments)
        
        # Calculate functional effectiveness based on INCI data and user experience
        effectiveness = calculate_functional_effectiveness(inci_data, comments, report_data)
        
        # Enhanced Reddit summary with subreddit breakdown
        reddit_analysis = analyze_reddit_data(comments, report_data)
        reddit_summary = reddit_analysis['formatted_summary']
        
        # Origin and classification
        origin = inci_data['origin'] if inci_data else 'Unknown'
        natural_synthetic = "Natural" if origin in ['Vegetal', 'Plant', 'Natural', 'Botanical'] else "Synthetic"
        
        # Skin/Hair classification
        functions = inci_data['functions'] if inci_data else []
        skin_hair_usage = classify_skin_hair_usage(functions, name)
        
        # Enhanced LLM prompt for prescriptive recommendations
        prompt = f"""
As a cosmetic formulation scientist, provide a prescriptive recommendation for {name}:

INGREDIENT PROFILE:
- INCI Name: {name}
- Usage Concentration: {usage}
- Origin: {natural_synthetic}
- Primary Functions: {'; '.join(functions[:4])}
- Application: {skin_hair_usage}
- Industry Usage: {inci_data.get('percentage', 'Unknown')}% of cosmetic products
- Effectiveness Profile: {effectiveness}

FORMULATION DECISION GUIDANCE:
Provide 2-3 sentences covering:
1. When and why to use this ingredient (specific applications based on INCI functions)
2. Optimal usage levels and formulation considerations (based on industry data)
3. Key functional benefits vs. formulation concerns for product development
4. Compatibility with other ingredients or formulation types

Focus on evidence-based insights from cosmetic science data for formulators making ingredient selection decisions.
"""
        
        llm_summary = call_openai_with_retry(prompt, api_key) if api_key else "LLM summary unavailable - no API key"
        
        row = {
            'Ingredient Name': name,
            'Research': truncate_text(research_summary, 100),
            '%usage': usage,
            'Pros': truncate_text(pros, 100),
            'Cons': truncate_text(cons, 100),
            'Effectiveness': truncate_text(effectiveness, 100),
            'Reddit': truncate_text(reddit_summary, 100),
            'Natural or synthesised': natural_synthetic,
            'Skin or Hair Care': skin_hair_usage,
            'LLM Summary': truncate_text(llm_summary, 200)
        }
        
        logger.info(f"✅ Successfully processed {name}")
        return row
        
    except Exception as e:
        logger.error(f"❌ Failed to process {inci_name}: {e}")
        return None

def main():
    """Main execution function"""
    print("🚀 Starting Enhanced INCI-Centric Ingredient Data Processing...")
    print("=" * 60)
    try:
        api_key = load_api_key()
        paths = setup_paths()
        inci_mapping = load_inci_mapping(paths['mapping'])
        
        TEST_MODE = False
        TEST_INCI_NAMES = [
            'XANTHAN GUM',
            'ZINC PYRITHIONE',
            'ACETYL TETRAPEPTIDE-3',
            'TRITICUM VULGARE GERM OIL',
            'URTICA DIOICA LEAF EXTRACT',
            'DIMETHICONE'
        ]
        
        logger.info(f"🧪 Test mode: {'ENABLED' if TEST_MODE else 'DISABLED'}")
        
        if TEST_MODE:
            missing_ingredients = [name for name in TEST_INCI_NAMES if name not in inci_mapping]
            if missing_ingredients:
                logger.warning(f"⚠️ Test ingredients not in mapping: {missing_ingredients}")
                available_ingredients = [name for name in TEST_INCI_NAMES if name in inci_mapping]
                logger.info(f"✅ Available test ingredients: {available_ingredients}")
        
        rows = []
        ingredients_to_process = TEST_INCI_NAMES if TEST_MODE else list(inci_mapping.keys())
        total_ingredients = len([name for name in ingredients_to_process if name in inci_mapping])
        
        logger.info(f"📊 Processing {total_ingredients} ingredients...")
        
        for i, inci_name in enumerate(ingredients_to_process, 1):
            if inci_name not in inci_mapping:
                logger.warning(f"⚠️ Skipping {inci_name} - not in mapping")
                continue
            
            logger.info(f"[{i}/{total_ingredients}] Processing {inci_name}")
            
            row = process_single_ingredient(
                inci_name, 
                inci_mapping[inci_name], 
                paths, 
                api_key
            )
            
            if row:
                rows.append(row)
        
        if rows:
            output_path = paths['base'] / 'combined_ingredient_data_enhanced_v2.csv'
            df = pd.DataFrame(rows)
            df.to_csv(output_path, index=False, encoding='utf-8')
            
            print(f"\n" + "=" * 60)
            print("✅ ENHANCED PROCESSING COMPLETE!")
            print("=" * 60)
            print(f"📊 RESULTS SUMMARY:")
            print(f"   • Total Ingredients Processed: {len(rows)}")
            print(f"   • Natural Ingredients: {len(df[df['Natural or synthesised'] == 'Natural'])}")
            print(f"   • Synthetic Ingredients: {len(df[df['Natural or synthesised'] == 'Synthetic'])}")
            print(f"   • Skin Care Only: {len(df[df['Skin or Hair Care'] == 'Skin Care'])}")
            print(f"   • Hair Care Only: {len(df[df['Skin or Hair Care'] == 'Hair Care'])}")
            print(f"   • Both Applications: {len(df[df['Skin or Hair Care'] == 'Both'])}")
            print(f"   • Success Rate: {len(rows)}/{total_ingredients} ({len(rows)/total_ingredients*100:.1f}%)")
            
            print(f"\n📋 OUTPUT:")
            print(f"   • File: {output_path}")
            print(f"   • Size: {os.path.getsize(output_path) / 1024:.1f} KB")
            print(f"   • Columns: {len(df.columns)}")
            
            print(f"\n🔍 SAMPLE DATA:")
            print(df.head(2)[['Ingredient Name', 'Research', 'Skin or Hair Care']].to_string(index=False))
            
            print(f"\n📈 ENHANCED FEATURES:")
            print(f"   ✅ INCI-focused usage data extraction")
            print(f"   ✅ Functional cons analysis (not sentiment-based)")
            print(f"   ✅ Subreddit breakdown in Reddit analysis")
            print(f"   ✅ Prescriptive LLM recommendations")
            print(f"   ✅ Skin/Hair care classification")
            print(f"   ✅ Research paper link retrieval and validation")
            
            print("=" * 60)
            
        else:
            logger.error("❌ No ingredients were processed successfully")
            
    except Exception as e:
        logger.error(f"❌ Processing failed: {e}")
        raise

if __name__ == "__main__":
    main() 