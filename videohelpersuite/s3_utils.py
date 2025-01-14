import os
import boto3
from typing import Optional, Tuple, List
from dotenv import load_dotenv

def _process_secret_key(secret_key: str) -> str:
    """Process AWS secret key by replacing _SLASH_ with /"""
    return secret_key.replace('_SLASH_', '/') if secret_key else ''

class S3Handler:
    def __init__(self, bucket_name: Optional[str] = None):
        self.bucket_name = bucket_name or "emprops-share"
        
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
            current_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Try .env first
            env_path = os.path.join(current_dir, '.env')
            if os.path.exists(env_path):
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
                    load_dotenv(env_local_path)
                    secret_key = secret_key or _process_secret_key(os.getenv('AWS_SECRET_ACCESS_KEY_ENCODED', ''))
                    if not secret_key:
                        secret_key = secret_key or os.getenv('AWS_SECRET_ACCESS_KEY', '')
                    access_key = access_key or os.getenv('AWS_ACCESS_KEY_ID', '')
                    region = region or os.getenv('AWS_DEFAULT_REGION', '')
        
        # Set default region if still not set
        region = region or 'us-east-1'
        
        # print(f"[S3Handler] Environment variables:")
        # print(f"AWS_ACCESS_KEY_ID: {'*' * len(access_key) if access_key else 'Not set'}")
        # print(f"AWS_SECRET_ACCESS_KEY: {'*' * len(secret_key) if secret_key else 'Not set'}")
        # print(f"AWS_DEFAULT_REGION: {region if region else 'Not set'}")
        # print(f"S3_BUCKET_NAME: {self.bucket_name}")
        
        if not all([access_key, secret_key]):
            missing = []
            if not access_key: missing.append('AWS_ACCESS_KEY_ID')
            if not secret_key: missing.append('AWS_SECRET_ACCESS_KEY')
            raise ValueError(f"Missing required AWS environment variables: {', '.join(missing)}")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )

    def verify_s3_upload(self, bucket: str, key: str, max_attempts: int = 5, delay: float = 1) -> bool:
        """Verify that a file exists in S3 by checking with head_object"""
        import time
        
        # print(f"[S3Handler] Starting verification for s3://{bucket}/{key}")
        for attempt in range(max_attempts):
            try:
                response = self.s3_client.head_object(Bucket=bucket, Key=key)
                # print(f"[S3Handler] File verified in S3: s3://{bucket}/{key}")
                # print(f"[S3Handler] File size: {response.get('ContentLength', 'unknown')} bytes")
                return True
            except Exception as e:
                if attempt < max_attempts - 1:
                    # print(f"[S3Handler] Waiting for S3 file to be available... attempt {attempt + 1}/{max_attempts}")
                    last_error = e
                    time.sleep(delay)
                else:
                    # print(f"[S3Handler] Could not verify S3 upload after {max_attempts} attempts")
                    raise e
        return False

    def upload_file(self, file_path: str, s3_prefix: Optional[str] = None, index: Optional[int] = None, target_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_path: Local path to the file
            s3_prefix: Optional prefix (folder) in S3 bucket
            index: Optional index for multiple files
            target_name: Optional target filename to use instead of the source filename
            
        Returns:
            Tuple of (success: bool, url: str)
        """
        try:
            if not os.path.exists(file_path):
                # print(f"[S3Handler] File not found: {file_path}")
                return False, f"File not found: {file_path}"
                
            # Get the filename - either target_name or from the path
            filename = target_name if target_name else os.path.basename(file_path)
            
            # Handle multiple files by adding index to filename if provided
            if index is not None and not target_name:  # Don't modify target_name with index
                base, ext = os.path.splitext(filename)
                filename = f"{base}_{index}{ext}"
            
            # Ensure prefix ends with '/' and doesn't start with '/'
            if s3_prefix:
                s3_prefix = s3_prefix.rstrip('/') + '/'
                if s3_prefix.startswith('/'):
                    s3_prefix = s3_prefix[1:]
            
            # Construct the S3 key (path in bucket)
            s3_key = f"{s3_prefix}{filename}" if s3_prefix else filename
            
            # print(f"[S3Handler] Uploading {file_path} to s3://{self.bucket_name}/{s3_key}")
            
            # Upload the file
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            # print(f"[S3Handler] Upload completed, verifying...")
            
            # Verify the upload
            if not self.verify_s3_upload(self.bucket_name, s3_key):
                return False, f"Failed to verify upload of {s3_key}"
            
            # Generate the URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            # print(f"[S3Handler] File available at: {url}")
            
            return True, url
        except Exception as e:
            # print(f"[S3Handler] Error uploading {file_path} to S3: {str(e)}")
            return False, str(e)

    def upload_files(self, file_paths: List[str], s3_prefix: Optional[str] = None) -> List[Tuple[bool, str]]:
        """
        Upload multiple files to S3 bucket
        
        Args:
            file_paths: List of local file paths
            s3_prefix: Optional prefix (folder) in S3 bucket
            
        Returns:
            List of tuples (success: bool, url: str) for each file
        """
        if not isinstance(file_paths, list):
            raise ValueError(f"Expected list of file paths, got {type(file_paths)}")
            
        return [self.upload_file(file_path, s3_prefix, index=i if len(file_paths) > 1 else None) 
                for i, file_path in enumerate(file_paths)]

    def download_file(self, s3_key: str, local_path: str, bucket: Optional[str] = None) -> Tuple[bool, str]:
        """
        Download a file from S3 bucket
        
        Args:
            s3_key: Key (path) of the file in S3
            local_path: Local path to save the file to
            bucket: Optional bucket name (defaults to self.bucket_name)
            
        Returns:
            Tuple of (success: bool, error_message: str)
        """
        try:
            bucket = bucket or self.bucket_name
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(bucket, s3_key, local_path)
            return True, ""
        except Exception as e:
            return False, str(e)
