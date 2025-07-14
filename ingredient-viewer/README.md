# Cosmetic Ingredient Database Viewer

A static site for browsing, searching, and visualizing cosmetic ingredient data, including INCI (International Nomenclature of Cosmetic Ingredients) and Reddit sentiment analysis.

## Overview

This site provides an interactive, searchable interface for exploring cosmetic ingredient data. Each ingredient includes:
- INCI name, CAS numbers, functions, origin, and description
- Safety score and assessment
- Product usage statistics
- Reddit community sentiment and analysis

## Features
- **Search and filter** by ingredient name or function
- **Alphabetical index** for quick navigation
- **Ingredient detail pages** with tabs for overview, safety, usage, and Reddit analysis
- **Interactive charts** (via Chart.js) for safety, usage, and sentiment
- **Mobile-friendly** design using Bulma CSS

## Data Format

- **`data/index.json`**: Main index of all ingredients (for search/list view)
- **`data/ingredients/{slug}.json`**: Detailed data for each ingredient

Example `index.json` entry:
```json
{
  "inci_name": "Caffeine",
  "cas_numbers": ["58-08-2"],
  "functions": ["Masking", "Skin conditioning", "Perfuming"],
  "safety_score": 0,
  "slug": "caffeine"
}
```

Example `ingredients/{slug}.json` structure:
```json
{
  "ingredient_overview": { ... },
  "safety_information": { ... },
  "product_usage_data": { ... },
  "reddit_community_analysis": { ... }
}
```

## Folder Structure
```
ingredient-viewer/
  index.html
  ingredient.html
  css/
    styles.css
  js/
    main.js
    detail.js
    visualizations.js
    search.js
  data/
    index.json
    ingredients/
      {slug}.json
```

## Local Development

1. Open `index.html` in your browser (no build step required).
2. For local development with AJAX (fetch), you may need to run a local server:
   - Python 3: `python3 -m http.server 8000`
   - Node: `npx serve .`
3. Navigate to `http://localhost:8000/ingredient-viewer/`.

## Deployment (GitHub Pages)

1. Commit and push the `ingredient-viewer/` folder to your repository.
2. In your repository settings, set GitHub Pages to serve from the `ingredient-viewer/` folder (or `/docs` if you move it).
3. Access your site at `https://<username>.github.io/<repo>/ingredient-viewer/`.

---

**Data and code are open-source.**

For questions or contributions, open an issue or pull request. 