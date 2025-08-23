#!/usr/bin/env python3
"""
Google Drive Uploader for Reddit Monitoring Files
Automatically uploads monitoring files to Google Drive
"""

import os
import json
from datetime import datetime
from pathlib import Path
import pickle
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Google Drive API scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Configuration
LOCAL_MONITORING_DIR = 'reddit_monitoring'
DRIVE_FOLDER_NAME = 'Reddit Monitoring'
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.pickle'

def authenticate_google_drive():
    """Authenticate with Google Drive API"""
    creds = None
    
    # Load existing token
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, 'rb') as token:
            creds = pickle.load(token)
    
    # If no valid credentials, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDENTIALS_FILE):
                print("❌ credentials.json not found!")
                print("📝 Please download credentials.json from Google Cloud Console")
                print("🔗 https://console.cloud.google.com/apis/credentials")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for next run
        with open(TOKEN_FILE, 'wb') as token:
            pickle.dump(creds, token)
    
    return creds

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
    print("🚀 Starting Google Drive upload...")
    
    # Authenticate
    creds = authenticate_google_drive()
    if not creds:
        return False
    
    try:
        # Build service
        service = build('drive', 'v3', credentials=creds)
        
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
            'files': uploaded_files
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

def setup_instructions():
    """Print setup instructions"""
    print("""
🔧 Google Drive Setup Instructions:

1. Go to Google Cloud Console:
   https://console.cloud.google.com/

2. Create a new project or select existing one

3. Enable Google Drive API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Drive API"
   - Click "Enable"

4. Create credentials:
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Application type: "Desktop application"
   - Download the JSON file

5. Rename the downloaded file to 'credentials.json'
   and place it in the project root directory

6. Run the uploader:
   python3 misc_py_root/google_drive_uploader.py

The first run will open a browser for authentication.
""")

def main():
    """Main function"""
    if not os.path.exists(CREDENTIALS_FILE):
        print("❌ credentials.json not found!")
        setup_instructions()
        return
    
    success = upload_monitoring_files()
    
    if success:
        print("\n🎉 All files uploaded to Google Drive successfully!")
    else:
        print("\n❌ Upload failed. Check the error messages above.")

if __name__ == "__main__":
    main()
