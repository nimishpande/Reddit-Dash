#!/usr/bin/env python3
"""
Subreddit Discovery Engine
Finds related subreddits based on user activity and interests
"""

import praw
import json
import os
from datetime import datetime, timezone
from collections import defaultdict, Counter
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SubredditDiscovery:
    def __init__(self):
        """Initialize Reddit API connection"""
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            user_agent=os.getenv('REDDIT_USER_AGENT', 'Subreddit Discovery v1.0')
        )
        print("✅ Reddit API connection established")
    
    def discover_related_subreddits(self, user_subreddits, limit=50):
        """Find subreddits related to user's activity"""
        print(f"🔍 Discovering related subreddits for {len(user_subreddits)} active subreddits...")
        
        related_subreddits = []
        
        for subreddit_name in user_subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Get related subreddits from sidebar/about
                related = self._extract_related_from_sidebar(subreddit)
                related_subreddits.extend(related)
                
                # Get subreddits mentioned in posts
                mentioned = self._extract_mentioned_subreddits(subreddit, limit=20)
                related_subreddits.extend(mentioned)
                
            except Exception as e:
                print(f"⚠️  Could not analyze r/{subreddit_name}: {e}")
                continue
        
        # Score and rank related subreddits
        scored_subreddits = self._score_related_subreddits(related_subreddits, user_subreddits)
        
        return scored_subreddits
    
    def _extract_related_from_sidebar(self, subreddit):
        """Extract related subreddits from sidebar/about section"""
        related = []
        
        try:
            # Get subreddit description and sidebar
            description = subreddit.description or ""
            sidebar = subreddit.description or ""
            
            # Look for r/subreddit patterns
            subreddit_pattern = r'r/([A-Za-z0-9_]+)'
            matches = re.findall(subreddit_pattern, description + " " + sidebar)
            
            for match in matches:
                if match.lower() not in ['reddit', 'subreddit', 'moderator']:
                    related.append({
                        'name': match,
                        'source': 'sidebar',
                        'confidence': 0.7
                    })
        
        except Exception as e:
            print(f"⚠️  Could not extract sidebar from r/{subreddit.display_name}: {e}")
        
        return related
    
    def _extract_mentioned_subreddits(self, subreddit, limit=20):
        """Extract subreddits mentioned in recent posts"""
        mentioned = []
        
        try:
            for submission in subreddit.hot(limit=limit):
                # Check title and selftext for subreddit mentions
                text = (submission.title or "") + " " + (submission.selftext or "")
                
                # Look for r/subreddit patterns
                subreddit_pattern = r'r/([A-Za-z0-9_]+)'
                matches = re.findall(subreddit_pattern, text)
                
                for match in matches:
                    if match.lower() not in ['reddit', 'subreddit', 'moderator']:
                        mentioned.append({
                            'name': match,
                            'source': 'post_mention',
                            'confidence': 0.5
                        })
        
        except Exception as e:
            print(f"⚠️  Could not extract mentions from r/{subreddit.display_name}: {e}")
        
        return mentioned
    
    def _score_related_subreddits(self, related_subreddits, user_subreddits):
        """Score and rank related subreddits"""
        subreddit_scores = defaultdict(float)
        subreddit_sources = defaultdict(list)
        
        # Count occurrences and sources
        for sub in related_subreddits:
            name = sub['name'].lower()
            if name not in [s.lower() for s in user_subreddits]:  # Exclude user's current subreddits
                subreddit_scores[name] += sub['confidence']
                subreddit_sources[name].append(sub['source'])
        
        # Get subreddit metadata and calculate final scores
        scored_subreddits = []
        
        for subreddit_name, score in subreddit_scores.items():
            try:
                subreddit = self.reddit.subreddit(subreddit_name)
                
                # Calculate relevance score
                relevance_score = self._calculate_relevance_score(subreddit, user_subreddits)
                final_score = score * relevance_score
                
                scored_subreddits.append({
                    'name': subreddit_name,
                    'display_name': subreddit.display_name,
                    'subscribers': subreddit.subscribers,
                    'description': subreddit.description[:200] + '...' if len(subreddit.description) > 200 else subreddit.description,
                    'public_description': subreddit.public_description[:100] + '...' if len(subreddit.public_description) > 100 else subreddit.public_description,
                    'subreddit_type': subreddit.subreddit_type,
                    'over18': subreddit.over18,
                    'score': final_score,
                    'sources': subreddit_sources[subreddit_name],
                    'relevance_factors': self._get_relevance_factors(subreddit, user_subreddits)
                })
                
            except Exception as e:
                print(f"⚠️  Could not analyze r/{subreddit_name}: {e}")
                continue
        
        # Sort by score and return top results
        scored_subreddits.sort(key=lambda x: x['score'], reverse=True)
        return scored_subreddits[:30]  # Return top 30
    
    def _calculate_relevance_score(self, subreddit, user_subreddits):
        """Calculate relevance score based on various factors"""
        score = 1.0
        
        # Factor 1: Subscriber count (prefer active communities)
        if subreddit.subscribers > 10000:
            score *= 1.2
        elif subreddit.subscribers < 1000:
            score *= 0.8
        
        # Factor 2: Subreddit type (prefer public communities)
        if subreddit.subreddit_type == 'public':
            score *= 1.1
        elif subreddit.subreddit_type == 'private':
            score *= 0.7
        
        # Factor 3: Content similarity (analyze description)
        description = (subreddit.description or "").lower()
        user_keywords = self._extract_keywords_from_subreddits(user_subreddits)
        
        keyword_matches = sum(1 for keyword in user_keywords if keyword in description)
        if keyword_matches > 0:
            score *= (1 + keyword_matches * 0.1)
        
        # Factor 4: Avoid NSFW unless user is in NSFW communities
        if subreddit.over18:
            score *= 0.5
        
        return score
    
    def _extract_keywords_from_subreddits(self, user_subreddits):
        """Extract common keywords from user's subreddit names"""
        keywords = set()
        
        for subreddit in user_subreddits:
            # Split subreddit name into words
            words = re.findall(r'[A-Za-z]+', subreddit)
            keywords.update([word.lower() for word in words if len(word) > 2])
        
        return list(keywords)
    
    def _get_relevance_factors(self, subreddit, user_subreddits):
        """Get detailed relevance factors for a subreddit"""
        factors = {
            'keyword_matches': 0,
            'size_appropriate': subreddit.subscribers > 1000,
            'public_community': subreddit.subreddit_type == 'public',
            'content_related': False,
            'activity_level': 'unknown'
        }
        
        # Check for keyword matches
        description = (subreddit.description or "").lower()
        user_keywords = self._extract_keywords_from_subreddits(user_subreddits)
        matches = sum(1 for keyword in user_keywords if keyword in description)
        factors['keyword_matches'] = matches
        factors['content_related'] = matches > 0
        
        return factors
    
    def discover_by_keywords(self, keywords, limit=20):
        """Discover subreddits by searching for keywords"""
        print(f"🔍 Discovering subreddits by keywords: {', '.join(keywords)}")
        
        discovered_subreddits = []
        
        for keyword in keywords:
            try:
                # Search for subreddits
                search_results = list(self.reddit.subreddits.search(keyword, limit=limit))
                
                for subreddit in search_results:
                    discovered_subreddits.append({
                        'name': str(subreddit),
                        'display_name': subreddit.display_name,
                        'subscribers': subreddit.subscribers,
                        'description': subreddit.description[:200] + '...' if len(subreddit.description) > 200 else subreddit.description,
                        'public_description': subreddit.public_description[:100] + '...' if len(subreddit.public_description) > 100 else subreddit.public_description,
                        'subreddit_type': subreddit.subreddit_type,
                        'over18': subreddit.over18,
                        'search_keyword': keyword,
                        'relevance_score': self._calculate_keyword_relevance(subreddit, keyword)
                    })
            
            except Exception as e:
                print(f"⚠️  Could not search for '{keyword}': {e}")
                continue
        
        # Remove duplicates and sort by relevance
        unique_subreddits = {}
        for sub in discovered_subreddits:
            name = sub['name']
            if name not in unique_subreddits or sub['relevance_score'] > unique_subreddits[name]['relevance_score']:
                unique_subreddits[name] = sub
        
        sorted_subreddits = sorted(unique_subreddits.values(), key=lambda x: x['relevance_score'], reverse=True)
        return sorted_subreddits[:30]
    
    def _calculate_keyword_relevance(self, subreddit, keyword):
        """Calculate relevance score for keyword-based discovery"""
        score = 1.0
        
        # Check if keyword appears in name
        if keyword.lower() in subreddit.display_name.lower():
            score *= 2.0
        
        # Check if keyword appears in description
        description = (subreddit.description or "").lower()
        if keyword.lower() in description:
            score *= 1.5
        
        # Factor in subscriber count
        if subreddit.subscribers > 10000:
            score *= 1.2
        elif subreddit.subscribers < 1000:
            score *= 0.8
        
        return score
    
    def generate_discovery_report(self, user_subreddits, user_keywords=None):
        """Generate comprehensive subreddit discovery report"""
        print("🚀 Starting comprehensive subreddit discovery...")
        
        # Discover related subreddits
        related_subreddits = self.discover_related_subreddits(user_subreddits)
        
        # Discover by keywords if provided
        keyword_subreddits = []
        if user_keywords:
            keyword_subreddits = self.discover_by_keywords(user_keywords)
        
        # Combine and deduplicate results
        all_subreddits = related_subreddits + keyword_subreddits
        unique_subreddits = {}
        
        for sub in all_subreddits:
            name = sub['name']
            if name not in unique_subreddits:
                unique_subreddits[name] = sub
            else:
                # Keep the one with higher score
                if sub.get('score', 0) > unique_subreddits[name].get('score', 0):
                    unique_subreddits[name] = sub
        
        # Sort by score
        final_subreddits = sorted(unique_subreddits.values(), key=lambda x: x.get('score', 0), reverse=True)
        
        # Generate report
        report = {
            'discovery_date': datetime.now(timezone.utc).isoformat(),
            'user_subreddits': user_subreddits,
            'discovered_subreddits': final_subreddits[:20],  # Top 20
            'discovery_stats': {
                'total_discovered': len(final_subreddits),
                'related_discovered': len(related_subreddits),
                'keyword_discovered': len(keyword_subreddits),
                'high_confidence': len([s for s in final_subreddits if s.get('score', 0) > 1.0])
            },
            'recommendations': self._generate_discovery_recommendations(final_subreddits)
        }
        
        return report
    
    def _generate_discovery_recommendations(self, subreddits):
        """Generate recommendations based on discovered subreddits"""
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'explore_later': []
        }
        
        for sub in subreddits[:15]:  # Top 15
            score = sub.get('score', 0)
            if score > 1.5:
                recommendations['high_priority'].append(sub['name'])
            elif score > 1.0:
                recommendations['medium_priority'].append(sub['name'])
            else:
                recommendations['explore_later'].append(sub['name'])
        
        return recommendations
    
    def save_discovery_report(self, report, filename=None):
        """Save discovery report to file"""
        if filename is None:
            timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
            filename = f"data/subreddit_discovery_{timestamp}.json"
        
        # Ensure output directory exists
        os.makedirs('data', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Discovery report saved to: {filename}")
        return filename

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python subreddit_discovery.py <subreddit1,subreddit2,...> [keywords]")
        print("Example: python subreddit_discovery.py skincareaddictsindia,IndianHaircare skincare,haircare")
        sys.exit(1)
    
    user_subreddits = [s.strip() for s in sys.argv[1].split(',')]
    user_keywords = sys.argv[2].split(',') if len(sys.argv) > 2 else None
    
    try:
        discovery = SubredditDiscovery()
        report = discovery.generate_discovery_report(user_subreddits, user_keywords)
        
        filename = discovery.save_discovery_report(report)
        
        print(f"\n🎉 Discovery complete! Found {len(report['discovered_subreddits'])} related subreddits")
        print(f"📊 High priority: {len(report['recommendations']['high_priority'])}")
        print(f"📊 Medium priority: {len(report['recommendations']['medium_priority'])}")
        
    except Exception as e:
        print(f"❌ Error during discovery: {e}")
        raise

if __name__ == "__main__":
    main()
