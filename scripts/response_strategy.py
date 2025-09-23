#!/usr/bin/env python3
"""
Response Strategy Generator
Generates personalized response suggestions based on post content and user profile
"""

import json
import re
from datetime import datetime, timezone
from collections import defaultdict, Counter
import os

class ResponseStrategyGenerator:
    def __init__(self, user_profile_path=None):
        """Initialize with user profile"""
        self.user_profile = self._load_user_profile(user_profile_path)
        self.expertise_keywords = self._extract_expertise_keywords()
        self.help_type_patterns = self._load_help_type_patterns()
        
    def _load_user_profile(self, profile_path):
        """Load user profile from file"""
        if profile_path and os.path.exists(profile_path):
            with open(profile_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # Load default profile
            default_path = 'config/user_profile_enhanced.json'
            if os.path.exists(default_path):
                with open(default_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        return {}
    
    def _extract_expertise_keywords(self):
        """Extract expertise keywords from user profile"""
        keywords = set()
        
        if 'accounts' in self.user_profile:
            active_account = self.user_profile.get('active_account', 'dotconsistent3677')
            account_data = self.user_profile['accounts'].get(active_account, {})
            
            # Get expertise areas
            expertise_areas = account_data.get('expertise_areas', [])
            keywords.update([area.lower() for area in expertise_areas])
            
            # Get interest keywords
            interest_keywords = account_data.get('interest_keywords', [])
            keywords.update([kw.lower() for kw in interest_keywords])
        
        return list(keywords)
    
    def _load_help_type_patterns(self):
        """Load patterns for classifying help types"""
        return {
            'routine_help': {
                'keywords': ['routine', 'regimen', 'schedule', 'order', 'step', 'morning', 'evening', 'night'],
                'patterns': [r'what.*routine', r'how.*routine', r'routine.*help', r'regimen.*help']
            },
            'product_recommendation': {
                'keywords': ['recommend', 'suggest', 'product', 'brand', 'buy', 'purchase', 'which', 'best'],
                'patterns': [r'what.*product', r'which.*product', r'recommend.*product', r'best.*product']
            },
            'troubleshooting': {
                'keywords': ['problem', 'issue', 'trouble', 'help', 'fix', 'solve', 'wrong', 'not working'],
                'patterns': [r'help.*with', r'problem.*with', r'issue.*with', r'what.*wrong']
            },
            'ingredient_question': {
                'keywords': ['ingredient', 'active', 'chemical', 'compound', 'acid', 'retinol', 'niacinamide'],
                'patterns': [r'ingredient.*question', r'what.*ingredient', r'ingredient.*help']
            },
            'skin_concern': {
                'keywords': ['acne', 'pimples', 'blackheads', 'dry', 'oily', 'sensitive', 'redness', 'irritation'],
                'patterns': [r'skin.*problem', r'skin.*issue', r'help.*skin', r'skin.*concern']
            },
            'hair_concern': {
                'keywords': ['hair', 'hair loss', 'hair growth', 'scalp', 'dandruff', 'curly', 'straight'],
                'patterns': [r'hair.*problem', r'hair.*issue', r'help.*hair', r'hair.*concern']
            }
        }
    
    def classify_help_type(self, post):
        """Classify the type of help needed"""
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        help_scores = defaultdict(float)
        
        for help_type, patterns in self.help_type_patterns.items():
            # Check keywords
            keyword_matches = sum(1 for keyword in patterns['keywords'] if keyword in text)
            help_scores[help_type] += keyword_matches * 0.5
            
            # Check regex patterns
            pattern_matches = sum(1 for pattern in patterns['patterns'] if re.search(pattern, text))
            help_scores[help_type] += pattern_matches * 1.0
        
        # Return the help type with highest score
        if help_scores:
            best_help_type = max(help_scores.items(), key=lambda x: x[1])
            return {
                'help_type': best_help_type[0],
                'confidence': min(best_help_type[1] / 5.0, 1.0),  # Normalize to 0-1
                'all_scores': dict(help_scores)
            }
        
        return {'help_type': 'general', 'confidence': 0.0, 'all_scores': {}}
    
    def extract_triggered_keywords(self, post):
        """Extract keywords that match user's expertise"""
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        triggered_keywords = []
        for keyword in self.expertise_keywords:
            if keyword in text:
                triggered_keywords.append(keyword)
        
        return triggered_keywords
    
    def match_expertise_areas(self, post):
        """Match post content to user's expertise areas"""
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        expertise_matches = []
        
        if 'accounts' in self.user_profile:
            active_account = self.user_profile.get('active_account', 'dotconsistent3677')
            account_data = self.user_profile['accounts'].get(active_account, {})
            
            # Check expertise areas
            expertise_areas = account_data.get('expertise_areas', [])
            for area in expertise_areas:
                if any(word in text for word in area.lower().split()):
                    expertise_matches.append(area)
            
            # Check content relevance areas
            content_areas = account_data.get('content_relevance_areas', {})
            for area, data in content_areas.items():
                keywords = data.get('keywords', [])
                if any(keyword in text for keyword in keywords):
                    expertise_matches.append(area)
        
        return expertise_matches
    
    def generate_response_angles(self, post, help_type_data):
        """Generate specific response angles based on post content"""
        angles = []
        
        help_type = help_type_data.get('help_type', 'general')
        triggered_keywords = self.extract_triggered_keywords(post)
        expertise_matches = self.match_expertise_areas(post)
        
        # Generate angles based on help type
        if help_type == 'routine_help':
            angles.extend([
                "Share your personal routine experience",
                "Suggest a step-by-step routine based on their skin type",
                "Recommend products for each step"
            ])
        
        elif help_type == 'product_recommendation':
            angles.extend([
                "Recommend specific products you've used",
                "Suggest budget-friendly alternatives",
                "Share your experience with similar products"
            ])
        
        elif help_type == 'troubleshooting':
            angles.extend([
                "Share how you solved a similar problem",
                "Suggest diagnostic questions to ask",
                "Recommend gentle solutions to try first"
            ])
        
        elif help_type == 'ingredient_question':
            angles.extend([
                "Explain the ingredient's benefits and usage",
                "Share your experience with that ingredient",
                "Suggest products containing that ingredient"
            ])
        
        elif help_type == 'skin_concern':
            angles.extend([
                "Share your experience with similar skin concerns",
                "Suggest gentle, proven solutions",
                "Recommend a consultation approach"
            ])
        
        elif help_type == 'hair_concern':
            angles.extend([
                "Share your hair care experience",
                "Suggest products for their hair type",
                "Recommend professional consultation if needed"
            ])
        
        # Add expertise-specific angles
        if expertise_matches:
            for match in expertise_matches[:2]:  # Top 2 matches
                if 'skincare' in match.lower():
                    angles.append("Share your skincare expertise and experience")
                elif 'hair' in match.lower():
                    angles.append("Share your haircare knowledge and tips")
                elif 'ingredient' in match.lower():
                    angles.append("Provide detailed ingredient information")
        
        return angles[:3]  # Return top 3 angles
    
    def calculate_urgency_level(self, post):
        """Calculate urgency level based on post content"""
        text = (post.get('title', '') + ' ' + post.get('content', '')).lower()
        
        urgency_indicators = {
            'high': ['urgent', 'emergency', 'help now', 'asap', 'immediately', 'crisis'],
            'medium': ['soon', 'quickly', 'fast', 'timely', 'important'],
            'low': ['eventually', 'sometime', 'when possible', 'no rush']
        }
        
        for level, indicators in urgency_indicators.items():
            if any(indicator in text for indicator in indicators):
                return level
        
        # Check for time-sensitive keywords
        time_keywords = ['today', 'tomorrow', 'this week', 'deadline', 'event']
        if any(keyword in text for keyword in time_keywords):
            return 'medium'
        
        return 'low'
    
    def analyze_competition(self, post):
        """Analyze existing responses to the post"""
        # This would require access to post comments, which we don't have in current structure
        # For now, return basic analysis
        return {
            'comment_count': post.get('comments', 0),
            'engagement_level': 'high' if post.get('comments', 0) > 10 else 'medium' if post.get('comments', 0) > 3 else 'low',
            'response_opportunity': 'good' if post.get('comments', 0) < 5 else 'moderate' if post.get('comments', 0) < 15 else 'limited'
        }
    
    def calculate_response_confidence(self, post, help_type_data, expertise_matches):
        """Calculate confidence score for responding to this post"""
        confidence = 0.0
        
        # Base confidence from help type
        confidence += help_type_data.get('confidence', 0) * 0.3
        
        # Boost from expertise matches
        confidence += len(expertise_matches) * 0.2
        
        # Boost from triggered keywords
        triggered_keywords = self.extract_triggered_keywords(post)
        confidence += len(triggered_keywords) * 0.1
        
        # Boost from subreddit familiarity
        subreddit = post.get('subreddit', '').lower()
        if 'accounts' in self.user_profile:
            active_account = self.user_profile.get('active_account', 'dotconsistent3677')
            account_data = self.user_profile['accounts'].get(active_account, {})
            subreddit_activity = account_data.get('account_analysis', {}).get('subreddit_activity', {})
            top_subreddits = [sub[0].lower() for sub in subreddit_activity.get('top_subreddits', [])]
            
            if subreddit in top_subreddits:
                confidence += 0.2
        
        return min(confidence, 1.0)
    
    def generate_enhanced_post_context(self, post):
        """Generate comprehensive context for a post"""
        print(f"🔍 Analyzing post: {post.get('title', '')[:50]}...")
        
        # Classify help type
        help_type_data = self.classify_help_type(post)
        
        # Extract triggered keywords
        triggered_keywords = self.extract_triggered_keywords(post)
        
        # Match expertise areas
        expertise_matches = self.match_expertise_areas(post)
        
        # Generate response angles
        response_angles = self.generate_response_angles(post, help_type_data)
        
        # Calculate urgency
        urgency_level = self.calculate_urgency_level(post)
        
        # Analyze competition
        competition_analysis = self.analyze_competition(post)
        
        # Calculate confidence
        confidence_score = self.calculate_response_confidence(post, help_type_data, expertise_matches)
        
        # Generate context
        context = {
            'triggered_keywords': triggered_keywords,
            'help_type': help_type_data['help_type'],
            'help_type_confidence': help_type_data['confidence'],
            'expertise_match': expertise_matches,
            'response_angles': response_angles,
            'urgency_level': urgency_level,
            'competition_analysis': competition_analysis,
            'confidence_score': confidence_score,
            'response_suggestions': self._generate_response_suggestions(help_type_data, expertise_matches, response_angles)
        }
        
        return context
    
    def _generate_response_suggestions(self, help_type_data, expertise_matches, response_angles):
        """Generate specific response suggestions"""
        suggestions = []
        
        help_type = help_type_data['help_type']
        confidence = help_type_data['confidence']
        
        if confidence > 0.7:
            suggestions.append(f"High confidence match for {help_type} - you can provide detailed, specific advice")
        elif confidence > 0.4:
            suggestions.append(f"Moderate match for {help_type} - share relevant experience and ask clarifying questions")
        else:
            suggestions.append(f"General match - provide helpful information and ask questions to understand their needs better")
        
        if expertise_matches:
            suggestions.append(f"Your expertise in {', '.join(expertise_matches[:2])} is highly relevant")
        
        if response_angles:
            suggestions.append(f"Consider these approaches: {', '.join(response_angles[:2])}")
        
        return suggestions
    
    def process_posts_with_context(self, posts):
        """Process multiple posts and add context to each"""
        print(f"🚀 Processing {len(posts)} posts with enhanced context...")
        
        enhanced_posts = []
        for post in posts:
            try:
                context = self.generate_enhanced_post_context(post)
                post['context'] = context
                enhanced_posts.append(post)
            except Exception as e:
                print(f"⚠️  Error processing post {post.get('id', 'unknown')}: {e}")
                post['context'] = {'error': str(e)}
                enhanced_posts.append(post)
        
        print(f"✅ Enhanced {len(enhanced_posts)} posts with context")
        return enhanced_posts

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python response_strategy.py <posts_json_file> [user_profile_file]")
        print("Example: python response_strategy.py data/analysis/latest.json config/user_profile_enhanced.json")
        sys.exit(1)
    
    posts_file = sys.argv[1]
    profile_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load posts
        with open(posts_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        posts = data.get('posts', [])
        if not posts:
            print("❌ No posts found in file")
            return
        
        # Initialize strategy generator
        generator = ResponseStrategyGenerator(profile_file)
        
        # Process posts
        enhanced_posts = generator.process_posts_with_context(posts)
        
        # Update data
        data['posts'] = enhanced_posts
        
        # Save enhanced data
        output_file = posts_file.replace('.json', '_enhanced.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Enhanced posts saved to: {output_file}")
        
        # Show sample results
        print(f"\n📊 Sample enhanced posts:")
        for i, post in enumerate(enhanced_posts[:3]):
            context = post.get('context', {})
            print(f"  {i+1}. {post.get('title', '')[:50]}...")
            print(f"     Help Type: {context.get('help_type', 'unknown')} (confidence: {context.get('help_type_confidence', 0):.2f})")
            print(f"     Expertise Match: {context.get('expertise_match', [])}")
            print(f"     Confidence Score: {context.get('confidence_score', 0):.2f}")
            print()
        
    except Exception as e:
        print(f"❌ Error processing posts: {e}")
        raise

if __name__ == "__main__":
    main()
