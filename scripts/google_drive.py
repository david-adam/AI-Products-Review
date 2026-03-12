#!/usr/bin/env python3
"""
Google Drive API Integration for ProductLens AI

Uploads images and videos to Google Drive and returns public URLs.
Supports both Service Account and OAuth2 token authentication.
Includes retry logic (3 attempts), error handling, and ProductLens folder support.
"""

import os
import time
import json
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
from google.oauth2.credentials import Credentials as OAuthCredentials
from google.api_core.exceptions import ServiceUnavailable, GatewayTimeout
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

GOOGLE_DRIVE_CREDENTIALS_PATH = os.getenv('GOOGLE_DRIVE_CREDENTIALS_PATH')
GOOGLE_DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '1b40voT9KBYONVIRb9ib_GyFHxQOilXO4')  # ProductLens folder
GOOGLE_DRIVE_TOKEN_PATH = os.getenv('GOOGLE_DRIVE_TOKEN_PATH', os.path.join(os.path.dirname(__file__), '..', '.google_drive_token.json'))
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Try to import api_core exceptions - handle if not available
try:
    from google.api_core.exceptions import ServiceUnavailable, GatewayTimeout
    HAS_API_CORE = True
except ImportError:
    HAS_API_CORE = False
    logger.warning("google-api-core not available, retry logic limited")


def get_drive_service(use_oauth=True):
    """
    Initialize Google Drive service.
    
    First tries OAuth2 token (user account), then falls back to service account.
    
    Args:
        use_oauth (bool): If True, prefer OAuth2 token over service account
    
    Returns:
        googleapiclient.discovery.Resource: Authenticated Drive service
    """
    # Try OAuth2 first (uses user's Google account - has storage quota)
    if use_oauth and os.path.exists(GOOGLE_DRIVE_TOKEN_PATH):
        try:
            creds = OAuthCredentials.from_authorized_user_file(
                GOOGLE_DRIVE_TOKEN_PATH,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            service = build('drive', 'v3', credentials=creds)
            logger.info("Using OAuth2 credentials (user account)")
            return service
        except Exception as e:
            logger.warning(f"OAuth2 failed, trying service account: {e}")
    
    # Fall back to service account
    if not GOOGLE_DRIVE_CREDENTIALS_PATH:
        raise ValueError("GOOGLE_DRIVE_CREDENTIALS_PATH not set in .env")
    
    if not os.path.exists(GOOGLE_DRIVE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"Credentials file not found: {GOOGLE_DRIVE_CREDENTIALS_PATH}")
    
    creds = Credentials.from_service_account_file(
        GOOGLE_DRIVE_CREDENTIALS_PATH,
        scopes=['https://www.googleapis.com/auth/drive']
    )
    
    service = build('drive', 'v3', credentials=creds)
    logger.info("Using service account credentials")
    return service


def upload_to_drive(file_path, folder_id=None, file_name=None, share_with_email=None, max_retries=MAX_RETRIES):
    """
    Upload a file to Google Drive and make it publicly accessible.
    
    Args:
        file_path (str): Local path to the file to upload
        folder_id (str): Google Drive folder ID (defaults to ProductLens folder from .env)
        file_name (str): Custom file name (optional, defaults to original name)
        share_with_email (str): Email to share the file with (optional)
        max_retries (int): Maximum number of retry attempts (default: 3)
    
    Returns:
        dict: {
            'file_id': str,
            'public_url': str,
            'direct_url': str,
            'view_url': str
        }
        or None if all retries failed
    """
    # Use default ProductLens folder if not specified
    if folder_id is None:
        folder_id = GOOGLE_DRIVE_FOLDER_ID
    
    # Validate file exists
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return None
    
    # Validate file has content
    if os.path.getsize(file_path) == 0:
        logger.error(f"File is empty: {file_path}")
        return None
    
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
    
    # Validate folder access - try to verify folder exists
    effective_folder_id = None
    use_oauth = os.path.exists(GOOGLE_DRIVE_TOKEN_PATH)  # Use OAuth if token exists
    
    if folder_id:
        try:
            service = get_drive_service(use_oauth=use_oauth)
            # Try to access the folder - if it fails, we'll upload to root
            service.files().get(fileId=folder_id, fields='id').execute()
            file_metadata['parents'] = [folder_id]
            effective_folder_id = folder_id
            logger.info(f"Uploading to folder: {folder_id}")
        except Exception as e:
            logger.warning(f"Folder {folder_id} not accessible: {e}")
            logger.warning("Falling back to root (My Drive)")
            # Upload to root - don't specify parents
    else:
        logger.info("No folder specified, uploading to root")
    
    last_error = None
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Upload attempt {attempt}/{max_retries}: {file_name}")
            
            # Get fresh service for each attempt - prefer OAuth if available
            service = get_drive_service(use_oauth=use_oauth)
            
            # Upload file
            media = MediaFileUpload(file_path, mimetype=mime_type, resumable=True)
            
            file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file['id']
            logger.info(f"File uploaded successfully: {file_id}")
            
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
                try:
                    service.permissions().create(
                        fileId=file_id,
                        body={
                            'role': 'reader',
                            'type': 'user',
                            'emailAddress': share_with_email
                        }
                    ).execute()
                    logger.info(f"Shared with: {share_with_email}")
                except Exception as e:
                    logger.warning(f"Could not share with {share_with_email}: {e}")
            
            # Generate URLs
            public_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            direct_url = f"https://lh3.googleusercontent.com/d/{file_id}"
            view_url = f"https://drive.google.com/file/d/{file_id}/view"
            
            return {
                'file_id': file_id,
                'public_url': public_url,
                'direct_url': direct_url,  # Use this for hotlinking
                'view_url': view_url,
                'folder_id': effective_folder_id  # Track where it was uploaded
            }
            
        except Exception as e:
            error_str = str(e)
            # Check if retryable
            is_retryable = (
                HAS_API_CORE and isinstance(e, (ServiceUnavailable, GatewayTimeout))
            ) or 'rateLimitExceeded' in error_str or '500' in error_str or '503' in error_str
            
            last_error = e
            if is_retryable:
                logger.warning(f"Retryable error on attempt {attempt}: {e}")
                if attempt < max_retries:
                    wait_time = RETRY_DELAY * attempt  # Exponential backoff
                    logger.info(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            else:
                # Non-retryable errors
                logger.error(f"Non-retryable error: {e}")
                break
    
    # All retries failed
    logger.error(f"Upload failed after {max_retries} attempts: {last_error}")
    return None


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
