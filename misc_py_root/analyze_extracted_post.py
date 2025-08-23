import json
import os
from collections import Counter
from datetime import datetime

def analyze_extracted_post(json_file_path):
    """Analyze the extracted Reddit post data and provide insights"""
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract key information
    post_data = data['post_data']
    comments = data['comments']
    stats = data['comment_statistics']
    
    print("🔍 REDDIT POST ANALYSIS")
    print("=" * 50)
    
    # Post Information
    print(f"\n📝 POST DETAILS:")
    print(f"   Title: {post_data['title']}")
    print(f"   Author: u/{post_data['author']}")
    print(f"   Subreddit: r/{post_data['subreddit']}")
    print(f"   Score: {post_data['score']} upvotes")
    print(f"   Upvote Ratio: {post_data['upvote_ratio']:.2%}")
    print(f"   Created: {datetime.fromtimestamp(post_data['created_utc']).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Subreddit Subscribers: {post_data['subreddit_subscribers']:,}")
    
    # Comment Statistics
    print(f"\n💬 COMMENT STATISTICS:")
    print(f"   Total Comments: {stats['total_comments']}")
    print(f"   Total Upvotes: {stats['total_upvotes']}")
    print(f"   Average Upvotes per Comment: {stats['average_upvotes']:.2f}")
    print(f"   Comment Depth Distribution: {stats['depth_distribution']}")
    
    # Top Comments Analysis
    print(f"\n🏆 TOP 5 COMMENTS BY UPVOTES:")
    for i, comment in enumerate(stats['top_comments'][:5], 1):
        print(f"   {i}. u/{comment['author']} ({comment['score']} upvotes)")
        print(f"      \"{comment['body'][:100]}{'...' if len(comment['body']) > 100 else ''}\"")
        print()
    
    # Author Analysis
    print(f"\n👥 AUTHOR ANALYSIS:")
    authors = [comment['author'] for comment in comments if comment['author'] not in ['[deleted]', '[removed]']]
    author_counts = Counter(authors)
    top_authors = author_counts.most_common(5)
    
    print(f"   Unique Authors: {len(author_counts)}")
    print(f"   Top 5 Most Active Authors:")
    for author, count in top_authors:
        print(f"      u/{author}: {count} comments")
    
    # Engagement Analysis
    print(f"\n📊 ENGAGEMENT ANALYSIS:")
    total_replies = sum(len(comment.get('replies', [])) for comment in comments)
    comments_with_replies = sum(1 for comment in comments if comment.get('replies'))
    
    print(f"   Comments with Replies: {comments_with_replies}")
    print(f"   Total Replies: {total_replies}")
    print(f"   Reply Rate: {comments_with_replies/stats['total_comments']:.1%}")
    
    # Content Analysis
    print(f"\n📝 CONTENT ANALYSIS:")
    
    # Most common words in comments
    all_text = ' '.join([comment['body'].lower() for comment in comments])
    words = [word for word in all_text.split() if len(word) > 3 and word.isalpha()]
    word_counts = Counter(words)
    
    print(f"   Most Common Words (excluding common words):")
    common_words = ['that', 'this', 'with', 'have', 'they', 'will', 'from', 'your', 'hair', 'care', 'product', 'want', 'need', 'good', 'like', 'very', 'more', 'some', 'time', 'make', 'take', 'come', 'know', 'just', 'what', 'when', 'where', 'here', 'there', 'their', 'them', 'then', 'than', 'been', 'were', 'said', 'each', 'which', 'she', 'will', 'would', 'could', 'should', 'about', 'into', 'through', 'during', 'before', 'after', 'above', 'below', 'between', 'among', 'within', 'without', 'against', 'toward', 'towards', 'upon', 'under', 'over', 'behind', 'beside', 'beyond', 'inside', 'outside', 'around', 'across', 'along', 'throughout', 'except', 'including', 'until', 'since', 'while', 'whereas', 'although', 'because', 'unless', 'whether', 'while', 'though', 'even', 'much', 'many', 'such', 'only', 'very', 'really', 'quite', 'rather', 'almost', 'nearly', 'about', 'almost', 'exactly', 'just', 'merely', 'simply', 'hardly', 'barely', 'scarcely', 'seldom', 'rarely', 'never', 'always', 'often', 'usually', 'sometimes', 'occasionally', 'frequently', 'generally', 'normally', 'typically', 'commonly', 'regularly', 'constantly', 'continuously', 'permanently', 'temporarily', 'briefly', 'momentarily', 'instantly', 'immediately', 'soon', 'quickly', 'rapidly', 'slowly', 'gradually', 'suddenly', 'eventually', 'finally', 'ultimately', 'initially', 'originally', 'previously', 'formerly', 'lately', 'recently', 'currently', 'presently', 'nowadays', 'today', 'yesterday', 'tomorrow', 'tonight', 'morning', 'afternoon', 'evening', 'night', 'week', 'month', 'year', 'day', 'hour', 'minute', 'second', 'moment', 'instant', 'period', 'time', 'date', 'weekend', 'holiday', 'vacation', 'break', 'pause', 'stop', 'start', 'begin', 'end', 'finish', 'complete', 'continue', 'resume', 'pause', 'stop', 'start', 'begin', 'end', 'finish', 'complete', 'continue', 'resume']
    
    filtered_words = [word for word in word_counts.most_common(20) if word[0] not in common_words]
    for word, count in filtered_words[:10]:
        print(f"      '{word}': {count} times")
    
    # Sentiment Analysis (basic)
    print(f"\n😊 BASIC SENTIMENT ANALYSIS:")
    positive_words = ['good', 'great', 'love', 'amazing', 'best', 'recommend', 'safe', 'effective', 'helpful', 'wonderful', 'excellent', 'perfect', 'fantastic', 'awesome', 'brilliant', 'outstanding', 'superb', 'terrific', 'fabulous', 'marvelous']
    negative_words = ['bad', 'hate', 'avoid', 'dangerous', 'toxic', 'harmful', 'worst', 'terrible', 'awful', 'horrible', 'dreadful', 'frightful', 'ghastly', 'hideous', 'repulsive', 'revolting', 'disgusting', 'nauseating', 'sickening', 'vile']
    
    positive_count = sum(1 for comment in comments if any(word in comment['body'].lower() for word in positive_words))
    negative_count = sum(1 for comment in comments if any(word in comment['body'].lower() for word in negative_words))
    neutral_count = stats['total_comments'] - positive_count - negative_count
    
    print(f"   Positive Comments: {positive_count} ({positive_count/stats['total_comments']:.1%})")
    print(f"   Negative Comments: {negative_count} ({negative_count/stats['total_comments']:.1%})")
    print(f"   Neutral Comments: {neutral_count} ({neutral_count/stats['total_comments']:.1%})")
    
    # Key Insights
    print(f"\n💡 KEY INSIGHTS:")
    print(f"   • Post received {post_data['score']} upvotes with {post_data['upvote_ratio']:.1%} upvote ratio")
    print(f"   • {stats['total_comments']} comments generated {stats['total_upvotes']} total upvotes")
    print(f"   • Average engagement: {stats['average_upvotes']:.1f} upvotes per comment")
    print(f"   • {comments_with_replies} comments ({comments_with_replies/stats['total_comments']:.1%}) received replies")
    print(f"   • Top comment by u/{stats['top_comments'][0]['author']} with {stats['top_comments'][0]['score']} upvotes")
    
    # File Information
    print(f"\n📁 FILE INFORMATION:")
    file_size = os.path.getsize(json_file_path) / 1024  # KB
    print(f"   File: {os.path.basename(json_file_path)}")
    print(f"   Size: {file_size:.1f} KB")
    print(f"   Location: {os.path.dirname(json_file_path)}")

if __name__ == "__main__":
    # Analyze the extracted post
    json_file = "reddit_data/json/specific_posts/indian_beauty_talks_launch_post_1mvhudo.json"
    
    if os.path.exists(json_file):
        analyze_extracted_post(json_file)
    else:
        print(f"File not found: {json_file}")
        print("Please run extract_specific_post.py first to generate the data.")
