// Main Dashboard JavaScript

// Configuration
const CONFIG = {
    dataUrl: 'https://raw.githubusercontent.com/nimishpande/ingredient_cosmetics/reddit-monitor/reddit-monitor/data/analysis/latest.json',
    refreshInterval: 4 * 60 * 60 * 1000, // 4 hours in milliseconds
    autoRefresh: true
};

// Global state
let dashboardData = null;
let refreshTimer = null;

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing Reddit Dashboard...');
    initializeDashboard();
});

// Initialize the dashboard
function initializeDashboard() {
    showLoading();
    loadDashboardData();
    
    // Set up auto-refresh if enabled
    if (CONFIG.autoRefresh) {
        setupAutoRefresh();
    }
    
    // Add keyboard shortcuts
    setupKeyboardShortcuts();
}

// Load dashboard data from JSON file
async function loadDashboardData() {
    try {
        console.log('📥 Loading dashboard data...');
        
        const response = await fetch(CONFIG.dataUrl);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('✅ Data loaded successfully:', data);
        
        // Validate data structure
        if (!validateDataStructure(data)) {
            throw new Error('Invalid data structure');
        }
        
        dashboardData = data;
        renderDashboard(data);
        
    } catch (error) {
        console.error('❌ Error loading dashboard data:', error);
        showError();
    }
}

// Validate data structure
function validateDataStructure(data) {
    return data && 
           data.dashboard_info && 
           data.posts && 
           Array.isArray(data.posts) &&
           data.subreddits;
}

// Render the dashboard with data
function renderDashboard(data) {
    const { dashboard_info, posts, subreddits } = data;
    
    // Update header stats
    updateHeaderStats(data);
    
    // Add freshness indicator
    addFreshnessIndicator(dashboard_info.last_updated);
    
    // Render posts
    if (posts && posts.length > 0) {
        renderPosts(posts);
        showPostsFeed();
    } else {
        showEmptyState();
    }
    
    // Log rendering completion
    console.log(`🎨 Dashboard rendered with ${posts.length} posts`);
}

// Render posts in the feed
function renderPosts(posts) {
    const postsFeed = document.getElementById('posts-feed');
    
    // Sort posts by engagement score (highest first)
    const sortedPosts = posts.sort((a, b) => b.engagement_score - a.engagement_score);
    
    // Create HTML for each post
    const postsHTML = sortedPosts.map(post => createPostCard(post)).join('');
    
    // Update the feed
    postsFeed.innerHTML = postsHTML;
    
    // Add click tracking
    addPostClickTracking();
}

// Add click tracking for analytics
function addPostClickTracking() {
    const postCards = document.querySelectorAll('.post-card');
    
    postCards.forEach(card => {
        card.addEventListener('click', function() {
            const postId = this.getAttribute('data-post-id');
            console.log(`📊 Post clicked: ${postId}`);
            
            // You can add analytics tracking here
            // trackPostClick(postId);
        });
    });
}

// Set up auto-refresh
function setupAutoRefresh() {
    if (refreshTimer) {
        clearInterval(refreshTimer);
    }
    
    refreshTimer = setInterval(() => {
        console.log('🔄 Auto-refreshing dashboard...');
        loadDashboardData();
    }, CONFIG.refreshInterval);
    
    console.log(`⏰ Auto-refresh set for every ${CONFIG.refreshInterval / (1000 * 60)} minutes`);
}

// Set up keyboard shortcuts
function setupKeyboardShortcuts() {
    document.addEventListener('keydown', function(event) {
        // Ctrl/Cmd + R to refresh
        if ((event.ctrlKey || event.metaKey) && event.key === 'r') {
            event.preventDefault();
            loadDashboardData();
        }
        
        // Escape to clear any selections
        if (event.key === 'Escape') {
            // Clear any active states
        }
    });
}

// Global function for manual refresh (called from HTML)
window.loadDashboardData = loadDashboardData;

// Add some additional utility functions
function getTopPosts(limit = 5) {
    if (!dashboardData || !dashboardData.posts) return [];
    
    return dashboardData.posts
        .sort((a, b) => b.engagement_score - a.engagement_score)
        .slice(0, limit);
}

function getPostsBySubreddit(subreddit) {
    if (!dashboardData || !dashboardData.posts) return [];
    
    return dashboardData.posts.filter(post => post.subreddit === subreddit);
}

function getPostsWithImages() {
    if (!dashboardData || !dashboardData.posts) return [];
    
    return dashboardData.posts.filter(post => post.has_images);
}

// Export functions for debugging
window.DashboardAPI = {
    getTopPosts,
    getPostsBySubreddit,
    getPostsWithImages,
    getData: () => dashboardData,
    refresh: loadDashboardData
};

// Add performance monitoring
function logPerformance() {
    if (performance && performance.getEntriesByType) {
        const navigation = performance.getEntriesByType('navigation')[0];
        if (navigation) {
            console.log(`⚡ Page load time: ${navigation.loadEventEnd - navigation.loadEventStart}ms`);
        }
    }
}

// Log performance when page is fully loaded
window.addEventListener('load', logPerformance);

// Add service worker for offline support (future enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
    });
}

console.log('🎯 Dashboard JavaScript loaded successfully!');
