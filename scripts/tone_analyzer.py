#!/usr/bin/env python3
"""
Tone Analyzer
Analyzes user's writing style and tone from comment history
"""

import json
import re
import os
from datetime import datetime, timezone
from collections import Counter, defaultdict
import math

class ToneAnalyzer:
    def __init__(self):
        """Initialize tone analyzer"""
        self.tone_indicators = self._load_tone_indicators()
        self.writing_patterns = self._load_writing_patterns()
        
    def _load_tone_indicators(self):
        """Load tone indicators and patterns"""
        return {
            'formal': {
                'indicators': ['therefore', 'however', 'furthermore', 'consequently', 'moreover', 'nevertheless'],
                'patterns': [r'\b(?:therefore|however|furthermore)\b', r'\b(?:consequently|moreover|nevertheless)\b']
            },
            'casual': {
                'indicators': ['lol', 'haha', 'tbh', 'imo', 'ngl', 'fr', 'tbh', 'ngl'],
                'patterns': [r'\b(?:lol|haha|tbh|imo|ngl|fr)\b', r'[!]{2,}', r'[?]{2,}']
            },
            'technical': {
                'indicators': ['ph', 'acid', 'compound', 'molecule', 'formulation', 'concentration', 'percentage'],
                'patterns': [r'\b(?:ph|acid|compound|molecule|formulation|concentration|percentage)\b']
            },
            'empathetic': {
                'indicators': ['understand', 'feel', 'sorry', 'hope', 'wish', 'care', 'support'],
                'patterns': [r'\b(?:understand|feel|sorry|hope|wish|care|support)\b']
            },
            'educational': {
                'indicators': ['should', 'recommend', 'suggest', 'advise', 'consider', 'try', 'avoid'],
                'patterns': [r'\b(?:should|recommend|suggest|advise|consider|try|avoid)\b']
            },
            'questioning': {
                'indicators': ['what', 'how', 'why', 'when', 'where', 'which', '?'],
                'patterns': [r'\b(?:what|how|why|when|where|which)\b', r'\?']
            },
            'enthusiastic': {
                'indicators': ['love', 'amazing', 'great', 'awesome', 'fantastic', 'wonderful', '!'],
                'patterns': [r'\b(?:love|amazing|great|awesome|fantastic|wonderful)\b', r'!{2,}']
            },
            'cautious': {
                'indicators': ['maybe', 'perhaps', 'might', 'could', 'possibly', 'unclear', 'uncertain'],
                'patterns': [r'\b(?:maybe|perhaps|might|could|possibly|unclear|uncertain)\b']
            }
        }
    
    def _load_writing_patterns(self):
        """Load writing style patterns"""
        return {
            'sentence_length': {
                'short': {'max_words': 10, 'weight': 1.0},
                'medium': {'min_words': 11, 'max_words': 25, 'weight': 1.0},
                'long': {'min_words': 26, 'weight': 1.0}
            },
            'punctuation': {
                'exclamation': {'pattern': r'!', 'weight': 1.0},
                'question': {'pattern': r'\?', 'weight': 1.0},
                'ellipsis': {'pattern': r'\.{3,}', 'weight': 1.0},
                'caps': {'pattern': r'[A-Z]{3,}', 'weight': 1.0}
            },
            'structure': {
                'lists': {'pattern': r'^\s*[-*•]\s', 'weight': 1.0},
                'numbered': {'pattern': r'^\s*\d+\.\s', 'weight': 1.0},
                'paragraphs': {'pattern': r'\n\s*\n', 'weight': 1.0}
            }
        }
    
    def analyze_comment_tone(self, comment_text):
        """Analyze tone of a single comment"""
        if not comment_text:
            return {}
        
        text = comment_text.lower()
        tone_scores = defaultdict(float)
        
        # Analyze tone indicators
        for tone, data in self.tone_indicators.items():
            score = 0
            
            # Check indicators
            for indicator in data['indicators']:
                if indicator in text:
                    score += 1
            
            # Check patterns
            for pattern in data['patterns']:
                matches = len(re.findall(pattern, text, re.IGNORECASE))
                score += matches * 0.5
            
            tone_scores[tone] = score
        
        # Normalize scores
        total_score = sum(tone_scores.values())
        if total_score > 0:
            tone_scores = {tone: score / total_score for tone, score in tone_scores.items()}
        
        return dict(tone_scores)
    
    def analyze_writing_style(self, comment_text):
        """Analyze writing style characteristics"""
        if not comment_text:
            return {}
        
        style_analysis = {
            'sentence_length': self._analyze_sentence_length(comment_text),
            'punctuation': self._analyze_punctuation(comment_text),
            'structure': self._analyze_structure(comment_text),
            'readability': self._calculate_readability(comment_text)
        }
        
        return style_analysis
    
    def _analyze_sentence_length(self, text):
        """Analyze sentence length patterns"""
        sentences = re.split(r'[.!?]+', text)
        sentence_lengths = [len(sentence.split()) for sentence in sentences if sentence.strip()]
        
        if not sentence_lengths:
            return {'avg_length': 0, 'distribution': {}}
        
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        
        # Categorize by length
        short_count = len([l for l in sentence_lengths if l <= 10])
        medium_count = len([l for l in sentence_lengths if 11 <= l <= 25])
        long_count = len([l for l in sentence_lengths if l > 25])
        
        total = len(sentence_lengths)
        
        return {
            'avg_length': round(avg_length, 2),
            'distribution': {
                'short': round(short_count / total, 2),
                'medium': round(medium_count / total, 2),
                'long': round(long_count / total, 2)
            }
        }
    
    def _analyze_punctuation(self, text):
        """Analyze punctuation usage"""
        punctuation_analysis = {}
        
        for punct_type, data in self.writing_patterns['punctuation'].items():
            pattern = data['pattern']
            matches = len(re.findall(pattern, text))
            punctuation_analysis[punct_type] = {
                'count': matches,
                'density': round(matches / len(text.split()), 3) if text.split() else 0
            }
        
        return punctuation_analysis
    
    def _analyze_structure(self, text):
        """Analyze text structure"""
        structure_analysis = {}
        
        for struct_type, data in self.writing_patterns['structure'].items():
            pattern = data['pattern']
            matches = len(re.findall(pattern, text, re.MULTILINE))
            structure_analysis[struct_type] = {
                'count': matches,
                'has_structure': matches > 0
            }
        
        return structure_analysis
    
    def _calculate_readability(self, text):
        """Calculate basic readability score"""
        sentences = re.split(r'[.!?]+', text)
        words = text.split()
        
        if not sentences or not words:
            return {'score': 0, 'level': 'unknown'}
        
        avg_sentence_length = len(words) / len(sentences)
        avg_word_length = sum(len(word) for word in words) / len(words)
        
        # Simple readability formula
        readability_score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_word_length)
        
        if readability_score >= 80:
            level = 'very_easy'
        elif readability_score >= 60:
            level = 'easy'
        elif readability_score >= 40:
            level = 'moderate'
        elif readability_score >= 20:
            level = 'difficult'
        else:
            level = 'very_difficult'
        
        return {
            'score': round(readability_score, 2),
            'level': level,
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_word_length': round(avg_word_length, 2)
        }
    
    def analyze_user_tone(self, comments):
        """Analyze overall tone from user's comments"""
        print(f"🎭 Analyzing tone from {len(comments)} comments...")
        
        if not comments:
            return {}
        
        # Analyze each comment
        comment_tones = []
        comment_styles = []
        
        for comment in comments:
            comment_text = comment.get('comment_text', '')
            if comment_text:
                tone = self.analyze_comment_tone(comment_text)
                style = self.analyze_writing_style(comment_text)
                
                comment_tones.append(tone)
                comment_styles.append(style)
        
        # Aggregate tone analysis
        aggregated_tone = self._aggregate_tone_scores(comment_tones)
        
        # Aggregate style analysis
        aggregated_style = self._aggregate_style_analysis(comment_styles)
        
        # Generate tone profile
        tone_profile = self._generate_tone_profile(aggregated_tone, aggregated_style)
        
        return {
            'tone_scores': aggregated_tone,
            'writing_style': aggregated_style,
            'tone_profile': tone_profile,
            'analysis_metadata': {
                'comments_analyzed': len(comment_tones),
                'analysis_date': datetime.now(timezone.utc).isoformat()
            }
        }
    
    def _aggregate_tone_scores(self, comment_tones):
        """Aggregate tone scores across all comments"""
        if not comment_tones:
            return {}
        
        # Sum all tone scores
        total_scores = defaultdict(float)
        for tone_scores in comment_tones:
            for tone, score in tone_scores.items():
                total_scores[tone] += score
        
        # Normalize by number of comments
        num_comments = len(comment_tones)
        normalized_scores = {tone: score / num_comments for tone, score in total_scores.items()}
        
        return normalized_scores
    
    def _aggregate_style_analysis(self, comment_styles):
        """Aggregate style analysis across all comments"""
        if not comment_styles:
            return {}
        
        # Aggregate sentence length
        all_lengths = [style['sentence_length']['avg_length'] for style in comment_styles if style.get('sentence_length')]
        avg_sentence_length = sum(all_lengths) / len(all_lengths) if all_lengths else 0
        
        # Aggregate readability
        all_readability = [style['readability']['score'] for style in comment_styles if style.get('readability')]
        avg_readability = sum(all_readability) / len(all_readability) if all_readability else 0
        
        # Aggregate punctuation usage
        punctuation_totals = defaultdict(int)
        for style in comment_styles:
            if 'punctuation' in style:
                for punct_type, data in style['punctuation'].items():
                    punctuation_totals[punct_type] += data['count']
        
        return {
            'avg_sentence_length': round(avg_sentence_length, 2),
            'avg_readability': round(avg_readability, 2),
            'punctuation_usage': dict(punctuation_totals),
            'writing_consistency': self._calculate_consistency(comment_styles)
        }
    
    def _calculate_consistency(self, comment_styles):
        """Calculate writing consistency across comments"""
        if len(comment_styles) < 2:
            return {'score': 1.0, 'level': 'consistent'}
        
        # Calculate variance in sentence length
        lengths = [style['sentence_length']['avg_length'] for style in comment_styles if style.get('sentence_length')]
        if len(lengths) < 2:
            return {'score': 1.0, 'level': 'consistent'}
        
        mean_length = sum(lengths) / len(lengths)
        variance = sum((x - mean_length) ** 2 for x in lengths) / len(lengths)
        std_dev = math.sqrt(variance)
        
        # Consistency score (lower std dev = more consistent)
        consistency_score = max(0, 1 - (std_dev / mean_length)) if mean_length > 0 else 1
        
        if consistency_score >= 0.8:
            level = 'very_consistent'
        elif consistency_score >= 0.6:
            level = 'consistent'
        elif consistency_score >= 0.4:
            level = 'moderate'
        else:
            level = 'inconsistent'
        
        return {
            'score': round(consistency_score, 3),
            'level': level,
            'std_deviation': round(std_dev, 2)
        }
    
    def _generate_tone_profile(self, tone_scores, style_analysis):
        """Generate comprehensive tone profile"""
        # Find dominant tones
        sorted_tones = sorted(tone_scores.items(), key=lambda x: x[1], reverse=True)
        dominant_tones = [tone for tone, score in sorted_tones if score > 0.1]
        
        # Determine primary tone
        primary_tone = sorted_tones[0][0] if sorted_tones else 'neutral'
        
        # Determine writing style
        avg_length = style_analysis.get('avg_sentence_length', 0)
        if avg_length < 10:
            writing_style = 'concise'
        elif avg_length > 20:
            writing_style = 'detailed'
        else:
            writing_style = 'balanced'
        
        # Determine formality
        formal_score = tone_scores.get('formal', 0)
        casual_score = tone_scores.get('casual', 0)
        
        if formal_score > casual_score:
            formality = 'formal'
        elif casual_score > formal_score:
            formality = 'casual'
        else:
            formality = 'neutral'
        
        # Determine engagement style
        questioning_score = tone_scores.get('questioning', 0)
        educational_score = tone_scores.get('educational', 0)
        
        if questioning_score > educational_score:
            engagement_style = 'inquisitive'
        elif educational_score > questioning_score:
            engagement_style = 'instructive'
        else:
            engagement_style = 'collaborative'
        
        return {
            'primary_tone': primary_tone,
            'dominant_tones': dominant_tones[:3],
            'writing_style': writing_style,
            'formality': formality,
            'engagement_style': engagement_style,
            'tone_confidence': max(tone_scores.values()) if tone_scores else 0
        }
    
    def generate_tone_recommendations(self, tone_analysis):
        """Generate recommendations based on tone analysis"""
        recommendations = []
        
        tone_profile = tone_analysis.get('tone_profile', {})
        primary_tone = tone_profile.get('primary_tone', 'neutral')
        formality = tone_profile.get('formality', 'neutral')
        engagement_style = tone_profile.get('engagement_style', 'collaborative')
        
        # Tone-specific recommendations
        if primary_tone == 'technical':
            recommendations.append("Your technical expertise is clear - continue providing detailed, scientific explanations")
        elif primary_tone == 'empathetic':
            recommendations.append("Your empathetic approach is valuable - maintain your supportive, understanding tone")
        elif primary_tone == 'educational':
            recommendations.append("Your educational style is effective - keep providing helpful, instructive responses")
        
        # Formality recommendations
        if formality == 'formal':
            recommendations.append("Consider occasionally using a more casual tone to connect with users")
        elif formality == 'casual':
            recommendations.append("Your casual tone is engaging - consider adding more technical details when appropriate")
        
        # Engagement style recommendations
        if engagement_style == 'inquisitive':
            recommendations.append("Your questioning approach is great - continue asking clarifying questions")
        elif engagement_style == 'instructive':
            recommendations.append("Your instructive style is helpful - consider asking questions to understand user needs better")
        
        return recommendations
    
    def save_tone_analysis(self, analysis, username):
        """Save tone analysis to file"""
        # Create output directory
        os.makedirs('data/tone_analysis', exist_ok=True)
        
        filename = f"data/tone_analysis/{username}_tone_analysis.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Tone analysis saved to: {filename}")
        return filename

