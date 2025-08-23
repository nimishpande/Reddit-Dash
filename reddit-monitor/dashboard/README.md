# Reddit Dashboard

A beautiful, responsive dashboard for displaying Reddit engagement data from skincare and haircare communities.

## 🚀 Features

- **Modern Design**: Clean, professional interface with smooth animations
- **Responsive Layout**: Works perfectly on desktop, tablet, and mobile
- **Real-time Data**: Auto-refreshes every 4 hours
- **Interactive Cards**: Click to open posts in new tabs
- **Smart Filtering**: Posts sorted by engagement score
- **Visual Indicators**: Shows image posts, engagement scores, and data freshness
- **Keyboard Shortcuts**: Ctrl/Cmd + R to refresh

## 📁 File Structure

```
dashboard/
├── index.html          # Main dashboard page
├── css/
│   └── styles.css      # All styling and responsive design
├── js/
│   ├── utils.js        # Utility functions
│   └── dashboard.js    # Main dashboard logic
└── README.md           # This file
```

## 🎨 Design Features

### Header
- Gradient background with title and subtitle
- Real-time statistics (last updated, total posts, communities)
- Data freshness indicator

### Post Cards
- Clean white cards with subtle shadows
- Subreddit color-coded pills
- Content previews with smart truncation
- Engagement metrics (score, comments, age)
- Image indicators for posts with media
- Hover effects and smooth animations

### Responsive Design
- **Desktop**: Full-width layout with side-by-side header stats
- **Tablet**: Adjusted spacing and typography
- **Mobile**: Stacked layout with optimized touch targets

## 🔧 Technical Features

### JavaScript
- **Async Data Loading**: Fetches JSON data from `../data/analysis/latest.json`
- **Error Handling**: Graceful fallbacks for network issues
- **Auto-refresh**: Configurable refresh intervals
- **Performance Monitoring**: Page load time tracking
- **Keyboard Shortcuts**: Enhanced user experience

### CSS
- **Modern Flexbox/Grid**: Responsive layouts
- **CSS Custom Properties**: Dynamic subreddit colors
- **Smooth Animations**: Fade-in effects and hover states
- **Mobile-first**: Progressive enhancement approach

## 🚀 Usage

1. **Open the dashboard**: Navigate to `index.html` in a web browser
2. **View posts**: Scroll through engaging posts sorted by engagement
3. **Click posts**: Open any post in a new tab to read the full content
4. **Refresh data**: Use the refresh button or Ctrl/Cmd + R
5. **Check freshness**: Look for the data freshness indicator in the header

## 📊 Data Requirements

The dashboard expects JSON data in this format:

```json
{
  "dashboard_info": {
    "title": "Reddit Engagement Dashboard",
    "subtitle": "Skincare & Haircare Communities",
    "last_updated": "2025-08-23T13:22:48.728242",
    "total_posts": 33,
    "subreddits_count": 1
  },
  "posts": [
    {
      "id": "1my0ki0",
      "title": "Post Title",
      "content_preview": "Post content preview...",
      "subreddit": "skincareaddictsindia",
      "subreddit_display": "r/skincareaddictsindia",
      "url": "https://reddit.com/...",
      "score": 1,
      "comments": 2,
      "engagement_score": 3,
      "age_human": "34m ago",
      "has_images": true,
      "flair": "Skincare"
    }
  ],
  "subreddits": {
    "skincareaddictsindia": {
      "name": "r/skincareaddictsindia",
      "color": "#0079d3",
      "post_count": 33
    }
  }
}
```

## 🎯 Browser Support

- **Chrome**: 80+
- **Firefox**: 75+
- **Safari**: 13+
- **Edge**: 80+

## 🔮 Future Enhancements

- **Search & Filter**: Filter posts by subreddit, flair, or engagement
- **Dark Mode**: Toggle between light and dark themes
- **Offline Support**: Service worker for offline viewing
- **Analytics**: Track user interactions and popular posts
- **Export**: Download data as CSV or PDF
- **Real-time Updates**: WebSocket connection for live updates

## 🛠️ Development

To modify the dashboard:

1. **Styling**: Edit `css/styles.css`
2. **Functionality**: Modify `js/dashboard.js`
3. **Utilities**: Update `js/utils.js`
4. **Structure**: Edit `index.html`

The dashboard is designed to be easily customizable and extensible.
