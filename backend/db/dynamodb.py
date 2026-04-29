"""
DynamoDB Storage Module
Handles persistence of cloud posture scan results in AWS DynamoDB.
"""

# Re-export from __init__ for convenience
from . import (
    DynamoDBStorage,
    save_scan,
    get_all_scans,
    get_scan,
    get_latest_scan,
    get_failed_checks,
    get_compliance_trend,
    TABLE_NAME
)

__all__ = [
    'DynamoDBStorage',
    'save_scan',
    'get_all_scans',
    'get_scan',
    'get_latest_scan',
    'get_failed_checks',
    'get_compliance_trend',
    'TABLE_NAME'
]
