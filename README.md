# Ingredient & Reddit Data Extractor

This project extracts ingredient data from an API and fetches related Reddit posts for cosmetic ingredients. It supports recursive flattening of API/Reddit data and organizes results in a clean directory structure.

## Features
- Search for cosmetic ingredients via API
- Fetch Reddit posts mentioning ingredients (all of Reddit or specific subreddits)
- Save results as JSON and CSV, with recursive flattening
- Configurable via `.env` file

## Directory Structure
```
Ingredient_cosmetic/
  reddit_data/
    json/
      all_reddit/
        reddit_search_results.json
      subreddits/
        reddit_skincareaddiction_results.json
        reddit_asianbeauty_results.json
        reddit_acne_results.json
    csv/
      all_reddit/
        reddit_search_results.csv
      subreddits/
        reddit_skincareaddiction_results.csv
        reddit_asianbeauty_results.csv
        reddit_acne_results.csv
  requirements.txt
  .env
  reddit_api_connector.py
  json_to_csv_converter.py
```

## Setup
1. Clone the repo and navigate to the project directory.
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root with your API keys:
   ```
   REDDIT_CLIENT_ID=your_client_id
   REDDIT_CLIENT_SECRET=your_client_secret
   ```

## Usage
- **Reddit API Search:**
  ```
  python3 reddit_api_connector.py
  ```
  This will fetch posts for the default ingredient ("salicylic acid") and save results in the `reddit_data/json/` folders.

- **Convert JSON to CSV:**
  ```
  python3 json_to_csv_converter.py
  ```
  This will convert JSON files to CSV and save them in the corresponding `reddit_data/csv/` folders.

## Customization
- To search for a different ingredient, edit the query in `reddit_api_connector.py`.
- To add more subreddits, update the `skincare_subreddits` list in the script.

## Notes
- The script creates all necessary folders automatically.
- Only public Reddit data is fetched.
- For large-scale or automated use, consider Reddit API rate limits.

---
Feel free to extend the scripts for more advanced analysis or data sources!
