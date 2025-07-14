function initializeDetailPage() {
    const ingredientId = getUrlParameter('id');
    if (!ingredientId) {
        showError('No ingredient specified');
        return;
    }
    loadIngredientData(ingredientId);
}

function loadIngredientData(ingredientId) {
    fetch(`data/ingredients/${ingredientId}.json`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Ingredient not found');
            }
            return response.json();
        })
        .then(data => {
            document.title = `${data.ingredient_overview.inci_name} - Cosmetic Ingredient Database`;
            displayIngredientHeader(data);
            populateOverviewTab(data);
            populateSafetyTab(data);
            populateUsageTab(data);
            populateRedditTab(data);
            initializeVisualizations(data);
        })
        .catch(error => {
            console.error('Error loading ingredient data:', error);
            showError('Error loading ingredient data. The ingredient may not exist or there was a problem accessing the data.');
        });
}

function displayIngredientHeader(data) {
    const detailContainer = document.getElementById('ingredient-detail');
    if (!detailContainer) return;
    const overview = data.ingredient_overview;
    const safety = data.safety_information;
    const safetyClass = `safety-${safety.safety_score || 0}`;
    detailContainer.innerHTML = `
        <div class="box">
            <h1 class="title is-2">${overview.inci_name}</h1>
            <div class="tags">
                <span class="tag is-medium ${safetyClass}">Safety Score: ${safety.safety_score !== undefined && safety.safety_score !== null ? safety.safety_score : 'N/A'}</span>
                ${overview.origin ? `<span class="tag is-medium is-info">Origin: ${overview.origin}</span>` : ''}
            </div>
            <div class="subtitle">
                <strong>CAS Number${overview.cas_numbers && overview.cas_numbers.length > 1 ? 's' : ''}:</strong> 
                ${overview.cas_numbers ? overview.cas_numbers.join(', ') : 'Not available'}
            </div>
            <div class="functions">
                <strong>Functions:</strong> 
                ${overview.functions ? overview.functions.map(f => `<span class="tag">${f}</span>`).join(' ') : 'Not specified'}
            </div>
        </div>
    `;
}

function initializeTabs() {
    const tabs = document.querySelectorAll('#detail-tabs li');
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            tabs.forEach(t => t.classList.remove('is-active'));
            this.classList.add('is-active');
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('is-active');
            });
            const tabName = this.querySelector('a').dataset.tab;
            document.getElementById(`tab-${tabName}`).classList.add('is-active');
        });
    });
}

function populateOverviewTab(data) {
    const tabPane = document.getElementById('tab-overview');
    if (!tabPane) return;
    const overview = data.ingredient_overview;
    tabPane.innerHTML = `
        <div class="content">
            <h2 class="title is-4">Overview</h2>
            <div class="description">
                ${overview.description || 'No detailed description available for this ingredient.'}
            </div>
            <div class="info-table mt-4">
                <table class="table is-fullwidth">
                    <tbody>
                        <tr>
                            <th>INCI Name</th>
                            <td>${overview.inci_name}</td>
                        </tr>
                        <tr>
                            <th>CAS Number${overview.cas_numbers && overview.cas_numbers.length > 1 ? 's' : ''}</th>
                            <td>${overview.cas_numbers ? overview.cas_numbers.join(', ') : 'Not available'}</td>
                        </tr>
                        <tr>
                            <th>Functions</th>
                            <td>${overview.functions ? overview.functions.join(', ') : 'Not specified'}</td>
                        </tr>
                        <tr>
                            <th>Origin</th>
                            <td>${overview.origin || 'Not specified'}</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    `;
}

