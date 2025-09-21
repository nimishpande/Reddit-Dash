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

// Update header stats with enhanced information
function updateHeaderStats(data) {
    const { dashboard_info, posts, subreddits } = data;
    
    document.getElementById('last-updated').textContent = formatDate(dashboard_info.last_updated);
    document.getElementById('total-posts').textContent = dashboard_info.total_posts;
    document.getElementById('communities-count').textContent = dashboard_info.subreddits_count;
    
    // Add enhanced stats if available
    if (posts && posts.length > 0) {
        const highRelevancePosts = posts.filter(post => post.relevance_score >= 10).length;
        const avgRelevance = posts.reduce((sum, post) => sum + (post.relevance_score || 0), 0) / posts.length;
        
        // Add enhanced stats to header if elements exist
        const enhancedStats = document.querySelector('.enhanced-stats');
        if (enhancedStats) {
            enhancedStats.innerHTML = `
                <div class="stat-item">
                    <span class="stat-label">High Relevance</span>
                    <span class="stat-value">${highRelevancePosts}</span>
                </div>
                <div class="stat-item">
                    <span class="stat-label">Avg Relevance</span>
                    <span class="stat-value">${avgRelevance.toFixed(1)}</span>
                </div>
            `;
        }
    }
}

// Create post card HTML
function createPostCard(post) {
    const subredditColor = getSubredditColor(post.subreddit);
    const opportunityClass = post.opportunity_rating || 'low';
    
    // Generate image HTML based on available image URLs
    let imageHTML = '';
    if (post.image_urls && post.image_urls.length > 0) {
        if (post.image_urls.length === 1) {
            // Single image
            const image = post.image_urls[0];
            imageHTML = `
                <div class="post-thumbnail">
                    <img src="${image.url}" alt="Post image" 
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'; console.log('Image failed:', '${image.url}')" 
                         onload="this.nextElementSibling.style.display='none'; console.log('Image loaded:', '${image.url}')">
                    <div class="image-placeholder">
                        <i class="fas fa-image"></i>
                    </div>
                </div>
            `;
        } else {
            // Multiple images - show first image with count indicator
            const firstImage = post.image_urls[0];
            imageHTML = `
                <div class="post-thumbnail multiple-images">
                    <img src="${firstImage.url}" alt="Post image"
                         onerror="this.style.display='none'; this.nextElementSibling.style.display='flex'; console.log('Image failed:', '${firstImage.url}')" 
                         onload="this.nextElementSibling.style.display='none'; console.log('Image loaded:', '${firstImage.url}')">
                    <div class="image-placeholder">
                        <i class="fas fa-image"></i>
                    </div>
                    <div class="image-count">
                        <i class="fas fa-images"></i>
                        <span>+${post.image_urls.length - 1}</span>
                    </div>
                </div>
            `;
        }
        console.log(`Generated image HTML for post ${post.id}:`, imageHTML);
    } else if (post.has_images) {
        // Fallback for posts marked as having images but no URLs
        imageHTML = `
            <div class="post-thumbnail">
                <img src="${getRedditThumbnail(post.url)}" alt="Post thumbnail"
                     onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                <div class="image-placeholder">
                    <i class="fas fa-image"></i>
                </div>
            </div>
        `;
    }
    
    return `
        <div class="post-card ${opportunityClass}-opportunity" style="--subreddit-color: ${subredditColor}" onclick="openPost('${post.url}')">
            ${post.has_images ? '<div class="image-indicator"><i class="fas fa-image"></i> Has Image</div>' : ''}
            
            <div class="post-header">
                <span class="subreddit-pill">${post.subreddit_display}</span>
                <div class="post-title">${post.title}</div>
            </div>
            
            <div class="post-content-wrapper">
                ${post.content_preview ? `<div class="post-content">${post.content_preview}</div>` : ''}
                ${imageHTML}
            </div>
            
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
                <div class="relevance-score">
                    <i class="fas fa-target"></i>
                    ${post.relevance_score?.toFixed(1) || '0'}
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

// Get Reddit thumbnail URL
function getRedditThumbnail(redditUrl) {
    // Convert Reddit URL to thumbnail URL
    // Example: https://reddit.com/r/subreddit/comments/id/title/
    // To: https://i.redd.it/thumbnail_id.jpg or similar
    const postId = redditUrl.split('/comments/')[1]?.split('/')[0];
    if (postId) {
        return `https://i.redd.it/${postId}.jpg`;
    }
    return 'https://via.placeholder.com/120x90/cccccc/666666?text=Image';
}

// Add comprehensive data status indicators
function addFreshnessIndicator(timestamp) {
    const isFresh = isDataFresh(timestamp);
    const timeAgo = formatTimestamp(timestamp);
    
    // Create main status indicator
    const mainIndicator = document.createElement('div');
    mainIndicator.className = `freshness-indicator main-status ${isFresh ? 'fresh' : 'stale'}`;
    mainIndicator.innerHTML = `
        <div class="status-header">
            <i class="fas ${isFresh ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
            <span class="status-text">${isFresh ? 'All Data Fresh' : 'Data May Be Stale'}</span>
        </div>
        <div class="status-details">
            <span class="last-update">Last updated: ${timeAgo}</span>
            <span class="next-update">Next update: ${getNextUpdateTime()}</span>
        </div>
    `;
    
    // Add to header stats
    const headerStats = document.querySelector('.header-stats');
    if (headerStats) {
        // Remove any existing freshness indicators
        const existingIndicators = headerStats.querySelectorAll('.freshness-indicator');
        existingIndicators.forEach(indicator => indicator.remove());
        
        headerStats.appendChild(mainIndicator);
    }
}

// Get next update time
function getNextUpdateTime() {
    const now = new Date();
    const nextUpdate = new Date(now);
    
    // Find next 4-hour interval (00:15, 04:15, 08:15, 12:15, 16:15, 20:15)
    const currentHour = now.getHours();
    const currentMinute = now.getMinutes();
    
    let nextHour = Math.ceil(currentHour / 4) * 4;
    if (nextHour >= 24) nextHour = 0;
    
    // If we're past 15 minutes of the current 4-hour block, move to next
    if (currentMinute > 15 && nextHour === currentHour) {
        nextHour = (nextHour + 4) % 24;
    }
    
    nextUpdate.setHours(nextHour, 15, 0, 0);
    
    return formatTimestamp(nextUpdate.getTime());
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
