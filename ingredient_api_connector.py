import os
import requests
import hmac
import hashlib
from urllib.parse import quote
from dotenv import load_dotenv
import csv
import json

# Load credentials and config from .env
load_dotenv()
ACCESS_KEY_ID = os.getenv('ACCESS_KEY_ID')
SECRET_KEY = os.getenv('SECRET_KEY')
print(f"ACCESS_KEY_ID loaded: {ACCESS_KEY_ID}")
print(f"SECRET_KEY loaded: {SECRET_KEY[:4]}...{SECRET_KEY[-4:] if SECRET_KEY else ''}")
BASE_URL = 'https://api.incibeauty.com'
try:
    MAX_ARRAY = int(os.getenv('MAX_ARRAY', 3))
except Exception:
    MAX_ARRAY = 3
try:
    MAX_DEPTH = int(os.getenv('MAX_DEPTH', 2))
except Exception:
    MAX_DEPTH = 2

# Define scalar fields in desired order
SCALAR_FIELDS = [
    'search_keyword', 'id', 'inci_name', 'name', 'description', 'regulation', 'reference',
    'cheminical_iupac_name', 'cas', 'einecs_elincs', 'cosmetic_restriction', 'score', 'percentage'
]


def generate_hmac(path: str, secret_key: str) -> str:
    return hmac.new(
        secret_key.encode('utf-8'),
        path.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()


def search_ingredient(keyword):
    encoded_keyword = quote(keyword)
    path = f"/ingredient/search/{encoded_keyword}?accessKeyId={ACCESS_KEY_ID}"
    hmac_signature = generate_hmac(path, SECRET_KEY)
    url = f"{BASE_URL}{path}&hmac={hmac_signature}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def get_ingredient_info(ingredient_id, locale='en_GB'):
    path = (
        f"/ingredient/{ingredient_id}?locale={locale}&accessKeyId={ACCESS_KEY_ID}"
    )
    hmac_signature = generate_hmac(path, SECRET_KEY)
    url = f"{BASE_URL}{path}&hmac={hmac_signature}"
    resp = requests.get(url)
    resp.raise_for_status()
    return resp.json()


def read_ingredient_keywords(filename='ingredient.txt'):
    with open(filename, 'r', encoding='utf-8') as f:
        return [line.strip() for line in f if line.strip()]


def flatten(obj, parent_key='', sep='_', max_array=3, max_depth=2, depth=0):
    items = {}
    if depth > max_depth:
        return items
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            items.update(flatten(v, new_key, sep, max_array, max_depth, depth + 1))
    elif isinstance(obj, list):
        for i in range(min(len(obj), max_array)):
            v = obj[i]
            new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
            items.update(flatten(v, new_key, sep, max_array, max_depth, depth + 1))
    else:
        items[parent_key] = obj
    return items


def extract_single_ingredient(ingredient_name, output_prefix="magnesium_ascorbyl"):
    """Extract data for a single ingredient and save as a single JSON file in separated_ingredients folder, named after the canonical INCI name."""
    import re
    output_dir = "/Users/nimishpande/Ingredient_cosmetic/IngredientsScrapper/separated_ingredients"
    os.makedirs(output_dir, exist_ok=True)
    print(f"Searching for ingredient: {ingredient_name}")
    
    # Step 1: Search for the ingredient
    try:
        search_result = search_ingredient(ingredient_name)
    except Exception as e:
        print(f"Error searching for {ingredient_name}: {e}")
        return
    
    docs = search_result.get('docs', [])
    if not docs:
        print(f"No results found for {ingredient_name}")
        return
    
    search_results = []
    detailed_info = []
    for doc in docs:
        search_results.append(doc)
        ingredient_id = doc.get('identifier')
        try:
            info = get_ingredient_info(ingredient_id)
            detailed_info.append(info)
        except Exception as e:
            print(f"Error fetching info for ID {ingredient_id}: {e}")
            continue
    # Compose output dict
    output = {
        "ingredient": ingredient_name,
        "search_results": search_results,
        "detailed_info": detailed_info
    }
    # Use canonical INCI name for filename if available
    canonical_inci = docs[0].get('inci_name') or ingredient_name
    safe_name = canonical_inci.replace('/', '_').replace('\\', '_')
    out_path = os.path.join(output_dir, f"{safe_name}.json")
    print(f"[INFO] Writing file as: {out_path}")
    try:
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        print(f"[OK] Wrote {out_path}")
    except Exception as e:
        print(f"[ERROR] Could not write {out_path}: {e}")


def main():
    # Read all ingredient names from ingredient.txt in the root directory
    input_file = "ingredient.txt"
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            ingredients = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"[ERROR] Could not read {input_file}: {e}")
        return
    print(f"[INFO] Processing {len(ingredients)} ingredients from {input_file}...")
    for idx, ingredient in enumerate(ingredients, 1):
        print(f"\n[{idx}/{len(ingredients)}] Processing: {ingredient}")
        try:
            extract_single_ingredient(ingredient, ingredient)
        except Exception as e:
            print(f"[FATAL] Error processing {ingredient}: {e}")
            print("Aborting batch.")
            return
    print("\n[INFO] All ingredients processed.")


if __name__ == "__main__":
    main() 