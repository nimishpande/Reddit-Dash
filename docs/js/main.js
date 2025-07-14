$(document).ready(function() {
    let ingredientsTable;

    // Initialize the table with minimal configuration first
    ingredientsTable = $('#ingredients-table').DataTable({
        processing: true,
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100], [10, 25, 50, 100]],
        deferRender: true,
        scrollX: true,
        dom: 'Blfrtip',
        buttons: [
            'copy', 'csv', 'excel',
            {
                extend: 'colvis',
                text: 'Show/Hide Columns'
            }
        ],
        columnDefs: [
            { targets: [11], visible: false } // Hide slug column
        ]
    });

    // Load data incrementally to prevent memory issues
    loadIngredientsData();

    function loadIngredientsData() {
        $('#loading-indicator').show();
        fetch('data/index.json')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Failed to load index data');
                }
                return response.json();
            })
            .then(data => {
                const chunkSize = 20;
                const ingredients = data.ingredients;
                for (let i = 0; i < ingredients.length; i += chunkSize) {
                    const chunk = ingredients.slice(i, i + chunkSize);
                    setTimeout(() => {
                        processIngredientChunk(chunk, i, ingredients.length);
                    }, (i / chunkSize) * 100);
                }
            })
            .catch(error => {
                console.error('Error loading ingredients data:', error);
                $('#loading-indicator').hide();
                $('#error-message').text('Failed to load ingredients data: ' + error.message).show();
            });
    }

    function processIngredientChunk(ingredients, startIndex, totalCount) {
        const rows = [];
        ingredients.forEach(ingredient => {
            const rowData = createRowData(ingredient);
            rows.push(rowData);
            loadDetailedData(ingredient.slug);
        });
        ingredientsTable.rows.add(rows).draw(false);
        if (startIndex + ingredients.length >= totalCount) {
            $('#loading-indicator').hide();
        }
    }

    function createRowData(ingredient) {
        return [
            ingredient.inci_name,
            formatCASNumbers(ingredient.cas_numbers),
            formatFunctions(ingredient.functions),
            formatSafetyScore(ingredient.safety_score),
            ingredient.origin || 'N/A',
            'Loading...', // Top product usage
            'Loading...', // Sentiment
            'Loading...', // Common forms
            'Loading...', // Body parts
            'Loading...', // Positive benefits
            'Loading...', // Negative concerns
            ingredient.slug // Hidden slug for reference
        ];
    }

    function loadDetailedData(slug) {
        fetch(`data/ingredients/${slug}.json`)
            .then(response => {
                if (!response.ok) {
                    throw new Error(`Failed to load data for ${slug}`);
                }
                return response.json();
            })
            .then(data => {
                ingredientsTable.rows().every(function() {
                    const rowData = this.data();
                    if (rowData[11] === slug) {
                        const updatedData = updateRowWithDetailedData(rowData, data);
                        this.data(updatedData);
                        return false;
                    }
                    return true;
                });
                ingredientsTable.rows().invalidate().draw(false);
            })
            .catch(error => {
                console.error(`Error loading detailed data for ${slug}:`, error);
            });
    }

    function updateRowWithDetailedData(rowData, detailData) {
        const newData = [...rowData];
        // Top Product Usage
        if (detailData.product_usage_data && detailData.product_usage_data.by_product_type && detailData.product_usage_data.by_product_type.length > 0) {
            const topProduct = detailData.product_usage_data.by_product_type[0];
            newData[5] = `${topProduct.product_type}: ${topProduct.usage_percentage}%`;
        } else {
            newData[5] = 'N/A';
        }
        // Sentiment
        if (detailData.reddit_community_analysis && detailData.reddit_community_analysis.sentiment_analysis) {
            const sentiment = detailData.reddit_community_analysis.sentiment_analysis.overall_sentiment;
            newData[6] = `<span class="sentiment-${sentiment.toLowerCase()}">${sentiment}</span>`;
        } else {
            newData[6] = 'N/A';
        }
        // Common Forms
        if (detailData.reddit_community_analysis && detailData.reddit_community_analysis.product_forms && detailData.reddit_community_analysis.product_forms.length > 0) {
            const forms = detailData.reddit_community_analysis.product_forms.slice(0, 3).map(form => `${form.form} (${form.mentions})`).join(', ');
            newData[7] = forms;
        } else {
            newData[7] = 'N/A';
        }
        // Body Parts
        if (detailData.reddit_community_analysis && detailData.reddit_community_analysis.body_parts_usage && detailData.reddit_community_analysis.body_parts_usage.length > 0) {
            const parts = detailData.reddit_community_analysis.body_parts_usage.slice(0, 3).map(part => `${part.body_part} (${part.mentions})`).join(', ');
            newData[8] = parts;
        } else {
            newData[8] = 'N/A';
        }
        // Positive Benefits
        if (detailData.reddit_community_analysis && detailData.reddit_community_analysis.sentiment_analysis && detailData.reddit_community_analysis.sentiment_analysis.positive_benefits) {
            const benefits = detailData.reddit_community_analysis.sentiment_analysis.positive_benefits;
            if (benefits.key_positive_themes && benefits.key_positive_themes.length > 0) {
                const topBenefits = benefits.key_positive_themes.slice(0, 2).join(', ');
                newData[9] = topBenefits;
            } else {
                newData[9] = benefits.total_positive_statements > 0 ? `${benefits.total_positive_statements} positive statements` : 'None';
            }
        } else {
            newData[9] = 'N/A';
        }
        // Negative Concerns
        if (detailData.reddit_community_analysis && detailData.reddit_community_analysis.sentiment_analysis && detailData.reddit_community_analysis.sentiment_analysis.negative_cons) {
            const cons = detailData.reddit_community_analysis.sentiment_analysis.negative_cons;
            if (cons.key_negative_themes && cons.key_negative_themes.length > 0) {
                const topCons = cons.key_negative_themes.slice(0, 2).join(', ');
                newData[10] = topCons;
            } else {
                newData[10] = cons.total_negative_statements > 0 ? `${cons.total_negative_statements} negative statements` : 'None';
            }
        } else {
            newData[10] = 'N/A';
        }
        return newData;
    }

    // Helper functions
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
        return validFunctions.join(', ');
    }
    function formatSafetyScore(score) {
        if (score === null || score === undefined) {
            return '<span class="safety-unknown">Unknown</span>';
        }
        return `<span class="safety-${score}">${score}</span>`;
    }
}); 