def main():
    """Main function for testing"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python tone_analyzer.py <username> [comments_file]")
        print("Example: python tone_analyzer.py dotconsistent3677 data/my_activity/my_reddit_activity_20250923_063732.json")
        sys.exit(1)
    
    username = sys.argv[1]
    comments_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    try:
        # Load comments
        if comments_file and os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            comments = data.get('recent_comments', [])
        else:
            print("❌ Comments file not found, using sample data")
            comments = []
        
        # Initialize analyzer
        analyzer = ToneAnalyzer()
        
        # Analyze tone
        tone_analysis = analyzer.analyze_user_tone(comments)
        
        # Generate recommendations
        recommendations = analyzer.generate_tone_recommendations(tone_analysis)
        tone_analysis['recommendations'] = recommendations
        
        # Save analysis
        filename = analyzer.save_tone_analysis(tone_analysis, username)
        
        # Print summary
        print(f"\n🎭 Tone Analysis Summary for u/{username}")
        print("="*50)
        
        tone_profile = tone_analysis.get('tone_profile', {})
        print(f"Primary Tone: {tone_profile.get('primary_tone', 'unknown')}")
        print(f"Writing Style: {tone_profile.get('writing_style', 'unknown')}")
        print(f"Formality: {tone_profile.get('formality', 'unknown')}")
        print(f"Engagement Style: {tone_profile.get('engagement_style', 'unknown')}")
        
        print(f"\nRecommendations:")
        for rec in recommendations:
            print(f"  • {rec}")
        
        print(f"\n✅ Tone analysis complete! Results saved to: {filename}")
        
    except Exception as e:
        print(f"❌ Error during tone analysis: {e}")
        raise

if __name__ == "__main__":
    main()
