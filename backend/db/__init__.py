"""
DynamoDB Storage Module
Handles persistence of cloud posture scan results in AWS DynamoDB.
"""

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import json
import logging

# Indian Standard Time (IST) UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

# Configure logging with IST timezone
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [IST] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure all logs use IST
for handler in logging.root.handlers:
    if hasattr(handler, 'formatter') and handler.formatter:
        handler.formatter.converter = lambda *args: datetime.now(IST).timetuple()

# DynamoDB table name
TABLE_NAME = "CloudPostureResults"


class DynamoDBStorage:
    """
    DynamoDB storage handler for cloud posture scan results.
    Provides methods to save and retrieve scan data with historical tracking.
    """
    
    def __init__(self, table_name: str = TABLE_NAME):
        """
        Initialize DynamoDB storage handler.
        
        Args:
            table_name: Name of the DynamoDB table (default: CloudPostureResults)
        """
        try:
            self.dynamodb = boto3.resource('dynamodb')
            self.table_name = table_name
            self.table = self.dynamodb.Table(table_name)
            logger.info(f"DynamoDB storage initialized for table: {table_name}")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS CLI.")
            raise
        except Exception as e:
            logger.error(f"Error initializing DynamoDB: {str(e)}")
            raise
    
    def _convert_floats_to_decimal(self, obj: Any) -> Any:
        """
        Convert float values to Decimal for DynamoDB compatibility.
        DynamoDB doesn't support native Python floats.
        
        Args:
            obj: Object to convert (dict, list, or primitive)
            
        Returns:
            Converted object with Decimals instead of floats
        """
        if isinstance(obj, list):
            return [self._convert_floats_to_decimal(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_floats_to_decimal(value) for key, value in obj.items()}
        elif isinstance(obj, float):
            return Decimal(str(obj))
        else:
            return obj
    
    def _convert_decimal_to_float(self, obj: Any) -> Any:
        """
        Convert Decimal values back to float for JSON serialization.
        Used when retrieving data from DynamoDB.
        
        Args:
            obj: Object to convert (dict, list, or primitive)
            
        Returns:
            Converted object with floats instead of Decimals
        """
        if isinstance(obj, list):
            return [self._convert_decimal_to_float(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_decimal_to_float(value) for key, value in obj.items()}
        elif isinstance(obj, Decimal):
            return float(obj)
        else:
            return obj
    
    def generate_scan_id(self) -> str:
        """
        Generate a unique scan ID based on timestamp (IST).
        
        Format: scan_YYYYMMDD_HHMMSS (IST)
        Example: scan_20260429_190022 (IST)
        
        Returns:
            Unique scan identifier
        """
        timestamp = datetime.now(IST).strftime("%Y%m%d_%H%M%S")
        scan_id = f"scan_{timestamp}"
        logger.info(f"Generated scan_id: {scan_id}")
        return scan_id
    
    def save_scan_results(self, scan_data: Dict[str, Any], scan_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Save cloud posture scan results to DynamoDB.
        
        Args:
            scan_data: Complete scan results (summary + checks)
            scan_id: Optional custom scan ID (auto-generated if not provided)
            
        Returns:
            Dictionary containing scan_id and save status
            
        Example:
            result = storage.save_scan_results({
                'summary': {...},
                'checks': [...]
            })
        """
        try:
            # Generate scan_id if not provided
            if not scan_id:
                scan_id = self.generate_scan_id()
            
            # Add metadata
            item = {
                'scan_id': scan_id,
                'timestamp': datetime.now(IST).isoformat(),
                'scan_type': 'cis_compliance',
                'summary': scan_data.get('summary', {}),
                'checks': scan_data.get('checks', [])
            }
            
            # Convert floats to Decimal for DynamoDB
            item = self._convert_floats_to_decimal(item)
            
            # Save to DynamoDB
            self.table.put_item(Item=item)
            
            logger.info(f"Scan results saved successfully with scan_id: {scan_id}")
            
            return {
                'scan_id': scan_id,
                'status': 'saved',
                'timestamp': item['timestamp'],
                'message': 'Scan results saved to DynamoDB successfully'
            }
            
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code', '')
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"DynamoDB ClientError: {error_code} - {error_msg}")
            
            return {
                'scan_id': scan_id if scan_id else 'unknown',
                'status': 'error',
                'message': f'Failed to save scan results: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error saving scan results: {str(e)}")
            return {
                'scan_id': scan_id if scan_id else 'unknown',
                'status': 'error',
                'message': f'Unexpected error: {str(e)}'
            }
    
    def get_all_scan_results(self, limit: int = 50) -> Dict[str, Any]:
        """
        Retrieve all historical scan results from DynamoDB.
        
        Args:
            limit: Maximum number of scans to retrieve (default: 50)
            
        Returns:
            Dictionary containing list of all scans with metadata
            
        Example:
            results = storage.get_all_scan_results(limit=10)
        """
        try:
            # Scan table (for production, use Query with GSI for better performance)
            response = self.table.scan(Limit=limit)
            
            items = response.get('Items', [])
            
            # Convert Decimal to float for JSON serialization
            items = self._convert_decimal_to_float(items)
            
            # Sort by timestamp (newest first)
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            logger.info(f"Retrieved {len(items)} scan results from DynamoDB")
            
            return {
                'total_scans': len(items),
                'scans': items
            }
            
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"Error retrieving scan results: {error_msg}")
            return {
                'total_scans': 0,
                'scans': [],
                'error': f'Failed to retrieve scans: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving scans: {str(e)}")
            return {
                'total_scans': 0,
                'scans': [],
                'error': f'Unexpected error: {str(e)}'
            }
    
    def get_scan_by_id(self, scan_id: str) -> Dict[str, Any]:
        """
        Retrieve a specific scan result by scan_id.
        
        Args:
            scan_id: Unique identifier of the scan
            
        Returns:
            Dictionary containing the scan data or error message
            
        Example:
            result = storage.get_scan_by_id('scan_20260429_143022')
        """
        try:
            # Get item by partition key
            response = self.table.get_item(Key={'scan_id': scan_id})
            
            if 'Item' not in response:
                logger.warning(f"Scan not found: {scan_id}")
                return {
                    'found': False,
                    'message': f'Scan with ID {scan_id} not found'
                }
            
            item = response['Item']
            
            # Convert Decimal to float for JSON serialization
            item = self._convert_decimal_to_float(item)
            
            logger.info(f"Retrieved scan: {scan_id}")
            
            return {
                'found': True,
                'scan': item
            }
            
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"Error retrieving scan {scan_id}: {error_msg}")
            return {
                'found': False,
                'message': f'Error retrieving scan: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving scan {scan_id}: {str(e)}")
            return {
                'found': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def delete_scan_by_id(self, scan_id: str) -> Dict[str, Any]:
        """
        Delete a specific scan result by scan_id.
        
        Args:
            scan_id: Unique identifier of the scan to delete
            
        Returns:
            Dictionary containing deletion status
        """
        try:
            self.table.delete_item(Key={'scan_id': scan_id})
            
            logger.info(f"Deleted scan: {scan_id}")
            
            return {
                'deleted': True,
                'scan_id': scan_id,
                'message': f'Scan {scan_id} deleted successfully'
            }
            
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"Error deleting scan {scan_id}: {error_msg}")
            return {
                'deleted': False,
                'scan_id': scan_id,
                'message': f'Error deleting scan: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error deleting scan {scan_id}: {str(e)}")
            return {
                'deleted': False,
                'scan_id': scan_id,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def table_exists(self) -> bool:
        """
        Check if the DynamoDB table exists.
        
        Returns:
            True if table exists, False otherwise
        """
        try:
            self.table.load()
            logger.info(f"Table '{self.table_name}' exists")
            return True
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                logger.warning(f"Table '{self.table_name}' does not exist")
                return False
            else:
                raise
    
    def get_latest_scan(self) -> Dict[str, Any]:
        """
        Get the most recent scan result from DynamoDB.
        
        Returns:
            Dictionary containing the latest scan or empty result
            
        Example:
            result = storage.get_latest_scan()
        """
        try:
            # Scan table and get all items (for production, use Query with GSI on timestamp)
            response = self.table.scan()
            items = response.get('Items', [])
            
            if not items:
                logger.info("No scans found in database")
                return {
                    'found': False,
                    'message': 'No scans found in database'
                }
            
            # Convert Decimal to float
            items = self._convert_decimal_to_float(items)
            
            # Sort by timestamp (newest first)
            items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            
            latest_scan = items[0]
            
            logger.info(f"Retrieved latest scan: {latest_scan.get('scan_id')}")
            
            return {
                'found': True,
                'scan': latest_scan
            }
            
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"Error retrieving latest scan: {error_msg}")
            return {
                'found': False,
                'message': f'Error retrieving latest scan: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving latest scan: {str(e)}")
            return {
                'found': False,
                'message': f'Unexpected error: {str(e)}'
            }
    
    def get_failed_checks(self) -> Dict[str, Any]:
        """
        Get all failed checks from the latest scan.
        
        Returns:
            Dictionary containing failed checks and metadata
            
        Example:
            result = storage.get_failed_checks()
        """
        try:
            # Get latest scan
            latest_result = self.get_latest_scan()
            
            if not latest_result.get('found'):
                return {
                    'scan_id': None,
                    'timestamp': None,
                    'total_failed': 0,
                    'failed_checks': [],
                    'message': 'No scans found in database'
                }
            
            latest_scan = latest_result['scan']
            scan_id = latest_scan.get('scan_id')
            timestamp = latest_scan.get('timestamp')
            all_checks = latest_scan.get('checks', [])
            
            # Filter only failed checks
            failed_checks = [
                check for check in all_checks 
                if check.get('status') == 'FAIL'
            ]
            
            logger.info(f"Found {len(failed_checks)} failed checks in latest scan {scan_id}")
            
            return {
                'scan_id': scan_id,
                'timestamp': timestamp,
                'total_failed': len(failed_checks),
                'failed_checks': failed_checks,
                'message': 'Success' if failed_checks else 'No failed checks - 100% compliance!'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving failed checks: {str(e)}")
            return {
                'scan_id': None,
                'timestamp': None,
                'total_failed': 0,
                'failed_checks': [],
                'message': f'Error: {str(e)}'
            }
    
    def get_compliance_trend(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get historical compliance score trend.
        
        Args:
            limit: Number of recent scans to include (default: 10)
            
        Returns:
            Dictionary containing compliance trend data
            
        Example:
            result = storage.get_compliance_trend(limit=5)
        """
        try:
            # Get all scans
            response = self.table.scan()
            items = response.get('Items', [])
            
            if not items:
                logger.info("No scans found for trend analysis")
                return {
                    'total_scans': 0,
                    'trend': [],
                    'average_score': 0,
                    'message': 'No scans found in database'
                }
            
            # Convert Decimal to float
            items = self._convert_decimal_to_float(items)
            
            # Sort by timestamp (oldest first for trend visualization)
            items.sort(key=lambda x: x.get('timestamp', ''))
            
            # Take last N scans
            recent_scans = items[-limit:] if len(items) > limit else items
            
            # Extract trend data
            trend_data = []
            for scan in recent_scans:
                summary = scan.get('summary', {})
                trend_data.append({
                    'scan_id': scan.get('scan_id'),
                    'timestamp': scan.get('timestamp'),
                    'compliance_score': summary.get('compliance_score', 0),
                    'passed': summary.get('passed', 0),
                    'failed': summary.get('failed', 0),
                    'total_checks': summary.get('total_checks', 0)
                })
            
            # Calculate average compliance score
            scores = [item['compliance_score'] for item in trend_data]
            average_score = sum(scores) / len(scores) if scores else 0
            
            logger.info(f"Retrieved compliance trend for {len(trend_data)} scans")
            
            return {
                'total_scans': len(items),
                'scans_in_trend': len(trend_data),
                'trend': trend_data,
                'average_score': round(average_score, 2),
                'latest_score': trend_data[-1]['compliance_score'] if trend_data else 0,
                'oldest_score': trend_data[0]['compliance_score'] if trend_data else 0,
                'improvement': round(trend_data[-1]['compliance_score'] - trend_data[0]['compliance_score'], 2) if len(trend_data) > 1 else 0
            }
            
        except ClientError as e:
            error_msg = e.response.get('Error', {}).get('Message', '')
            logger.error(f"Error retrieving compliance trend: {error_msg}")
            return {
                'total_scans': 0,
                'trend': [],
                'average_score': 0,
                'message': f'Error: {error_msg}'
            }
            
        except Exception as e:
            logger.error(f"Unexpected error retrieving compliance trend: {str(e)}")
            return {
                'total_scans': 0,
                'trend': [],
                'average_score': 0,
                'message': f'Unexpected error: {str(e)}'
            }


# Convenience functions for easy import
def save_scan(scan_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to save scan results."""
    storage = DynamoDBStorage()
    return storage.save_scan_results(scan_data)


def get_all_scans(limit: int = 50) -> Dict[str, Any]:
    """Convenience function to get all scan results."""
    storage = DynamoDBStorage()
    return storage.get_all_scan_results(limit)


def get_scan(scan_id: str) -> Dict[str, Any]:
    """Convenience function to get a specific scan."""
    storage = DynamoDBStorage()
    return storage.get_scan_by_id(scan_id)


def get_latest_scan() -> Dict[str, Any]:
    """Convenience function to get the most recent scan."""
    storage = DynamoDBStorage()
    return storage.get_latest_scan()


def get_failed_checks() -> Dict[str, Any]:
    """Convenience function to get failed checks from latest scan."""
    storage = DynamoDBStorage()
    return storage.get_failed_checks()


def get_compliance_trend(limit: int = 10) -> Dict[str, Any]:
    """Convenience function to get compliance trend."""
    storage = DynamoDBStorage()
    return storage.get_compliance_trend(limit)
