#!/usr/bin/env python3
"""
Google Drive Uploader using Service Account
Better for automation - no browser authentication needed
"""

import os
import json
from datetime import datetime
from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Configuration
LOCAL_MONITORING_DIR = 'reddit_monitoring'
DRIVE_FOLDER_NAME = 'Reddit Monitoring'
SERVICE_ACCOUNT_FILE = 'service-account-key.json'

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def authenticate_service_account():
    """Authenticate using service account"""
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        print(f"❌ {SERVICE_ACCOUNT_FILE} not found!")
        print("\n📝 To get service account credentials:")
        print("1. Go to Google Cloud Console → IAM & Admin → Service Accounts")
        print("2. Create a new service account")
        print("3. Add 'Google Drive API' role")
        print("4. Create and download JSON key")
        print("5. Rename to 'service-account-key.json'")
        return None
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES
        )
        print("✅ Service account authentication successful")
        return credentials
    except Exception as e:
        print(f"❌ Service account authentication failed: {e}")
        return None

def get_or_create_folder(service, folder_name):
    """Get existing folder or create new one"""
    # Search for existing folder
    query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        print(f"✅ Found existing folder: {folder_name}")
        return files[0]['id']
    
    # Create new folder
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    print(f"✅ Created new folder: {folder_name}")
    return folder.get('id')

def upload_file_to_drive(service, file_path, folder_id, filename=None):
    """Upload a file to Google Drive"""
    if not os.path.exists(file_path):
        print(f"❌ File not found: {file_path}")
        return None
    
    if filename is None:
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
    print("🚀 Starting Google Drive upload (Service Account)...")
    
    # Authenticate
    credentials = authenticate_service_account()
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
        
        # Create upload summary
        summary = {
            'upload_timestamp': datetime.now().isoformat(),
            'folder_name': DRIVE_FOLDER_NAME,
            'folder_id': folder_id,
            'files_uploaded': len(uploaded_files),
            'files': uploaded_files,
            'auth_method': 'service_account'
        }
        
        # Save upload summary locally
        summary_file = monitoring_dir / 'upload_summary.json'
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\n✅ Upload complete!")
        print(f"📁 Folder: {DRIVE_FOLDER_NAME}")
        print(f"📊 Files uploaded: {len(uploaded_files)}")
        print(f"🔗 Drive folder ID: {folder_id}")
        
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
