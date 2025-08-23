# Reddit Monitoring System

This system automatically monitors r/skincareaddictsindia every 4 hours and generates daily summaries of engaging posts.

## 📁 File Structure

```
reddit_monitoring/
├── daily_summary_YYYY-MM-DD.txt    # Daily text summaries
├── posts_YYYY-MM-DD.json          # JSON backup of all posts
├── last_run_timestamp.txt         # Timestamp of last run
└── README.md                      # This file
```

## 🚀 Setup Instructions

### 1. Reddit API Credentials

You need to create a Reddit app to get API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Fill in the details:
   - **Name**: `skincare_monitor`
   - **Type**: `script`
   - **Description**: `Reddit monitoring for skincare discussions`
   - **About URL**: Leave blank
   - **Redirect URI**: `http://localhost:8080`
4. Note down the **Client ID** (under the app name) and **Client Secret**

### 2. Environment Variables

Create a `.env` file in the root directory:

```env
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
```

### 3. GitHub Secrets (for automated runs)

If using GitHub Actions, add these secrets to your repository:

1. Go to your repository → Settings → Secrets and variables → Actions
2. Add these repository secrets:
   - `REDDIT_CLIENT_ID`: Your Reddit client ID
   - `REDDIT_CLIENT_SECRET`: Your Reddit client secret

## 🔧 Configuration

Edit `misc_py_root/monitor_config.py` to customize:

- **Subreddit**: Change `SUBREDDIT` to monitor different subreddits
- **Engagement criteria**: Adjust `MIN_ENGAGEMENT_SCORE`, `MIN_UPVOTES`, `MIN_COMMENTS`
- **Post limit**: Change `POSTS_LIMIT` to fetch more/fewer posts
- **Sorting**: Change `SORT_METHOD` ('new', 'hot', 'top', 'rising')

## 📊 Output Format

### Daily Summary (Text File)

Each post includes:
- Title and author
- Posting time
- Upvotes and comments count
- Engagement score
- Full post content
- Image URLs (if any)
- Direct link to the post

### JSON Backup

Structured data with:
- Monitoring metadata
- Engagement criteria used
- Complete post data
- Timestamps

## ⏰ Scheduling

### Manual Run
```bash
python3 misc_py_root/reddit_monitor.py
```

### Automated (GitHub Actions)
The system runs automatically every 4 hours via GitHub Actions.

To trigger manually:
1. Go to your repository on GitHub
2. Click "Actions" tab
3. Select "Reddit Monitor" workflow
4. Click "Run workflow"

## 📈 Engagement Criteria

Posts are considered "engaging" if they meet ANY of these criteria:
- **Engagement Score ≥ 7** (upvotes + comments)
- **Upvotes ≥ 5**
- **Comments ≥ 2**

## 🔍 Monitoring Results

The system found **38 engaging posts** in the latest run, including:
- Cyst treatment discussions
- Pigmentation concerns
- Vitamin C serum recommendations
- Budget-friendly skincare advice

## 🛠 Customization

### Add More Subreddits

Edit `monitor_config.py`:
```python
ADDITIONAL_SUBREDDITS = [
    'IndianBeautyTalks',
    'SkincareAddiction',
    'AsianBeauty'
]
```

### Change Frequency

Edit `.github/workflows/reddit_monitor.yml`:
```yaml
schedule:
  - cron: '0 */2 * * *'  # Every 2 hours
  - cron: '0 0 * * *'    # Daily at midnight
```

### Add Keyword Filtering

The system includes skincare keywords for future enhancement:
- Vitamin C, Retinol, Niacinamide
- Hyaluronic Acid, Salicylic Acid
- Ceramides, Peptides, Sunscreen
- Moisturizer, Cleanser, Serum

## 📝 Sample Output

```
================================================================================
POST #1
================================================================================
Title: Suggest me a good serum or vitamin c serum please!!?
Author: u/Free_Newspaper_4382
Posted: 2025-08-22 19:48:53
Score: 2 upvotes
Comments: 8
Engagement Score: 10
URL: https://reddit.com/r/skincareaddictsindia/comments/...

Content:
Hey i am 21(F) My skin is getting dull as far now i have no other concern...
```

## 🔧 Troubleshooting

### Common Issues

1. **"Missing Reddit credentials"**
   - Check your `.env` file exists and has correct credentials
   - Verify GitHub secrets are set (for automated runs)

2. **"No posts fetched"**
   - Check subreddit name is correct
   - Verify Reddit API is accessible
   - Check rate limiting

3. **"No engaging posts found"**
   - Lower the engagement criteria in `monitor_config.py`
   - Check if subreddit is active

### Rate Limiting

Reddit API has rate limits. The script includes delays to respect these limits.

## 📊 Analytics

The system tracks:
- Posts found per run
- Engagement distribution
- Image content analysis
- Temporal patterns

## 🔮 Future Enhancements

- **Sentiment Analysis**: Analyze post sentiment
- **Keyword Extraction**: Identify trending topics
- **Image Download**: Save high-engagement images
- **Email Notifications**: Alert for high-engagement posts
- **Trend Analysis**: Track engagement patterns over time
