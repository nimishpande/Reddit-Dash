# Configuration Files

This directory contains configuration files for the Reddit monitoring system.

## Files

### `user_profile.json`
Contains your personal preferences for relevance scoring:
- **expertise_areas**: Topics you're knowledgeable about
- **interest_keywords**: Keywords that interest you
- **avoid_keywords**: Content to avoid
- **min_relevance_score**: Minimum relevance score (1-20)

### `subreddits.json`
Contains subreddit monitoring configuration:
- **subreddits**: List of subreddits to monitor
  - `name`: Reddit subreddit name
  - `display_name`: Human-readable name
  - `color`: Hex color for dashboard
  - `enabled`: Whether to monitor this subreddit
  - `posts_limit`: Max posts to fetch per subreddit
- **settings**: Global monitoring settings
  - `total_posts_limit`: Maximum total posts across all subreddits
  - `refresh_interval_hours`: How often to run monitoring
  - `min_engagement_score`: Minimum engagement score
  - `min_upvotes`: Minimum upvotes required
  - `min_comments`: Minimum comments required

## Customization

### Adding New Subreddits
1. Edit `subreddits.json`
2. Add new subreddit object with required fields
3. Set `enabled: true` to start monitoring

### Adjusting Relevance Scoring
1. Edit `user_profile.json`
2. Add/remove expertise areas and keywords
3. Adjust `min_relevance_score` (lower = more posts, higher = fewer but more relevant)

### Disabling Subreddits
1. Set `enabled: false` for any subreddit in `subreddits.json`
2. The system will skip monitoring that subreddit
