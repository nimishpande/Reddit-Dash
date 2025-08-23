import os
import sys
import json
import subprocess

INGREDIENT_LIST = 'ingredient.txt'
RAW_DATA_DIR = 'IngredientsScrapper/raw data'
REDDIT_ANALYSIS_DIR = 'IngredientsScrapper/reddit analysis'
ANALYSIS_SCRIPT = 'unified_ingredient_analysis.py'

os.makedirs(REDDIT_ANALYSIS_DIR, exist_ok=True)

def normalize(s):
    return s.lower().replace(' ', '').replace('_', '')

def find_matching_json(ingredient):
    target_norm = normalize(ingredient)
    for fname in os.listdir(RAW_DATA_DIR):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(RAW_DATA_DIR, fname)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            ing = data.get('ingredient', '')
            if normalize(ing) == target_norm:
                return path, ing
        except Exception as e:
            print(f"[WARN] Could not read {fname}: {e}")
    return None, None

def main():
    with open(INGREDIENT_LIST, 'r', encoding='utf-8') as f:
        ingredients = [line.strip() for line in f if line.strip()]
    missing = []
    for idx, ingredient in enumerate(ingredients, 1):
        print(f"\n[{idx}/{len(ingredients)}] Processing: {ingredient}")
        json_path, canonical_inci = find_matching_json(ingredient)
        if not json_path:
            print(f"[ERROR] No JSON file found for {ingredient} (by ingredient field)")
            missing.append(ingredient)
            continue
        print(f"[INFO] Using JSON file: {json_path}")
        # Run unified_ingredient_analysis.py
        try:
            subprocess.run([
                sys.executable, ANALYSIS_SCRIPT, canonical_inci, json_path
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f"[FATAL] Analysis failed for {ingredient}: {e}")
            continue
        # Move the .txt report to the reddit analysis folder
        report_name = f"{canonical_inci.replace(' ', '_').replace('/', '_')}_comprehensive_report.txt"
        src_report = os.path.join('.', report_name)
        dst_report = os.path.join(REDDIT_ANALYSIS_DIR, report_name)
        if os.path.exists(src_report):
            os.replace(src_report, dst_report)
            print(f"[OK] Moved report to {dst_report}")
        else:
            print(f"[ERROR] Expected report {src_report} not found!")
    if missing:
        print(f"\n[SUMMARY] Missing JSON files for {len(missing)} ingredients:")
        for m in missing:
            print(f" - {m}")
    print("\n[INFO] All ingredients processed.")

if __name__ == "__main__":
    main() 