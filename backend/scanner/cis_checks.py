"""
CIS AWS Benchmark Security Checks Module
Performs automated security compliance checks based on CIS AWS Foundations Benchmark.
"""

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from typing import List, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# CIS check metadata: cis_id, severity, remediation
CIS_METADATA = {
    'S3 Bucket Public Access': {
        'cis_id': 'CIS 2.1.5',
        'severity': 'HIGH',
        'remediation': (
            'Enable S3 Block Public Access at the account level: '
            'aws s3api put-public-access-block --bucket BUCKET_NAME '
            '--public-access-block-configuration BlockPublicAcls=true,'
            'IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true. '
            'Also enable account-level block via S3 console → Block Public Access settings for this account.'
        ),
    },
    'S3 Bucket Encryption': {
        'cis_id': 'CIS 2.1.1',
        'severity': 'HIGH',
        'remediation': (
            'Enable default encryption on the bucket: '
            'aws s3api put-bucket-encryption --bucket BUCKET_NAME '
            '--server-side-encryption-configuration \'{"Rules":[{"ApplyServerSideEncryptionByDefault":'
            '{"SSEAlgorithm":"AES256"}}]}\'. '
            'Prefer aws:kms for regulated workloads.'
        ),
    },
    'Root Account MFA': {
        'cis_id': 'CIS 1.5',
        'severity': 'CRITICAL',
        'remediation': (
            'Enable MFA on the AWS root account immediately: '
            '1) Sign in as root. '
            '2) Go to IAM → My Security Credentials. '
            '3) Enable a virtual MFA device (Google Authenticator, Authy). '
            'Use a hardware MFA token for maximum security. '
            'After enabling MFA, restrict root usage to only emergency break-glass scenarios.'
        ),
    },
    'CloudTrail Enabled': {
        'cis_id': 'CIS 3.1',
        'severity': 'HIGH',
        'remediation': (
            'Create a CloudTrail trail covering all regions: '
            'aws cloudtrail create-trail --name management-events '
            '--s3-bucket-name YOUR_LOG_BUCKET --is-multi-region-trail '
            '--enable-log-file-validation && '
            'aws cloudtrail start-logging --name management-events. '
            'Store logs in a dedicated S3 bucket with access logging enabled.'
        ),
    },
    'Security Group - No Open SSH': {
        'cis_id': 'CIS 5.2',
        'severity': 'CRITICAL',
        'remediation': (
            'Remove the 0.0.0.0/0 inbound rule for port 22 (SSH): '
            'aws ec2 revoke-security-group-ingress --group-id SG_ID '
            '--protocol tcp --port 22 --cidr 0.0.0.0/0. '
            'Replace with your specific IP or use AWS Systems Manager Session Manager '
            'for passwordless, keyless, zero-port-22 access.'
        ),
    },
    'Security Group - No Open RDP': {
        'cis_id': 'CIS 5.3',
        'severity': 'CRITICAL',
        'remediation': (
            'Remove the 0.0.0.0/0 inbound rule for port 3389 (RDP): '
            'aws ec2 revoke-security-group-ingress --group-id SG_ID '
            '--protocol tcp --port 3389 --cidr 0.0.0.0/0. '
            'Use AWS Systems Manager Fleet Manager for browser-based RDP without opening port 3389.'
        ),
    },
    'Security Group - No Open SSH/RDP': {
        'cis_id': 'CIS 5.2/5.3',
        'severity': 'CRITICAL',
        'remediation': (
            'Restrict all security groups: remove 0.0.0.0/0 rules for ports 22 and 3389. '
            'Use AWS Systems Manager Session Manager as a zero-trust alternative. '
            'If SSH is required, restrict to specific CIDR ranges (your office IP or VPN range).'
        ),
    },
}


def _enrich_check(check: Dict[str, Any]) -> Dict[str, Any]:
    """Enrich a check result with cis_id, severity, and remediation metadata."""
    check_name = check.get('check_name', '')
    # Match by prefix for dynamic names (e.g. "Security Group - No Open SSH")
    for key, meta in CIS_METADATA.items():
        if check_name.startswith(key) or key in check_name:
            check.setdefault('cis_id', meta['cis_id'])
            check.setdefault('severity', meta['severity'])
            check.setdefault('remediation', meta['remediation'] if check.get('status') != 'PASS' else '')
            return check
    # Default fallback
    check.setdefault('cis_id', 'N/A')
    check.setdefault('severity', 'MEDIUM')
    check.setdefault('remediation', '')
    return check


