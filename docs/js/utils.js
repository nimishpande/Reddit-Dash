// Utility functions for the Reddit Dashboard

// Format timestamp to human-readable format
function formatTimestamp(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) {
        return `${diffInSeconds}s ago`;
    } else if (diffInSeconds < 3600) {
        const minutes = Math.floor(diffInSeconds / 60);
        return `${minutes}m ago`;
    } else if (diffInSeconds < 86400) {
        const hours = Math.floor(diffInSeconds / 3600);
        return `${hours}h ago`;
    } else {
        const days = Math.floor(diffInSeconds / 86400);
        return `${days}d ago`;
    }
}

// Format date for display
function formatDate(timestamp) {
    const date = new Date(timestamp);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// Truncate text to specified length
function truncateText(text, maxLength = 150) {
    if (!text || text.length <= maxLength) {
        return text;
    }
    
    const truncated = text.substring(0, maxLength);
    const lastSpace = truncated.lastIndexOf(' ');
    
    if (lastSpace > maxLength * 0.8) {
        return truncated.substring(0, lastSpace) + '...';
    } else {
        return truncated + '...';
    }
}

// Get subreddit color
function getSubredditColor(subreddit) {
    const colors = {
        'skincareaddictsindia': '#0079d3',
        'IndianSkincareAddicts': '#ff4500',
        'SkincareAddiction': '#7193ff',
        'HaircareScience': '#00c851',
        'curlyhair': '#ff6b35',
        'tressless': '#8e44ad',
        'Hair': '#e74c3c',
        'beauty': '#f39c12'
    };
    
    return colors[subreddit] || '#0079d3';
}

// Format engagement score
function formatEngagementScore(score) {
    if (score >= 1000) {
        return (score / 1000).toFixed(1) + 'k';
    }
    return score.toString();
}

// Show loading state
function showLoading() {
    document.getElementById('loading-state').style.display = 'block';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('posts-feed').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';
}

// Show error state
function showError() {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'block';
    document.getElementById('posts-feed').style.display = 'none';
    document.getElementById('empty-state').style.display = 'none';
}

// Show posts feed
function showPostsFeed() {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('posts-feed').style.display = 'block';
    document.getElementById('empty-state').style.display = 'none';
}

// Show empty state
function showEmptyState() {
    document.getElementById('loading-state').style.display = 'none';
    document.getElementById('error-state').style.display = 'none';
    document.getElementById('posts-feed').style.display = 'none';
    document.getElementById('empty-state').style.display = 'block';
}

// Update header stats
function updateHeaderStats(data) {
    const { dashboard_info } = data;
    
    document.getElementById('last-updated').textContent = formatDate(dashboard_info.last_updated);
    document.getElementById('total-posts').textContent = dashboard_info.total_posts;
    document.getElementById('communities-count').textContent = dashboard_info.subreddits_count;
}

// Create post card HTML
function createPostCard(post) {
    const subredditColor = getSubredditColor(post.subreddit);
    
    return `
        <div class="post-card" style="--subreddit-color: ${subredditColor}" onclick="openPost('${post.url}')">
            ${post.has_images ? '<div class="image-indicator"><i class="fas fa-image"></i> Has Image</div>' : ''}
            
            <div class="post-header">
                <span class="subreddit-pill">${post.subreddit_display}</span>
                <div class="post-title">${post.title}</div>
            </div>
            
            ${post.content_preview ? `<div class="post-content">${post.content_preview}</div>` : ''}
            
            <div class="post-meta">
                <div class="meta-item">
                    <i class="fas fa-clock"></i>
                    <span>${post.age_human}</span>
                </div>
                <div class="meta-item">
                    <i class="fas fa-arrow-up"></i>
                    <span>${post.score}</span>
                </div>
                <div class="meta-item">
                    <i class="fas fa-comment"></i>
                    <span>${post.comments}</span>
                </div>
                <div class="engagement-score">
                    <i class="fas fa-chart-line"></i>
                    ${formatEngagementScore(post.engagement_score)}
                </div>
                ${post.flair ? `<div class="post-flair">${post.flair}</div>` : ''}
            </div>
        </div>
    `;
}

// Open post in new tab
function openPost(url) {
    window.open(url, '_blank');
}

// Debounce function for performance
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Check if data is fresh (less than 4 hours old)
function isDataFresh(timestamp) {
    const dataTime = new Date(timestamp);
    const now = new Date();
    const diffInHours = (now - dataTime) / (1000 * 60 * 60);
    return diffInHours < 4;
}

// Add data freshness indicator
function addFreshnessIndicator(timestamp) {
    const isFresh = isDataFresh(timestamp);
    const indicator = document.createElement('div');
    indicator.className = `freshness-indicator ${isFresh ? 'fresh' : 'stale'}`;
    indicator.innerHTML = `
        <i class="fas ${isFresh ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
        ${isFresh ? 'Data is fresh' : 'Data may be stale'}
    `;
    
    // Add to header stats
    const headerStats = document.querySelector('.header-stats');
    headerStats.appendChild(indicator);
}

// Export functions for use in other scripts
window.DashboardUtils = {
    formatTimestamp,
    formatDate,
    truncateText,
    getSubredditColor,
    formatEngagementScore,
    showLoading,
    showError,
    showPostsFeed,
    showEmptyState,
    updateHeaderStats,
    createPostCard,
    openPost,
    debounce,
    isDataFresh,
    addFreshnessIndicator
};
