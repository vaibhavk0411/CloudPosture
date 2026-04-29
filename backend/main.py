"""
Cloud Posture Scanner - FastAPI Backend
Main application file with API endpoints for AWS resource discovery.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Any
import logging
from datetime import datetime, timedelta, timezone
from threading import Lock

# Indian Standard Time (IST) UTC+5:30
IST = timezone(timedelta(hours=5, minutes=30))

# Import scanner modules
from scanner.ec2_scanner import get_ec2_instances
from scanner.s3_scanner import get_s3_buckets
from scanner.cis_checks import run_cis_checks

# Import database modules
from db.dynamodb import (
    DynamoDBStorage, 
    save_scan, 
    get_all_scans, 
    get_scan,
    get_latest_scan,
    get_failed_checks,
    get_compliance_trend
)

# Configure logging with IST timezone
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [IST] - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Ensure all logs use IST
import logging.config
for handler in logging.root.handlers:
    if hasattr(handler, 'formatter') and handler.formatter:
        handler.formatter.converter = lambda *args: datetime.now(IST).timetuple()

# Simple in-memory cache with TTL (Time To Live)
class SimpleCache:
    def __init__(self):
        self.cache = {}
        self.lock = Lock()
    
    def get(self, key: str, ttl_seconds: int = 300):
        """Get cached value if not expired (default 5 min TTL)"""
        with self.lock:
            if key in self.cache:
                value, expiry = self.cache[key]
                if datetime.now(IST) < expiry:
                    logger.info(f"Cache HIT for {key}")
                    return value
                else:
                    logger.info(f"Cache EXPIRED for {key}")
                    del self.cache[key]
        logger.info(f"Cache MISS for {key}")
        return None
    
    def set(self, key: str, value: Any, ttl_seconds: int = 480):
        """Set cache value with TTL"""
        with self.lock:
            expiry = datetime.now(IST) + timedelta(seconds=ttl_seconds)
            self.cache[key] = (value, expiry)
            logger.info(f"Cache SET for {key} (TTL: {ttl_seconds}s)")
    
    def clear(self, key: str = None):
        """Clear specific key or entire cache"""
        with self.lock:
            if key:
                self.cache.pop(key, None)
                logger.info(f"Cache CLEARED for {key}")
            else:
                self.cache.clear()
                logger.info("Cache CLEARED (all)")

# Initialize cache
cache = SimpleCache()

# Initialize FastAPI application
app = FastAPI(
    title="Cloud Posture Scanner API",
    description="AWS Cloud Security Platform - Resource Discovery, CIS Compliance, Persistent Storage & Analytics",
    version="4.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS middleware (allows frontend to call API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> Dict[str, Any]:
    """
    Root endpoint - API health check.
    
    Returns:
        Welcome message and API status
    """
    return {
        "message": "Cloud Posture Scanner API",
        "status": "running",
        "version": "4.0.0",
        "phase": "Phase 4 - Analytics & Reporting Platform",
        "features": "⚡ Optimized with 5-minute caching & parallel region scanning",
        "endpoints": {
            "summary": "GET /summary - Latest scan summary",
            "failed_checks": "GET /failed-checks - Failed checks from latest scan",
            "trend": "GET /trend - Compliance trend analysis",
            "health": "GET /health - API health check",
            "cache_clear": "POST /cache/clear - Clear cache for fresh data",
            "scan": "POST /scan - Run full scan and save to DynamoDB",
            "scans": "GET /scans - Get all historical scans",
            "scan_by_id": "GET /scan/{scan_id} - Get specific scan",
            "instances": "GET /instances - List EC2 instances (cached)",
            "buckets": "GET /buckets - List S3 buckets (cached)",
            "cis_results": "GET /cis-results - Run CIS checks (cached)",
            "docs": "GET /docs - API documentation"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Returns:
        API health status
    """
    return {
        "status": "healthy",
        "service": "cloud-posture-scanner"
    }


@app.post("/cache/clear")
async def clear_cache() -> Dict[str, Any]:
    """
    Clear all cached data to force fresh scans on next request.
    
    Returns:
        Confirmation message
    """
    cache.clear()
    logger.info("Cache manually cleared via API")
    return {
        "status": "success",
        "message": "Cache cleared - next requests will fetch fresh data"
    }


