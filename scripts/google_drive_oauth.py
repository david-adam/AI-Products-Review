#!/usr/bin/env python3
"""
Google Drive OAuth 2.0 Integration for ProductLens AI

Uses OAuth 2.0 flow to upload files to your personal Google Drive.
"""

import os
import json
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# OAuth scopes
SCOPES = ['https://www.googleapis.com/auth/drive.file']

# Token storage
TOKEN_FILE = '.google_drive_token.json'
CREDENTIALS_FILE = 'oauth_credentials.json'


def get_credentials():
    """
    Get OAuth credentials, handling token refresh.
    
    Returns:
        Credentials: Valid OAuth credentials
    """
    creds = None
    
    # Load existing token if available
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    
    # If credentials are invalid or missing, get new ones
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # For first-time setup, we need OAuth client ID
            if not os.path.exists(CREDENTIALS_FILE):
                raise FileNotFoundError(
                    f"{CREDENTIALS_FILE} not found. Please create it with your OAuth client ID.\n"
                    "Get OAuth credentials from: https://console.cloud.google.com/apis/credentials"
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save credentials for future use
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())
    
    return creds


def upload_to_drive(file_path, folder_id=None, file_name=None):
    """
    Upload a file to Google Drive using OAuth 2.0.
    
    Args:
        file_path (str): Local path to the file to upload
        folder_id (str): Google Drive folder ID (optional)
        file_name (str): Custom file name (optional)
    
    Returns:
        dict: {
            'file_id': str,
            'direct_url': str,
            'view_url': str
        }
    """
    creds = get_credentials()
    
    if not file_name:
        file_name = os.path.basename(file_path)
    
    # Determine MIME type
    mime_type = 'image/png'
    if file_path.endswith(('.jpg', '.jpeg')):
        mime_type = 'image/jpeg'
    elif file_path.endswith('.webp'):
        mime_type = 'image/webp'
    elif file_path.endswith('.mp4'):
        mime_type = 'video/mp4'
    elif file_path.endswith('.webm'):
        mime_type = 'video/webm'
    
    # File metadata
    file_metadata = {
        'name': file_name,
    }
    
    # Add to folder if specified
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    # Upload file
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    
    service = build('drive', 'v3', credentials=creds)
    media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    file_id = file['id']
    
    # Make file public (anyone with link can view)
    service.permissions().create(
        fileId=file_id,
        body={
            'role': 'reader',
            'type': 'anyone'
        }
    ).execute()
    
    # Generate URLs
    direct_url = f"https://lh3.googleusercontent.com/d/{file_id}"
    view_url = f"https://drive.google.com/file/d/{file_id}/view"
    
    return {
        'file_id': file_id,
        'direct_url': direct_url,
        'view_url': view_url
    }


def create_folder(folder_name, parent_folder_id=None):
    """
    Create a folder in Google Drive.
    
    Args:
        folder_name (str): Name of the folder to create
        parent_folder_id (str): Parent folder ID (optional)
    
    Returns:
        str: New folder ID
    """
    creds = get_credentials()
    
    from googleapiclient.discovery import build
    
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_folder_id:
        file_metadata['parents'] = [parent_folder_id]
    
    folder = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return folder['id']


# Test function
def test_upload():
    """
    Test the Google Drive upload functionality.
    """
    import tempfile
    
    # Create a test image
    from PIL import Image, ImageDraw
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img = Image.new('RGB', (800, 600), color='green')
        draw = ImageDraw.Draw(img)
        draw.text((400, 300), "ProductLens AI OAuth Test", fill='white')
        img.save(tmp.name)
        
        print(f"Uploading test image: {tmp.name}")
        
        try:
            result = upload_to_drive(tmp.name, file_name="productlens-oauth-test.png")
            print(f"✅ Upload successful!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Direct URL: {result['direct_url']}")
            print(f"   View URL: {result['view_url']}")
            
            # Clean up
            os.unlink(tmp.name)
            
            return result
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            os.unlink(tmp.name)
            return None


if __name__ == "__main__":
    print("Google Drive OAuth 2.0 Integration Test")
    print("=" * 50)
    
    try:
        result = test_upload()
        
        if result:
            print("\n✅ Test passed!")
            print("\nNote: Token saved to .google_drive_token.json")
            print("Future runs will use the saved token (no need to re-authenticate)")
        else:
            print("\n❌ Test failed!")
    
    except FileNotFoundError as e:
        print(f"\n⚠️ Setup Required: {e}")
        print("\nTo get OAuth credentials:")
        print("1. Go to: https://console.cloud.google.com/apis/credentials")
        print("2. Create a project (or use existing)")
        print("3. Create OAuth 2.0 Client ID (Desktop app)")
        print("4. Download the JSON credentials")
        print("5. Save as 'oauth_credentials.json' in the project directory")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
