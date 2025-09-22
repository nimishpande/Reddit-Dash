// Main Dashboard JavaScript

// Configuration
const CONFIG = {
    dataUrl: './data.json?v=' + Date.now(), // Use relative path with cache busting
    refreshInterval: 20 * 60 * 1000, // 20 minutes in milliseconds
    autoRefresh: true
};

// Global state
let dashboardData = null;
let refreshTimer = null;
let currentView = 'compact'; // Default to compact view

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
    
    // Set up filtering and search
    setupFiltering();
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

// Render posts in the table
function renderPosts(posts) {
    const postsTableContainer = document.getElementById('posts-table-container');
    const postsTbody = document.getElementById('posts-tbody');
    
    // Sort posts by engagement score (highest first)
    const sortedPosts = posts.sort((a, b) => b.engagement_score - a.engagement_score);
    
    // Create table rows
    const tableRows = sortedPosts.map(post => createTableRow(post)).join('');
    
    // Update the table
    postsTbody.innerHTML = tableRows;
    
    // Show table container
    postsTableContainer.style.display = 'block';
    
    // Add click tracking
    addPostClickTracking();
}

// Add click tracking for analytics
function addPostClickTracking() {
    const postRows = document.querySelectorAll('.post-row');
    
    postRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger if clicking on a button or link
            if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A') {
                return;
            }
            
            const postId = this.getAttribute('data-post-id');
            const postUrl = this.getAttribute('data-post-url');
            console.log(`📊 Post clicked: ${postId}`);
            
            // Open post in new tab
            window.open(postUrl, '_blank');
            
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

// Set up filtering and search functionality
function setupFiltering() {
    const sortFilter = document.getElementById('sort-filter');
    const opportunityToggles = document.querySelectorAll('.toggle');
    const searchInput = document.getElementById('search-input');
    const viewToggles = document.querySelectorAll('.view-toggle');
    
    if (sortFilter) {
        sortFilter.addEventListener('change', applyFilters);
    }
    
    opportunityToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            // Remove active class from all toggles
            opportunityToggles.forEach(t => t.classList.remove('active'));
            // Add active class to clicked toggle
            this.classList.add('active');
            applyFilters();
        });
    });
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(applyFilters, 300));
    }
    
    // View toggle functionality
    viewToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            // Remove active class from all view toggles
            viewToggles.forEach(t => t.classList.remove('active'));
            // Add active class to clicked toggle
            this.classList.add('active');
            
            // Update current view
            currentView = this.dataset.view;
            
            // Re-render posts with new view
            if (dashboardData && dashboardData.posts) {
                renderPosts(dashboardData.posts);
            }
        });
    });
}

// Apply filters to posts
function applyFilters() {
    if (!dashboardData || !dashboardData.posts) return;
    
    const sortFilter = document.getElementById('sort-filter');
    const activeToggle = document.querySelector('.toggle.active');
    const searchInput = document.getElementById('search-input');
    
    let filteredPosts = [...dashboardData.posts];
    
    // Filter by opportunity level
    if (activeToggle && activeToggle.dataset.filter !== 'all') {
        const filterLevel = activeToggle.dataset.filter;
        filteredPosts = filteredPosts.filter(post => {
            const relevanceScore = post.relevance_score || 0;
            if (filterLevel === 'high') return relevanceScore >= 15;
            if (filterLevel === 'medium') return relevanceScore >= 8 && relevanceScore < 15;
            if (filterLevel === 'low') return relevanceScore < 8;
            return true;
        });
    }
    
    // Filter by search term
    if (searchInput && searchInput.value.trim()) {
        const searchTerm = searchInput.value.toLowerCase();
        filteredPosts = filteredPosts.filter(post => 
            post.title.toLowerCase().includes(searchTerm) ||
            (post.content_preview && post.content_preview.toLowerCase().includes(searchTerm)) ||
            post.subreddit.toLowerCase().includes(searchTerm)
        );
    }
    
    // Sort posts
    if (sortFilter) {
        const sortBy = sortFilter.value;
        switch (sortBy) {
            case 'engagement':
                filteredPosts.sort((a, b) => b.engagement_score - a.engagement_score);
                break;
            case 'relevance':
                filteredPosts.sort((a, b) => (b.relevance_score || 0) - (a.relevance_score || 0));
                break;
            case 'opportunity':
                filteredPosts.sort((a, b) => (b.combined_score || 0) - (a.combined_score || 0));
                break;
            case 'recent':
                filteredPosts.sort((a, b) => new Date(b.created_utc * 1000) - new Date(a.created_utc * 1000));
                break;
        }
    }
    
    // Render filtered posts
    renderPosts(filteredPosts);
}

// Quick reply modal function
function openReplyModal(postId) {
    // This would open a modal with quick reply options
    // For now, just show an alert
    alert(`Quick reply feature for post ${postId} - Coming soon!`);
}

// Add service worker for offline support (future enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
    });
}

console.log('🎯 Dashboard JavaScript loaded successfully!');
