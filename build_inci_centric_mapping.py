import os
import json
import re
from collections import defaultdict
from difflib import get_close_matches

MAPPING_PATH = 'IngredientsScrapper/ingredient_file_mapping.json'
RAW_DATA_DIR = 'IngredientsScrapper/raw data'
OUTPUT_PATH = 'IngredientsScrapper/ingredient_file_mapping_inci_centric.json'

def normalize(s):
    return re.sub(r'[_\-\s]', '', s or '').lower()

def main():
    # 1. Load mapping and raw data filenames
    with open(MAPPING_PATH, 'r', encoding='utf-8') as f:
        mapping = json.load(f)
    raw_files = [f for f in os.listdir(RAW_DATA_DIR) if f.endswith('_all_comments.json')]
    normalized_raw = {normalize(f.replace('_all_comments.json', '')): f for f in raw_files}

    # 2. Build INCI-centric mapping
    inci_map = defaultdict(lambda: {
        'reddit_ingredient_names': [],
        'reddit_analysis_files': [],
        'separated_ingredient_files': [],
        'raw_data_files': []
    })

    for entry in mapping:
        inci = (entry.get('matched_json_inci_name') or '').strip().upper()
        if not inci:
            continue
        # Add mapping fields
        if entry.get('reddit_ingredient_name') and entry['reddit_ingredient_name'] not in inci_map[inci]['reddit_ingredient_names']:
            inci_map[inci]['reddit_ingredient_names'].append(entry['reddit_ingredient_name'])
        if entry.get('reddit_analysis_file') and entry['reddit_analysis_file'] not in inci_map[inci]['reddit_analysis_files']:
            inci_map[inci]['reddit_analysis_files'].append(entry['reddit_analysis_file'])
        if entry.get('separated_ingredient_file') and entry['separated_ingredient_file'] not in inci_map[inci]['separated_ingredient_files']:
            inci_map[inci]['separated_ingredient_files'].append(entry['separated_ingredient_file'])
        # Find raw data file
        base = entry.get('reddit_analysis_file', '').replace('_comprehensive_report.txt', '')
        norm_base = normalize(base)
        candidates = [fname for norm, fname in normalized_raw.items() if norm_base in norm or norm in norm_base]
        if not candidates:
            close = get_close_matches(norm_base, normalized_raw.keys(), n=1, cutoff=0.7)
            if close:
                candidates = [normalized_raw[close[0]]]
        for fname in candidates:
            if fname not in inci_map[inci]['raw_data_files']:
                inci_map[inci]['raw_data_files'].append(fname)
    # 3. Write new mapping
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(inci_map, f, indent=2)
    print(f"Wrote INCI-centric mapping to {OUTPUT_PATH}")

if __name__ == '__main__':
    main() 