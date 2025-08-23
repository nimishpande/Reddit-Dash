#!/usr/bin/env python3
"""
Simple Google Drive Uploader using Environment Variables
Perfect for GitHub Actions and automation
"""

import os
import json
import base64
from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configuration
LOCAL_MONITORING_DIR = 'reddit_monitoring'
DRIVE_FOLDER_NAME = 'Reddit Monitoring'

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_from_env():
    """Authenticate using environment variables"""
    # Check for service account JSON in environment variable
    service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
    
    if service_account_json:
        try:
            # Decode base64 if needed
            if service_account_json.startswith('{'):
                # Direct JSON string
                service_account_info = json.loads(service_account_json)
            else:
                # Base64 encoded
                service_account_info = json.loads(base64.b64decode(service_account_json))
            
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info, scopes=SCOPES
            )
            print("✅ Service account authentication from environment successful")
            return credentials
        except Exception as e:
            print(f"❌ Environment authentication failed: {e}")
            return None
    
    # Check for service account file
    service_account_file = 'service-account-key.json'
    if os.path.exists(service_account_file):
        try:
            credentials = service_account.Credentials.from_service_account_file(
                service_account_file, scopes=SCOPES
            )
            print("✅ Service account authentication from file successful")
            return credentials
        except Exception as e:
            print(f"❌ File authentication failed: {e}")
            return None
    
    print("❌ No authentication method found!")
    print("\n📝 Setup options:")
    print("1. Set GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
    print("2. Place service-account-key.json in project root")
    print("3. For GitHub Actions, add GOOGLE_SERVICE_ACCOUNT_JSON as repository secret")
    return None

def get_or_create_folder(service, folder_name):
    """Get existing folder or create new one"""
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        print(f"✅ Found existing folder: {folder_name}")
        return files[0]['id']
    
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print(f"✅ Created new folder: {folder_name}")
    return folder.get('id')

def upload_file_to_drive(service, file_path, folder_id):
    """Upload a file to Google Drive"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    filename = os.path.basename(file_path)
    
    # Check if file already exists
    query = f"name='{filename}' and '{folder_id}' in parents and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    existing_files = results.get('files', [])
    
    if existing_files:
        # Update existing file
        file_id = existing_files[0]['id']
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().update(
            fileId=file_id,
            media_body=media,
            fields='id, name, size'
        ).execute()
        print(f"🔄 Updated: {filename}")
    else:
        # Upload new file
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        
        media = MediaFileUpload(file_path, resumable=True)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id, name, size'
        ).execute()
        print(f"📤 Uploaded: {filename}")
    
    return file.get('id')

def upload_monitoring_files():
    """Upload all monitoring files to Google Drive"""
    print("🚀 Starting Google Drive upload...")
    
    # Authenticate
    credentials = authenticate_from_env()
    if not credentials:
        return False
    
    try:
        # Build service
        service = build('drive', 'v3', credentials=credentials)
        
        # Get or create folder
        folder_id = get_or_create_folder(service, DRIVE_FOLDER_NAME)
        
        # Upload files
        monitoring_dir = Path(LOCAL_MONITORING_DIR)
        if not monitoring_dir.exists():
            print(f"❌ Monitoring directory not found: {LOCAL_MONITORING_DIR}")
            return False
        
        uploaded_files = []
        
        # Upload all files in monitoring directory
        for file_path in monitoring_dir.glob('*'):
            if file_path.is_file():
                file_id = upload_file_to_drive(service, str(file_path), folder_id)
                if file_id:
                    uploaded_files.append({
                        'name': file_path.name,
                        'id': file_id,
                        'size': file_path.stat().st_size
                    })
        
        print(f"\n✅ Upload complete!")
        print(f"📁 Folder: {DRIVE_FOLDER_NAME}")
        print(f"📊 Files uploaded: {len(uploaded_files)}")
        
        return True
        
    except HttpError as error:
        print(f"❌ Google Drive API error: {error}")
        return False
    except Exception as error:
        print(f"❌ Upload failed: {error}")
        return False

def main():
    """Main function"""
    success = upload_monitoring_files()
    
    if success:
        print("\n🎉 All files uploaded to Google Drive successfully!")
    else:
        print("\n❌ Upload failed. Check the error messages above.")

if __name__ == "__main__":
    main()
