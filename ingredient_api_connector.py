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
    """Extract data for a single ingredient and save to new files"""
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
    
    # Step 2: Store search results
    search_rows = []
    for doc in docs:
        doc_row = doc.copy()
        doc_row['search_keyword'] = ingredient_name
        search_rows.append(doc_row)
    
    # Write search results to new CSV
    if search_rows:
        search_fieldnames = list(search_rows[0].keys())
        search_filename = f"{output_prefix}_search_results.csv"
        with open(search_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=search_fieldnames)
            writer.writeheader()
            for row in search_rows:
                writer.writerow(row)
        print(f"Search results written to {search_filename} ({len(search_rows)} rows)")
    
    # Step 3: Extract detailed information
    detail_rows = []
    all_fieldnames = set(SCALAR_FIELDS)
    
    for row in search_rows:
        ingredient_id = row.get('identifier')
        if not ingredient_id:
            continue
        
        try:
            info = get_ingredient_info(ingredient_id)
        except Exception as e:
            print(f"Error fetching info for ID {ingredient_id}: {e}")
            continue
        
        # Log the full JSON response to a new txt file
        log_filename = f"{output_prefix}_json_log.txt"
        with open(log_filename, 'w', encoding='utf-8') as logf:
            logf.write(f"ID: {ingredient_id}\n")
            logf.write(json.dumps(info, ensure_ascii=False, indent=2))
            logf.write("\n\n")
        
        # Flatten all fields recursively
        base_row = {
            field: info.get(field, '') if field != 'search_keyword' 
            else row.get('search_keyword', '') 
            for field in SCALAR_FIELDS
        }
        flat_row = flatten(info, '', '_', MAX_ARRAY, MAX_DEPTH, 0)
        base_row.update(flat_row)
        detail_rows.append(base_row)
        all_fieldnames.update(base_row.keys())
    
    # Compose the full header in the desired order
    all_fieldnames = list(SCALAR_FIELDS) + [f for f in sorted(all_fieldnames) if f not in SCALAR_FIELDS]
    
    # Write details to new CSV
    if detail_rows:
        details_filename = f"{output_prefix}_details.csv"
        with open(details_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=all_fieldnames)
            writer.writeheader()
            for row in detail_rows:
                writer.writerow(row)
        print(f"Detailed ingredient info written to {details_filename} ({len(detail_rows)} rows)")
    else:
        print("No ingredient details found.")


def main():
    # Extract data for cocamidopropyl
    extract_single_ingredient("cocamidopropyl", "cocamidopropyl")


if __name__ == "__main__":
    main() 