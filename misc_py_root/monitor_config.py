# Reddit Monitoring Configuration
# Edit these settings to customize the monitoring behavior

# Subreddit to monitor
SUBREDDIT = 'skincareaddictsindia'

# Engagement filtering criteria
MIN_ENGAGEMENT_SCORE = 7  # upvotes + comments
MIN_UPVOTES = 5
MIN_COMMENTS = 2

# Number of posts to fetch from subreddit
POSTS_LIMIT = 50

# Sorting method: 'new', 'hot', 'top', 'rising'
SORT_METHOD = 'new'

# Output directory
MONITORING_DIR = 'reddit_monitoring'

# File naming patterns
SUMMARY_FILE_PATTERN = 'daily_summary_{date}.txt'
POSTS_FILE_PATTERN = 'posts_{date}.json'
TIMESTAMP_FILE = 'last_run_timestamp.txt'

# Additional subreddits to monitor (for future expansion)
ADDITIONAL_SUBREDDITS = [
    # 'IndianBeautyTalks',
    # 'SkincareAddiction',
    # 'AsianBeauty'
]

# Keywords to highlight in summaries (optional)
HIGHLIGHT_KEYWORDS = [
    'vitamin c',
    'retinol',
    'niacinamide',
    'hyaluronic acid',
    'salicylic acid',
    'ceramides',
    'peptides',
    'sunscreen',
    'moisturizer',
    'cleanser',
    'serum',
    'toner',
    'mask',
    'exfoliant'
]

# Image handling
SAVE_IMAGE_URLS = True
DOWNLOAD_IMAGES = False  # Set to True if you want to download images
IMAGE_DIR = 'images'

# Notification settings (for future enhancement)
SEND_NOTIFICATIONS = False
NOTIFICATION_THRESHOLD = 10  # Minimum engagement score for notifications
