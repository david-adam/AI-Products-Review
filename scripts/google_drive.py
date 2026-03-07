#!/usr/bin/env python3
"""
Google Drive API Integration for ProductLens AI

Uploads images and videos to Google Drive and returns public URLs.
"""

import os
import json
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')


def get_drive_service():
    """
    Initialize Google Drive service using service account credentials.
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Drive service
    """
    if not GOOGLE_DRIVE_CREDENTIALS_PATH:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS_PATH not set in .env")
    
    if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"Credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
    
    creds = Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    
    service = build('drive', 'v3', credentials=creds)
    return service


def upload_to_drive(file_path, folder_id=None, file_name=None, share_with_email=None):
    """
    Upload a file to Google Drive and make it publicly accessible.
    
    Args:
        file_path (str): Local path to the file to upload
        folder_id (str): Google Drive folder ID (optional, None = service account's root)
        file_name (str): Custom file name (optional, defaults to original name)
        share_with_email (str): Email to share the file with (optional)
    
    Returns:
        dict: {
            'file_id': str,
            'public_url': str,
            'direct_url': str,
            'view_url': str
        }
    """
    service = get_drive_service()
    
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
    
    # Add to folder if specified (otherwise uploads to service account's root)
    if folder_id:
        file_metadata['parents'] = [folder_id]
    
    # Upload file
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
    
    # Optionally share with specific email
    if share_with_email:
        service.permissions().create(
            fileId=file_id,
            body={
                'role': 'reader',
                'type': 'user',
                'emailAddress': share_with_email
            }
        ).execute()
    
    # Generate URLs
    public_url = f"https://drive.google.com/uc?export=view&id={file_id}"
    direct_url = f"https://lh3.googleusercontent.com/d/{file_id}"
    view_url = f"https://drive.google.com/file/d/{file_id}/view"
    
    return {
        'file_id': file_id,
        'public_url': public_url,
        'direct_url': direct_url,  # Use this for hotlinking
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
    service = get_drive_service()
    
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


def list_files_in_folder(folder_id=None):
    """
    List files in a Google Drive folder.
    
    Args:
        folder_id (str): Folder ID (optional, lists all if not specified)
    
    Returns:
        list: List of file metadata dicts
    """
    service = get_drive_service()
    
    query = f"'{folder_id}' in parents" if folder_id else ""
    
    results = service.files().list(
        q=query,
        pageSize=100,
        fields="nextPageToken, files(id, name, mimeType, createdTime)"
    ).execute()
    
    items = results.get('files', [])
    return items


def delete_file(file_id):
    """
    Delete a file from Google Drive.
    
    Args:
        file_id (str): ID of the file to delete
    """
    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()


# Test function
def test_upload():
    """
    Test the Google Drive upload functionality.
    """
    import tempfile
    
    # Create a test image
    from PIL import Image, ImageDraw
    
    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
        img = Image.new('RGB', (800, 600), color='blue')
        draw = ImageDraw.Draw(img)
        draw.text((400, 300), "ProductLens AI Test", fill='white')
        img.save(tmp.name)
        
        print(f"Uploading test image: {tmp.name}")
        
        try:
            # Upload to service account's root (no folder_id)
            result = upload_to_drive(
                tmp.name,
                file_name="productlens-test.png",
                share_with_email="daviddw7214@gmail.com"  # Share with you
            )
            print(f"✅ Upload successful!")
            print(f"   File ID: {result['file_id']}")
            print(f"   Direct URL: {result['direct_url']}")
            print(f"   View URL: {result['view_url']}")
            print(f"   Shared with: daviddw7214@gmail.com")
            
            # Clean up
            os.unlink(tmp.name)
            
            return result
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            os.unlink(tmp.name)
            return None


if __name__ == "__main__":
    print("Google Drive API Integration Test")
    print("=" * 50)
    
    try:
        # Test upload
        result = test_upload()
        
        if result:
            print("\n✅ All tests passed!")
        else:
            print("\n❌ Tests failed!")
    
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
