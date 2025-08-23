# Reddit Monitor

A GitHub Actions-based Reddit monitoring system that tracks engaging posts from skincare and haircare communities.

## 🚀 Features

- **Automated Monitoring**: Runs every 4 hours via GitHub Actions
- **Engagement Filtering**: Identifies posts with high engagement (upvotes + comments)
- **Structured Data**: Generates JSON files with detailed post information
- **Date-based Organization**: Stores data in organized folder structure
- **Dashboard Ready**: JSON output formatted for web dashboard consumption

## 📁 Project Structure

```
├── reddit-monitor/
│   ├── scripts/
│   │   └── reddit_monitor_phase1.py    # Main monitoring script
│   ├── workflows/
│   │   ├── phase1_test.yml             # Test workflow (manual trigger)
│   │   └── reddit_monitor.yml          # Production workflow (scheduled)
│   ├── data/                           # Generated data (created by script)
│   ├── requirements.txt                # Python dependencies
│   ├── .gitignore                      # Git ignore rules
│   └── README.md                       # Detailed documentation
├── .github/
│   └── workflows/
│       ├── phase1_test.yml             # GitHub Actions test workflow
│       └── reddit_monitor.yml          # GitHub Actions production workflow
└── README.md                           # This file
```

## 🛠️ Setup

1. **Fork this repository**
2. **Set up GitHub Secrets**:
   - `REDDIT_CLIENT_ID`: Your Reddit API client ID
   - `REDDIT_CLIENT_SECRET`: Your Reddit API client secret

3. **Install dependencies**:
   ```bash
   pip install -r reddit-monitor/requirements.txt
   ```

## 🧪 Testing

### Manual Testing
```bash
python reddit-monitor/scripts/reddit_monitor_phase1.py
```

### GitHub Actions Testing
1. Go to **Actions** tab
2. Find **"Phase 1 Test"** workflow
3. Click **"Run workflow"**
4. Select the branch and run

## 📊 Output

The script generates:
- `reddit-monitor/data/analysis/YYYY-MM-DD/HH_MM_summary.json` - Timestamped data files
- `reddit-monitor/data/analysis/latest.json` - Latest data for dashboard consumption

## 🔧 Configuration

Edit `reddit-monitor/scripts/reddit_monitor_phase1.py` to modify:
- Target subreddit (`SUBREDDIT`)
- Engagement thresholds (`MIN_ENGAGEMENT_SCORE`, `MIN_UPVOTES`, `MIN_COMMENTS`)
- Number of posts to fetch (`POSTS_LIMIT`)

## 🔄 Workflows

- **Phase 1 Test**: Manual trigger for testing the monitoring system
- **Reddit Monitor**: Automated workflow that runs every 4 hours

## 🎯 Development Roadmap

This is Phase 1 of the Reddit monitoring system. Future phases will include:
- Web dashboard
- Additional subreddits
- Enhanced analytics
- Real-time notifications

## 📝 License

This project is open source and available under the MIT License.
