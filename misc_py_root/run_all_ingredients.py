#!/usr/bin/env python3
"""
Run enhanced sentiment analysis on all ingredients from empty_raw_data_ingredients.txt
"""

import os
import sys
import subprocess
import time

def read_ingredients_list(filename):
    """Read the list of ingredients from the file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            ingredients = [line.strip() for line in f if line.strip()]
        return ingredients
    except FileNotFoundError:
        print(f"❌ File not found: {filename}")
        return []
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return []

def run_ingredient_analysis(ingredient):
    """Run sentiment analysis for a single ingredient."""
    print(f"\n🔍 Processing: {ingredient}")
    print("-" * 50)
    
    try:
        result = subprocess.run([
            'python3', 'reddit_api_connector.py', ingredient
        ], capture_output=True, text=True, cwd=os.getcwd())
        
        if result.returncode == 0:
            print(f"✅ Successfully processed: {ingredient}")
            # Extract key metrics from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'Overall Sentiment:' in line:
                    print(f"   {line.strip()}")
                elif 'Significant Posts:' in line:
                    print(f"   {line.strip()}")
                elif 'Effectiveness Sentiment:' in line:
                    print(f"   {line.strip()}")
                elif 'Safety Sentiment:' in line:
                    print(f"   {line.strip()}")
                elif 'Enhanced results saved to' in line:
                    print(f"   {line.strip()}")
        else:
            print(f"❌ Failed to process: {ingredient}")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Exception processing {ingredient}: {e}")
        return False
    
    return True

def main():
    """Main function to run analysis on all ingredients."""
    # Read ingredients list
    ingredients_file = "../empty_raw_data_ingredients.txt"
    ingredients = read_ingredients_list(ingredients_file)
    
    if not ingredients:
        print("❌ No ingredients found to process")
        return
    
    print(f"🚀 Starting enhanced sentiment analysis for {len(ingredients)} ingredients")
    print("=" * 60)
    
    # Track progress
    successful = 0
    failed = 0
    failed_ingredients = []
    
    for i, ingredient in enumerate(ingredients, 1):
        print(f"\n[{i}/{len(ingredients)}] Processing: {ingredient}")
        
        if run_ingredient_analysis(ingredient):
            successful += 1
        else:
            failed += 1
            failed_ingredients.append(ingredient)
        
        # Add delay between requests to be respectful to Reddit API
        if i < len(ingredients):  # Don't sleep after the last one
            print("   ⏳ Waiting 3 seconds before next request...")
            time.sleep(3)
    
    # Summary
    print(f"\n" + "=" * 60)
    print(f"📊 BATCH PROCESSING SUMMARY")
    print(f"   Total Ingredients: {len(ingredients)}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   📈 Success Rate: {(successful/len(ingredients)*100):.1f}%")
    
    if failed_ingredients:
        print(f"\n❌ Failed Ingredients:")
        for ingredient in failed_ingredients:
            print(f"   - {ingredient}")
    
    print(f"\n🎉 Batch processing complete!")
    print(f"   📁 Results saved in: IngredientsScrapper/raw data/")

if __name__ == "__main__":
    main() 