# Reddit Monitor

A GitHub Actions-based Reddit monitoring system that tracks engaging posts from skincare and haircare communities.

## Features

- **Automated Monitoring**: Runs every 4 hours via GitHub Actions
- **Engagement Filtering**: Identifies posts with high engagement (upvotes + comments)
- **Structured Data**: Generates JSON files with detailed post information
- **Date-based Organization**: Stores data in organized folder structure
- **Dashboard Ready**: JSON output formatted for web dashboard consumption

## Structure

```
reddit-monitor/
├── scripts/
│   └── reddit_monitor_phase1.py    # Main monitoring script
├── workflows/
│   └── phase1_test.yml             # GitHub Actions workflow
├── data/                           # Generated data (created by script)
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Setup

1. **Fork this repository**
2. **Set up GitHub Secrets**:
   - `REDDIT_CLIENT_ID`: Your Reddit API client ID
   - `REDDIT_CLIENT_SECRET`: Your Reddit API client secret

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Manual Testing
```bash
python scripts/reddit_monitor_phase1.py
```

### Automated Monitoring
The GitHub Actions workflow runs automatically every 4 hours and can be triggered manually.

## Output

The script generates:
- `data/analysis/YYYY-MM-DD/HH_MM_summary.json` - Timestamped data files
- `data/analysis/latest.json` - Latest data for dashboard consumption

## Data Format

Each JSON file contains:
- **Dashboard Info**: Metadata about the monitoring run
- **Posts**: Array of engaging posts with detailed information
- **Subreddits**: Summary statistics by subreddit

## Configuration

Edit `scripts/reddit_monitor_phase1.py` to modify:
- Target subreddit (`SUBREDDIT`)
- Engagement thresholds (`MIN_ENGAGEMENT_SCORE`, `MIN_UPVOTES`, `MIN_COMMENTS`)
- Number of posts to fetch (`POSTS_LIMIT`)

## Development

This is Phase 1 of the Reddit monitoring system. Future phases will include:
- Web dashboard
- Additional subreddits
- Enhanced analytics
- Real-time notifications
