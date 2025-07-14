function initializeDetailPage() {
    const ingredientId = getUrlParameter('id');
    if (!ingredientId) {
        showError('No ingredient specified');
        return;
    }
    loadIngredientData(ingredientId);
    initializeTabs();
}
function loadIngredientData(ingredientId) {
    fetch(`${API_BASE_URL}ingredients/${ingredientId}.json`)
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
                <span class="tag is-medium ${safetyClass}">Safety Score: ${safety.safety_score || 'N/A'}</span>
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
            <div class="notification ${safetyClass}">
                <p class="is-size-4"><strong>Safety Score: ${safety.safety_score || 'N/A'}</strong></p>
                <p>${safety.assessment || 'No assessment available'}</p>
            </div>
            ${safety.categories && Object.keys(safety.categories).length > 0 ? `
                <h3 class="title is-5">Assessment Categories</h3>
                <table class="table is-fullwidth">
                    <thead>
                        <tr>
                            <th>Category</th>
                            <th>Assessment</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${Object.entries(safety.categories).map(([category, assessment]) => `
                            <tr>
                                <td>${category}</td>
                                <td>${assessment}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            ` : '<p>No detailed category assessments available for this ingredient.</p>'}
            <div class="chart-container mt-5">
                <canvas id="safetyChart"></canvas>
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
    tabPane.innerHTML = `
        <div class="content">
            <h2 class="title is-4">Reddit Community Analysis</h2>
            <div class="columns">
                <div class="column">
                    <div class="box">
                        <h3 class="title is-5">Overview</h3>
                        <table class="table is-fullwidth">
                            <tbody>
                                <tr>
                                    <th>Total Posts Analyzed</th>
                                    <td>${reddit.overview.total_posts_analyzed}</td>
                                </tr>
                                <tr>
                                    <th>Posts with Comments</th>
                                    <td>${reddit.overview.posts_with_comments}</td>
                                </tr>
                                <tr>
                                    <th>Comment Coverage</th>
                                    <td>${reddit.overview.comment_coverage_percentage}%</td>
                                </tr>
                            </tbody>
                        </table>
                    </div>
                </div>
                <div class="column">
                    <div class="box">
                        <h3 class="title is-5">Sentiment Analysis</h3>
                        <p><strong>Overall Sentiment:</strong> ${reddit.sentiment_analysis.overall_sentiment}</p>
                        <p>
                            <strong>Positive Keywords:</strong> ${reddit.sentiment_analysis.sentiment_keywords.positive.count} 
                            (${reddit.sentiment_analysis.sentiment_keywords.positive.percentage}%)
                        </p>
                        <p>
                            <strong>Negative Keywords:</strong> ${reddit.sentiment_analysis.sentiment_keywords.negative.count} 
                            (${reddit.sentiment_analysis.sentiment_keywords.negative.percentage}%)
                        </p>
                    </div>
                </div>
            </div>
            <div class="chart-container mt-4">
                <canvas id="sentimentChart"></canvas>
            </div>
            <div class="columns mt-5">
                <div class="column is-half">
                    <div class="reddit-section">
                        <h3 class="title is-5">Positive Benefits</h3>
                        ${reddit.sentiment_analysis.positive_benefits.total_positive_statements > 0 ? `
                            <p>Total Positive Statements: ${reddit.sentiment_analysis.positive_benefits.total_positive_statements}</p>
                            ${reddit.sentiment_analysis.positive_benefits.key_positive_themes.length > 0 ? `
                                <h4 class="subtitle is-6">Key Positive Themes:</h4>
                                <ul>
                                    ${reddit.sentiment_analysis.positive_benefits.key_positive_themes.map(theme => `
                                        <li>${theme}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p>No specific positive themes identified.</p>'}
                        ` : '<p>No positive statements identified in the analysis.</p>'}
                    </div>
                </div>
                <div class="column is-half">
                    <div class="reddit-section">
                        <h3 class="title is-5">Negative Cons</h3>
                        ${reddit.sentiment_analysis.negative_cons.total_negative_statements > 0 ? `
                            <p>Total Negative Statements: ${reddit.sentiment_analysis.negative_cons.total_negative_statements}</p>
                            ${reddit.sentiment_analysis.negative_cons.key_negative_themes.length > 0 ? `
                                <h4 class="subtitle is-6">Key Negative Themes:</h4>
                                <ul>
                                    ${reddit.sentiment_analysis.negative_cons.key_negative_themes.map(theme => `
                                        <li>${theme}</li>
                                    `).join('')}
                                </ul>
                            ` : '<p>No specific negative themes identified.</p>'}
                        ` : '<p>No negative statements identified in the analysis.</p>'}
                    </div>
                </div>
            </div>
            <div class="reddit-section mt-5">
                <h3 class="title is-5">Temporal Patterns</h3>
                <div class="chart-container">
                    <canvas id="temporalChart"></canvas>
                </div>
            </div>
            <div class="reddit-section mt-5">
                <h3 class="title is-5">Category Breakdown</h3>
                <div class="chart-container">
                    <canvas id="categoryChart"></canvas>
                </div>
            </div>
            ${reddit.key_insights && reddit.key_insights.length > 0 ? `
                <div class="reddit-section mt-5">
                    <h3 class="title is-5">Key Insights</h3>
                    <ul>
                        ${reddit.key_insights.map(insight => `
                            <li>${insight}</li>
                        `).join('')}
                    </ul>
                </div>
            ` : ''}
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
    document.querySelectorAll('.tab-pane').forEach(pane => {
        pane.style.display = 'none';
    });
} 