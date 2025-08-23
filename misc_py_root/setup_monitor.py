#!/usr/bin/env python3
"""
Reddit Monitor Setup Script
Helps configure the monitoring system for different subreddits
"""

import os
import sys
from pathlib import Path

def create_env_template():
    """Create .env template file"""
    env_content = """# Reddit API Credentials
# Get these from https://www.reddit.com/prefs/apps
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
"""
    
    env_file = Path('.env')
    if env_file.exists():
        print("⚠️  .env file already exists")
        return
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print("✅ Created .env template file")
    print("📝 Please edit .env with your Reddit API credentials")

def update_config():
    """Interactive configuration update"""
    print("\n🔧 Reddit Monitor Configuration")
    print("=" * 40)
    
    # Read current config
    config_file = Path('misc_py_root/monitor_config.py')
    if not config_file.exists():
        print("❌ Config file not found")
        return
    
    with open(config_file, 'r') as f:
        config_content = f.read()
    
    # Get user preferences
    print("\nCurrent settings:")
    print("1. Subreddit: skincareaddictsindia")
    print("2. Engagement Score: 7")
    print("3. Min Upvotes: 5")
    print("4. Min Comments: 2")
    print("5. Posts Limit: 50")
    print("6. Sort Method: new")
    
    print("\nWould you like to change any settings? (y/n): ", end='')
    if input().lower() != 'y':
        return
    
    # Get new subreddit
    print("\nEnter subreddit name (without r/): ", end='')
    new_subreddit = input().strip()
    if new_subreddit:
        config_content = config_content.replace(
            "SUBREDDIT = 'skincareaddictsindia'",
            f"SUBREDDIT = '{new_subreddit}'"
        )
    
    # Get engagement criteria
    print("\nEnter minimum engagement score (upvotes + comments): ", end='')
    try:
        new_score = int(input().strip())
        config_content = config_content.replace(
            "MIN_ENGAGEMENT_SCORE = 7",
            f"MIN_ENGAGEMENT_SCORE = {new_score}"
        )
    except ValueError:
        pass
    
    # Save updated config
    with open(config_file, 'w') as f:
        f.write(config_content)
    
    print("✅ Configuration updated!")

def test_connection():
    """Test Reddit API connection"""
    print("\n🔍 Testing Reddit API Connection...")
    
    # Check if .env exists
    if not Path('.env').exists():
        print("❌ .env file not found. Run setup first.")
        return
    
    # Try to import and test
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        import requests
        import base64
        
        client_id = os.getenv('REDDIT_CLIENT_ID')
        client_secret = os.getenv('REDDIT_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            print("❌ Missing Reddit credentials in .env file")
            return
        
        # Test token request
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        
        headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'User-Agent': 'skincare_monitor/1.0 (by /u/your_username)',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {'grant_type': 'client_credentials'}
        
        response = requests.post(
            'https://www.reddit.com/api/v1/access_token',
            headers=headers,
            data=data
        )
        
        if response.status_code == 200:
            print("✅ Reddit API connection successful!")
        else:
            print(f"❌ API connection failed: {response.text}")
            
    except ImportError:
        print("❌ Missing required packages. Install with: pip install requests python-dotenv")
    except Exception as e:
        print(f"❌ Connection test failed: {e}")

def show_help():
    """Show setup help"""
    print("""
🚀 Reddit Monitor Setup

This script helps you configure the Reddit monitoring system.

Commands:
1. setup    - Create .env template and configure settings
2. test     - Test Reddit API connection
3. help     - Show this help message

Usage:
    python3 misc_py_root/setup_monitor.py setup
    python3 misc_py_root/setup_monitor.py test
    python3 misc_py_root/setup_monitor.py help

Steps to get started:
1. Create Reddit app at https://www.reddit.com/prefs/apps
2. Run: python3 misc_py_root/setup_monitor.py setup
3. Edit .env with your credentials
4. Run: python3 misc_py_root/setup_monitor.py test
5. Start monitoring: python3 misc_py_root/reddit_monitor.py
""")

def main():
    """Main setup function"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'setup':
        print("🔧 Setting up Reddit Monitor...")
        create_env_template()
        update_config()
        print("\n✅ Setup complete!")
        print("📝 Next steps:")
        print("1. Edit .env with your Reddit API credentials")
        print("2. Run: python3 misc_py_root/setup_monitor.py test")
        print("3. Start monitoring: python3 misc_py_root/reddit_monitor.py")
        
    elif command == 'test':
        test_connection()
        
    elif command == 'help':
        show_help()
        
    else:
        print(f"❌ Unknown command: {command}")
        show_help()

if __name__ == "__main__":
    main()
