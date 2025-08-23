$(document).ready(function() {
    // Helper functions for formatting data
    function formatCASNumbers(casNumbers) {
        if (!casNumbers || !Array.isArray(casNumbers) || casNumbers.length === 0) {
            return 'N/A';
        }
        return casNumbers.join(', ');
    }
    function formatFunctions(functions) {
        if (!functions || !Array.isArray(functions) || functions.length === 0) {
            return 'N/A';
        }
        const validFunctions = functions.filter(f => typeof f === 'string' && f.length < 50);
        if (validFunctions.length === 0) {
            return 'N/A';
        }
        if (validFunctions.length > 3) {
            return validFunctions.slice(0, 3).join(', ') + '...';
        }
        return validFunctions.join(', ');
    }
    function formatSafetyScore(score) {
        if (score === null || score === undefined) {
            return '<span class="safety-unknown">Unknown</span>';
        }
        return `<span class="safety-${score}">${score}</span>`;
    }
    // DataTables initialization
    const table = $('#ingredients-table').DataTable({
        processing: true,
        deferRender: true,
        scrollX: true,
        pageLength: 10,
        order: [[0, 'asc']], // Sort by INCI Name
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        dom: 'Blfrtip',
        buttons: [
            'copy', 'csv', 'excel',
            {
                extend: 'colvis',
                text: 'Show/Hide Columns',
                columns: ':not(.noVis)'
            }
        ],
        columnDefs: [
            { "width": "120px", targets: 0 },  // INCI Name
            { "width": "100px", targets: 1 },  // CAS Numbers
            { "width": "150px", targets: 2 },  // Functions
            { "width": "60px", targets: 3 },   // Safety Score
            { "width": "130px", targets: 4 },  // Safety Assessment
            { "width": "80px", targets: 5 },   // Origin
            { "width": "150px", targets: 6 },  // Top Product Usage
            { "width": "70px", targets: 7 },   // Posts Analyzed
            { "width": "80px", targets: 8 },   // Comment Coverage
            { "width": "90px", targets: 9 },   // Overall Sentiment
            { "width": "70px", targets: 10 },  // Positive Statements
            { "width": "130px", targets: 11 }, // Key Benefits
            { "width": "70px", targets: 12 },  // Negative Statements
            { "width": "130px", targets: 13 }, // Key Concerns
            { "width": "120px", targets: 14 }, // Common Dosages
            { "width": "150px", targets: 15 }, // Popular Forms
            { "width": "150px", targets: 16 }, // Body Parts
            { "width": "180px", targets: 17 }, // Top Ingredients Combined
            { "width": "130px", targets: 18 }, // Top Brands
            { "width": "130px", targets: 19 }, // Top Subreddits
            { "width": "120px", targets: 20 }  // Most Active Year
        ],
        initComplete: function() {
            // Hide less critical columns by default
            this.api().columns([4, 8, 12, 14, 18, 19, 20]).visible(false);
        }
    });
    // Throttled fetch and cache for ingredient details
    const MAX_CONCURRENT_FETCHES = 6;
    let currentFetches = 0;
    const fetchQueue = [];
    const ingredientDetailCache = {};
    function throttledFetch(url) {
        return new Promise((resolve, reject) => {
            const task = () => {
                currentFetches++;
                fetch(url)
                    .then(response => {
                        currentFetches--;
                        processQueue();
                        if (!response.ok) throw new Error('Network response was not ok');
                        return response.json();
                    })
                    .then(resolve)
                    .catch(err => {
                        currentFetches--;
                        processQueue();
                        reject(err);
                    });
            };
            fetchQueue.push(task);
            processQueue();
        });
    }
    function processQueue() {
        while (currentFetches < MAX_CONCURRENT_FETCHES && fetchQueue.length > 0) {
            const nextTask = fetchQueue.shift();
            nextTask();
        }
    }
    function getIngredientDetail(slug, url) {
        if (ingredientDetailCache[slug]) {
            return Promise.resolve(ingredientDetailCache[slug]);
        }
        return throttledFetch(url).then(data => {
            ingredientDetailCache[slug] = data;
            return data;
        });
    }
    // Batch loading logic
    function populateTableWithIngredientData() {
        $('#loading-indicator').show();
        fetch('data/index.json')
            .then(response => response.json())
            .then(data => {
                // Sort ingredients by INCI Name (A-Z)
                const ingredients = data.ingredients.slice().sort((a, b) => a.inci_name.localeCompare(b.inci_name));
                const batchSize = 15;
                processIngredientBatch(ingredients, 0, batchSize);
            })
            .catch(error => {
                console.error('Error loading ingredients:', error);
                $('#loading-indicator').hide();
                $('#error-message').text('Error loading ingredients data').show();
            });
    }
    function processIngredientBatch(ingredients, startIndex, batchSize) {
        const endIndex = Math.min(startIndex + batchSize, ingredients.length);
        const currentBatch = ingredients.slice(startIndex, endIndex);
        currentBatch.forEach(ingredient => {
            const row = [
                ingredient.inci_name,
                formatCASNumbers(ingredient.cas_numbers),
                formatFunctions(ingredient.functions),
                formatSafetyScore(ingredient.safety_score),
                'Loading...', // Safety Assessment
                ingredient.origin || 'N/A',
                'Loading...', // Top Product Usage
                'Loading...', // Posts Analyzed
                'Loading...', // Comment Coverage
                'Loading...', // Overall Sentiment
                'Loading...', // Positive Statements
                'Loading...', // Key Benefits
                'Loading...', // Negative Statements
                'Loading...', // Key Concerns
                'Loading...', // Common Dosages
                'Loading...', // Popular Forms
                'Loading...', // Body Parts
                'Loading...', // Top Ingredients Combined
                'Loading...', // Top Brands
                'Loading...', // Top Subreddits
                'Loading...'  // Most Active Year
            ];
            const addedRow = table.row.add(row).draw(false);
            loadDetailedIngredientData(ingredient.slug, table.row(addedRow).index());
        });
        if (endIndex < ingredients.length) {
            setTimeout(() => {
                processIngredientBatch(ingredients, endIndex, batchSize);
            }, 100);
        } else {
            $('#loading-indicator').hide();
        }
    }
    function loadDetailedIngredientData(slug, rowIndex) {
        getIngredientDetail(slug, `data/ingredients/${slug}.json`)
            .then(data => {
                const row = table.row(rowIndex);
                if (!row) return;
                const rowData = [...row.data()];
                // Safety Assessment
                if (data.safety_information && data.safety_information.assessment) {
                    rowData[4] = data.safety_information.assessment.replace(/"/g, '');
                } else {
                    rowData[4] = 'N/A';
                }
                // Top Product Usage
                if (data.product_usage_data && data.product_usage_data.by_product_type && data.product_usage_data.by_product_type.length > 0) {
                    const topProduct = data.product_usage_data.by_product_type[0];
                    rowData[6] = `${topProduct.product_type}: ${topProduct.usage_percentage}%`;
                } else {
                    rowData[6] = 'N/A';
                }
                // Reddit Analysis
                if (data.reddit_community_analysis) {
                    const reddit = data.reddit_community_analysis;
                    rowData[7] = reddit.overview && reddit.overview.total_posts_analyzed ? reddit.overview.total_posts_analyzed : 'N/A';
                    rowData[8] = reddit.overview && reddit.overview.comment_coverage_percentage ? `${reddit.overview.comment_coverage_percentage}%` : 'N/A';
                    if (reddit.sentiment_analysis && reddit.sentiment_analysis.overall_sentiment) {
                        const sentiment = reddit.sentiment_analysis.overall_sentiment;
                        rowData[9] = `<span class="sentiment-${sentiment.toLowerCase()}">${sentiment}</span>`;
                    } else {
                        rowData[9] = 'N/A';
                    }
                    rowData[10] = reddit.sentiment_analysis && reddit.sentiment_analysis.positive_benefits ? (reddit.sentiment_analysis.positive_benefits.total_positive_statements || 0) : 0;
                    rowData[11] = reddit.sentiment_analysis && reddit.sentiment_analysis.positive_benefits && reddit.sentiment_analysis.positive_benefits.key_positive_themes && reddit.sentiment_analysis.positive_benefits.key_positive_themes.length > 0 ? reddit.sentiment_analysis.positive_benefits.key_positive_themes.slice(0, 2).join(', ') : 'None reported';
                    rowData[12] = reddit.sentiment_analysis && reddit.sentiment_analysis.negative_cons ? (reddit.sentiment_analysis.negative_cons.total_negative_statements || 0) : 0;
                    rowData[13] = reddit.sentiment_analysis && reddit.sentiment_analysis.negative_cons && reddit.sentiment_analysis.negative_cons.key_negative_themes && reddit.sentiment_analysis.negative_cons.key_negative_themes.length > 0 ? reddit.sentiment_analysis.negative_cons.key_negative_themes.slice(0, 2).join(', ') : 'None reported';
                    rowData[14] = reddit.dosage_effectiveness && reddit.dosage_effectiveness.most_common_dosages && reddit.dosage_effectiveness.most_common_dosages.length > 0 ? reddit.dosage_effectiveness.most_common_dosages.slice(0, 2).map(d => d.dosage).join(', ') : 'N/A';
                    rowData[15] = reddit.product_forms && reddit.product_forms.length > 0 ? reddit.product_forms.slice(0, 3).map(form => `${form.form} (${form.mentions})`).join(', ') : 'N/A';
                    rowData[16] = reddit.body_parts_usage && reddit.body_parts_usage.length > 0 ? reddit.body_parts_usage.slice(0, 3).map(part => `${part.body_part} (${part.mentions})`).join(', ') : 'N/A';
                    rowData[17] = reddit.ingredient_combinations && reddit.ingredient_combinations.top_combinations && reddit.ingredient_combinations.top_combinations.length > 0 ? reddit.ingredient_combinations.top_combinations.slice(0, 2).map(combo => combo.ingredients.join(', ')).join('; ') : 'N/A';
                    rowData[18] = reddit.brands_mentioned && reddit.brands_mentioned.length > 0 ? reddit.brands_mentioned.slice(0, 3).map(brand => brand.brand).join(', ') : 'N/A';
                    rowData[19] = reddit.subreddit_distribution && reddit.subreddit_distribution.length > 0 ? reddit.subreddit_distribution.slice(0, 3).map(sub => sub.subreddit).join(', ') : 'N/A';
                    if (reddit.temporal_patterns && reddit.temporal_patterns.posts_by_year && reddit.temporal_patterns.posts_by_year.length > 0) {
                        let maxYear = null;
                        let maxCount = 0;
                        reddit.temporal_patterns.posts_by_year.forEach(item => {
                            if (item.post_count > maxCount) {
                                maxCount = item.post_count;
                                maxYear = item.year;
                            }
                        });
                        rowData[20] = maxYear ? `${maxYear} (${maxCount} posts)` : 'N/A';
                    } else {
                        rowData[20] = 'N/A';
                    }
                } else {
                    for (let i = 7; i <= 20; i++) {
                        rowData[i] = 'N/A';
                    }
                }
                row.data(rowData).draw(false);
            })
            .catch(error => {
                console.error(`Error loading detailed data for ${slug}:`, error);
            });
    }
    // Add tooltips to column headers
    const tooltips = {
        0: "International Nomenclature of Cosmetic Ingredients name",
        1: "Chemical Abstracts Service registry number",
        2: "Primary functions in cosmetic formulations",
        3: "Safety score from 0 (safe) to 10 (concern)",
        4: "Summary of safety assessment",
        5: "Natural or synthetic origin of the ingredient",
        6: "Product type with highest usage percentage",
        7: "Number of Reddit posts analyzed",
        8: "Percentage of posts with comments",
        9: "Overall sentiment from Reddit analysis",
        10: "Count of positive statements in Reddit posts",
        11: "Top reported benefits from Reddit",
        12: "Count of negative statements in Reddit posts",
        13: "Top reported concerns from Reddit",
        14: "Most commonly mentioned dosages on Reddit",
        15: "Most popular product forms on Reddit",
        16: "Body parts where most commonly used",
        17: "Ingredients most often used together",
        18: "Most mentioned brands on Reddit",
        19: "Subreddits with most discussions",
        20: "Year with most Reddit activity"
    };
    $('#ingredients-table thead th').each(function(index) {
        if (tooltips[index]) {
            $(this).attr('title', tooltips[index]);
        }
    });
    // Memory management
    function cleanupMemory() {
        if (window.gc) {
            window.gc();
        }
        setTimeout(cleanupMemory, 60000);
    }
    function monitorMemory() {
        if (window.performance && window.performance.memory) {
            const memoryInfo = window.performance.memory;
            const memoryUsage = memoryInfo.usedJSHeapSize / memoryInfo.jsHeapSizeLimit;
            if (memoryUsage > 0.7) {
                const table = $('#ingredients-table').DataTable();
                table.state.clear();
                table.clear().draw();
                setTimeout(() => {
                    location.reload();
                }, 1000);
            }
        }
        setTimeout(monitorMemory, 10000);
    }
    setTimeout(monitorMemory, 5000);
    setTimeout(cleanupMemory, 60000);
    // Start loading data
    populateTableWithIngredientData();
}); 