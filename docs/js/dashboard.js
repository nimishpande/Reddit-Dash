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

// Show posts feed
function showPostsFeed() {
    const loadingState = document.getElementById('loading-state');
    const postsTableContainer = document.getElementById('posts-table-container');
    const emptyState = document.getElementById('empty-state');
    
    if (loadingState) loadingState.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
    if (postsTableContainer) postsTableContainer.style.display = 'block';
}

// Show empty state
function showEmptyState() {
    const loadingState = document.getElementById('loading-state');
    const postsTableContainer = document.getElementById('posts-table-container');
    const emptyState = document.getElementById('empty-state');
    
    if (loadingState) loadingState.style.display = 'none';
    if (postsTableContainer) postsTableContainer.style.display = 'none';
    if (emptyState) emptyState.style.display = 'block';
}

// Show loading state
function showLoading() {
    const loadingState = document.getElementById('loading-state');
    const postsTableContainer = document.getElementById('posts-table-container');
    const emptyState = document.getElementById('empty-state');
    
    if (loadingState) loadingState.style.display = 'block';
    if (postsTableContainer) postsTableContainer.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
}

// Show error state
function showError() {
    const loadingState = document.getElementById('loading-state');
    const postsTableContainer = document.getElementById('posts-table-container');
    const emptyState = document.getElementById('empty-state');
    const errorState = document.getElementById('error-state');
    
    if (loadingState) loadingState.style.display = 'none';
    if (postsTableContainer) postsTableContainer.style.display = 'none';
    if (emptyState) emptyState.style.display = 'none';
    if (errorState) errorState.style.display = 'block';
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
    
    // New advanced filters
    const subredditFilter = document.getElementById('subreddit-filter');
    const categoryFilter = document.getElementById('category-filter');
    const helpTypeFilter = document.getElementById('help-type-filter');
    const expertiseFilter = document.getElementById('expertise-filter');
    
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
    
    // Set up new advanced filters
    if (subredditFilter) {
        subredditFilter.addEventListener('change', applyFilters);
    }
    
    if (categoryFilter) {
        categoryFilter.addEventListener('change', applyFilters);
    }
    
    if (helpTypeFilter) {
        helpTypeFilter.addEventListener('change', applyFilters);
    }
    
    if (expertiseFilter) {
        expertiseFilter.addEventListener('change', applyFilters);
    }
    
    // Set up clear filters button
    const clearFiltersBtn = document.getElementById('clear-filters');
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
    
    // Set up toggle advanced filters button
    const toggleAdvancedBtn = document.getElementById('toggle-advanced');
    if (toggleAdvancedBtn) {
        toggleAdvancedBtn.addEventListener('click', toggleAdvancedFilters);
    }
    
    // Set up toggle columns button
    const toggleColumnsBtn = document.getElementById('toggle-columns');
    if (toggleColumnsBtn) {
        toggleColumnsBtn.addEventListener('click', toggleContextColumns);
    }
    
    // Set up table sorting
    setupTableSorting();
    
    // Set up enhanced filtering for table
    setupTableFiltering();
    
    // Populate filter options when data is loaded
    populateFilterOptions();
}

// Populate filter dropdown options based on available data
function populateFilterOptions() {
    if (!dashboardData || !dashboardData.posts) return;
    
    // Populate subreddit filter
    const subredditFilter = document.getElementById('subreddit-filter');
    if (subredditFilter) {
        const subreddits = [...new Set(dashboardData.posts.map(post => post.subreddit))];
        subreddits.sort();
        
        // Clear existing options except "All Subreddits"
        subredditFilter.innerHTML = '<option value="all">All Subreddits</option>';
        
        // Add subreddit options
        subreddits.forEach(subreddit => {
            const option = document.createElement('option');
            option.value = subreddit;
            option.textContent = `r/${subreddit}`;
            subredditFilter.appendChild(option);
        });
    }
}

// Clear all filters and reset to default state
function clearAllFilters() {
    // Reset all filter dropdowns
    const subredditFilter = document.getElementById('subreddit-filter');
    const categoryFilter = document.getElementById('category-filter');
    const helpTypeFilter = document.getElementById('help-type-filter');
    const expertiseFilter = document.getElementById('expertise-filter');
    const sortFilter = document.getElementById('sort-filter');
    const searchInput = document.getElementById('search-input');
    
    if (subredditFilter) subredditFilter.value = 'all';
    if (categoryFilter) categoryFilter.value = 'all';
    if (helpTypeFilter) helpTypeFilter.value = 'all';
    if (expertiseFilter) expertiseFilter.value = 'all';
    if (sortFilter) sortFilter.value = 'engagement';
    if (searchInput) searchInput.value = '';
    
    // Reset opportunity toggles
    const opportunityToggles = document.querySelectorAll('.toggle');
    opportunityToggles.forEach(toggle => toggle.classList.remove('active'));
    const allToggle = document.querySelector('.toggle[data-filter="all"]');
    if (allToggle) allToggle.classList.add('active');
    
    // Apply filters to show all posts
    applyFilters();
    
    console.log('🧹 All filters cleared');
}

