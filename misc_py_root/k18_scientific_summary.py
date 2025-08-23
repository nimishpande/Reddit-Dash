#!/usr/bin/env python3
"""
K18 Hair Mask Scientific Analysis Summary
Generates a readable summary of the scientific content analysis results.
"""

import json
from collections import Counter
from datetime import datetime

def load_analysis_results():
    """Load the scientific analysis results."""
    analysis_file = "/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/raw data/K18_enhanced_scientific_analysis.json"
    
    try:
        with open(analysis_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ Error loading analysis results: {e}")
        return None

def print_scientific_summary():
    """Print a comprehensive summary of the scientific analysis."""
    print("🔬 ENHANCED K18 HAIR MASK SCIENTIFIC CONTENT ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"📅 Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Load results
    results = load_analysis_results()
    if not results:
        return
    
    summary = results['summary']
    
    # Overall statistics
    print("📊 OVERALL STATISTICS")
    print("-" * 40)
    print(f"📝 Total Posts Analyzed: {summary['total_posts']:,}")
    print(f"🔬 Posts with Scientific Content: {summary['scientific_posts']:,} ({summary['scientific_posts']/summary['total_posts']*100:.1f}%)")
    print(f"🧬 K18-Specific Scientific Posts: {summary['k18_specific_posts']:,} ({summary['k18_specific_posts']/summary['total_posts']*100:.1f}%)")
    print(f"❓ Posts with Inquiries: {summary['posts_with_inquiries']:,} ({summary['posts_with_inquiries']/summary['total_posts']*100:.1f}%)")
    print(f"💬 Total Comments Analyzed: {summary['total_comments']:,}")
    print(f"🔬 Comments with Scientific Content: {summary['scientific_comments']:,} ({summary['scientific_comments']/summary['total_comments']*100:.1f}%)")
    print()
    
    # Subreddit analysis
    print("📊 SUBREDDIT BREAKDOWN (Top 15 by Scientific Content)")
    print("-" * 60)
    
    # Sort subreddits by scientific posts
    subreddit_stats = summary['subreddit_breakdown']
    sorted_subreddits = sorted(
        subreddit_stats.items(),
        key=lambda x: x[1]['scientific_posts'],
        reverse=True
    )
    
    for i, (subreddit, stats) in enumerate(sorted_subreddits[:15], 1):
        if stats['posts'] > 0:
            scientific_pct = stats['scientific_posts'] / stats['posts'] * 100
            k18_pct = stats['k18_specific_posts'] / stats['posts'] * 100
            inquiry_pct = stats['posts_with_inquiries'] / stats['posts'] * 100 if 'posts_with_inquiries' in stats else 0
            print(f"{i:2d}. r/{subreddit:<20} | Posts: {stats['posts']:3d} | Scientific: {stats['scientific_posts']:3d} ({scientific_pct:5.1f}%) | K18: {stats['k18_specific_posts']:2d} ({k18_pct:5.1f}%) | Inquiries: {stats.get('posts_with_inquiries', 0):2d} ({inquiry_pct:5.1f}%)")
    print()
    
    # NEW: Inquiry breakdown
    print("❓ INQUIRY TYPE BREAKDOWN")
    print("-" * 40)
    inquiry_breakdown = summary.get('inquiry_breakdown', {})
    if inquiry_breakdown:
        for inquiry_type, count in sorted(inquiry_breakdown.items(), key=lambda x: x[1], reverse=True):
            formatted_type = inquiry_type.replace('_', ' ').title()
            print(f"  {formatted_type}: {count}")
    else:
        print("  No inquiry data available")
    print()
    
    # NEW: Top inquiry posts
    print("🏆 TOP INQUIRY POSTS")
    print("-" * 40)
    top_inquiry_posts = results.get('inquiry_analysis', {}).get('top_inquiry_posts', [])
    for i, post in enumerate(top_inquiry_posts[:10], 1):
        total_confidence = sum(post.get('inquiry_confidence', {}).values())
        inquiry_types = ', '.join(post.get('inquiry_types', []))
        print(f"{i}. Confidence: {total_confidence} | Types: {inquiry_types}")
        print(f"   r/{post['subreddit']} | {post['title'][:60]}...")
        if post.get('question_sentences'):
            print(f"   Q: {post['question_sentences'][0][:80]}...")
        print()
    
    # NEW: Searchable post titles by type
    print("🔍 SEARCHABLE POST TITLES FOR REDDIT")
    print("=" * 50)
    print("Copy these titles to search on Reddit for the full conversations:")
    print()
    
    inquiry_by_type = results.get('inquiry_analysis', {}).get('by_type', {})
    for inquiry_type, posts in inquiry_by_type.items():
        if posts:
            # Deduplicate posts by creating unique identifiers
            unique_posts = []
            seen_posts = set()
            
            for post in posts:
                # Create unique identifier from subreddit + title
                post_id = f"{post['subreddit']}_{post['title']}"
                if post_id not in seen_posts:
                    seen_posts.add(post_id)
                    unique_posts.append(post)
            
            formatted_type = inquiry_type.replace('_', ' ').title()
            print(f"\n📋 {formatted_type.upper()} ({len(unique_posts)} unique posts):")
            print("-" * 50)
            for i, post in enumerate(unique_posts, 1):
                subreddit = post['subreddit']
                title = post['title']
                print(f"{i:2d}. {title}")
                print(f"    Subreddit: r/{subreddit}")
                print()
            print()
    
    # NEW: Clean title list for easy copying
    print("\n📝 CLEAN TITLE LIST FOR COPYING:")
    print("=" * 50)
    print("Copy these exact titles to search on Reddit:")
    print()
    
    for inquiry_type, posts in inquiry_by_type.items():
        if posts:
            # Deduplicate posts by creating unique identifiers
            unique_posts = []
            seen_posts = set()
            
            for post in posts:
                # Create unique identifier from subreddit + title
                post_id = f"{post['subreddit']}_{post['title']}"
                if post_id not in seen_posts:
                    seen_posts.add(post_id)
                    unique_posts.append(post)
            
            formatted_type = inquiry_type.replace('_', ' ').title()
            print(f"\n--- {formatted_type.upper()} ({len(unique_posts)} unique posts) ---")
            for post in unique_posts:
                print(f'"{post["title"]}"')
            print()
    
    # Top scientific posts
    print("🏆 TOP 10 MOST SCIENTIFIC POSTS")
    print("-" * 60)
    
    top_posts = results.get('top_scientific_posts', [])
    for i, post in enumerate(top_posts[:10], 1):
        print(f"{i:2d}. Score: {post['scientific_score']:2d} | r/{post['subreddit']}")
        print(f"    Title: {post['title'][:70]}...")
        if post.get('k18_specific'):
            print(f"    🧬 K18-Specific Scientific Content")
        print()
    
    # Research mentions
    print("📚 MOST FREQUENT RESEARCH-RELATED TERMS")
    print("-" * 50)
    
    research_mentions = results.get('research_mentions', [])
    if research_mentions:
        research_counter = Counter(research_mentions)
        for term, count in research_counter.most_common(15):
            print(f"   {term:<20} : {count:3d}")
    else:
        print("   No research-related terms found")
    print()
    
    # Efficacy mentions
    print("✅ MOST FREQUENT EFFICACY-RELATED TERMS")
    print("-" * 50)
    
    efficacy_mentions = results.get('efficacy_mentions', [])
    if efficacy_mentions:
        efficacy_counter = Counter(efficacy_mentions)
        for term, count in efficacy_counter.most_common(15):
            print(f"   {term:<20} : {count:3d}")
    else:
        print("   No efficacy-related terms found")
    print()
    
    # Mechanism mentions
    print("⚙️  MOST FREQUENT MECHANISM-RELATED TERMS")
    print("-" * 50)
    
    mechanism_mentions = results.get('mechanism_mentions', [])
    if mechanism_mentions:
        mechanism_counter = Counter(mechanism_mentions)
        for term, count in mechanism_counter.most_common(15):
            print(f"   {term:<20} : {count:3d}")
    else:
        print("   No mechanism-related terms found")
    print()
    
    # Scientific sentences
    print("🔬 SAMPLE SCIENTIFIC SENTENCES")
    print("-" * 50)
    
    scientific_sentences = results.get('scientific_sentences', [])
    if scientific_sentences:
        # Sort by score and show top 10
        sorted_sentences = sorted(scientific_sentences, key=lambda x: x.get('score', 0), reverse=True)
        for i, sentence_data in enumerate(sorted_sentences[:10], 1):
            sentence = sentence_data.get('sentence', '')
            score = sentence_data.get('score', 0)
            mentions = sentence_data.get('mentions', [])
            
            print(f"{i:2d}. Score: {score} | {sentence[:100]}...")
            if mentions:
                print(f"    Mentions: {', '.join(mentions[:3])}")
            print()
    else:
        print("   No scientific sentences found")
    print()
    
    # K18-specific analysis
    print("🧬 K18-SPECIFIC SCIENTIFIC CONTENT")
    print("-" * 50)
    
    k18_posts = results.get('k18_specific_posts', [])
    if k18_posts:
        print(f"Found {len(k18_posts)} posts with K18-specific scientific content:")
        print()
        
        for i, post in enumerate(k18_posts[:5], 1):
            print(f"{i}. r/{post['subreddit']} | Score: {post['scientific_score']}")
            print(f"   Title: {post['title'][:80]}...")
            print()
    else:
        print("No K18-specific scientific content found")
    print()
    
    # Key insights
    print("💡 KEY INSIGHTS FROM ENHANCED ANALYSIS")
    print("-" * 50)
    
    total_posts = summary['total_posts']
    scientific_posts = summary['scientific_posts']
    k18_specific_posts = summary['k18_specific_posts']
    posts_with_inquiries = summary.get('posts_with_inquiries', 0)
    
    print(f"• {scientific_posts/total_posts*100:.1f}% of posts contain scientific terminology")
    print(f"• {k18_specific_posts/total_posts*100:.1f}% of posts specifically discuss K18 science")
    print(f"• {posts_with_inquiries/total_posts*100:.1f}% of posts contain specific inquiries about K18")
    
    if inquiry_breakdown:
        top_inquiry = max(inquiry_breakdown.items(), key=lambda x: x[1])
        print(f"• Most common inquiry type: {top_inquiry[0].replace('_', ' ').title()} ({top_inquiry[1]} posts)")
    
    peptide_mechanism_posts = inquiry_by_type.get('peptide_mechanism', [])
    clinical_trial_posts = inquiry_by_type.get('clinical_trials', [])
    patent_posts = inquiry_by_type.get('patent_inquiry', [])
    
    print(f"• Peptide mechanism questions: {len(peptide_mechanism_posts)} posts")
    print(f"• Clinical trial inquiries: {len(clinical_trial_posts)} posts") 
    print(f"• Patent/IP discussions: {len(patent_posts)} posts")
    
    if results.get('inquiry_analysis', {}).get('question_sentences'):
        print(f"• Total question sentences extracted: {len(results['inquiry_analysis']['question_sentences'])}")
    
    # NEW: Detailed post titles for specific inquiry types (with deduplication)
    print("\n🔬 DETAILED POST TITLES BY INQUIRY TYPE")
    print("=" * 50)
    
    # Helper function to deduplicate posts
    def deduplicate_posts(posts):
        unique_posts = []
        seen_posts = set()
        for post in posts:
            post_id = f"{post['subreddit']}_{post['title']}"
            if post_id not in seen_posts:
                seen_posts.add(post_id)
                unique_posts.append(post)
        return unique_posts
    
    # Peptide mechanism questions
    unique_peptide_posts = deduplicate_posts(peptide_mechanism_posts)
    print(f"\n🧬 PEPTIDE MECHANISM QUESTIONS ({len(unique_peptide_posts)} unique posts):")
    print("-" * 40)
    if unique_peptide_posts:
        for i, post in enumerate(unique_peptide_posts, 1):
            print(f"{i:2d}. r/{post['subreddit']} | {post['title']}")
            if post.get('question_sentences'):
                print(f"    Q: {post['question_sentences'][0][:100]}...")
            print()
    else:
        print("   No peptide mechanism questions found")
    
    # Clinical trial inquiries
    unique_clinical_posts = deduplicate_posts(clinical_trial_posts)
    print(f"\n📊 CLINICAL TRIAL INQUIRIES ({len(unique_clinical_posts)} unique posts):")
    print("-" * 40)
    if unique_clinical_posts:
        for i, post in enumerate(unique_clinical_posts, 1):
            print(f"{i:2d}. r/{post['subreddit']} | {post['title']}")
            if post.get('question_sentences'):
                print(f"    Q: {post['question_sentences'][0][:100]}...")
            print()
    else:
        print("   No clinical trial inquiries found")
    
    # Patent/IP discussions
    unique_patent_posts = deduplicate_posts(patent_posts)
    print(f"\n📜 PATENT/IP DISCUSSIONS ({len(unique_patent_posts)} unique posts):")
    print("-" * 40)
    if unique_patent_posts:
        for i, post in enumerate(unique_patent_posts, 1):
            print(f"{i:2d}. r/{post['subreddit']} | {post['title']}")
            if post.get('question_sentences'):
                print(f"    Q: {post['question_sentences'][0][:100]}...")
            print()
    else:
        print("   No patent/IP discussions found")
    
    print("\n🎯 ANALYSIS FOCUS AREAS IDENTIFIED:")
    print("=" * 40)
    print("✓ Peptide mechanism questions - How does K18 peptide actually work?")
    print("✓ Patent inquiries - Do they have exclusive rights?")
    print("✓ Clinical trial discussions - What research backs their claims?")
    print("✓ Skeptical analysis - Is it worth the hype?")
    print("✓ Company background - Who makes K18?")
    print("✓ Product comparisons - How does it compare to alternatives?")
    print("✓ Ingredient deep dives - What's actually in the formula?")
    print()
    
    print("=" * 80)
    print("✅ Enhanced analysis complete! Check the detailed JSON file for more information.")

def main():
    """Main function."""
    print_scientific_summary()

if __name__ == "__main__":
    main() 