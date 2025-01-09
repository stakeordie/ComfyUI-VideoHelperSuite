import os
import boto3
from typing import Optional, Tuple, List

class S3Handler:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        if not all([os.getenv('AWS_ACCESS_KEY_ID'), os.getenv('AWS_SECRET_ACCESS_KEY'), 
                   os.getenv('AWS_REGION'), os.getenv('S3_BUCKET_NAME')]):
            raise ValueError("Missing required AWS environment variables")

    def upload_file(self, file_path: str, s3_prefix: Optional[str] = None) -> Tuple[bool, str]:
        """
        Upload a file to S3 bucket
        
        Args:
            file_path: Local path to the file
            s3_prefix: Optional prefix (folder) in S3 bucket
            
        Returns:
            Tuple of (success: bool, url: str)
        """
        try:
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
                
            # Get the filename from the path
            filename = os.path.basename(file_path)
            
            # Construct the S3 key (path in bucket)
            s3_key = f"{s3_prefix.rstrip('/')}/{filename}" if s3_prefix else filename
            
            print(f"Uploading {file_path} to s3://{self.bucket_name}/{s3_key}")
            
            # Upload the file
            self.s3_client.upload_file(
                Filename=file_path,
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            # Generate the URL
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
            
            return True, url
        except Exception as e:
            print(f"Error uploading {file_path} to S3: {str(e)}")
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
            
        return [self.upload_file(file_path, s3_prefix) for file_path in file_paths]
