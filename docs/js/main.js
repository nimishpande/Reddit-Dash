// Global variables
const API_BASE_URL = 'data/';
let allIngredients = [];
let uniqueFunctions = new Set();
let currentSafetyScore = null;

document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('ingredients-list')) {
        initializeIndexPage();
    } else if (document.getElementById('ingredient-detail')) {
        initializeDetailPage();
    }
    const lastUpdatedEl = document.getElementById('last-updated');
    if (lastUpdatedEl) {
        lastUpdatedEl.textContent = new Date().toLocaleDateString();
    }
});

function initializeIndexPage() {
    fetch(`${API_BASE_URL}index.json`)
        .then(response => response.json())
        .then(data => {
            allIngredients = data.ingredients;
            allIngredients.forEach(ingredient => {
                if (ingredient.functions && Array.isArray(ingredient.functions)) {
                    ingredient.functions.forEach(func => uniqueFunctions.add(func));
                }
            });
            populateFunctionFilter();
            createAlphabeticalIndex();
            displayIngredients(allIngredients);
            initializeSearchAndFilters();
        })
        .catch(error => {
            console.error('Error loading ingredient index:', error);
            document.getElementById('ingredients-list').innerHTML = 
                `<div class="column is-full"><div class="notification is-danger">
                    Error loading ingredients. Please try again later.
                </div></div>`;
        });
}

function populateFunctionFilter() {
    const filterElement = document.getElementById('function-filter');
    if (!filterElement) return;
    while (filterElement.options.length > 1) {
        filterElement.remove(1);
    }
    Array.from(uniqueFunctions).sort().forEach(func => {
        const option = document.createElement('option');
        option.value = func;
        option.textContent = func;
        filterElement.appendChild(option);
    });
}

function createAlphabeticalIndex() {
    const alphaButtonsContainer = document.getElementById('alpha-buttons');
    if (!alphaButtonsContainer) return;
    for (let i = 65; i <= 90; i++) {
        const letter = String.fromCharCode(i);
        const button = document.createElement('a');
        button.href = '#';
        button.textContent = letter;
        button.dataset.letter = letter;
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const letterIngredients = allIngredients.filter(ingredient => 
                ingredient.inci_name && ingredient.inci_name.charAt(0).toUpperCase() === letter
            );
            displayIngredients(letterIngredients);
            document.querySelectorAll('.alpha-buttons a').forEach(el => {
                el.classList.remove('active');
            });
            this.classList.add('active');
        });
        alphaButtonsContainer.appendChild(button);
    }
    const allButton = document.createElement('a');
    allButton.href = '#';
    allButton.textContent = 'All';
    allButton.addEventListener('click', function(e) {
        e.preventDefault();
        displayIngredients(allIngredients);
        document.querySelectorAll('.alpha-buttons a').forEach(el => {
            el.classList.remove('active');
        });
    });
    alphaButtonsContainer.appendChild(allButton);
}

function displayIngredients(ingredients) {
    const container = document.getElementById('ingredients-list');
    if (!container) return;
    container.innerHTML = '';
    if (ingredients.length === 0) {
        container.innerHTML = `
            <div class="column is-full">
                <div class="notification is-warning">
                    No ingredients found matching your criteria.
                </div>
            </div>
        `;
        return;
    }
    ingredients.sort((a, b) => a.inci_name.localeCompare(b.inci_name));
    ingredients.forEach(ingredient => {
        const slug = slugify(ingredient.inci_name);
        const safetyClass = `safety-${ingredient.safety_score || 0}`;
        const column = document.createElement('div');
        column.className = 'column is-one-third-desktop is-half-tablet';
        column.innerHTML = `
            <div class="card ingredient-card">
                <div class="card-content">
                    <div class="content">
                        <h4 class="title is-4">
                            <a href="ingredient.html?id=${slug}">${ingredient.inci_name}</a>
                        </h4>
                        <p>
                            <span class="safety-badge ${safetyClass}">
                                Safety: ${ingredient.safety_score !== undefined && ingredient.safety_score !== null ? ingredient.safety_score : 'N/A'}
                            </span>
                        </p>
                        <p>
                            <strong>Functions:</strong> ${ingredient.functions ? ingredient.functions.join(', ') : 'Unknown'}
                        </p>
                    </div>
                </div>
                <footer class="card-footer">
                    <a href="ingredient.html?id=${slug}" class="card-footer-item">View Details</a>
                </footer>
            </div>
        `;
        container.appendChild(column);
    });
}

function slugify(text) {
    return text
        .toString()
        .toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^\w-]+/g, '')
        .replace(/--+/g, '-')
        .trim();
}

function getUrlParameter(name) {
    const params = new URLSearchParams(window.location.search);
    return params.get(name);
}

function initializeSearchAndFilters() {
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    const functionFilter = document.getElementById('function-filter');
    const safetySlider = document.getElementById('safety-slider');
    const safetyValue = document.getElementById('safety-value');

    // Safety slider logic
    if (safetySlider && safetyValue) {
        safetySlider.addEventListener('input', function() {
            const val = safetySlider.value;
            safetyValue.textContent = val === '0' ? 'Any' : val;
            currentSafetyScore = val === '0' ? null : parseInt(val);
            filterAndDisplay();
        });
    }

    // Function filter logic
    if (functionFilter) {
        functionFilter.addEventListener('change', filterAndDisplay);
    }

    // Search logic
    if (searchInput) {
        searchInput.addEventListener('input', filterAndDisplay);
    }
    if (searchButton) {
        searchButton.addEventListener('click', filterAndDisplay);
    }
}

function filterAndDisplay() {
    const searchInput = document.getElementById('search-input');
    const functionFilter = document.getElementById('function-filter');
    const safetySlider = document.getElementById('safety-slider');
    let filtered = allIngredients;
    // Search
    if (searchInput && searchInput.value.trim()) {
        const query = searchInput.value.trim().toLowerCase();
        filtered = filtered.filter(ingredient =>
            ingredient.inci_name && ingredient.inci_name.toLowerCase().includes(query)
        );
    }
    // Function filter
    if (functionFilter) {
        const selected = Array.from(functionFilter.selectedOptions).map(opt => opt.value).filter(Boolean);
        if (selected.length > 0) {
            filtered = filtered.filter(ingredient =>
                ingredient.functions && selected.some(f => ingredient.functions.includes(f))
            );
        }
    }
    // Safety filter
    if (safetySlider && safetySlider.value !== '0') {
        const score = parseInt(safetySlider.value);
        filtered = filtered.filter(ingredient => ingredient.safety_score === score);
    }
    displayIngredients(filtered);
} 