"""
EC2 Scanner Module
Scans AWS EC2 instances across all regions and retrieves key metadata.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EC2Scanner:
    """Scanner for AWS EC2 instances across all regions."""
    
    def __init__(self):
        """Initialize EC2 scanner with boto3 client."""
        try:
            self.ec2_client = boto3.client('ec2')
            logger.info("EC2 Scanner initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS CLI.")
            raise
    
    def get_all_regions(self) -> List[str]:
        """
        Retrieve all available AWS regions.
        
        Returns:
            List of region names
        """
        try:
            response = self.ec2_client.describe_regions()
            regions = [region['RegionName'] for region in response['Regions']]
            logger.info(f"Found {len(regions)} AWS regions")
            return regions
        except ClientError as e:
            logger.error(f"Error fetching regions: {str(e)}")
            return []
    
    def scan_instances_in_region(self, region: str) -> List[Dict[str, Any]]:
        """
        Scan EC2 instances in a specific region.
        
        Args:
            region: AWS region name
            
        Returns:
            List of instance metadata dictionaries
        """
        instances = []
        
        try:
            # Create region-specific EC2 client
            regional_client = boto3.client('ec2', region_name=region)
            
            # Describe all instances in the region
            response = regional_client.describe_instances()
            
            # Extract instance details from reservations
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_data = {
                        'instance_id': instance.get('InstanceId', 'N/A'),
                        'instance_type': instance.get('InstanceType', 'N/A'),
                        'region': region,
                        'state': instance.get('State', {}).get('Name', 'N/A'),
                        'public_ip': instance.get('PublicIpAddress', 'N/A'),
                        'private_ip': instance.get('PrivateIpAddress', 'N/A'),
                        'security_groups': [
                            {
                                'group_id': sg.get('GroupId', 'N/A'),
                                'group_name': sg.get('GroupName', 'N/A')
                            }
                            for sg in instance.get('SecurityGroups', [])
                        ],
                        'launch_time': instance.get('LaunchTime').isoformat() if instance.get('LaunchTime') else 'N/A',
                        'vpc_id': instance.get('VpcId', 'N/A'),
                        'subnet_id': instance.get('SubnetId', 'N/A'),
                        'tags': {tag['Key']: tag['Value'] for tag in instance.get('Tags', [])}
                    }
                    instances.append(instance_data)
            
            logger.info(f"Found {len(instances)} instances in {region}")
            
        except ClientError as e:
            logger.error(f"Error scanning region {region}: {str(e)}")
        
        return instances
    
    def scan_all_instances(self) -> Dict[str, Any]:
        """
        Scan EC2 instances across all AWS regions in parallel.
        
        Returns:
            Dictionary containing scan results and metadata
        """
        logger.info("Starting EC2 instance scan across all regions...")
        
        all_instances = []
        regions = self.get_all_regions()
        
        # Scan regions in parallel using ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as executor:
            # Submit all region scans
            future_to_region = {
                executor.submit(self.scan_instances_in_region, region): region 
                for region in regions
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_region):
                region = future_to_region[future]
                try:
                    regional_instances = future.result()
                    all_instances.extend(regional_instances)
                except Exception as e:
                    logger.error(f"Error scanning region {region}: {str(e)}")
        
        result = {
            'total_instances': len(all_instances),
            'regions_scanned': len(regions),
            'instances': all_instances
        }
        
        logger.info(f"Scan complete. Found {len(all_instances)} total instances across {len(regions)} regions")
        
        return result


def get_ec2_instances() -> Dict[str, Any]:
    """
    Main function to retrieve all EC2 instances.
    
    Returns:
        Dictionary containing EC2 scan results
    """
    try:
        scanner = EC2Scanner()
        return scanner.scan_all_instances()
    except NoCredentialsError:
        return {
            'error': 'AWS credentials not configured. Please run: aws configure',
            'total_instances': 0,
            'regions_scanned': 0,
            'instances': []
        }
    except Exception as e:
        logger.error(f"Unexpected error during EC2 scan: {str(e)}")
        return {
            'error': str(e),
            'total_instances': 0,
            'regions_scanned': 0,
            'instances': []
        }
