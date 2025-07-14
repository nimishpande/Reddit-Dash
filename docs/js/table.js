document.addEventListener('DOMContentLoaded', function() {
    // Load all ingredients data
    fetch('data/index.json')
        .then(response => response.json())
        .then(data => {
            // Prepare data for DataTable
            populateIngredientsTable(data.ingredients);
        })
        .catch(error => {
            console.error('Error loading ingredients data:', error);
            document.querySelector('.table-container').innerHTML = `
                <div class="error-message">
                    Failed to load ingredients data. Please try again later.
                </div>
            `;
        });
});

function populateIngredientsTable(ingredients) {
    // Process ingredients to include all necessary data
    const tableData = ingredients.map(ingredient => {
        return [
            ingredient.inci_name,
            ingredient.cas_numbers ? ingredient.cas_numbers.join(', ') : '',
            formatFunctions(ingredient.functions),
            formatSafetyScore(ingredient.safety_score),
            ingredient.origin || 'Not specified',
            '', // Product usage will be populated later
            '', // Reddit sentiment will be populated later
            '', // Popular forms will be populated later
            `<button class="detail-btn" data-slug="${ingredient.slug}">View</button>`
        ];
    });

    // Initialize DataTable
    const table = $('#ingredients-table').DataTable({
        data: tableData,
        responsive: true,
        dom: 'Bfrtip',
        buttons: [
            'copy', 'csv', 'excel'
        ],
        pageLength: 25,
        language: {
            search: "Global Search:",
            searchPlaceholder: "Search any field..."
        },
        initComplete: function() {
            // Add individual column filters
            this.api().columns().every(function(colIdx) {
                let column = this;
                // Skip the details column
                if(colIdx === 8) return;
                // Create filter input element
                let title = $(column.header()).text();
                let input = $('<input type="text" placeholder="Filter ' + title + '" />')
                    .appendTo($(column.header()))
                    .on('keyup change', function() {
                        column
                            .search(this.value)
                            .draw();
                    });
                // Special handling for safety score - dropdown instead of text
                if(colIdx === 3) {
                    input.remove();
                    let select = $('<select><option value="">All</option><option value="0">0 (Safe)</option><option value="1-3">1-3</option><option value="4-6">4-6</option><option value="7-10">7-10 (Hazardous)</option></select>')
                        .appendTo($(column.header()))
                        .on('change', function() {
                            let val = $.fn.dataTable.util.escapeRegex($(this).val());
                            if(val === "") {
                                column.search('').draw();
                            } else if(val.includes('-')) {
                                // Range search
                                let range = val.split('-').map(Number);
                                column.search(getScoreRangeRegex(range[0], range[1]), true, false).draw();
                            } else {
                                column.search('^' + val + '$', true, false).draw();
                            }
                        });
                }
            });
            // Load additional data for visible rows
            loadAdditionalData(this.api());
        },
        drawCallback: function() {
            // When table is redrawn (pagination, filtering), load additional data for visible rows
            loadAdditionalData(this.api());
        }
    });

    // Handle detail button clicks
    $('#ingredients-table').on('click', '.detail-btn', function() {
        const slug = $(this).data('slug');
        showIngredientDetail(slug);
    });
}

// Load additional data for visible rows
function loadAdditionalData(tableApi) {
    // Get visible rows
    const visibleRows = tableApi.rows({page: 'current'}).nodes();
    // For each visible row, load additional data if not already loaded
    $(visibleRows).each(function(index) {
        const row = tableApi.row(this);
        const rowData = row.data();
        const slug = $(rowData[8]).data('slug');
        if(rowData[5] === '') { // If product usage not loaded
            // Load additional data for this ingredient
            fetch(`data/ingredients/${slug}.json`)
                .then(response => response.json())
                .then(data => {
                    // Update product usage
                    if(data.product_usage_data && data.product_usage_data.by_product_type) {
                        const topProducts = data.product_usage_data.by_product_type
                            .slice(0, 2)
                            .map(p => `${p.product_type}: ${p.usage_percentage}%`)
                            .join('<br>');
                        rowData[5] = topProducts;
                    }
                    // Update Reddit sentiment
                    if(data.reddit_community_analysis && data.reddit_community_analysis.sentiment_analysis) {
                        const sentiment = data.reddit_community_analysis.sentiment_analysis.overall_sentiment;
                        rowData[6] = `<span class="sentiment-${sentiment ? sentiment.toLowerCase() : 'neutral'}">${sentiment || 'N/A'}</span>`;
                    }
                    // Update popular forms
                    if(data.reddit_community_analysis && data.reddit_community_analysis.product_forms) {
                        const topForms = data.reddit_community_analysis.product_forms
                            .slice(0, 3)
                            .map(f => f.form)
                            .join(', ');
                        rowData[7] = topForms;
                    }
                    // Update the row data
                    row.data(rowData).draw(false);
                })
                .catch(error => {
                    console.error(`Error loading data for ${slug}:`, error);
                });
        }
    });
}

// Format functions array for display
function formatFunctions(functions) {
    if(!functions || !Array.isArray(functions) || functions.length === 0) {
        return 'Not specified';
    }
    // Filter out long descriptions that are mistakenly included as functions
    const validFunctions = functions.filter(f => typeof f === 'string' && f.length < 50);
    return validFunctions.join(', ');
}

