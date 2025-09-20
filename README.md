# Reddit Engagement Dashboard

A comprehensive monitoring system for Reddit communities focused on skincare and haircare discussions.

## 🚀 Features

- **Automated Monitoring**: Fetches posts from r/skincareaddictsindia every 4 hours
- **Smart Filtering**: Only captures posts with meaningful engagement (scores, comments)
- **Beautiful Dashboard**: Clean, responsive web interface with thumbnails
- **Real-time Updates**: Auto-refreshing dashboard with fresh data
- **GitHub Pages**: Hosted directly on GitHub with automatic deployments

## 📊 Dashboard

The dashboard displays:
- Post titles with clickable links to Reddit
- Content previews (1-2 sentences)
- Engagement metrics (upvotes, comments, engagement score)
- Post thumbnails with lazy loading
- Subreddit indicators and post flair
- Responsive design for mobile and desktop

## 🔧 Technical Stack

- **Backend**: Python with Reddit API integration
- **Frontend**: Vanilla HTML, CSS, JavaScript
- **Automation**: GitHub Actions for scheduled runs
- **Hosting**: GitHub Pages
- **Data Storage**: JSON files in repository

## 📁 Project Structure

```
reddit-dashboard/
├── .github/workflows/     # GitHub Actions workflows
│   └── reddit_monitor.yml # Main monitoring workflow
├── dashboard/             # Web dashboard files
│   ├── index.html        # Main dashboard page
│   ├── css/styles.css    # Dashboard styling
│   └── js/               # JavaScript files
├── scripts/              # Python monitoring scripts
│   └── reddit_monitor_phase1.py
├── data/                 # Generated data files
│   └── analysis/         # Time-stamped data
└── requirements.txt      # Python dependencies
```

## 🛠️ Setup

### Prerequisites
- Reddit API credentials (Client ID & Secret)
- GitHub repository with Actions enabled

### Configuration
1. Set up Reddit API credentials in GitHub Secrets:
   - `REDDIT_CLIENT_ID`
   - `REDDIT_CLIENT_SECRET`

2. The monitoring script runs automatically every 4 hours via GitHub Actions

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
echo "REDDIT_CLIENT_ID=your_client_id" > .env
echo "REDDIT_CLIENT_SECRET=your_client_secret" >> .env

# Run monitoring script
python scripts/reddit_monitor_phase1.py

# Serve dashboard locally
cd dashboard && python -m http.server 8000
```

## 📈 Data Flow

1. **GitHub Actions** triggers every 4 hours
2. **Python script** fetches posts from Reddit API
3. **Data processing** filters and enhances post information
4. **JSON files** are generated and committed to repository
5. **Dashboard** automatically displays updated data

## 🎯 Monitoring Criteria

Posts are included if they meet:
- Minimum engagement score: 7
- Minimum upvotes: 5
- Minimum comments: 2
- From target subreddit: r/skincareaddictsindia

## 🔄 Automation

The system runs completely automatically:
- **Scheduled runs**: Every 4 hours via GitHub Actions
- **Data updates**: Automatic commits to repository
- **Dashboard refresh**: Auto-updates every 4 hours
- **Error handling**: Graceful fallbacks and logging

## 📱 Dashboard Features

- **Responsive Design**: Works on desktop and mobile
- **Lazy Loading**: Images load as you scroll
- **Real-time Indicators**: Shows data freshness
- **Click Tracking**: Direct links to Reddit posts
- **Clean UI**: Minimal, focused design

## 🚀 Live Dashboard

Visit the live dashboard: [Reddit Engagement Dashboard](https://nimishpande.github.io/Reddit-Dash/)

## 📝 License

This project is open source and available under the MIT License.