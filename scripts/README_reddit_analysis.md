# Reddit Activity Analysis

This directory contains scripts to analyze your Reddit activity, including where you've commented and which subreddits you follow.

## 🚀 Quick Start

### 1. Setup Reddit API Credentials

First, you need to create a Reddit app to get API credentials:

1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" or "Create Another App"
3. Choose "script" as the app type
4. Fill in the details and create the app
5. Copy the client ID and secret

### 2. Run Setup Script

```bash
python scripts/setup_reddit_analysis.py
```

This will help you configure your Reddit API credentials.

### 3. Analyze Your Activity

```bash
python scripts/reddit_my_activity.py
```

## 📊 What You'll Get

The analysis will show you:

- **Where you've commented**: All subreddits you've been active in
- **Comment activity patterns**: Which subreddits you comment in most
- **Subscribed subreddits**: All subreddits you're following
- **Recent activity**: Your latest comments with scores and URLs
- **Activity summary**: Statistics about your Reddit usage

## 📁 Output Files

The analysis creates JSON files in `data/my_activity/` with:
- Your comment history
- Subreddit activity counts
- Subscribed subreddits list
- Activity timeline

## 🔧 Advanced Analysis

For more detailed analysis, use the comprehensive analyzer:

```bash
python scripts/reddit_activity_analyzer.py --comments-limit 2000 --submissions-limit 1000
```

## 📋 Scripts Available

- `reddit_my_activity.py` - Simple activity tracker
- `reddit_activity_analyzer.py` - Comprehensive analysis
- `setup_reddit_analysis.py` - Setup helper

## 🔒 Security Note

Never commit your `.env` file to version control. It contains your Reddit credentials.

## 🎯 Use Cases

- **Track your Reddit engagement**: See where you're most active
- **Discover new communities**: Find subreddits you might have forgotten about
- **Analyze commenting patterns**: Understand your Reddit behavior
- **Export your activity**: Save your Reddit activity data for analysis
