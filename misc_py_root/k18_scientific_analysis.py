#!/usr/bin/env python3
"""
K18 Hair Mask Scientific Analysis
Analyzes Reddit posts and comments for scientific references, research mentions, 
efficacy discussions, and peptide-related content.
"""

import json
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict, Counter
from datetime import datetime

# Note: spaCy removed due to compatibility issues - using regex-based analysis
SPACY_AVAILABLE = False
print("⚠ Using regex-based analysis (spaCy not available)")

class EnhancedK18ScientificAnalyzer:
    def __init__(self):
        # Original scientific keywords (keeping existing ones)
        self.scientific_keywords = {
            'research': ['research', 'study', 'studies', 'clinical trial', 'clinical study', 
                        'scientifically', 'evidence', 'evidence-based', 'peer-reviewed',
                        'published', 'journal', 'paper', 'article', 'literature', 'meta-analysis',
                        'systematic review', 'randomized', 'controlled trial', 'double-blind'],
            
            'peptide_specific': ['peptide', 'peptides', 'oligopeptide', 'polypeptide', 'amino acid',
                                'molecular', 'molecularly', 'bond repair', 'keratin', 'keratinocyte',
                                'collagen', 'elastin', 'fibroblast', 'cellular', 'cell repair',
                                'protein synthesis', 'protein repair', 'molecular repair'],
            
            'efficacy': ['efficacy', 'effective', 'effectiveness', 'results', 'outcome', 'improvement',
                        'benefit', 'benefits', 'performance', 'efficiency', 'success rate', 'successful',
                        'proven', 'validated', 'verified', 'tested', 'trialed', 'studied'],
            
            'mechanism': ['mechanism', 'mechanism of action', 'how it works', 'process', 'pathway',
                         'reaction', 'interaction', 'binding', 'activation', 'stimulation', 'promotion',
                         'inhibition', 'regulation', 'synthesis', 'production', 'formation'],
            
            'ingredients': ['ingredient', 'ingredients', 'formula', 'formulation', 'compound', 'compounds',
                           'molecule', 'molecules', 'chemical', 'chemistry', 'composition', 'active ingredient',
                           'key ingredient', 'main ingredient', 'primary ingredient'],
            
            'clinical': ['clinical', 'clinically', 'medical', 'medically', 'therapeutic', 'therapeutically',
                        'treatment', 'therapy', 'dermatological', 'dermatology', 'cosmetic science',
                        'cosmetic chemistry', 'formulation science', 'hair science', 'trichology']
        }
        
        # NEW: Specific inquiry patterns for K18 background questions
        self.inquiry_patterns = {
            'peptide_mechanism': {
                'questions': [
                    r'how does.*peptide.*work',
                    r'what does.*peptide.*do',
                    r'how.*k18.*peptide.*function',
                    r'mechanism.*peptide',
                    r'peptide.*mechanism',
                    r'how.*molecular.*repair.*work',
                    r'what.*molecular.*repair',
                    r'science.*behind.*k18',
                    r'how.*bond.*repair.*work',
                    r'what.*bond.*repair.*do'
                ],
                'keywords': ['peptide mechanism', 'how peptide works', 'peptide function', 
                           'molecular repair mechanism', 'bond repair process', 'peptide science',
                           'k18 science', 'peptide technology', 'molecular technology']
            },
            
            'patent_inquiry': {
                'questions': [
                    r'.*patent.*k18',
                    r'k18.*patent',
                    r'patent.*peptide',
                    r'peptide.*patent',
                    r'intellectual property.*k18',
                    r'k18.*intellectual property',
                    r'proprietary.*k18',
                    r'k18.*proprietary',
                    r'exclusive.*peptide',
                    r'peptide.*exclusive'
                ],
                'keywords': ['patent', 'patents', 'patented', 'intellectual property', 'proprietary',
                           'exclusive technology', 'licensed', 'trademark', 'copyrighted']
            },
            
            'clinical_trials': {
                'questions': [
                    r'clinical.*trial.*k18',
                    r'k18.*clinical.*trial',
                    r'study.*k18',
                    r'k18.*study',
                    r'research.*k18',
                    r'k18.*research',
                    r'test.*k18',
                    r'k18.*test',
                    r'trial.*k18',
                    r'k18.*trial'
                ],
                'keywords': ['clinical trial', 'clinical study', 'research study', 'laboratory test',
                           'efficacy study', 'safety study', 'consumer study', 'independent study',
                           'third party study', 'peer reviewed study']
            },
            
            'skeptical_analysis': {
                'questions': [
                    r'k18.*scam',
                    r'k18.*fake',
                    r'k18.*marketing.*hype',
                    r'k18.*really.*work',
                    r'k18.*worth.*it',
                    r'k18.*overpriced',
                    r'k18.*overhyped',
                    r'skeptical.*k18',
                    r'doubt.*k18',
                    r'k18.*placebo'
                ],
                'keywords': ['scam', 'fake', 'marketing hype', 'overhyped', 'overpriced', 
                           'placebo effect', 'skeptical', 'doubtful', 'questionable',
                           'too good to be true', 'marketing claims']
            },
            
            'company_background': {
                'questions': [
                    r'who.*makes.*k18',
                    r'k18.*company',
                    r'company.*behind.*k18',
                    r'k18.*manufacturer',
                    r'k18.*brand.*history',
                    r'k18.*founder',
                    r'k18.*lab',
                    r'k18.*laboratory'
                ],
                'keywords': ['k18 company', 'k18 brand', 'k18 labs', 'k18 laboratory',
                           'founder', 'company history', 'brand history', 'manufacturer',
                           'parent company', 'laboratory', 'research team']
            },
            
            'comparison_inquiry': {
                'questions': [
                    r'k18.*vs.*other.*peptide',
                    r'k18.*compare.*other',
                    r'better.*than.*k18',
                    r'k18.*better.*than',
                    r'alternative.*k18',
                    r'k18.*alternative',
                    r'similar.*k18',
                    r'k18.*similar'
                ],
                'keywords': ['comparison', 'alternative', 'similar product', 'competitor',
                           'versus', 'vs', 'better than', 'worse than', 'equivalent']
            },
            
            'ingredient_deep_dive': {
                'questions': [
                    r'k18.*ingredient.*list',
                    r'what.*in.*k18',
                    r'k18.*formula',
                    r'k18.*formulation',
                    r'k18.*peptide.*sequence',
                    r'peptide.*chain.*k18',
                    r'molecular.*weight.*k18'
                ],
                'keywords': ['ingredient analysis', 'formula breakdown', 'peptide sequence',
                           'molecular weight', 'amino acid sequence', 'peptide chain',
                           'formulation science', 'ingredient science']
            }
        }
        
        # Question words and phrases that indicate inquiry
        self.question_indicators = [
            'how', 'what', 'why', 'when', 'where', 'who', 'which', 'whose',
            'does', 'is', 'are', 'can', 'could', 'would', 'should', 'will',
            'do you know', 'anyone know', 'has anyone', 'wondering',
            'curious', 'question', 'confused', 'explain', 'help me understand'
        ]
        
        # Existing terms (keeping all original functionality)
        self.k18_specific_terms = [
            'k18 peptide', 'k-18 peptide', 'k18 molecular repair', 'k18 bond repair',
            'k18 leave-in molecular repair', 'k18 molecular repair hair mask',
            'k18 peptide technology', 'k18 peptide complex', 'k18 molecular technology',
            'k18 bond repair technology', 'k18 peptide science', 'k18 molecular science'
        ]
        
        # Research institutions and companies
        self.research_entities = [
            'university', 'college', 'institute', 'laboratory', 'lab', 'research center',
            'clinical research', 'medical research', 'cosmetic research', 'dermatology research',
            'k18', 'k18 labs', 'k18 laboratory', 'k18 research', 'k18 science'
        ]
        
        # Scientific measurement terms
        self.measurement_terms = [
            'percentage', 'percent', '%', 'improvement', 'increase', 'decrease', 'reduction',
            'better', 'worse', 'significant', 'statistically significant', 'p-value', 'p value',
            'correlation', 'correlated', 'association', 'linked', 'related', 'connected'
        ]

    def analyze_text_for_scientific_content(self, text: str) -> Dict:
        """Enhanced analysis including inquiry detection."""
        if not text:
            return {'scientific_score': 0, 'categories': {}, 'mentions': [], 'confidence': 0}
        
        # Get original analysis
        text_lower = text.lower()
        analysis = {
            'scientific_score': 0,
            'categories': defaultdict(int),
            'mentions': [],
            'confidence': 0,
            'k18_specific': False,
            'research_mentions': [],
            'efficacy_mentions': [],
            'mechanism_mentions': [],
            'inquiry_analysis': {}  # NEW
        }
        
        # Original scientific analysis (keeping existing logic)
        for term in self.k18_specific_terms:
            if term in text_lower:
                analysis['k18_specific'] = True
                analysis['scientific_score'] += 3
                analysis['mentions'].append(f"K18-specific: {term}")
        
        for category, keywords in self.scientific_keywords.items():
            category_score = 0
            category_mentions = []
            
            for keyword in keywords:
                if keyword in text_lower:
                    category_score += 1
                    category_mentions.append(keyword)
            
            if category_score > 0:
                analysis['categories'][category] = category_score
                analysis['scientific_score'] += category_score
                analysis['mentions'].extend([f"{category}: {mention}" for mention in category_mentions])
                
                if category == 'research':
                    analysis['research_mentions'].extend(category_mentions)
                elif category == 'efficacy':
                    analysis['efficacy_mentions'].extend(category_mentions)
                elif category == 'mechanism':
                    analysis['mechanism_mentions'].extend(category_mentions)
        
        # Check for research entities
        for entity in self.research_entities:
            if entity in text_lower:
                analysis['scientific_score'] += 2
                analysis['mentions'].append(f"Research entity: {entity}")
        
        # Check for measurement terms
        for term in self.measurement_terms:
            if term in text_lower:
                analysis['scientific_score'] += 1
                analysis['mentions'].append(f"Measurement: {term}")
        
        # NEW: Add inquiry analysis
        inquiry_analysis = self.detect_inquiry_type(text)
        analysis['inquiry_analysis'] = inquiry_analysis
        
        # Boost scientific score for inquiries
        if inquiry_analysis['inquiry_types']:
            max_inquiry_score = max(inquiry_analysis['confidence_scores'].values()) if inquiry_analysis['confidence_scores'] else 0
            analysis['scientific_score'] += max_inquiry_score
        
        # Calculate confidence
        analysis['confidence'] = min(1.0, analysis['scientific_score'] / 15.0)  # Adjusted for higher scores
        
        return analysis

    def detect_inquiry_type(self, text: str) -> Dict:
        """Detect what type of inquiry/question is being asked about K18."""
        if not text:
            return {'inquiry_types': [], 'confidence_scores': {}, 'question_sentences': []}
        
        text_lower = text.lower()
        detected_inquiries = {
            'inquiry_types': [],
            'confidence_scores': {},
            'question_sentences': [],
            'matched_patterns': {}
        }
        
        # Check if text contains question indicators
        has_question_indicator = any(indicator in text_lower for indicator in self.question_indicators)
        
        # Analyze each inquiry type
        for inquiry_type, patterns in self.inquiry_patterns.items():
            score = 0
            matched_patterns = []
            
            # Check regex patterns
            for pattern in patterns['questions']:
                matches = re.findall(pattern, text_lower, re.IGNORECASE)
                if matches:
                    score += 3  # High score for pattern matches
                    matched_patterns.extend(matches)
            
            # Check keywords
            for keyword in patterns['keywords']:
                if keyword in text_lower:
                    score += 1
                    matched_patterns.append(keyword)
            
            # Bonus for having question indicators
            if has_question_indicator and score > 0:
                score += 1
            
            if score > 0:
                detected_inquiries['inquiry_types'].append(inquiry_type)
                detected_inquiries['confidence_scores'][inquiry_type] = score
                detected_inquiries['matched_patterns'][inquiry_type] = matched_patterns
        
        # Extract sentences that look like questions
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) > 10:
                sentence_lower = sentence.lower()
                if (any(indicator in sentence_lower for indicator in self.question_indicators) or
                    sentence.endswith('?')):
                    # Check if sentence mentions K18
                    if 'k18' in sentence_lower or 'peptide' in sentence_lower:
                        detected_inquiries['question_sentences'].append(sentence)
        
        return detected_inquiries

    def extract_scientific_sentences(self, text: str) -> List[str]:
        """Extract sentences that contain scientific content (keeping existing logic)."""
        if not text:
            return []
        
        sentences = re.split(r'[.!?]+', text)
        scientific_sentences = []
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:
                continue
            
            analysis = self.analyze_text_for_scientific_content(sentence)
            if analysis['scientific_score'] >= 2:
                scientific_sentences.append({
                    'sentence': sentence,
                    'score': analysis['scientific_score'],
                    'mentions': analysis['mentions'],
                    'inquiry_types': analysis.get('inquiry_analysis', {}).get('inquiry_types', [])
                })
        
        return scientific_sentences

    def analyze_post_scientific_content(self, post: Dict) -> Dict:
        """Enhanced post analysis with inquiry detection."""
        post_analysis = {
            'post_id': post.get('id'),
            'title': post.get('title', ''),
            'subreddit': post.get('subreddit', ''),
            'scientific_score': 0,
            'categories': defaultdict(int),
            'scientific_sentences': [],
            'k18_specific': False,
            'research_mentions': [],
            'efficacy_mentions': [],
            'mechanism_mentions': [],
            'inquiry_types': [],  # NEW
            'question_sentences': [],  # NEW
            'inquiry_confidence': {}  # NEW
        }
        
        # Analyze title
        title_analysis = self.analyze_text_for_scientific_content(post.get('title', ''))
        post_analysis['scientific_score'] += title_analysis['scientific_score']
        post_analysis['k18_specific'] = title_analysis['k18_specific']
        
        # Analyze post body
        body_analysis = self.analyze_text_for_scientific_content(post.get('selftext', ''))
        post_analysis['scientific_score'] += body_analysis['scientific_score']
        post_analysis['k18_specific'] = post_analysis['k18_specific'] or body_analysis.get('k18_specific', False)
        
        # Combine inquiry analysis
        all_inquiry_types = set()
        all_question_sentences = []
        combined_confidence = {}
        
        for analysis in [title_analysis, body_analysis]:
            inquiry_data = analysis.get('inquiry_analysis', {})
            all_inquiry_types.update(inquiry_data.get('inquiry_types', []))
            all_question_sentences.extend(inquiry_data.get('question_sentences', []))
            
            for inquiry_type, score in inquiry_data.get('confidence_scores', {}).items():
                if inquiry_type in combined_confidence:
                    combined_confidence[inquiry_type] = max(combined_confidence[inquiry_type], score)
                else:
                    combined_confidence[inquiry_type] = score
        
        post_analysis['inquiry_types'] = list(all_inquiry_types)
        post_analysis['question_sentences'] = all_question_sentences
        post_analysis['inquiry_confidence'] = combined_confidence
        
        # Extract scientific sentences from body
        post_analysis['scientific_sentences'] = self.extract_scientific_sentences(post.get('selftext', ''))
        
        # Combine mentions (keeping existing logic)
        post_analysis['research_mentions'] = title_analysis.get('research_mentions', []) + body_analysis.get('research_mentions', [])
        post_analysis['efficacy_mentions'] = title_analysis.get('efficacy_mentions', []) + body_analysis.get('efficacy_mentions', [])
        post_analysis['mechanism_mentions'] = title_analysis.get('mechanism_mentions', []) + body_analysis.get('mechanism_mentions', [])
        
        # Analyze comments
        comments_analysis = []
        for comment in post.get('comments', []):
            comment_analysis = self.analyze_comment_scientific_content(comment)
            if comment_analysis['scientific_score'] > 0:
                comments_analysis.append(comment_analysis)
                post_analysis['scientific_score'] += comment_analysis['scientific_score']
                post_analysis['k18_specific'] = post_analysis['k18_specific'] or comment_analysis.get('k18_specific', False)
                
                # Combine comment inquiries
                all_inquiry_types.update(comment_analysis.get('inquiry_types', []))
                all_question_sentences.extend(comment_analysis.get('question_sentences', []))
                
                for inquiry_type, score in comment_analysis.get('inquiry_confidence', {}).items():
                    if inquiry_type in combined_confidence:
                        combined_confidence[inquiry_type] = max(combined_confidence[inquiry_type], score)
                    else:
                        combined_confidence[inquiry_type] = score
        
        # Update with comment data
        post_analysis['inquiry_types'] = list(all_inquiry_types)
        post_analysis['question_sentences'] = list(set(all_question_sentences))  # Remove duplicates
        post_analysis['inquiry_confidence'] = combined_confidence
        post_analysis['comments_analysis'] = comments_analysis
        
        return post_analysis

    def analyze_comment_scientific_content(self, comment: Dict) -> Dict:
        """Enhanced comment analysis with inquiry detection."""
        comment_analysis = {
            'comment_id': comment.get('id'),
            'body': comment.get('body', ''),
            'scientific_score': 0,
            'scientific_sentences': [],
            'k18_specific': False,
            'research_mentions': [],
            'efficacy_mentions': [],
            'mechanism_mentions': [],
            'inquiry_types': [],  # NEW
            'question_sentences': [],  # NEW
            'inquiry_confidence': {}  # NEW
        }
        
        # Analyze comment body
        body_analysis = self.analyze_text_for_scientific_content(comment.get('body', ''))
        comment_analysis['scientific_score'] = body_analysis['scientific_score']
        comment_analysis['k18_specific'] = body_analysis.get('k18_specific', False)
        comment_analysis['research_mentions'] = body_analysis.get('research_mentions', [])
        comment_analysis['efficacy_mentions'] = body_analysis.get('efficacy_mentions', [])
        comment_analysis['mechanism_mentions'] = body_analysis.get('mechanism_mentions', [])
        
        # Add inquiry analysis
        inquiry_data = body_analysis.get('inquiry_analysis', {})
        comment_analysis['inquiry_types'] = inquiry_data.get('inquiry_types', [])
        comment_analysis['question_sentences'] = inquiry_data.get('question_sentences', [])
        comment_analysis['inquiry_confidence'] = inquiry_data.get('confidence_scores', {})
        
        # Extract scientific sentences
        comment_analysis['scientific_sentences'] = self.extract_scientific_sentences(comment.get('body', ''))
        
        return comment_analysis

    def analyze_all_posts(self, data: Dict) -> Dict:
        """Enhanced analysis with inquiry tracking."""
        print("🔬 Starting enhanced scientific content analysis...")
        
        all_analysis = {
            'summary': {
                'total_posts': 0,
                'scientific_posts': 0,
                'k18_specific_posts': 0,
                'total_comments': 0,
                'scientific_comments': 0,
                'k18_specific_comments': 0,
                'posts_with_inquiries': 0,  # NEW
                'inquiry_breakdown': defaultdict(int),  # NEW
                'subreddit_breakdown': defaultdict(lambda: {
                    'posts': 0,
                    'scientific_posts': 0,
                    'k18_specific_posts': 0,
                    'posts_with_inquiries': 0,  # NEW
                    'comments': 0,
                    'scientific_comments': 0,
                    'k18_specific_comments': 0
                })
            },
            'scientific_posts': [],
            'k18_specific_posts': [],
            'inquiry_posts': [],  # NEW
            'top_scientific_posts': [],
            'subreddit_analysis': defaultdict(list),
            'research_mentions': [],
            'efficacy_mentions': [],
            'mechanism_mentions': [],
            'scientific_sentences': [],
            'inquiry_analysis': {  # NEW
                'by_type': defaultdict(list),
                'question_sentences': [],
                'top_inquiry_posts': []
            }
        }
        
        posts = data.get('results', [])
        all_analysis['summary']['total_posts'] = len(posts)
        
        for i, post in enumerate(posts, 1):
            if i % 100 == 0:
                print(f"📊 Analyzing post {i}/{len(posts)}...")
            
            post_analysis = self.analyze_post_scientific_content(post)
            subreddit = post_analysis['subreddit']
            
            # Update subreddit breakdown
            subreddit_stats = all_analysis['summary']['subreddit_breakdown'][subreddit]
            subreddit_stats['posts'] += 1
            subreddit_stats['comments'] += len(post.get('comments', []))
            
            # Track scientific posts
            if post_analysis['scientific_score'] > 0:
                all_analysis['summary']['scientific_posts'] += 1
                subreddit_stats['scientific_posts'] += 1
                all_analysis['scientific_posts'].append(post_analysis)
                all_analysis['subreddit_analysis'][subreddit].append(post_analysis)
            
            # Track K18-specific posts
            if post_analysis['k18_specific']:
                all_analysis['summary']['k18_specific_posts'] += 1
                subreddit_stats['k18_specific_posts'] += 1
                all_analysis['k18_specific_posts'].append(post_analysis)
            
            # NEW: Track inquiry posts
            if post_analysis['inquiry_types']:
                all_analysis['summary']['posts_with_inquiries'] += 1
                subreddit_stats['posts_with_inquiries'] += 1
                all_analysis['inquiry_posts'].append(post_analysis)
                
                # Track inquiry types
                for inquiry_type in post_analysis['inquiry_types']:
                    all_analysis['summary']['inquiry_breakdown'][inquiry_type] += 1
                    all_analysis['inquiry_analysis']['by_type'][inquiry_type].append(post_analysis)
                
                # Collect question sentences
                all_analysis['inquiry_analysis']['question_sentences'].extend(
                    post_analysis['question_sentences']
                )
            
            # Track comments (keeping existing logic)
            for comment_analysis in post_analysis.get('comments_analysis', []):
                all_analysis['summary']['total_comments'] += 1
                
                if comment_analysis['scientific_score'] > 0:
                    all_analysis['summary']['scientific_comments'] += 1
                    subreddit_stats['scientific_comments'] += 1
                
                if comment_analysis['k18_specific']:
                    all_analysis['summary']['k18_specific_comments'] += 1
                    subreddit_stats['k18_specific_comments'] += 1
            
            # Collect mentions (keeping existing logic)
            all_analysis['research_mentions'].extend(post_analysis['research_mentions'])
            all_analysis['efficacy_mentions'].extend(post_analysis['efficacy_mentions'])
            all_analysis['mechanism_mentions'].extend(post_analysis['mechanism_mentions'])
            all_analysis['scientific_sentences'].extend(post_analysis['scientific_sentences'])
            
            for comment_analysis in post_analysis.get('comments_analysis', []):
                all_analysis['scientific_sentences'].extend(comment_analysis['scientific_sentences'])
        
        # Get top posts
        all_analysis['top_scientific_posts'] = sorted(
            all_analysis['scientific_posts'], 
            key=lambda x: x['scientific_score'], 
            reverse=True
        )[:20]
        
        # NEW: Get top inquiry posts
        all_analysis['inquiry_analysis']['top_inquiry_posts'] = sorted(
            all_analysis['inquiry_posts'],
            key=lambda x: sum(x['inquiry_confidence'].values()),
            reverse=True
        )[:15]
        
        # Convert defaultdict to regular dict
        all_analysis['summary']['subreddit_breakdown'] = dict(all_analysis['summary']['subreddit_breakdown'])
        all_analysis['summary']['inquiry_breakdown'] = dict(all_analysis['summary']['inquiry_breakdown'])
        all_analysis['subreddit_analysis'] = dict(all_analysis['subreddit_analysis'])
        all_analysis['inquiry_analysis']['by_type'] = dict(all_analysis['inquiry_analysis']['by_type'])
        
        return all_analysis

