#!/usr/bin/env python3
"""
Simple test script for GitHub Actions environment
"""

import os
import sys
from dotenv import load_dotenv

def test_environment():
    """Test basic environment setup"""
    print("🔍 Testing GitHub Actions environment...")
    
    # Test Python version
    print(f"🐍 Python version: {sys.version}")
    
    # Test imports
    try:
        import requests
        print("✅ requests module imported successfully")
    except ImportError as e:
        print(f"❌ requests import failed: {e}")
        return False
    
    try:
        from github import Github
        print("✅ PyGithub module imported successfully")
    except ImportError as e:
        print(f"❌ PyGithub import failed: {e}")
        return False
    
    # Test environment variables
    load_dotenv()
    
    reddit_client_id = os.getenv('REDDIT_CLIENT_ID')
    reddit_client_secret = os.getenv('REDDIT_CLIENT_SECRET')
    git_token = os.getenv('GIT_TOKEN')
    
    print(f"🔑 REDDIT_CLIENT_ID: {'✅ Found' if reddit_client_id else '❌ Missing'}")
    print(f"🔑 REDDIT_CLIENT_SECRET: {'✅ Found' if reddit_client_secret else '❌ Missing'}")
    print(f"🔑 GIT_TOKEN: {'✅ Found' if git_token else '❌ Missing'}")
    
    # Test Reddit API connection
    if reddit_client_id and reddit_client_secret:
        try:
            import base64
            import requests
            
            credentials = f"{reddit_client_id}:{reddit_client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                'Authorization': f'Basic {encoded_credentials}',
                'User-Agent': 'test_script/1.0',
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            data = {'grant_type': 'client_credentials'}
            response = requests.post('https://www.reddit.com/api/v1/access_token', 
                                   headers=headers, data=data, timeout=10)
            
            if response.status_code == 200:
                print("✅ Reddit API authentication successful")
            else:
                print(f"❌ Reddit API authentication failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Reddit API test failed: {e}")
    
    # Test GitHub API connection
    if git_token:
        try:
            g = Github(git_token)
            user = g.get_user()
            print(f"✅ GitHub API authentication successful: {user.login}")
        except Exception as e:
            print(f"❌ GitHub API authentication failed: {e}")
    
    # Test file operations
    try:
        test_dir = 'test_output'
        os.makedirs(test_dir, exist_ok=True)
        
        test_file = os.path.join(test_dir, 'test.txt')
        with open(test_file, 'w') as f:
            f.write('Test successful')
        
        print(f"✅ File operations successful: {test_file}")
        
        # Cleanup
        os.remove(test_file)
        os.rmdir(test_dir)
        
    except Exception as e:
        print(f"❌ File operations failed: {e}")
    
    print("🎉 Environment test complete!")
    return True

if __name__ == "__main__":
    test_environment()