// Toggle advanced filters visibility
function toggleAdvancedFilters() {
    const advancedFilters = document.querySelectorAll('.advanced-filters');
    const toggleBtn = document.getElementById('toggle-advanced');
    
    const isVisible = advancedFilters[0].style.display !== 'none';
    
    advancedFilters.forEach(filter => {
        if (isVisible) {
            filter.style.display = 'none';
        } else {
            filter.style.display = 'flex';
        }
    });
    
    if (toggleBtn) {
        if (isVisible) {
            toggleBtn.innerHTML = '<i class="fas fa-sliders-h"></i> Advanced';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-sliders-h"></i> Hide Advanced';
        }
    }
    
    console.log(`🔧 Advanced filters ${isVisible ? 'hidden' : 'shown'}`);
}

// Toggle context columns visibility
function toggleContextColumns() {
    const contextColumns = document.querySelectorAll('.col-help-type, .col-expertise, .col-confidence');
    const toggleBtn = document.getElementById('toggle-columns');
    
    // Check if columns are currently visible (either inline style or computed style)
    const isVisible = contextColumns[0].style.display === 'table-cell' || 
                      getComputedStyle(contextColumns[0]).display !== 'none';
    
    contextColumns.forEach(column => {
        if (isVisible) {
            column.style.display = 'none';
        } else {
            column.style.display = 'table-cell';
        }
    });
    
    if (toggleBtn) {
        if (isVisible) {
            toggleBtn.innerHTML = '<i class="fas fa-columns"></i> Show Context';
        } else {
            toggleBtn.innerHTML = '<i class="fas fa-columns"></i> Hide Context';
        }
    }
    
    console.log(`📊 Context columns ${isVisible ? 'hidden' : 'shown'}`);
}

// Set up table column sorting
function setupTableSorting() {
    const tableHeaders = document.querySelectorAll('.posts-table th');
    
    tableHeaders.forEach(header => {
        header.addEventListener('click', function() {
            const column = this.className.replace('col-', '');
            sortTable(column);
        });
        
        // Add keyboard navigation
        header.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const column = this.className.replace('col-', '');
                sortTable(column);
            }
        });
        
        // Add cursor pointer and sort indicators
        header.style.cursor = 'pointer';
        header.innerHTML += ' <i class="fas fa-sort sort-icon"></i>';
    });
}

// Sort table by column
function sortTable(column) {
    const tbody = document.getElementById('posts-tbody');
    const rows = Array.from(tbody.querySelectorAll('tr'));
    
    rows.sort((a, b) => {
        let aValue, bValue;
        
        switch(column) {
            case 'subreddit':
                aValue = a.querySelector('.subreddit-badge').textContent.trim();
                bValue = b.querySelector('.subreddit-badge').textContent.trim();
                return aValue.localeCompare(bValue);
                
            case 'title':
                aValue = a.querySelector('.post-title-link').textContent.trim();
                bValue = b.querySelector('.post-title-link').textContent.trim();
                return aValue.localeCompare(bValue);
                
            case 'engagement':
                aValue = parseFloat(a.dataset.engagement) || 0;
                bValue = parseFloat(b.dataset.engagement) || 0;
                return bValue - aValue;
                
            case 'comments':
                aValue = parseInt(a.querySelector('.comment-count').textContent.trim()) || 0;
                bValue = parseInt(b.querySelector('.comment-count').textContent.trim()) || 0;
                return bValue - aValue;
                
            case 'relevance':
                aValue = parseFloat(a.dataset.relevance) || 0;
                bValue = parseFloat(b.dataset.relevance) || 0;
                return bValue - aValue;
                
            case 'category':
                aValue = a.querySelector('.category-badge').textContent.trim();
                bValue = b.querySelector('.category-badge').textContent.trim();
                return aValue.localeCompare(bValue);
                
            case 'age':
                aValue = a.querySelector('.age-indicator').textContent.trim();
                bValue = b.querySelector('.age-indicator').textContent.trim();
                return aValue.localeCompare(bValue);
                
            default:
                return 0;
        }
    });
    
    // Clear tbody and re-append sorted rows
    tbody.innerHTML = '';
    rows.forEach(row => tbody.appendChild(row));
}

// Set up enhanced table filtering
function setupTableFiltering() {
    const searchInput = document.getElementById('search-input');
    const opportunityToggles = document.querySelectorAll('.toggle');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce(filterTableRows, 300));
    }
    
    opportunityToggles.forEach(toggle => {
        toggle.addEventListener('click', function() {
            opportunityToggles.forEach(t => t.classList.remove('active'));
            this.classList.add('active');
            filterTableRows();
        });
    });
}