class CISSecurityChecker:
    """
    CIS AWS Benchmark Security Checker.
    Implements key security checks for cloud posture assessment.
    """
    
    def __init__(self):
        """Initialize AWS service clients for security checks."""
        try:
            self.s3_client = boto3.client('s3')
            self.iam_client = boto3.client('iam')
            self.cloudtrail_client = boto3.client('cloudtrail')
            self.ec2_client = boto3.client('ec2')
            logger.info("CIS Security Checker initialized successfully")
        except NoCredentialsError:
            logger.error("AWS credentials not found. Please configure AWS CLI.")
            raise
    
    def check_s3_public_access(self) -> List[Dict[str, Any]]:
        """
        CIS 2.1.5: Check if S3 buckets are publicly accessible.
        
        SECURITY RISK: Public S3 buckets can expose sensitive data to the internet.
        
        Returns:
            List of check results for each S3 bucket
        """
        logger.info("Running CIS Check: S3 Public Access")
        results = []
        
        try:
            # List all S3 buckets
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            if not buckets:
                results.append({
                    'check_name': 'S3 Bucket Public Access',
                    'status': 'PASS',
                    'resource': 'No buckets found',
                    'evidence': 'No S3 buckets exist in the account'
                })
                return results
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    # Get public access block configuration
                    response = self.s3_client.get_public_access_block(Bucket=bucket_name)
                    config = response.get('PublicAccessBlockConfiguration', {})
                    
                    # Check if all public access is blocked
                    all_blocked = all([
                        config.get('BlockPublicAcls', False),
                        config.get('IgnorePublicAcls', False),
                        config.get('BlockPublicPolicy', False),
                        config.get('RestrictPublicBuckets', False)
                    ])
                    
                    if all_blocked:
                        results.append({
                            'check_name': 'S3 Bucket Public Access',
                            'status': 'PASS',
                            'resource': bucket_name,
                            'evidence': 'All public access blocked'
                        })
                    else:
                        results.append({
                            'check_name': 'S3 Bucket Public Access',
                            'status': 'FAIL',
                            'resource': bucket_name,
                            'evidence': f'Public access not fully blocked: BlockPublicAcls={config.get("BlockPublicAcls")}, IgnorePublicAcls={config.get("IgnorePublicAcls")}, BlockPublicPolicy={config.get("BlockPublicPolicy")}, RestrictPublicBuckets={config.get("RestrictPublicBuckets")}'
                        })
                        
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code == 'NoSuchPublicAccessBlockConfiguration':
                        # No public access block = potentially public
                        results.append({
                            'check_name': 'S3 Bucket Public Access',
                            'status': 'FAIL',
                            'resource': bucket_name,
                            'evidence': 'No public access block configuration found - bucket may be public'
                        })
                    else:
                        results.append({
                            'check_name': 'S3 Bucket Public Access',
                            'status': 'ERROR',
                            'resource': bucket_name,
                            'evidence': f'Error checking public access: {str(e)}'
                        })
                        
        except ClientError as e:
            logger.error(f"Error listing S3 buckets: {str(e)}")
            results.append({
                'check_name': 'S3 Bucket Public Access',
                'status': 'ERROR',
                'resource': 'N/A',
                'evidence': f'Error listing buckets: {str(e)}'
            })
        
        return results
    
    def check_s3_encryption(self) -> List[Dict[str, Any]]:
        """
        CIS 2.1.1: Check if S3 buckets have encryption enabled.
        
        SECURITY RISK: Unencrypted buckets expose data at rest.
        
        Returns:
            List of check results for each S3 bucket
        """
        logger.info("Running CIS Check: S3 Encryption")
        results = []
        
        try:
            # List all S3 buckets
            response = self.s3_client.list_buckets()
            buckets = response.get('Buckets', [])
            
            if not buckets:
                results.append({
                    'check_name': 'S3 Bucket Encryption',
                    'status': 'PASS',
                    'resource': 'No buckets found',
                    'evidence': 'No S3 buckets exist in the account'
                })
                return results
            
            for bucket in buckets:
                bucket_name = bucket['Name']
                
                try:
                    # Get bucket encryption configuration
                    response = self.s3_client.get_bucket_encryption(Bucket=bucket_name)
                    rules = response.get('ServerSideEncryptionConfiguration', {}).get('Rules', [])
                    
                    if rules:
                        encryption_type = rules[0].get('ApplyServerSideEncryptionByDefault', {}).get('SSEAlgorithm', 'Unknown')
                        results.append({
                            'check_name': 'S3 Bucket Encryption',
                            'status': 'PASS',
                            'resource': bucket_name,
                            'evidence': f'Encryption enabled with {encryption_type}'
                        })
                    else:
                        results.append({
                            'check_name': 'S3 Bucket Encryption',
                            'status': 'FAIL',
                            'resource': bucket_name,
                            'evidence': 'Encryption configuration exists but no rules found'
                        })
                        
                except ClientError as e:
                    error_code = e.response.get('Error', {}).get('Code', '')
                    if error_code == 'ServerSideEncryptionConfigurationNotFoundError':
                        results.append({
                            'check_name': 'S3 Bucket Encryption',
                            'status': 'FAIL',
                            'resource': bucket_name,
                            'evidence': 'No encryption configuration found - bucket is not encrypted'
                        })
                    else:
                        results.append({
                            'check_name': 'S3 Bucket Encryption',
                            'status': 'ERROR',
                            'resource': bucket_name,
                            'evidence': f'Error checking encryption: {str(e)}'
                        })
                        
        except ClientError as e:
            logger.error(f"Error listing S3 buckets: {str(e)}")
            results.append({
                'check_name': 'S3 Bucket Encryption',
                'status': 'ERROR',
                'resource': 'N/A',
                'evidence': f'Error listing buckets: {str(e)}'
            })
        
        return results
    
    def check_root_mfa(self) -> List[Dict[str, Any]]:
        """
        CIS 1.5: Check if IAM root account has MFA enabled.
        
        SECURITY RISK: Root account without MFA is vulnerable to compromise.
        
        Returns:
            List with single check result for root MFA status
        """
        logger.info("Running CIS Check: Root Account MFA")
        results = []
        
        try:
            # Get account summary which includes MFA device count
            response = self.iam_client.get_account_summary()
            summary = response.get('SummaryMap', {})
            
            # Check if root account has MFA devices
            account_mfa_enabled = summary.get('AccountMFAEnabled', 0)
            
            if account_mfa_enabled == 1:
                results.append({
                    'check_name': 'IAM Root Account MFA',
                    'status': 'PASS',
                    'resource': 'Root Account',
                    'evidence': 'MFA is enabled on root account'
                })
            else:
                results.append({
                    'check_name': 'IAM Root Account MFA',
                    'status': 'FAIL',
                    'resource': 'Root Account',
                    'evidence': 'MFA is NOT enabled on root account - HIGH RISK'
                })
                
        except ClientError as e:
            logger.error(f"Error checking root MFA: {str(e)}")
            results.append({
                'check_name': 'IAM Root Account MFA',
                'status': 'ERROR',
                'resource': 'Root Account',
                'evidence': f'Error checking MFA status: {str(e)}'
            })
        
        return results
    
    def check_cloudtrail(self) -> List[Dict[str, Any]]:
        """
        CIS 3.1: Check if CloudTrail is enabled.
        
        SECURITY RISK: Without CloudTrail, there's no audit log of AWS API calls.
        
        Returns:
            List with single check result for CloudTrail status
        """
        logger.info("Running CIS Check: CloudTrail Enabled")
        results = []
        
        try:
            # List all CloudTrail trails
            response = self.cloudtrail_client.describe_trails()
            trails = response.get('trailList', [])
            
            if not trails:
                results.append({
                    'check_name': 'CloudTrail Enabled',
                    'status': 'FAIL',
                    'resource': 'No trails found',
                    'evidence': 'No CloudTrail trails configured - no audit logging'
                })
                return results
            
            # Check if at least one trail is logging
            active_trails = []
            for trail in trails:
                trail_name = trail.get('Name', 'Unknown')
                trail_arn = trail.get('TrailARN', '')
                
                try:
                    # Get trail status
                    status_response = self.cloudtrail_client.get_trail_status(Name=trail_arn)
                    is_logging = status_response.get('IsLogging', False)
                    
                    if is_logging:
                        active_trails.append(trail_name)
                        
                except ClientError as e:
                    logger.warning(f"Error checking trail {trail_name}: {str(e)}")
            
            if active_trails:
                results.append({
                    'check_name': 'CloudTrail Enabled',
                    'status': 'PASS',
                    'resource': ', '.join(active_trails),
                    'evidence': f'{len(active_trails)} CloudTrail trail(s) actively logging'
                })
            else:
                results.append({
                    'check_name': 'CloudTrail Enabled',
                    'status': 'FAIL',
                    'resource': 'All trails',
                    'evidence': f'{len(trails)} trail(s) found but none are actively logging'
                })
                
        except ClientError as e:
            logger.error(f"Error checking CloudTrail: {str(e)}")
            results.append({
                'check_name': 'CloudTrail Enabled',
                'status': 'ERROR',
                'resource': 'N/A',
                'evidence': f'Error checking CloudTrail: {str(e)}'
            })
        
        return results
    
    def check_security_groups(self) -> List[Dict[str, Any]]:
        """
        CIS 5.2 & 5.3: Check if Security Groups allow unrestricted access on SSH/RDP.
        
        SECURITY RISK: Open SSH (22) or RDP (3389) to 0.0.0.0/0 allows brute force attacks.
        
        Returns:
            List of check results for security groups with risky rules
        """
        logger.info("Running CIS Check: Security Group Rules")
        results = []
        dangerous_ports = [22, 3389]  # SSH and RDP
        
        try:
            # Get all regions
            regions_response = self.ec2_client.describe_regions()
            regions = [region['RegionName'] for region in regions_response['Regions']]
            
            total_sgs_checked = 0
            risky_sgs = []
            
            # Check security groups in each region
            for region in regions:
                try:
                    regional_client = boto3.client('ec2', region_name=region)
                    response = regional_client.describe_security_groups()
                    security_groups = response.get('SecurityGroups', [])
                    
                    total_sgs_checked += len(security_groups)
                    
                    for sg in security_groups:
                        sg_id = sg.get('GroupId', 'Unknown')
                        sg_name = sg.get('GroupName', 'Unknown')
                        
                        # Check ingress rules
                        for rule in sg.get('IpPermissions', []):
                            from_port = rule.get('FromPort', 0)
                            to_port = rule.get('ToPort', 0)
                            
                            # Check if rule covers dangerous ports
                            for port in dangerous_ports:
                                if from_port <= port <= to_port:
                                    # Check if accessible from anywhere (0.0.0.0/0)
                                    for ip_range in rule.get('IpRanges', []):
                                        cidr = ip_range.get('CidrIp', '')
                                        if cidr == '0.0.0.0/0':
                                            port_name = 'SSH' if port == 22 else 'RDP'
                                            risky_sgs.append({
                                                'sg_id': sg_id,
                                                'sg_name': sg_name,
                                                'region': region,
                                                'port': port,
                                                'port_name': port_name
                                            })
                                            
                                            results.append({
                                                'check_name': f'Security Group - No Open {port_name}',
                                                'status': 'FAIL',
                                                'resource': f'{sg_id} ({sg_name}) in {region}',
                                                'evidence': f'Port {port} ({port_name}) is open to 0.0.0.0/0 - HIGH RISK'
                                            })
                                            break
                                            
                except ClientError as e:
                    logger.warning(f"Error checking security groups in {region}: {str(e)}")
            
            # If no risky security groups found
            if not risky_sgs:
                results.append({
                    'check_name': 'Security Group - No Open SSH/RDP',
                    'status': 'PASS',
                    'resource': f'{total_sgs_checked} security groups checked',
                    'evidence': 'No security groups allow unrestricted SSH (22) or RDP (3389) access'
                })
                
        except ClientError as e:
            logger.error(f"Error checking security groups: {str(e)}")
            results.append({
                'check_name': 'Security Group - No Open SSH/RDP',
                'status': 'ERROR',
                'resource': 'N/A',
                'evidence': f'Error checking security groups: {str(e)}'
            })
        
        return results
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        Run all CIS security checks and aggregate results.
        
        Returns:
            Dictionary containing all check results with summary statistics
        """
        logger.info("Starting comprehensive CIS security check...")
        
        all_results = []
        
        # Run each check and collect results
        all_results.extend(self.check_s3_public_access())
        all_results.extend(self.check_s3_encryption())
        all_results.extend(self.check_root_mfa())
        all_results.extend(self.check_cloudtrail())
        all_results.extend(self.check_security_groups())
        
        # Enrich all results with severity, cis_id, and remediation
        all_results = [_enrich_check(r) for r in all_results]
        
        # Calculate summary statistics
        total_checks = len(all_results)
        passed = sum(1 for r in all_results if r['status'] == 'PASS')
        failed = sum(1 for r in all_results if r['status'] == 'FAIL')
        errors = sum(1 for r in all_results if r['status'] == 'ERROR')
        
        # Calculate compliance score
        compliance_score = (passed / total_checks * 100) if total_checks > 0 else 0
        
        result = {
            'summary': {
                'total_checks': total_checks,
                'passed': passed,
                'failed': failed,
                'errors': errors,
                'compliance_score': round(compliance_score, 2)
            },
            'checks': all_results
        }
        
        logger.info(f"CIS security check complete. Score: {compliance_score:.2f}% ({passed}/{total_checks} passed)")
        
        return result


def run_cis_checks() -> Dict[str, Any]:
    """
    Main function to execute CIS security checks.
    
    Returns:
        Dictionary containing CIS check results and summary
    """
    try:
        checker = CISSecurityChecker()
        return checker.run_all_checks()
    except NoCredentialsError:
        return {
            'error': 'AWS credentials not configured. Please run: aws configure',
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'compliance_score': 0
            },
            'checks': []
        }
    except Exception as e:
        logger.error(f"Unexpected error during CIS checks: {str(e)}")
        return {
            'error': str(e),
            'summary': {
                'total_checks': 0,
                'passed': 0,
                'failed': 0,
                'errors': 0,
                'compliance_score': 0
            },
            'checks': []
        }
