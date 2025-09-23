#!/usr/bin/env python3
"""
Account Analysis Script for GitHub Actions
Analyzes Reddit accounts based on usernames.json configuration
"""

import json
import subprocess
import sys
import os

def main():
    """Main function to analyze accounts from usernames.json"""
    try:
        # Load usernames configuration
        with open('config/usernames.json', 'r') as f:
            config = json.load(f)

        usernames = config.get('usernames', [])
        comments_limit = config.get('analysis_settings', {}).get('comments_limit', 100)

        print(f'📊 Found {len(usernames)} usernames to analyze')

        for username in usernames:
            print(f'🔍 Analyzing u/{username}...')
            try:
                result = subprocess.run([
                    'python3', 'scripts/account_analyzer.py', 
                    username, str(comments_limit)
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print(f'✅ Analysis complete for u/{username}')
                else:
                    print(f'⚠️ Analysis failed for u/{username}: {result.stderr}')
            except Exception as e:
                print(f'❌ Error analyzing u/{username}: {e}')
                
    except FileNotFoundError:
        print("❌ config/usernames.json not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error loading configuration: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