def main():
    """Main function with enhanced analysis reporting."""
    print("🔬 Enhanced K18 Hair Mask Scientific Content Analysis")
    print("=" * 60)
    
    # Load the K18 data
    data_file = "/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/raw data/K18_Hair_Mask_all_comments.json"
    
    try:
        print(f"📂 Loading data from {data_file}...")
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ Data loaded successfully")
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        return
    
    # Analyze the data
    analyzer = EnhancedK18ScientificAnalyzer()
    analysis_results = analyzer.analyze_all_posts(data)
    
    # Print enhanced summary
    print("\n📊 ENHANCED SCIENTIFIC CONTENT SUMMARY")
    print("=" * 60)
    summary = analysis_results['summary']
    
    print(f"📝 Total Posts: {summary['total_posts']}")
    print(f"🔬 Scientific Posts: {summary['scientific_posts']} ({summary['scientific_posts']/summary['total_posts']*100:.1f}%)")
    print(f"🧬 K18-Specific Posts: {summary['k18_specific_posts']} ({summary['k18_specific_posts']/summary['total_posts']*100:.1f}%)")
    print(f"❓ Posts with Inquiries: {summary['posts_with_inquiries']} ({summary['posts_with_inquiries']/summary['total_posts']*100:.1f}%)")
    print(f"💬 Total Comments: {summary['total_comments']}")
    print(f"🔬 Scientific Comments: {summary['scientific_comments']} ({summary['scientific_comments']/summary['total_comments']*100:.1f}%)")
    
    # NEW: Inquiry breakdown
    print(f"\n❓ INQUIRY TYPE BREAKDOWN")
    print("=" * 40)
    inquiry_breakdown = summary['inquiry_breakdown']
    for inquiry_type, count in sorted(inquiry_breakdown.items(), key=lambda x: x[1], reverse=True):
        formatted_type = inquiry_type.replace('_', ' ').title()
        print(f"  {formatted_type}: {count}")
    
    # Top inquiry posts
    print(f"\n🏆 TOP INQUIRY POSTS")
    print("=" * 40)
    top_inquiry_posts = analysis_results['inquiry_analysis']['top_inquiry_posts']
    for i, post in enumerate(top_inquiry_posts[:10], 1):
        total_confidence = sum(post['inquiry_confidence'].values())
        inquiry_types = ', '.join(post['inquiry_types'])
        print(f"{i}. Confidence: {total_confidence} | Types: {inquiry_types}")
        print(f"   r/{post['subreddit']} | {post['title'][:60]}...")
        if post['question_sentences']:
            print(f"   Q: {post['question_sentences'][0][:80]}...")
        print()
    
    # Sample questions by type
    print(f"\n❓ SAMPLE QUESTIONS BY TYPE")
    print("=" * 40)
    inquiry_by_type = analysis_results['inquiry_analysis']['by_type']
    for inquiry_type, posts in inquiry_by_type.items():
        if posts:
            formatted_type = inquiry_type.replace('_', ' ').title()
            print(f"\n{formatted_type}:")
            for post in posts[:3]:  # Show top 3 examples
                if post['question_sentences']:
                    print(f"  - {post['question_sentences'][0]}")
    
    # Subreddit breakdown with inquiries
    print(f"\n📊 SUBREDDIT BREAKDOWN (with Inquiries)")
    print("=" * 50)
    for subreddit, stats in summary['subreddit_breakdown'].items():
        if stats['posts'] > 0:
            scientific_pct = stats['scientific_posts'] / stats['posts'] * 100
            k18_pct = stats['k18_specific_posts'] / stats['posts'] * 100
            inquiry_pct = stats['posts_with_inquiries'] / stats['posts'] * 100
            print(f"r/{subreddit}:")
            print(f"  Posts: {stats['posts']} | Scientific: {stats['scientific_posts']} ({scientific_pct:.1f}%) | K18: {stats['k18_specific_posts']} ({k18_pct:.1f}%) | Inquiries: {stats['posts_with_inquiries']} ({inquiry_pct:.1f}%)")
    
    # Research mentions (keeping existing functionality)
    print(f"\n📚 RESEARCH MENTIONS")
    print("=" * 30)
    research_counter = Counter(analysis_results['research_mentions'])
    for term, count in research_counter.most_common(10):
        print(f"{term}: {count}")
    
    # Save enhanced analysis
    output_file = "/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/raw data/K18_enhanced_scientific_analysis.json"
    print(f"\n💾 Saving enhanced analysis to {output_file}...")
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Enhanced analysis saved successfully!")
    print(f"📏 File size: {len(json.dumps(analysis_results, ensure_ascii=False)) / (1024*1024):.2f} MB")
    
    # Print key insights
    print(f"\n💡 KEY INSIGHTS FROM ENHANCED ANALYSIS")
    print("=" * 50)
    print(f"• {summary['posts_with_inquiries']/summary['total_posts']*100:.1f}% of posts contain specific inquiries about K18")
    
    if inquiry_breakdown:
        top_inquiry = max(inquiry_breakdown.items(), key=lambda x: x[1])
        print(f"• Most common inquiry type: {top_inquiry[0].replace('_', ' ').title()} ({top_inquiry[1]} posts)")
    
    peptide_mechanism_posts = len(inquiry_by_type.get('peptide_mechanism', []))
    clinical_trial_posts = len(inquiry_by_type.get('clinical_trials', []))
    patent_posts = len(inquiry_by_type.get('patent_inquiry', []))
    
    print(f"• Peptide mechanism questions: {peptide_mechanism_posts} posts")
    print(f"• Clinical trial inquiries: {clinical_trial_posts} posts") 
    print(f"• Patent/IP discussions: {patent_posts} posts")
    
    if analysis_results['inquiry_analysis']['question_sentences']:
        print(f"• Total question sentences extracted: {len(analysis_results['inquiry_analysis']['question_sentences'])}")
    
    print("\n🎯 ANALYSIS FOCUS AREAS IDENTIFIED:")
    print("=" * 40)
    print("✓ Peptide mechanism questions - How does K18 peptide actually work?")
    print("✓ Patent inquiries - Do they have exclusive rights?")
    print("✓ Clinical trial discussions - What research backs their claims?")
    print("✓ Skeptical analysis - Is it worth the hype?")
    print("✓ Company background - Who makes K18?")
    print("✓ Product comparisons - How does it compare to alternatives?")
    print("✓ Ingredient deep dives - What's actually in the formula?")

if __name__ == "__main__":
    main() 