// Format safety score with color coding
function formatSafetyScore(score) {
    if(score === null || score === undefined) {
        return '<span class="safety-unknown">Unknown</span>';
    }
    return `<span class="safety-${score}">${score}</span>`;
}

// Get regex for safety score range search
function getScoreRangeRegex(min, max) {
    let regex = '^(';
    for(let i = min; i <= max; i++) {
        regex += i + (i < max ? '|' : '');
    }
    regex += ')$';
    return regex;
}

// Show ingredient detail in modal
function showIngredientDetail(slug) {
    fetch(`data/ingredients/${slug}.json`)
        .then(response => response.json())
        .then(data => {
            // Populate modal with data
            const modalContent = document.getElementById('modal-content');
            modalContent.innerHTML = `
                <h2>${data.ingredient_overview.inci_name}</h2>
                <div class="tabs">
                    <button class="tab-btn active" data-tab="overview">Overview</button>
                    <button class="tab-btn" data-tab="safety">Safety</button>
                    <button class="tab-btn" data-tab="usage">Usage</button>
                    <button class="tab-btn" data-tab="reddit">Reddit Analysis</button>
                </div>
                <div class="tab-content active" id="tab-overview">
                    ${renderOverviewTab(data.ingredient_overview)}
                </div>
                <div class="tab-content" id="tab-safety">
                    ${renderSafetyTab(data.safety_information)}
                </div>
                <div class="tab-content" id="tab-usage">
                    ${renderUsageTab(data.product_usage_data)}
                </div>
                <div class="tab-content" id="tab-reddit">
                    ${renderRedditTab(data.reddit_community_analysis)}
                </div>
            `;
            // Show the modal
            document.getElementById('detail-modal').style.display = 'block';
            // Add tab functionality
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.addEventListener('click', function() {
                    // Remove active class from all tabs and content
                    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
                    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
                    // Add active class to clicked tab and corresponding content
                    this.classList.add('active');
                    document.getElementById(`tab-${this.dataset.tab}`).classList.add('active');
                });
            });
        })
        .catch(error => {
            console.error(`Error loading detail for ${slug}:`, error);
        });
}

// Close modal when clicking X or outside the modal
document.addEventListener('click', function(event) {
    const modal = document.getElementById('detail-modal');
    const closeBtn = document.querySelector('.close');
    if(event.target === modal || event.target === closeBtn) {
        modal.style.display = 'none';
    }
});

// Tab content rendering functions
function renderOverviewTab(overview) {
    return `
        <table class="detail-table">
            <tr>
                <th>INCI Name</th>
                <td>${overview.inci_name}</td>
            </tr>
            <tr>
                <th>CAS Number(s)</th>
                <td>${overview.cas_numbers ? overview.cas_numbers.join(', ') : 'Not available'}</td>
            </tr>
            <tr>
                <th>Functions</th>
                <td>${formatFunctions(overview.functions)}</td>
            </tr>
            <tr>
                <th>Origin</th>
                <td>${overview.origin || 'Not specified'}</td>
            </tr>
            <tr>
                <th>Description</th>
                <td>${overview.description || 'No description available'}</td>
            </tr>
        </table>
    `;
}

function renderSafetyTab(safety) {
    if(!safety) return '<p>No safety information available</p>';
    return `
        <div class="safety-summary">
            <div class="safety-score ${safety.safety_score !== undefined ? 'safety-' + safety.safety_score : ''}">
                <h3>Safety Score</h3>
                <p class="score">${safety.safety_score !== undefined ? safety.safety_score : 'Unknown'}</p>
            </div>
            <div class="safety-assessment">
                <h3>Assessment</h3>
                <p>${safety.assessment || 'No assessment available'}</p>
            </div>
        </div>
    `;
}

function renderUsageTab(usage) {
    if(!usage || !usage.by_product_type || usage.by_product_type.length === 0) {
        return '<p>No usage data available</p>';
    }
    return `
        <table class="detail-table">
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
    `;
}

function renderRedditTab(reddit) {
    if(!reddit) return '<p>No Reddit analysis available</p>';
    return `
        <div class="reddit-summary">
            <h3>Overview</h3>
            <table class="detail-table">
                <tr>
                    <th>Total Posts Analyzed</th>
                    <td>${reddit.overview ? reddit.overview.total_posts_analyzed : 'N/A'}</td>
                </tr>
                <tr>
                    <th>Overall Sentiment</th>
                    <td>${reddit.sentiment_analysis ? reddit.sentiment_analysis.overall_sentiment : 'N/A'}</td>
                </tr>
            </table>
            ${reddit.product_forms && reddit.product_forms.length > 0 ? `
                <h3>Product Forms</h3>
                <ul>
                    ${reddit.product_forms.slice(0, 5).map(form => `
                        <li>${form.form} (${form.mentions} mentions)</li>
                    `).join('')}
                </ul>
            ` : ''}
            ${reddit.body_parts_usage && reddit.body_parts_usage.length > 0 ? `
                <h3>Body Parts Usage</h3>
                <ul>
                    ${reddit.body_parts_usage.slice(0, 5).map(part => `
                        <li>${part.body_part} (${part.mentions} mentions)</li>
                    `).join('')}
                </ul>
            ` : ''}
        </div>
    `;
} 