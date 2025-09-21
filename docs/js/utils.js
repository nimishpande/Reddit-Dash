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
    
    // Determine opportunity level for badge
    const relevanceScore = post.relevance_score || 0;
    const opportunityLevel = relevanceScore >= 15 ? 'high' : relevanceScore >= 8 ? 'medium' : 'low';
    const opportunityText = opportunityLevel === 'high' ? 'High Opportunity' : 
                           opportunityLevel === 'medium' ? 'Medium Opportunity' : 'Low Opportunity';

    return `
        <article class="post-card ${opportunityClass}-opportunity" style="--subreddit-color: ${subredditColor}" 
             data-post-id="${post.id}" data-post-url="${post.url}" data-opportunity="${opportunityLevel}"
             role="article" aria-label="Reddit post: ${post.title}" 
             data-ai-readable="true" data-scroll-target="true">
            
            <div class="post-header">
                <div class="subreddit-info">
                    <span class="subreddit-pill">${post.subreddit_display}</span>
                    ${post.flair ? `<span class="post-flair">${post.flair}</span>` : ''}
                </div>
                <div class="post-timing">
                    <i class="fas fa-clock"></i>
                    <span>${post.age_human}</span>
                </div>
            </div>
            
            <div class="post-content">
                <h3 class="post-title">${post.title}</h3>
                ${post.content_preview ? `<p class="post-preview">${post.content_preview}</p>` : ''}
                ${imageHTML}
            </div>
            
            <div class="post-metrics">
                <div class="metrics-grid">
                    <div class="metric">
                        <i class="fas fa-arrow-up"></i>
                        <span>${post.score} upvotes</span>
                    </div>
                    <div class="metric">
                        <i class="fas fa-comment"></i>
                        <span>${post.comments} replies</span>
                    </div>
                    <div class="metric engagement-score">
                        <i class="fas fa-fire"></i>
                        <span>${formatEngagementScore(post.engagement_score)} engagement</span>
                    </div>
                    <div class="metric relevance-score">
                        <i class="fas fa-target"></i>
                        <span>${post.relevance_score?.toFixed(1) || '0'} relevance</span>
                    </div>
                </div>
                
                <div class="action-buttons">
                    <button class="btn-action btn-view" onclick="openPost('${post.url}')">
                        <i class="fas fa-external-link-alt"></i>
                        View Post
                    </button>
                    <button class="btn-action btn-reply" onclick="openReplyModal('${post.id}')">
                        <i class="fas fa-reply"></i>
                        Quick Reply
                    </button>
                </div>
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

// Quick reply modal function
function openReplyModal(postId) {
    // This would open a modal with quick reply options
    // For now, just show an alert
    alert(`Quick reply feature for post ${postId} - Coming soon!`);
}

// Check if data is fresh (less than 20 minutes old)
function isDataFresh(timestamp) {
    const dataTime = new Date(timestamp);
    const now = new Date();
    const diffInMinutes = (now - dataTime) / (1000 * 60);
    return diffInMinutes < 20;
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

// Get next update time (every 20 minutes)
function getNextUpdateTime() {
    const now = new Date();
    const nextUpdate = new Date(now);
    
    // Find next 20-minute interval
    const currentMinute = now.getMinutes();
    const nextMinute = Math.ceil(currentMinute / 20) * 20;
    
    if (nextMinute >= 60) {
        nextUpdate.setHours(nextUpdate.getHours() + 1);
        nextUpdate.setMinutes(0);
    } else {
        nextUpdate.setMinutes(nextMinute);
    }
    
    nextUpdate.setSeconds(0);
    nextUpdate.setMilliseconds(0);
    
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
