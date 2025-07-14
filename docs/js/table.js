$(document).ready(function() {
    // Enhanced DataTables initialization
    const table = $('#ingredients-table').DataTable({
        responsive: true,
        dom: 'Blfrtip',
        buttons: [
            'copy', 'csv', 'excel',
            {
                text: 'Toggle Columns',
                action: function (e, dt, node, config) {
                    $('#column-visibility-modal').toggle();
                }
            }
        ],
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]],
        pageLength: 25,
        fixedHeader: true,
        stateSave: true,
        deferRender: true
    });

    // --- Filter row logic ---
    // For each filter input/select in the filter row, wire up column search
    $('#ingredients-table thead .filter-row th').each(function(colIdx) {
        const input = $(this).find('.column-filter');
        if (input.length) {
            input.on('keyup change', function() {
                let val = $(this).val();
                // Special handling for safety score select
                if ($(this).is('select')) {
                    // Remove previous custom search for this column
                    $.fn.dataTable.ext.search = $.fn.dataTable.ext.search.filter(fn => !fn._isSafetyScore);
                    if (val && val.includes('-')) {
                        const [min, max] = val.split('-').map(Number);
                        const fn = function(settings, data, dataIndex) {
                            // Safety score is column 3 (index 3)
                            const score = parseInt($(data[3]).text() || data[3]) || 0;
                            return score >= min && score <= max;
                        };
                        fn._isSafetyScore = true;
                        $.fn.dataTable.ext.search.push(fn);
                        table.draw();
                        return;
                    } else if (val) {
                        table.column(colIdx).search('^' + val + '$', true, false).draw();
                        return;
                    } else {
                        table.column(colIdx).search('').draw();
                        table.draw();
                        return;
                    }
                } else {
                    table.column(colIdx).search(val).draw();
                }
            });
        }
    });

    // Setup column visibility controls
    function setupColumnVisibility() {
        const container = $('#column-toggles');
        container.empty();
        table.columns().every(function(index) {
            const column = this;
            const title = $(column.header()).text();
            const toggle = $(`
                <div class="column-toggle">
                    <label>
                        <input type="checkbox" ${column.visible() ? 'checked' : ''}>
                        ${title}
                    </label>
                </div>
            `);
            $('input', toggle).on('change', function() {
                column.visible(this.checked);
            });
            container.append(toggle);
        });
        $('#close-column-modal').on('click', function() {
            $('#column-visibility-modal').hide();
        });
    }
    setupColumnVisibility();

    // Optimized data loading
    function loadIngredientData() {
        $('#loading-indicator').show();
        fetch('data/index.json')
            .then(response => response.json())
            .then(data => {
                table.clear();
                const rowData = data.ingredients.map(ingredient => [
                    ingredient.inci_name,
                    ingredient.cas_numbers ? ingredient.cas_numbers.join(', ') : '',
                    formatFunctions(ingredient.functions),
                    formatSafetyScore(ingredient.safety_score),
                    ingredient.origin || 'Not specified',
                    '...', // Top Product Usage
                    '...', // Sentiment
                    '...', // Popular Forms
                    '...', // Body Parts
                    '...', // Key Insights
                    `<button class="detail-btn" data-slug="${ingredient.slug}">View</button>`
                ]);
                table.rows.add(rowData).draw();
                loadDetailedDataForVisibleRows();
                $('#loading-indicator').hide();
            })
            .catch(error => {
                console.error('Error loading ingredient data:', error);
                $('#loading-indicator').hide();
                alert('Failed to load ingredient data. Please try again later.');
            });
    }
    // --- Throttled fetch and cache for ingredient details ---
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

    function loadDetailedDataForVisibleRows() {
        const visibleRows = table.rows({page: 'current'}).nodes();
        $(visibleRows).each(function() {
            const row = table.row(this);
            const rowData = row.data();
            const detailBtn = $(rowData[10]);
            const slug = detailBtn.data('slug');
            if (rowData[5] === '...') {
                getIngredientDetail(slug, `data/ingredients/${slug}.json`)
                    .then(data => {
                        // Top Product Usage
                        if (data.product_usage_data && data.product_usage_data.by_product_type && data.product_usage_data.by_product_type.length > 0) {
                            const topProduct = data.product_usage_data.by_product_type[0];
                            rowData[5] = `${topProduct.product_type}: ${topProduct.usage_percentage}%`;
                        } else {
                            rowData[5] = 'N/A';
                        }
                        // Sentiment
                        if (data.reddit_community_analysis && data.reddit_community_analysis.sentiment_analysis) {
                            const sentiment = data.reddit_community_analysis.sentiment_analysis.overall_sentiment;
                            rowData[6] = `<span class="sentiment-${sentiment ? sentiment.toLowerCase() : 'neutral'}">${sentiment || 'N/A'}</span>`;
                        } else {
                            rowData[6] = 'N/A';
                        }
                        // Popular Forms
                        if (data.reddit_community_analysis && data.reddit_community_analysis.product_forms && data.reddit_community_analysis.product_forms.length > 0) {
                            const topForms = data.reddit_community_analysis.product_forms.slice(0, 3).map(f => f.form).join(', ');
                            rowData[7] = topForms;
                        } else {
                            rowData[7] = 'N/A';
                        }
                        // Body Parts
                        if (data.reddit_community_analysis && data.reddit_community_analysis.body_parts_usage && data.reddit_community_analysis.body_parts_usage.length > 0) {
                            const topParts = data.reddit_community_analysis.body_parts_usage.slice(0, 3).map(p => p.body_part).join(', ');
                            rowData[8] = topParts;
                        } else {
                            rowData[8] = 'N/A';
                        }
                        // Key Insights
                        if (data.reddit_community_analysis && data.reddit_community_analysis.key_insights && data.reddit_community_analysis.key_insights.length > 0) {
                            rowData[9] = data.reddit_community_analysis.key_insights[0];
                        } else {
                            rowData[9] = 'N/A';
                        }
                        row.data(rowData).draw(false);
                    })
                    .catch(error => {
                        console.error(`Error loading detailed data for ${slug}:`, error);
                        rowData[5] = rowData[6] = rowData[7] = rowData[8] = rowData[9] = 'N/A';
                        row.data(rowData).draw(false);
                    });
            }
        });
    }
    $('#ingredients-table').on('draw.dt', function() {
        loadDetailedDataForVisibleRows();
    });
    loadIngredientData();

    // Advanced filtering
    function setupAdvancedFilters() {
        $('#toggle-advanced-filters').on('click', function() {
            $('#advanced-filters-container').slideToggle();
            $(this).text(function(_, text) {
                return text === 'Advanced Filters ▼' ? 'Advanced Filters ▲' : 'Advanced Filters ▼';
            });
        });
        fetch('data/index.json')
            .then(response => response.json())
            .then(data => {
                const allFunctions = new Set();
                data.ingredients.forEach(ingredient => {
                    if (ingredient.functions && Array.isArray(ingredient.functions)) {
                        ingredient.functions.forEach(func => {
                            if (typeof func === 'string' && func.length < 50) {
                                allFunctions.add(func);
                            }
                        });
                    }
                });
                const functionFilter = $('#function-filter');
                [...allFunctions].sort().forEach(func => {
                    functionFilter.append(`<option value="${func}">${func}</option>`);
                });
                if (functionFilter.select2) {
                    functionFilter.select2({ placeholder: 'Select functions', width: '100%' });
                }
            });
        $('#apply-advanced-filters').on('click', function() {
            const safetyFilter = $('#safety-filter').val();
            $.fn.dataTable.ext.search = $.fn.dataTable.ext.search.filter(fn => !fn._isAdvancedSafety);
            if (safetyFilter) {
                if (safetyFilter.includes('-')) {
                    const [min, max] = safetyFilter.split('-').map(Number);
                    const fn = function(settings, data, dataIndex) {
                        const score = parseInt(data[3].replace(/\D/g, '')) || 0;
                        return score >= min && score <= max;
                    };
                    fn._isAdvancedSafety = true;
                    $.fn.dataTable.ext.search.push(fn);
                } else {
                    table.column(3).search(`^${safetyFilter}$`, true, false);
                }
            } else {
                table.column(3).search('');
            }
            const originFilter = $('#origin-filter').val();
            if (originFilter) {
                table.column(4).search(originFilter);
            } else {
                table.column(4).search('');
            }
            const selectedFunctions = $('#function-filter').val();
            if (selectedFunctions && selectedFunctions.length > 0) {
                const functionRegex = selectedFunctions.map(f => f.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('|');
                table.column(2).search(functionRegex, true, false);
            } else {
                table.column(2).search('');
            }
            table.draw();
        });
        $('#reset-advanced-filters').on('click', function() {
            $('#safety-filter').val('');
            $('#origin-filter').val('');
            $('#function-filter').val(null).trigger('change');
            table.search('').columns().search('').draw();
            $.fn.dataTable.ext.search = [];
        });
    }
    setupAdvancedFilters();

    // Detail modal logic
    function setupDetailModal() {
        $('#ingredients-table').on('click', '.detail-btn', function() {
            const slug = $(this).data('slug');
            showIngredientDetail(slug);
        });
        $('.close, .modal').on('click', function(event) {
            if (event.target === this) {
                $('.modal').hide();
            }
        });
        $('.tab-btn').on('click', function() {
            $('.tab-btn').removeClass('active');
            $(this).addClass('active');
            $('.tab-content').removeClass('active');
            $(`#tab-${$(this).data('tab')}`).addClass('active');
        });
    }
    setupDetailModal();
    function showIngredientDetail(slug) {
        fetch(`data/ingredients/${slug}.json`)
            .then(response => response.json())
            .then(data => {
                $('#modal-title').text(data.ingredient_overview.inci_name);
                $('#tab-overview').html(`
                    <table class="detail-table">
                        <tr><th>INCI Name</th><td>${data.ingredient_overview.inci_name}</td></tr>
                        <tr><th>CAS Number(s)</th><td>${data.ingredient_overview.cas_numbers ? data.ingredient_overview.cas_numbers.join(', ') : 'Not available'}</td></tr>
                        <tr><th>Functions</th><td>${formatFunctions(data.ingredient_overview.functions)}</td></tr>
                        <tr><th>Origin</th><td>${data.ingredient_overview.origin || 'Not specified'}</td></tr>
                        <tr><th>Description</th><td>${data.ingredient_overview.description || 'No description available'}</td></tr>
                    </table>
                `);
                $('#tab-safety').html(`
                    <div class="safety-score safety-${data.safety_information.safety_score}">
                        <h3>Safety Score</h3>
                        <div class="score">${data.safety_information.safety_score}</div>
                    </div>
                    <p><strong>Assessment:</strong> ${data.safety_information.assessment || 'No assessment available'}</p>
                `);
                if (data.product_usage_data && data.product_usage_data.by_product_type && data.product_usage_data.by_product_type.length > 0) {
                    let usageHtml = '<table class="detail-table"><thead><tr><th>Product Type</th><th>Usage %</th><th>Sample Size</th></tr></thead><tbody>';
                    data.product_usage_data.by_product_type.forEach(item => {
                        usageHtml += `<tr><td>${item.product_type}</td><td>${item.usage_percentage}%</td><td>${item.sample_size}</td></tr>`;
                    });
                    usageHtml += '</tbody></table>';
                    $('#tab-usage').html(usageHtml);
                } else {
                    $('#tab-usage').html('<p>No product usage data available</p>');
                }
                if (data.reddit_community_analysis) {
                    const reddit = data.reddit_community_analysis;
                    let redditHtml = `
                        <div class="reddit-overview">
                            <p><strong>Posts Analyzed:</strong> ${reddit.overview ? reddit.overview.total_posts_analyzed : 'N/A'}</p>
                            <p><strong>Overall Sentiment:</strong> <span class="sentiment-${reddit.sentiment_analysis ? reddit.sentiment_analysis.overall_sentiment.toLowerCase() : 'neutral'}">${reddit.sentiment_analysis ? reddit.sentiment_analysis.overall_sentiment : 'N/A'}</span></p>
                        </div>
                    `;
                    if (reddit.product_forms && reddit.product_forms.length > 0) {
                        redditHtml += '<h3>Product Forms</h3><ul>';
                        reddit.product_forms.slice(0, 5).forEach(form => {
                            redditHtml += `<li>${form.form} (${form.mentions} mentions)</li>`;
                        });
                        redditHtml += '</ul>';
                    }
                    if (reddit.body_parts_usage && reddit.body_parts_usage.length > 0) {
                        redditHtml += '<h3>Body Parts</h3><ul>';
                        reddit.body_parts_usage.slice(0, 5).forEach(part => {
                            redditHtml += `<li>${part.body_part} (${part.mentions} mentions)</li>`;
                        });
                        redditHtml += '</ul>';
                    }
                    if (reddit.key_insights && reddit.key_insights.length > 0) {
                        redditHtml += '<h3>Key Insights</h3><ul>';
                        reddit.key_insights.forEach(insight => {
                            redditHtml += `<li>${insight}</li>`;
                        });
                        redditHtml += '</ul>';
                    }
                    $('#tab-reddit').html(redditHtml);
                } else {
                    $('#tab-reddit').html('<p>No Reddit analysis available</p>');
                }
                $('#ingredient-modal').show();
            })
            .catch(error => {
                console.error(`Error loading ingredient detail for ${slug}:`, error);
                alert('Failed to load ingredient detail. Please try again later.');
            });
    }
    // Helper functions
    function formatFunctions(functions) {
        if (!functions || !Array.isArray(functions)) {
            return 'Not specified';
        }
        // Truncate long lists, add tooltip for full list
        const valid = functions.filter(f => typeof f === 'string' && f.length < 50);
        if (valid.length === 0) return 'Not specified';
        const display = valid.slice(0, 3).join(', ');
        const tooltip = valid.join(', ');
        return valid.length > 3
            ? `<span title="${tooltip}">${display} &hellip;</span>`
            : display;
    }
    function formatSafetyScore(score) {
        if (score === null || score === undefined) {
            return '<span class="safety-unknown">Unknown</span>';
        }
        return `<span class="safety-${score}">${score}</span>`;
    }
}); 