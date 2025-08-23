#!/usr/bin/env python3
"""
GitHub Storage for Reddit Monitoring Files
Uploads files to GitHub releases - free and easy!
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
import requests
from github import Github

# Configuration
LOCAL_MONITORING_DIR = 'reddit_monitoring'
RELEASE_TAG_PREFIX = 'reddit-monitor'
REPO_NAME = 'nimishpande/ingredient_cosmetics'  # Your repository name (username/repo)

def authenticate_github():
    """Authenticate with GitHub using token"""
    github_token = os.getenv('GIT_TOKEN')
    
    if not github_token:
        print("❌ GIT_TOKEN not found in environment variables")
        print("\n📝 To set up GitHub token:")
        print("1. Go to GitHub → Settings → Developer settings → Personal access tokens")
        print("2. Generate new token with 'repo' permissions")
        print("3. Set as environment variable: export GIT_TOKEN=your_token")
        print("4. For GitHub Actions, add as repository secret with name: GIT_TOKEN")
        return None
    
    try:
        g = Github(github_token)
        user = g.get_user()
        print(f"✅ GitHub authentication successful: {user.login}")
        return g
    except Exception as e:
        print(f"❌ GitHub authentication failed: {e}")
        return None

def create_release_assets(github, repo_name, files):
    """Create GitHub release with monitoring files"""
    try:
        # Get repository
        repo = github.get_repo(repo_name)
        
        # Create release tag
        today = datetime.now().strftime('%Y-%m-%d')
        tag_name = f"{RELEASE_TAG_PREFIX}-{today}"
        release_name = f"Reddit Monitor - {today}"
        
        # Check if release already exists
        try:
            release = repo.get_release(tag_name)
            print(f"✅ Found existing release: {tag_name}")
        except:
            # Create new release
            release = repo.create_git_release(
                tag=tag_name,
                name=release_name,
                message=f"Reddit monitoring data for {today}",
                draft=False,
                prerelease=False
            )
            print(f"✅ Created new release: {tag_name}")
        
        # Upload files
        uploaded_files = []
        for file_path in files:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                
                # Check if asset already exists
                existing_assets = [asset for asset in release.get_assets() if asset.name == filename]
                if existing_assets:
                    # Delete existing asset
                    existing_assets[0].delete_asset()
                
                # Upload new asset
                with open(file_path, 'rb') as f:
                    asset = release.upload_asset(file_path, filename)
                    uploaded_files.append({
                        'name': filename,
                        'size': os.path.getsize(file_path),
                        'url': asset.browser_download_url
                    })
                    print(f"📤 Uploaded: {filename}")
        
        return {
            'release_url': release.html_url,
            'tag_name': tag_name,
            'files_uploaded': len(uploaded_files),
            'files': uploaded_files
        }
        
    except Exception as e:
        print(f"❌ GitHub release creation failed: {e}")
        return None

def upload_to_github():
    """Upload monitoring files to GitHub releases"""
    print("🚀 Starting GitHub storage upload...")
    
    # Authenticate
    github = authenticate_github()
    if not github:
        return False
    
    # Get files to upload
    monitoring_dir = Path(LOCAL_MONITORING_DIR)
    if not monitoring_dir.exists():
        print(f"❌ Monitoring directory not found: {LOCAL_MONITORING_DIR}")
        return False
    
    # Collect files
    files_to_upload = []
    for file_path in monitoring_dir.glob('*'):
        if file_path.is_file() and file_path.suffix in ['.txt', '.json']:
            files_to_upload.append(str(file_path))
    
    if not files_to_upload:
        print("❌ No files to upload")
        return False
    
    print(f"📁 Found {len(files_to_upload)} files to upload")
    
    # Upload to GitHub releases
    result = create_release_assets(github, REPO_NAME, files_to_upload)
    
    if result:
        print(f"\n✅ Upload complete!")
        print(f"🔗 Release URL: {result['release_url']}")
        print(f"📊 Files uploaded: {result['files_uploaded']}")
        
        # Save upload summary
        summary = {
            'upload_timestamp': datetime.now().isoformat(),
            'storage_method': 'github_releases',
            'release_url': result['release_url'],
            'tag_name': result['tag_name'],
            'files_uploaded': result['files_uploaded'],
            'files': result['files']
        }
        
        summary_file = monitoring_dir / 'github_upload_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return True
    
    return False

def main():
    """Main function"""
    success = upload_to_github()
    
    if success:
        print("\n🎉 All files uploaded to GitHub releases successfully!")
    else:
        print("\n❌ Upload failed. Check the error messages above.")

if __name__ == "__main__":
    main()
