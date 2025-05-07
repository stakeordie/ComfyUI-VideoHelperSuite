import os
import mimetypes
import traceback
from typing import Optional, Tuple, List, Dict, Any, Union
from dotenv import load_dotenv
from .logger import logger

# Import AWS S3 client library
try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False
    logger.warning("AWS S3 not available. Install with 'pip install boto3'")

# Import Google Cloud Storage client library
try:
    from google.cloud import storage
    from google.oauth2 import service_account
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    logger.warning("Google Cloud Storage not available. Install with 'pip install google-cloud-storage'")

# Import Azure Blob Storage client library
try:
    from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
    AZURE_AVAILABLE = True
except ImportError:
    AZURE_AVAILABLE = False
    logger.warning("Azure Blob Storage not available. Install with 'pip install azure-storage-blob'")

def log_debug(message: str) -> None:
    """Helper function to log debug messages"""
    logger.debug(f"[CloudStorage] {message}")

def unescape_env_value(encoded_value: str) -> str:
    """
    Unescapes a base64 encoded environment variable value.
    Also handles _SLASH_ replacement in the raw string.
    
    Args:
        encoded_value (str): The potentially encoded string
        
    Returns:
        str: The decoded string, or empty string if decoding fails
    """
    try:
        if not encoded_value:
            return ''
            
        # First replace _SLASH_ with actual forward slashes
        decoded_value = encoded_value.replace('_SLASH_', '/')
        
        # Try to decode as base64 if it looks like base64
        import base64
        try:
            # Check if it might be base64 encoded
            if len(decoded_value) % 4 == 0 and all(c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=' for c in decoded_value):
                decoded_bytes = base64.b64decode(decoded_value)
                return decoded_bytes.decode('utf-8')
        except:
            pass  # Not base64, return the string with _SLASH_ replaced
            
        return decoded_value
    except Exception as e:
        log_debug(f"Error unescaping environment value: {str(e)}")
        return ''

def _process_secret_key(secret_key: str) -> str:
    """Process AWS secret key by replacing _SLASH_ with /"""
    return secret_key.replace('_SLASH_', '/') if secret_key else ''

class CloudStorageHandler:
    """
    Provider-agnostic cloud storage handler that supports AWS S3, Google Cloud Storage, and Azure Blob Storage.
    Added: 2025-04-24T20:05:00-04:00
    """
    
    def __init__(self, provider: str = None, bucket_name: Optional[str] = None):
        """
        Initialize the cloud storage handler.
        
        Args:
            provider: The cloud provider to use ('aws', 'google', or 'azure'). If None, will try to get from environment.
            bucket_name: The bucket/container name to use. If None, will use default or get from environment.
        """
        log_debug(f"Initializing CloudStorageHandler with provider={provider}, bucket={bucket_name}")
        
        # Get provider from environment if not specified
        # Added: 2025-05-07T15:22:00-04:00 - Improved provider detection
        self.provider = provider or os.getenv('CLOUD_PROVIDER', 'aws').lower()
        # Validate provider
        if self.provider not in ['aws', 'google', 'azure']:
            log_debug(f"Warning: Unknown CLOUD_PROVIDER value: {self.provider}, defaulting to 'aws'")
            self.provider = 'aws'
        log_debug(f"Using cloud provider: {self.provider}")
        
        # Check for test mode
        self.test_mode = os.getenv('STORAGE_TEST_MODE', 'false').lower() == 'true'
        log_debug(f"Test mode: {self.test_mode}")
        
        # Initialize provider-specific handlers
        self.aws_handler = None
        self.gcs_handler = None
        self.azure_handler = None
        
        # Set bucket name based on provider and test mode
        if bucket_name:
            self.bucket_name = bucket_name
        else:
            self.bucket_name = "emprops-share"
            if self.test_mode:
                self.bucket_name = f"{self.bucket_name}-test"
        
        log_debug(f"Using bucket/container: {self.bucket_name}")
        
        # Initialize the appropriate handler based on provider
        try:
            if self.provider == 'aws':
                if AWS_AVAILABLE:
                    self.aws_handler = self._init_aws_handler()
                else:
                    raise ImportError("AWS S3 support is not available. Install with 'pip install boto3'")
            elif self.provider == 'google':
                if GCS_AVAILABLE:
                    self.gcs_handler = self._init_gcs_handler()
                else:
                    raise ImportError("Google Cloud Storage support is not available. Install with 'pip install google-cloud-storage'")
            elif self.provider == 'azure':
                if AZURE_AVAILABLE:
                    self.azure_handler = self._init_azure_handler()
                else:
                    raise ImportError("Azure Blob Storage support is not available. Install with 'pip install azure-storage-blob'")
            else:
                raise ValueError(f"Unsupported cloud provider: {self.provider}. Must be one of: aws, google, azure")
        except Exception as e:
            log_debug(f"Error initializing cloud storage handler: {str(e)}")
            log_debug(traceback.format_exc())
            raise
    
    def _init_aws_handler(self):
        """Initialize AWS S3 handler"""
        log_debug("Initializing AWS S3 handler")
        
        # First try system environment
        access_key = os.getenv('AWS_ACCESS_KEY_ID')
        secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
        region = os.getenv('AWS_DEFAULT_REGION')

        # Try encoded secret key if regular one not found
        if not secret_key:
            secret_key = os.getenv('AWS_SECRET_ACCESS_KEY_ENCODED')
            if secret_key:
                secret_key = _process_secret_key(secret_key)

        # If not found, try .env and .env.local files
        if not access_key or not secret_key or not region:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Try .env first
            env_path = os.path.join(current_dir, '.env')
            if os.path.exists(env_path):
                log_debug(f"Loading .env from: {env_path}")
                load_dotenv(env_path)
                secret_key = secret_key or _process_secret_key(os.getenv('AWS_SECRET_ACCESS_KEY_ENCODED', ''))
                if not secret_key:
                    secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY', '')
                access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID', '')
                region = region or os.getenv('AWS_DEFAULT_REGION', '')
            
            # If still not found, try .env.local
            if not access_key or not secret_key or not region:
                env_local_path = os.path.join(current_dir, '.env.local')
                if os.path.exists(env_local_path):
                    log_debug(f"Loading .env.local from: {env_local_path}")
                    load_dotenv(env_local_path)
                    secret_key = secret_key or _process_secret_key(os.getenv('AWS_SECRET_ACCESS_KEY_ENCODED', ''))
                    if not secret_key:
                        secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY', '')
                    access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID', '')
                    region = region or os.getenv('AWS_DEFAULT_REGION', '')
        
        # Set default region if still not set
        region = region or 'us-east-1'
        
        if not all([access_key, secret_key]):
            missing = []
            if not access_key: missing.append('AWS_ACCESS_KEY_ID')
            if not secret_key: missing.append('AWS_SECRET_ACCESS_KEY')
            raise ValueError(f"Missing required AWS environment variables: {', '.join(missing)}")
        
        return boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
    
    def _init_gcs_handler(self):
        """Initialize Google Cloud Storage handler"""
        log_debug("Initializing Google Cloud Storage handler")
        
        # First try system environment for service account key path
        credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        # If not found, try .env and .env.local files
        if not credentials_path:
            current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            
            # Try .env first
            env_path = os.path.join(current_dir, '.env')
            if os.path.exists(env_path):
                log_debug(f"Loading .env from: {env_path}")
                load_dotenv(env_path)
                credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
            
            # If still not found, try .env.local
            if not credentials_path:
                env_local_path = os.path.join(current_dir, '.env.local')
                if os.path.exists(env_local_path):
                    log_debug(f"Loading .env.local from: {env_local_path}")
                    load_dotenv(env_local_path)
                    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
        
        # Check if credentials are available
        if not credentials_path:
            log_debug("Warning: GOOGLE_APPLICATION_CREDENTIALS not set. GCS operations may fail.")
            # Initialize client without explicit credentials (will use default if available)
            return storage.Client()
        else:
            # Initialize client with credentials from file
            try:
                log_debug(f"Using credentials from: {credentials_path}")
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                return storage.Client(credentials=credentials)
            except Exception as e:
                log_debug(f"Error initializing GCS client: {str(e)}")
                raise
    
    def _init_azure_handler(self):
        """Initialize Azure Blob Storage handler"""
        log_debug("Initializing Azure Blob Storage handler")
        
        # Get credentials from environment - support both provider-specific and provider-agnostic variables
        # Added: 2025-05-07T15:21:00-04:00 - Support for provider-agnostic environment variables
        account_name = os.getenv('STORAGE_ACCOUNT_NAME') or os.getenv('AZURE_STORAGE_ACCOUNT')
        account_key = os.getenv('STORAGE_ACCOUNT_KEY') or os.getenv('AZURE_STORAGE_KEY')
        container_name = os.getenv('STORAGE_CONTAINER') or os.getenv('AZURE_STORAGE_CONTAINER', self.bucket_name)
        
        # Validate credentials
        if not all([account_name, account_key]):
            missing = []
            if not account_name: missing.append('STORAGE_ACCOUNT_NAME/AZURE_STORAGE_ACCOUNT')
            if not account_key: missing.append('STORAGE_ACCOUNT_KEY/AZURE_STORAGE_KEY')
            raise ValueError(f"Missing required Azure environment variables: {', '.join(missing)}")
        
        # Initialize Azure Blob Service client
        connection_string = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client(container_name)
        
        # Create container if it doesn't exist
        try:
            container_properties = container_client.get_container_properties()
            log_debug(f"Using existing Azure container: {container_name}")
        except Exception as e:
            try:
                log_debug(f"Creating Azure container: {container_name}")
                container_client.create_container()
            except Exception as create_error:
                log_debug(f"Warning: Could not create Azure container: {str(create_error)}")
                raise
        
        return {
            'blob_service_client': blob_service_client,
            'container_client': container_client,
            'container_name': container_name
        }
    
    def verify_upload(self, key: str, max_attempts: int = 5, delay: float = 1) -> bool:
        """
        Verify that a file exists in cloud storage by checking with the appropriate provider.
        
        Args:
            key: The object key/path
            max_attempts: Maximum number of attempts to verify
            delay: Delay between attempts in seconds
            
        Returns:
            bool: True if file exists, False otherwise
        """
        import time
        
        log_debug(f"Starting verification for {self.provider}://{self.bucket_name}/{key}")
        for attempt in range(max_attempts):
            try:
                if self.provider == 'aws' and self.aws_handler:
                    self.aws_handler.head_object(Bucket=self.bucket_name, Key=key)
                elif self.provider == 'google' and self.gcs_handler:
                    bucket = self.gcs_handler.bucket(self.bucket_name)
                    blob = bucket.blob(key)
                    blob.reload()  # Will raise exception if blob doesn't exist
                elif self.provider == 'azure' and self.azure_handler:
                    blob_client = self.azure_handler['container_client'].get_blob_client(key)
                    blob_client.get_blob_properties()
                else:
                    raise ValueError(f"No handler available for provider: {self.provider}")
                
                log_debug(f"File verified in {self.provider}: {self.provider}://{self.bucket_name}/{key}")
                return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    log_debug(f"Waiting for file to be available... attempt {attempt + 1}/{max_attempts}")
                    last_error = e
                    time.sleep(delay)
                else:
                    log_debug(f"Could not verify upload after {max_attempts} attempts: {str(e)}")
                    return False
        return False
    
    def upload_file(self, file_path: str, prefix: Optional[str] = None, index: Optional[int] = None, target_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to cloud storage.
        
        Args:
            file_path: Local path to the file
            prefix: Optional prefix (folder) in cloud storage
            index: Optional index for multiple files
            target_name: Optional target filename to use instead of the source filename
            
        Returns:
            Tuple[bool, str]: (success, url_or_error_message)
        """
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            # Determine the key (path in cloud storage)
            filename = target_name or os.path.basename(file_path)
            if index is not None:
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{index}{ext}"
            
            key = filename
            if prefix:
                # Ensure prefix ends with a slash
                if not prefix.endswith('/'):
                    prefix += '/'
                key = f"{prefix}{filename}"
            
            log_debug(f"Uploading {file_path} to {self.provider}://{self.bucket_name}/{key}")
            
            # Get content type
            content_type = mimetypes.guess_type(file_path)[0]
            if not content_type:
                # Default to binary/octet-stream
                content_type = 'application/octet-stream'
            
            # Upload based on provider
            if self.provider == 'aws' and self.aws_handler:
                with open(file_path, 'rb') as file_data:
                    self.aws_handler.upload_fileobj(
                        file_data,
                        self.bucket_name,
                        key,
                        ExtraArgs={'ContentType': content_type}
                    )
                
                # Verify upload
                if self.verify_upload(key):
                    # Generate URL
                    url = f"https://{self.bucket_name}.s3.amazonaws.com/{key}"
                    return True, url
                else:
                    return False, "Failed to verify AWS S3 upload"
                
            elif self.provider == 'google' and self.gcs_handler:
                bucket = self.gcs_handler.bucket(self.bucket_name)
                blob = bucket.blob(key)
                blob.upload_from_filename(file_path, content_type=content_type)
                
                # Verify upload
                if self.verify_upload(key):
                    # Generate URL
                    url = f"https://storage.googleapis.com/{self.bucket_name}/{key}"
                    return True, url
                else:
                    return False, "Failed to verify Google Cloud Storage upload"
                
            elif self.provider == 'azure' and self.azure_handler:
                blob_client = self.azure_handler['container_client'].get_blob_client(key)
                # Use proper ContentSettings object instead of dictionary
                # Added: 2025-05-07T15:21:30-04:00 - Fix Azure content settings
                from azure.storage.blob import ContentSettings
                content_settings = ContentSettings(content_type=content_type)
                with open(file_path, 'rb') as file_data:
                    blob_client.upload_blob(file_data, overwrite=True, content_settings=content_settings)
                
                # Verify upload
                if self.verify_upload(key):
                    # Generate URL
                    account_name = os.getenv('AZURE_STORAGE_ACCOUNT')
                    container_name = self.azure_handler['container_name']
                    url = f"https://{account_name}.blob.core.windows.net/{container_name}/{key}"
                    return True, url
                else:
                    return False, "Failed to verify Azure Blob Storage upload"
            else:
                return False, f"No handler available for provider: {self.provider}"
                
        except Exception as e:
            error_message = f"Error uploading file: {str(e)}"
            log_debug(error_message)
            log_debug(traceback.format_exc())
            return False, error_message