function populateSafetyTab(data) {
    const tabPane = document.getElementById('tab-safety');
    if (!tabPane) return;
    const safety = data.safety_information;
    const safetyClass = `safety-${safety.safety_score || 0}`;
    tabPane.innerHTML = `
        <div class="content">
            <h2 class="title is-4">Safety Information</h2>
            <div class="stat-box ${safetyClass}">
                <h3>Safety Score</h3>
                <div class="stat-value">${safety.safety_score !== undefined && safety.safety_score !== null ? safety.safety_score : 'N/A'}</div>
            </div>
            <div class="notification ${safetyClass}">
                <p>${safety.assessment || 'No assessment available'}</p>
            </div>
            <div class="chart-container mt-5">
                <canvas id="safety-chart"></canvas>
            </div>
        </div>
    `;
}

function populateUsageTab(data) {
    const tabPane = document.getElementById('tab-usage');
    if (!tabPane) return;
    const usage = data.product_usage_data;
    tabPane.innerHTML = `
        <div class="content">
            <h2 class="title is-4">Product Usage Data</h2>
            ${usage && usage.by_product_type && usage.by_product_type.length > 0 ? `
                <div class="table-container">
                    <table class="table is-fullwidth is-striped">
                        <thead>
                            <tr>
                                <th>Product Type</th>
                                <th>Usage Percentage</th>
                                <th>Sample Size</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${usage.by_product_type.map(item => `
                                <tr>
                                    <td>${item.product_type}</td>
                                    <td>${item.usage_percentage}%</td>
                                    <td>${item.sample_size}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                <div class="chart-container mt-5">
                    <canvas id="usageChart"></canvas>
                </div>
            ` : '<p>No product usage data available for this ingredient.</p>'}
        </div>
    `;
}

function populateRedditTab(data) {
    const tabPane = document.getElementById('tab-reddit');
    if (!tabPane) return;
    const reddit = data.reddit_community_analysis;
    if (!reddit) {
        tabPane.innerHTML = '<p>No Reddit community analysis available for this ingredient.</p>';
        return;
    }
    // Stat boxes and chart containers for Reddit analysis
    tabPane.innerHTML = `
        <div class="content">
            <h2 class="title is-4">Reddit Community Analysis</h2>
            <div class="reddit-overview">
                <div class="columns">
                    <div class="column">
                        <div class="stat-box">
                            <h3>Total Posts</h3>
                            <div class="stat-value">${reddit.overview && reddit.overview.total_posts_analyzed ? reddit.overview.total_posts_analyzed : 'N/A'}</div>
                        </div>
                    </div>
                    <div class="column">
                        <div class="stat-box">
                            <h3>Sentiment</h3>
                            <div class="stat-value sentiment-${(reddit.sentiment_analysis && reddit.sentiment_analysis.overall_sentiment) ? reddit.sentiment_analysis.overall_sentiment.toLowerCase() : 'neutral'}">${reddit.sentiment_analysis && reddit.sentiment_analysis.overall_sentiment ? reddit.sentiment_analysis.overall_sentiment : 'N/A'}</div>
                        </div>
                    </div>
                    <div class="column">
                        <div class="stat-box">
                            <h3>Most Popular Form</h3>
                            <div class="stat-value">N/A</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="chart-row">
                <div class="chart-container half">
                    <h3>Sentiment Analysis</h3>
                    <canvas id="sentiment-chart"></canvas>
                </div>
                <div class="chart-container half">
                    <h3>Product Forms</h3>
                    <canvas id="forms-chart"></canvas>
                </div>
            </div>
            <div class="subreddit-distribution">
                <h3>Top Subreddits</h3>
                <div class="tag-cloud" id="subreddit-tags"></div>
            </div>
        </div>
    `;
}

function showError(message) {
    const detailContainer = document.getElementById('ingredient-detail');
    if (!detailContainer) return;
    detailContainer.innerHTML = `
        <div class="notification is-danger">
            <p>${message}</p>
            <p><a href="index.html">Return to ingredient list</a></p>
        </div>
    `;
    document.getElementById('detail-tabs').style.display = 'none';
    document.querySelectorAll('.tab-content').forEach(pane => {
        pane.style.display = 'none';
    });
} 