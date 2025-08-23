#!/usr/bin/env python3
"""
Setup Verification Script for Ingredient Data Processing
Run this first to ensure your environment is properly configured
"""

import json
import os
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def verify_setup():
    """Verify all required files and directories exist"""
    
    print("🔍 VERIFYING INGREDIENT DATA PROCESSING SETUP")
    print("=" * 60)
    
    issues = []
    
    # 1. Check directory structure
    required_dirs = [
        'IngredientsScrapper',
        'IngredientsScrapper/separated_ingredients',
        'IngredientsScrapper/raw data',
        'IngredientsScrapper/reddit analysis'
    ]
    
    print("\n📁 CHECKING DIRECTORY STRUCTURE:")
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} - MISSING")
            issues.append(f"Missing directory: {dir_path}")
    
    # 2. Check mapping file
    print("\n📋 CHECKING MAPPING FILE:")
    mapping_file = Path('IngredientsScrapper/ingredient_file_mapping_inci_centric.json')
    if mapping_file.exists():
        print(f"  ✅ {mapping_file}")
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            print(f"  📊 Found {len(mapping)} INCI ingredients in mapping")
        except Exception as e:
            print(f"  ⚠️ Error reading mapping file: {e}")
            issues.append(f"Mapping file error: {e}")
    else:
        print(f"  ❌ {mapping_file} - MISSING")
        issues.append("Missing INCI mapping file")
    
    # 3. Check test ingredients exist in mapping
    if mapping_file.exists():
        print("\n🧪 CHECKING TEST INGREDIENTS:")
        test_ingredients = [
            'XANTHAN GUM',
            'VITIS VINIFERA SEED OIL', 
            'URTICA DIOICA LEAF EXTRACT',
            'TRITICUM VULGARE GERM OIL',
            'ZINC PYRITHIONE',
            'ACETYL TETRAPEPTIDE-3'
        ]
        
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            for ingredient in test_ingredients:
                if ingredient in mapping:
                    print(f"  ✅ {ingredient}")
                else:
                    print(f"  ❌ {ingredient} - NOT IN MAPPING")
                    issues.append(f"Test ingredient not found: {ingredient}")
        except:
            pass
    
    # 4. Check for data files
    print("\n📄 CHECKING DATA FILES FOR TEST INGREDIENTS:")
    if mapping_file.exists():
        try:
            with open(mapping_file, 'r', encoding='utf-8') as f:
                mapping = json.load(f)
            
            test_ingredients = ['XANTHAN GUM', 'ZINC PYRITHIONE']  # Check a couple
            
            for ingredient in test_ingredients:
                if ingredient not in mapping:
                    continue
                    
                print(f"\n  🔍 {ingredient}:")
                ingredient_data = mapping[ingredient]
                
                # Check separated ingredient files
                for file in ingredient_data.get('separated_ingredient_files', []):
                    file_path = Path('IngredientsScrapper/separated_ingredients') / file
                    status = "✅" if file_path.exists() else "❌"
                    print(f"    {status} INCI data: {file}")
                
                # Check analysis files
                for file in ingredient_data.get('reddit_analysis_files', []):
                    found = False
                    for dir_name in ['separated_ingredients', 'reddit analysis']:
                        file_path = Path(f'IngredientsScrapper/{dir_name}') / file
                        if file_path.exists():
                            print(f"    ✅ Analysis: {file} (in {dir_name})")
                            found = True
                            break
                    if not found:
                        print(f"    ❌ Analysis: {file}")
                
                # Check raw data files
                for file in ingredient_data.get('raw_data_files', []):
                    file_path = Path('IngredientsScrapper/raw data') / file
                    status = "✅" if file_path.exists() else "❌"
                    print(f"    {status} Comments: {file}")
        except Exception as e:
            print(f"  ⚠️ Error checking data files: {e}")
    
    # 5. Check environment configuration
    print("\n🔑 CHECKING ENVIRONMENT:")
    env_files = ['.env', '../.env', '../../.env']
    env_found = False
    
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"  ✅ Found .env file: {env_file}")
            env_found = True
            
            # Check for OpenAI key
            try:
                with open(env_file, 'r') as f:
                    content = f.read()
                    if 'OPENAI' in content:
                        print(f"  ✅ OpenAI API key configured")
                    else:
                        print(f"  ⚠️ No OpenAI API key found in {env_file}")
                        issues.append("OpenAI API key not found in .env")
            except:
                pass
            break
    
    if not env_found:
        print(f"  ⚠️ No .env file found")
        print(f"  💡 Create .env with: OPENAI_API_KEY=your_key_here")
        issues.append("No .env file found")
    
    # Check environment variables
    api_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENAI_SECRET_KEY')
    if api_key:
        print(f"  ✅ OpenAI API key available in environment")
    else:
        print(f"  ⚠️ OpenAI API key not in environment variables")
    
    # 6. Summary
    print("\n" + "=" * 60)
    if issues:
        print("❌ SETUP ISSUES FOUND:")
        for issue in issues:
            print(f"  • {issue}")
        print(f"\n🔧 Please resolve {len(issues)} issues before running the main script")
    else:
        print("✅ SETUP VERIFICATION COMPLETE - Ready to process!")
        print("🚀 You can now run your ingredient processing script")
    
    print("=" * 60)
    return len(issues) == 0

if __name__ == "__main__":
    verify_setup() 