@app.get("/instances")
async def get_instances() -> Dict[str, Any]:
    """
    Get all EC2 instances across all AWS regions (cached for 5 minutes).
    
    Returns:
        JSON response containing EC2 instance data
        
    Example Response:
        {
            "total_instances": 5,
            "regions_scanned": 16,
            "instances": [
                {
                    "instance_id": "i-1234567890abcdef0",
                    "instance_type": "t2.micro",
                    "region": "us-east-1",
                    "state": "running",
                    "public_ip": "54.123.45.67",
                    "security_groups": [...]
                }
            ]
        }
    """
    try:
        logger.info("Received request to scan EC2 instances")
        
        # Check cache first (5 minute TTL)
        cached = cache.get("ec2_instances", ttl_seconds=300)
        if cached:
            return JSONResponse(status_code=200, content=cached)
        
        # Call EC2 scanner
        result = get_ec2_instances()
        
        # Check for errors
        if 'error' in result:
            logger.error(f"EC2 scan error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        # Cache the result
        cache.set("ec2_instances", result, ttl_seconds=300)
        
        logger.info(f"EC2 scan successful: {result['total_instances']} instances found")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /instances endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/buckets")
async def get_buckets() -> Dict[str, Any]:
    """
    Get all S3 buckets with security posture information (cached for 5 minutes).
    
    Returns:
        JSON response containing S3 bucket data
        
    Example Response:
        {
            "total_buckets": 3,
            "buckets": [
                {
                    "bucket_name": "my-app-bucket",
                    "region": "us-east-1",
                    "encryption_status": "Enabled (AES256)",
                    "access_level": "Private",
                    "versioning": "Enabled"
                }
            ]
        }
    """
    try:
        logger.info("Received request to scan S3 buckets")
        
        # Check cache first (5 minute TTL)
        cached = cache.get("s3_buckets", ttl_seconds=300)
        if cached:
            return JSONResponse(status_code=200, content=cached)
        
        # Call S3 scanner
        result = get_s3_buckets()
        
        # Check for errors
        if 'error' in result:
            logger.error(f"S3 scan error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        # Cache the result
        cache.set("s3_buckets", result, ttl_seconds=300)
        
        logger.info(f"S3 scan successful: {result['total_buckets']} buckets found")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /buckets endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/cis-results")
async def get_cis_results() -> Dict[str, Any]:
    """
    Get CIS AWS Benchmark security compliance check results (cached for 5 minutes).
    
    Performs automated security checks including:
    - S3 bucket public access
    - S3 bucket encryption
    - IAM root account MFA
    - CloudTrail logging
    - Security group rules (SSH/RDP)
    
    Returns:
        JSON response containing security check results and compliance score
        
    Example Response:
        {
            "summary": {
                "total_checks": 10,
                "passed": 7,
                "failed": 3,
                "errors": 0,
                "compliance_score": 70.0
            },
            "checks": [
                {
                    "check_name": "S3 Bucket Encryption",
                    "status": "PASS",
                    "resource": "my-bucket",
                    "evidence": "Encryption enabled with AES256"
                },
                {
                    "check_name": "IAM Root Account MFA",
                    "status": "FAIL",
                    "resource": "Root Account",
                    "evidence": "MFA is NOT enabled on root account - HIGH RISK"
                }
            ]
        }
    """
    try:
        logger.info("Received request to run CIS security checks")
        
        # Check cache first (5 minute TTL)
        cached = cache.get("cis_results", ttl_seconds=300)
        if cached:
            return JSONResponse(status_code=200, content=cached)
        
        # Call CIS security checker
        result = run_cis_checks()
        
        # Check for errors
        if 'error' in result:
            logger.error(f"CIS checks error: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        # Cache the result
        cache.set("cis_results", result, ttl_seconds=300)
        
        compliance_score = result.get('summary', {}).get('compliance_score', 0)
        total_checks = result.get('summary', {}).get('total_checks', 0)
        passed = result.get('summary', {}).get('passed', 0)
        
        logger.info(f"CIS checks complete: {compliance_score}% compliance ({passed}/{total_checks} passed)")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /cis-results endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.post("/scan")
async def run_full_scan() -> Dict[str, Any]:
    """
    Run complete cloud posture scan and save results to DynamoDB.
    Clears cache to ensure fresh data on next request.
    
    This endpoint performs:
    1. CIS security compliance checks
    2. Generates unique scan_id (timestamp-based)
    3. Saves results to DynamoDB
    4. Returns saved scan with scan_id
    
    Returns:
        JSON response containing scan results and DynamoDB save status
        
    Example Response:
        {
            "scan_id": "scan_20260429_143022",
            "timestamp": "2026-04-29T14:30:22.123456",
            "storage_status": "saved",
            "summary": {
                "total_checks": 11,
                "passed": 11,
                "failed": 0,
                "compliance_score": 100.0
            },
            "checks": [...]
        }
    """
    try:
        logger.info("Received request for full cloud posture scan")
        
        # Clear cache to ensure fresh scan
        cache.clear()
        
        # Run CIS security checks
        scan_results = run_cis_checks()
        
        # Check for errors in scan
        if 'error' in scan_results:
            logger.error(f"Scan error: {scan_results['error']}")
            raise HTTPException(
                status_code=500,
                detail=scan_results['error']
            )
        
        # Save to DynamoDB
        logger.info("Saving scan results to DynamoDB...")
        storage_result = save_scan(scan_results)
        
        # Check if save was successful
        if storage_result.get('status') != 'saved':
            logger.warning(f"Failed to save to DynamoDB: {storage_result.get('message')}")
            # Continue but include warning in response
        
        # Prepare response
        response = {
            'scan_id': storage_result.get('scan_id'),
            'timestamp': storage_result.get('timestamp'),
            'storage_status': storage_result.get('status'),
            'storage_message': storage_result.get('message'),
            'summary': scan_results.get('summary', {}),
            'checks': scan_results.get('checks', [])
        }
        
        compliance_score = scan_results.get('summary', {}).get('compliance_score', 0)
        logger.info(f"Full scan complete. Compliance: {compliance_score}%. Saved as: {storage_result.get('scan_id')}")
        
        return JSONResponse(
            status_code=200,
            content=response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /scan endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/scans")
async def get_historical_scans(limit: int = 50) -> Dict[str, Any]:
    """
    Get all historical cloud posture scan results from DynamoDB.
    
    Args:
        limit: Maximum number of scans to retrieve (default: 50, max: 100)
        
    Returns:
        JSON response containing list of all historical scans
        
    Example Response:
        {
            "total_scans": 5,
            "scans": [
                {
                    "scan_id": "scan_20260429_143022",
                    "timestamp": "2026-04-29T14:30:22",
                    "summary": {
                        "compliance_score": 100.0,
                        "passed": 11,
                        "failed": 0
                    }
                }
            ]
        }
    """
    try:
        logger.info(f"Received request for historical scans (limit: {limit})")
        
        # Validate limit
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 10
        
        # Retrieve from DynamoDB
        result = get_all_scans(limit=limit)
        
        # Check for errors
        if 'error' in result:
            logger.error(f"Error retrieving scans: {result['error']}")
            raise HTTPException(
                status_code=500,
                detail=result['error']
            )
        
        total_scans = result.get('total_scans', 0)
        logger.info(f"Retrieved {total_scans} historical scans")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /scans endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/scan/{scan_id}")
async def get_scan_by_id(scan_id: str) -> Dict[str, Any]:
    """
    Get a specific cloud posture scan by scan_id.
    
    Args:
        scan_id: Unique identifier of the scan (e.g., scan_20260429_143022)
        
    Returns:
        JSON response containing the specific scan data
        
    Example Response:
        {
            "found": true,
            "scan": {
                "scan_id": "scan_20260429_143022",
                "timestamp": "2026-04-29T14:30:22",
                "summary": {...},
                "checks": [...]
            }
        }
    """
    try:
        logger.info(f"Received request for scan: {scan_id}")
        
        # Retrieve from DynamoDB
        result = get_scan(scan_id)
        
        # Check if scan was found
        if not result.get('found', False):
            logger.warning(f"Scan not found: {scan_id}")
            raise HTTPException(
                status_code=404,
                detail=result.get('message', f'Scan {scan_id} not found')
            )
        
        logger.info(f"Retrieved scan: {scan_id}")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /scan/{scan_id} endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/summary")
async def get_scan_summary() -> Dict[str, Any]:
    """
    Get summary of the latest cloud posture scan.
    
    Returns latest scan summary including:
    - scan_id
    - timestamp
    - compliance_score
    - total_checks
    - passed/failed/errors counts
    
    Returns:
        JSON response containing latest scan summary
        
    Example Response:
        {
            "scan_id": "scan_20260429_143022",
            "timestamp": "2026-04-29T14:30:22",
            "summary": {
                "total_checks": 11,
                "passed": 11,
                "failed": 0,
                "errors": 0,
                "compliance_score": 100.0
            }
        }
    """
    try:
        logger.info("Received request for latest scan summary")
        
        # Get latest scan
        result = get_latest_scan()
        
        if not result.get('found'):
            logger.warning("No scans found in database")
            raise HTTPException(
                status_code=404,
                detail=result.get('message', 'No scans found in database')
            )
        
        scan = result['scan']
        
        # Extract summary data
        summary_response = {
            'scan_id': scan.get('scan_id'),
            'timestamp': scan.get('timestamp'),
            'scan_type': scan.get('scan_type', 'cis_compliance'),
            'summary': scan.get('summary', {})
        }
        
        compliance_score = scan.get('summary', {}).get('compliance_score', 0)
        logger.info(f"Latest scan summary retrieved: {summary_response['scan_id']} - {compliance_score}% compliance")
        
        return JSONResponse(
            status_code=200,
            content=summary_response
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in /summary endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/failed-checks")
async def get_failed_checks_endpoint() -> Dict[str, Any]:
    """
    Get all failed security checks from the latest scan.
    
    Useful for dashboards showing current security issues.
    
    Returns:
        JSON response containing only failed checks
        
    Example Response:
        {
            "scan_id": "scan_20260429_143022",
            "timestamp": "2026-04-29T14:30:22",
            "total_failed": 2,
            "failed_checks": [
                {
                    "check_name": "IAM Root Account MFA",
                    "status": "FAIL",
                    "resource": "Root Account",
                    "evidence": "MFA is NOT enabled - HIGH RISK"
                },
                {
                    "check_name": "Security Group - No Open SSH",
                    "status": "FAIL",
                    "resource": "sg-123 (web-sg)",
                    "evidence": "Port 22 is open to 0.0.0.0/0"
                }
            ],
            "message": "Success"
        }
    """
    try:
        logger.info("Received request for failed checks")
        
        # Get failed checks from latest scan
        result = get_failed_checks()
        
        total_failed = result.get('total_failed', 0)
        
        if total_failed == 0:
            logger.info("No failed checks found - 100% compliance!")
        else:
            logger.info(f"Found {total_failed} failed checks in latest scan")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in /failed-checks endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/trend")
async def get_compliance_trend_endpoint(limit: int = 10) -> Dict[str, Any]:
    """
    Get historical compliance score trend.
    
    Shows compliance progression over time for dashboard charts.
    
    Args:
        limit: Number of recent scans to include (default: 10, max: 50)
        
    Returns:
        JSON response containing compliance trend data
        
    Example Response:
        {
            "total_scans": 15,
            "scans_in_trend": 10,
            "average_score": 87.5,
            "latest_score": 100.0,
            "oldest_score": 71.43,
            "improvement": 28.57,
            "trend": [
                {
                    "scan_id": "scan_20260428_120000",
                    "timestamp": "2026-04-28T12:00:00",
                    "compliance_score": 71.43,
                    "passed": 5,
                    "failed": 2,
                    "total_checks": 7
                },
                {
                    "scan_id": "scan_20260429_143022",
                    "timestamp": "2026-04-29T14:30:22",
                    "compliance_score": 100.0,
                    "passed": 11,
                    "failed": 0,
                    "total_checks": 11
                }
            ]
        }
    """
    try:
        logger.info(f"Received request for compliance trend (limit: {limit})")
        
        # Validate limit
        if limit > 50:
            limit = 50
        if limit < 1:
            limit = 10
        
        # Get compliance trend
        result = get_compliance_trend(limit=limit)
        
        scans_count = result.get('scans_in_trend', 0)
        average_score = result.get('average_score', 0)
        
        logger.info(f"Compliance trend retrieved: {scans_count} scans, avg score: {average_score}%")
        
        return JSONResponse(
            status_code=200,
            content=result
        )
        
    except Exception as e:
        logger.error(f"Unexpected error in /trend endpoint: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# Custom exception handler for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with structured error responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting Cloud Posture Scanner API...")
    
    # Run the application
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
