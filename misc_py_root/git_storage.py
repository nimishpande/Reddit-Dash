#!/usr/bin/env python3
"""
Git Storage for Reddit Monitoring Files
Simple local storage with git commits
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
LOCAL_MONITORING_DIR = 'reddit_monitoring'

def git_commit_files():
    """Commit monitoring files to git"""
    print("🚀 Starting Git storage...")
    
    try:
        # Check if we're in a git repository
        result = subprocess.run(['git', 'rev-parse', '--git-dir'], 
                              capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Not in a git repository")
            return False
        
        # Add all files in monitoring directory
        subprocess.run(['git', 'add', LOCAL_MONITORING_DIR], check=True)
        
        # Check if there are changes to commit
        result = subprocess.run(['git', 'diff', '--cached', '--name-only'], 
                              capture_output=True, text=True)
        
        if not result.stdout.strip():
            print("ℹ️ No changes to commit")
            return True
        
        # Commit with timestamp
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        commit_message = f"Update Reddit monitoring data - {timestamp}"
        
        subprocess.run(['git', 'commit', '-m', commit_message], check=True)
        print(f"✅ Committed: {commit_message}")
        
        # Push to remote (optional)
        try:
            subprocess.run(['git', 'push'], check=True)
            print("✅ Pushed to remote repository")
        except subprocess.CalledProcessError:
            print("⚠️ Could not push to remote (files still committed locally)")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Git storage failed: {e}")
        return False

def main():
    """Main function"""
    success = git_commit_files()
    
    if success:
        print("\n🎉 Files stored in git successfully!")
    else:
        print("\n❌ Git storage failed. Check the error messages above.")

if __name__ == "__main__":
    main()
