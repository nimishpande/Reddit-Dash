function initializeVisualizations(data) {
    if (!document.getElementById('tab-safety')) return;
    if (data.safety_information) {
        createSafetyChart(data.safety_information);
    }
    if (data.product_usage_data && data.product_usage_data.by_product_type) {
        createUsageChart(data.product_usage_data);
    }
    if (data.reddit_community_analysis) {
        createSentimentChart(data.reddit_community_analysis);
        createTemporalChart(data.reddit_community_analysis);
        createCategoryChart(data.reddit_community_analysis);
    }
}
function createSafetyChart(safetyData) {
    const ctx = document.getElementById('safetyChart');
    if (!ctx) return;
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Safety Score'],
            datasets: [{
                label: 'Safety Score',
                data: [safetyData.safety_score || 0],
                backgroundColor: getSafetyColor(safetyData.safety_score || 0)
            }]
        },
        options: {
            responsive: true,
            title: { display: true, text: 'Safety Score' },
            scales: { y: { beginAtZero: true, max: 10 } }
        }
    });
}
function createUsageChart(usageData) {
    const ctx = document.getElementById('usageChart');
    if (!ctx) return;
    const productTypes = usageData.by_product_type.map(item => item.product_type);
    const usagePercentages = usageData.by_product_type.map(item => item.usage_percentage);
    const sampleSizes = usageData.by_product_type.map(item => item.sample_size);
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: productTypes,
            datasets: [{
                label: 'Usage Percentage (%)',
                data: usagePercentages,
                backgroundColor: 'rgba(54, 162, 235, 0.5)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Percentage (%)' } },
                x: { title: { display: true, text: 'Product Type' } }
            },
            plugins: {
                tooltip: {
                    callbacks: {
                        afterLabel: function(context) {
                            return `Sample Size: ${sampleSizes[context.dataIndex]}`;
                        }
                    }
                }
            }
        }
    });
}
function createSentimentChart(redditData) {
    const ctx = document.getElementById('sentimentChart');
    if (!ctx) return;
    const sentiment = redditData.sentiment_analysis;
    new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Positive', 'Negative'],
            datasets: [{
                data: [
                    sentiment.sentiment_keywords.positive.count || 0,
                    sentiment.sentiment_keywords.negative.count || 0
                ],
                backgroundColor: [
                    'rgba(75, 192, 192, 0.5)',
                    'rgba(255, 99, 132, 0.5)'
                ],
                borderColor: [
                    'rgba(75, 192, 192, 1)',
                    'rgba(255, 99, 132, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Sentiment Distribution' },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.formattedValue || '';
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((context.raw / total) * 100);
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}
function createTemporalChart(redditData) {
    const ctx = document.getElementById('temporalChart');
    if (!ctx) return;
    if (!redditData.temporal_patterns || !redditData.temporal_patterns.posts_by_year) {
        return;
    }
    const years = redditData.temporal_patterns.posts_by_year.map(item => item.year);
    const postCounts = redditData.temporal_patterns.posts_by_year.map(item => item.post_count);
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: years,
            datasets: [{
                label: 'Number of Posts',
                data: postCounts,
                fill: false,
                borderColor: 'rgba(153, 102, 255, 1)',
                backgroundColor: 'rgba(153, 102, 255, 0.5)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, title: { display: true, text: 'Number of Posts' } },
                x: { title: { display: true, text: 'Year' } }
            },
            plugins: {
                title: { display: true, text: 'Posts by Year' }
            }
        }
    });
}
function createCategoryChart(redditData) {
    const ctx = document.getElementById('categoryChart');
    if (!ctx) return;
    if (!redditData.category_breakdown || redditData.category_breakdown.length === 0) {
        return;
    }
    const categories = redditData.category_breakdown.map(item => item.category);
    const postCounts = redditData.category_breakdown.map(item => item.post_count);
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: categories,
            datasets: [{
                label: 'Number of Posts',
                data: postCounts,
                backgroundColor: 'rgba(255, 159, 64, 0.5)',
                borderColor: 'rgba(255, 159, 64, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { beginAtZero: true, title: { display: true, text: 'Number of Posts' } }
            },
            plugins: {
                title: { display: true, text: 'Posts by Category' }
            }
        }
    });
}
function getSafetyColor(score) {
    const colors = [
        'rgba(76, 175, 80, 0.5)',
        'rgba(139, 195, 74, 0.5)',
        'rgba(205, 220, 57, 0.5)',
        'rgba(255, 235, 59, 0.5)',
        'rgba(255, 193, 7, 0.5)',
        'rgba(255, 152, 0, 0.5)',
        'rgba(255, 87, 34, 0.5)',
        'rgba(244, 67, 54, 0.5)',
        'rgba(233, 30, 99, 0.5)',
        'rgba(156, 39, 176, 0.5)',
        'rgba(103, 58, 183, 0.5)'
    ];
    const safeScore = Math.max(0, Math.min(10, score));
    return colors[safeScore];
} 