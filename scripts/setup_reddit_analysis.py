#!/usr/bin/env python3
"""
Setup script for Reddit Activity Analysis
Helps you configure Reddit API credentials
"""

import os
import sys

def create_env_file():
    """Create .env file with Reddit API credentials"""
    print("🔧 Setting up Reddit Activity Analysis...")
    print()
    
    # Check if .env already exists
    if os.path.exists('.env'):
        print("⚠️  .env file already exists!")
        response = input("Do you want to overwrite it? (y/N): ").lower()
        if response != 'y':
            print("❌ Setup cancelled")
            return
    
    print("📋 To use Reddit Activity Analysis, you need Reddit API credentials.")
    print("   Follow these steps:")
    print()
    print("1. Go to https://www.reddit.com/prefs/apps")
    print("2. Click 'Create App' or 'Create Another App'")
    print("3. Choose 'script' as the app type")
    print("4. Fill in the details and create the app")
    print("5. Copy the client ID and secret")
    print()
    
    # Get credentials from user
    client_id = input("Enter your Reddit Client ID: ").strip()
    client_secret = input("Enter your Reddit Client Secret: ").strip()
    username = input("Enter your Reddit username: ").strip()
    password = input("Enter your Reddit password: ").strip()
    
    if not all([client_id, client_secret, username, password]):
        print("❌ All fields are required!")
        return
    
    # Create .env file
    env_content = f"""# Reddit API Credentials
REDDIT_CLIENT_ID={client_id}
REDDIT_CLIENT_SECRET={client_secret}
REDDIT_USER_AGENT=My Reddit Activity Tracker v1.0
REDDIT_USERNAME={username}
REDDIT_PASSWORD={password}
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("✅ .env file created successfully!")
    print()
    print("🚀 You can now run the Reddit activity analysis:")
    print("   python scripts/reddit_my_activity.py")
    print()
    print("💡 The analysis will show you:")
    print("   • Where you've commented (subreddits)")
    print("   • Which subreddits you're subscribed to")
    print("   • Your comment activity patterns")
    print("   • Recent comment history")

def main():
    """Main setup function"""
    print("="*60)
    print("🔧 REDDIT ACTIVITY ANALYSIS SETUP")
    print("="*60)
    print()
    
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n⏹️  Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")

if __name__ == "__main__":
    main()
