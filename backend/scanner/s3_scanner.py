"""
S3 Scanner Module
Scans AWS S3 buckets and retrieves security and configuration metadata.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class S3Scanner:
    """Scanner for AWS S3 buckets with security posture analysis."""
    
    def __init__(self):
        """Initialize S3 scanner with boto3 client."""
        try:
            self.s3_client = boto3.client('s3')
            logger.info("S3 Scanner initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS CLI.")
            raise
    
    def get_bucket_encryption(self, bucket_name: str) -> str:
        """
        Check if bucket has encryption enabled.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Encryption status string
        """
        try:
            response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
            rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
            
            if rules:
                encryption_type = rules[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm', 'Unknown')
                return f"Enabled ({encryption_type})"
            else:
                return "Enabled (Unknown Algorithm)"
                
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                return "Not Enabled"
            else:
                logger.warning(f"Error checking encryption for {bucket_name}: {str(e)}")
                return "Unknown"
    
    def get_bucket_public_access(self, bucket_name: str) -> Dict[str, Any]:
        """
        Check if bucket has public access.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Dictionary with public access details
        """
        try:
            # Check public access block configuration
            response = self.s3_client.get_public_access_block(Bucket=bucket_name)
            config = response.get('PublicAccessBlockConfiguration', {})
            
            # All settings should be True for private bucket
            is_private = all([
                config.get('BlockPublicAcls', False),
                config.get('IgnorePublicAcls', False),
                config.get('BlockPublicPolicy', False),
                config.get('RestrictPublicBuckets', False)
            ])
            
            return {
                'access_level': 'Private' if is_private else 'Public',
                'block_public_acls': config.get('BlockPublicAcls', False),
                'ignore_public_acls': config.get('IgnorePublicAcls', False),
                'block_public_policy': config.get('BlockPublicPolicy', False),
                'restrict_public_buckets': config.get('RestrictPublicBuckets', False)
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            if error_code == 'NoSuchPublicAccessBlockConfiguration':
                # No public access block means potentially public
                return {
                    'access_level': 'Potentially Public',
                    'block_public_acls': False,
                    'ignore_public_acls': False,
                    'block_public_policy': False,
                    'restrict_public_buckets': False
                }
            else:
                logger.warning(f"Error checking public access for {bucket_name}: {str(e)}")
                return {
                    'access_level': 'Unknown',
                    'block_public_acls': None,
                    'ignore_public_acls': None,
                    'block_public_policy': None,
                    'restrict_public_buckets': None
                }
    
    def get_bucket_region(self, bucket_name: str) -> str:
        """
        Get the region where the bucket is located.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Region name
        """
        try:
            response = self.s3_client.get_bucket_location(Bucket=bucket_name)
            location = response.get('LocationConstraint')
            
            # If LocationConstraint is None, bucket is in us-east-1
            return location if location else 'us-east-1'
            
        except ClientError as e:
            logger.warning(f"Error getting region for {bucket_name}: {str(e)}")
            return "Unknown"
    
    def get_bucket_versioning(self, bucket_name: str) -> str:
        """
        Check if bucket has versioning enabled.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Versioning status
        """
        try:
            response = self.s3_client.get_bucket_versioning(Bucket=bucket_name)
            status = response.get('Status', 'Disabled')
            return status
            
        except ClientError as e:
            logger.warning(f"Error checking versioning for {bucket_name}: {str(e)}")
            return "Unknown"
    
    def scan_bucket(self, bucket_name: str) -> Dict[str, Any]:
        """
        Scan a single S3 bucket and retrieve metadata.
        
        Args:
            bucket_name: Name of the S3 bucket
            
        Returns:
            Dictionary containing bucket metadata
        """
        logger.info(f"Scanning bucket: {bucket_name}")
        
        # Get bucket details
        public_access_info = self.get_bucket_public_access(bucket_name)
        
        bucket_data = {
            'bucket_name': bucket_name,
            'region': self.get_bucket_region(bucket_name),
            'encryption_status': self.get_bucket_encryption(bucket_name),
            'access_level': public_access_info['access_level'],
            'versioning': self.get_bucket_versioning(bucket_name),
            'public_access_block': {
                'block_public_acls': public_access_info['block_public_acls'],
                'ignore_public_acls': public_access_info['ignore_public_acls'],
                'block_public_policy': public_access_info['block_public_policy'],
                'restrict_public_buckets': public_access_info['restrict_public_buckets']
            }
        }
        
        return bucket_data
    
    def scan_all_buckets(self) -> Dict[str, Any]:
        """
        Scan all S3 buckets in the AWS account.
        
        Returns:
            Dictionary containing scan results and metadata
        """
        logger.info("Starting S3 bucket scan...")
        
        all_buckets = []
        
        try:
            # List all buckets
            response = self.s3_client.list_buckets()
            bucket_list = response.get('Buckets', [])
            
            logger.info(f"Found {len(bucket_list)} S3 buckets")
            
            # Scan each bucket
            for bucket in bucket_list:
                bucket_name = bucket['Name']
                bucket_data = self.scan_bucket(bucket_name)
                bucket_data['creation_date'] = bucket['CreationDate'].isoformat()
                all_buckets.append(bucket_data)
            
        except ClientError as e:
            logger.error(f"Error listing buckets: {str(e)}")
        
        result = {
            'total_buckets': len(all_buckets),
            'buckets': all_buckets
        }
        
        logger.info(f"Scan complete. Found {len(all_buckets)} total buckets")
        
        return result


def get_s3_buckets() -> Dict[str, Any]:
    """
    Main function to retrieve all S3 buckets with security metadata.
    
    Returns:
        Dictionary containing S3 scan results
    """
    try:
        scanner = S3Scanner()
        return scanner.scan_all_buckets()
    except NoCredentialsError:
        return {
            'error': 'AWS credentials not configured. Please run: aws configure',
            'total_buckets': 0,
            'buckets': []
        }
    except Exception as e:
        logger.error(f"Unexpected error during S3 scan: {str(e)}")
        return {
            'error': str(e),
            'total_buckets': 0,
            'buckets': []
        }