// Filter table rows based on search and opportunity filters
function filterTableRows() {
    const searchInput = document.getElementById('search-input');
    const activeToggle = document.querySelector('.toggle.active');
    const searchTerm = searchInput ? searchInput.value.toLowerCase() : '';
    const opportunityFilter = activeToggle ? activeToggle.dataset.filter : 'all';
    
    const rows = document.querySelectorAll('.post-row');
    
    rows.forEach(row => {
        const title = row.querySelector('.post-title-link').textContent.toLowerCase();
        const subreddit = row.querySelector('.subreddit-badge').textContent.toLowerCase();
        const opportunity = row.dataset.opportunity;
        
        let showRow = true;
        
        // Search filter
        if (searchTerm && !title.includes(searchTerm) && !subreddit.includes(searchTerm)) {
            showRow = false;
        }
        
        // Opportunity filter
        if (opportunityFilter !== 'all' && opportunity !== opportunityFilter) {
            showRow = false;
        }
        
        row.style.display = showRow ? '' : 'none';
    });
    
    // Update visible row count
    updateVisibleRowCount();
}

// Update visible row count
function updateVisibleRowCount() {
    const visibleRows = document.querySelectorAll('.post-row:not([style*="display: none"])');
    const totalRows = document.querySelectorAll('.post-row');
    
    console.log(`📊 Filtered: ${visibleRows.length}/${totalRows.length} posts visible`);
}

// Apply filters to posts
function applyFilters() {
    if (!dashboardData || !dashboardData.posts) return;
    
    const sortFilter = document.getElementById('sort-filter');
    const activeToggle = document.querySelector('.toggle.active');
    const searchInput = document.getElementById('search-input');
    
    // New advanced filters
    const subredditFilter = document.getElementById('subreddit-filter');
    const categoryFilter = document.getElementById('category-filter');
    const helpTypeFilter = document.getElementById('help-type-filter');
    const expertiseFilter = document.getElementById('expertise-filter');
    
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
    
    // Filter by subreddit
    if (subredditFilter && subredditFilter.value !== 'all') {
        filteredPosts = filteredPosts.filter(post => 
            post.subreddit === subredditFilter.value
        );
    }
    
    // Filter by category
    if (categoryFilter && categoryFilter.value !== 'all') {
        filteredPosts = filteredPosts.filter(post => {
            const category = post.category || 'general';
            return category.toLowerCase() === categoryFilter.value.toLowerCase();
        });
    }
    
    // Filter by help type
    if (helpTypeFilter && helpTypeFilter.value !== 'all') {
        filteredPosts = filteredPosts.filter(post => {
            const helpType = post.context?.help_type || 'general';
            return helpType === helpTypeFilter.value;
        });
    }
    
    // Filter by expertise match
    if (expertiseFilter && expertiseFilter.value !== 'all') {
        filteredPosts = filteredPosts.filter(post => {
            const expertiseMatches = post.context?.expertise_match || [];
            const confidenceScore = post.context?.confidence_score || 0;
            
            if (expertiseFilter.value === 'none') {
                return expertiseMatches.length === 0;
            } else if (expertiseFilter.value === 'high') {
                return confidenceScore >= 0.8;
            } else if (expertiseFilter.value === 'medium') {
                return confidenceScore >= 0.5 && confidenceScore < 0.8;
            } else if (expertiseFilter.value === 'low') {
                return confidenceScore > 0 && confidenceScore < 0.5;
            }
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

// Auto-refresh functionality
let autoRefreshInterval;
let currentDataTimestamp;

// Check for updates every 5 minutes
function startAutoRefresh() {
    autoRefreshInterval = setInterval(() => {
        checkForUpdates();
    }, 300000); // 5 minutes
}

// Check if data has been updated
function checkForUpdates() {
    fetch(CONFIG.dataUrl)
        .then(response => response.json())
        .then(data => {
            const newTimestamp = data.dashboard_info.last_updated;
            if (currentDataTimestamp && newTimestamp !== currentDataTimestamp) {
                console.log('🔄 New data detected, refreshing page...');
                showRefreshNotification();
                setTimeout(() => {
                    location.reload();
                }, 2000);
            }
            currentDataTimestamp = newTimestamp;
        })
        .catch(error => {
            console.log('Failed to check for updates:', error);
        });
}

// Show refresh notification
function showRefreshNotification() {
    const notification = document.createElement('div');
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: #4CAF50;
        color: white;
        padding: 15px 20px;
        border-radius: 5px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    `;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; gap: 10px;">
            <i class="fas fa-sync-alt" style="animation: spin 1s linear infinite;"></i>
            <span>New data available! Refreshing...</span>
        </div>
    `;
    document.body.appendChild(notification);
    
    setTimeout(() => {
        if (notification.parentNode) {
            notification.parentNode.removeChild(notification);
        }
    }, 2000);
}

// Initialize auto-refresh when page loads
document.addEventListener('DOMContentLoaded', function() {
    // Start auto-refresh after initial load
    setTimeout(() => {
        startAutoRefresh();
        console.log('🔄 Auto-refresh enabled (checks every 5 minutes)');
    }, 10000); // Start after 10 seconds
});

// Add service worker for offline support (future enhancement)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        // navigator.serviceWorker.register('/sw.js')
        //     .then(registration => console.log('SW registered'))
        //     .catch(error => console.log('SW registration failed'));
    });
}

console.log('🎯 Dashboard JavaScript loaded successfully!');
