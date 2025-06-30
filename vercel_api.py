"""
Vercel API integration for automated custom domain management
"""
import os
import requests
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class VercelDomainManager:
    """Manages custom domains via Vercel API"""
    
    def __init__(self, api_token: str = None, project_id: str = None):
        self.api_token = api_token or os.environ.get('VERCEL_API_TOKEN')
        self.project_id = project_id or os.environ.get('VERCEL_PROJECT_ID')
        self.team_id = os.environ.get('VERCEL_TEAM_ID')  # Optional, for team accounts
        self.api_base = "https://api.vercel.com"
        
        if not self.api_token:
            raise ValueError("VERCEL_API_TOKEN environment variable is required")
    
    def _make_request(self, method: str, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """Make request to Vercel API"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        # Add team ID if available
        params = {}
        if self.team_id:
            params['teamId'] = self.team_id
        
        url = f"{self.api_base}{endpoint}"
        
        try:
            if method == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method == "POST":
                response = requests.post(url, json=data, headers=headers, params=params)
            elif method == "DELETE":
                response = requests.delete(url, headers=headers, params=params)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Vercel API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise Exception(f"Vercel API error: {str(e)}")
    
    def add_custom_domain(self, domain: str) -> Dict[str, Any]:
        """
        Add a custom domain to Vercel project
        
        Args:
            domain: The custom domain to add (e.g., 'links.customer.com')
            
        Returns:
            Dict containing the domain configuration
        """
        endpoint = f"/v10/projects/{self.project_id}/domains"
        
        data = {
            "name": domain
        }
        
        logger.info(f"Adding custom domain {domain} to Vercel project")
        
        try:
            result = self._make_request("POST", endpoint, data)
            
            logger.info(f"Successfully added domain {domain} to Vercel")
            
            # Check verification status
            if result.get('verified', False):
                return {
                    'id': result.get('domain', domain),
                    'domain': domain,
                    'status': 'verified',
                    'message': 'Domain added and verified successfully'
                }
            else:
                # Domain needs verification
                verification = result.get('verification', [])
                return {
                    'id': result.get('domain', domain),
                    'domain': domain,
                    'status': 'pending_verification',
                    'message': 'Domain added, verification required',
                    'verification': verification
                }
                
        except Exception as e:
            error_msg = str(e)
            
            # Handle domain already exists
            if 'already exists' in error_msg.lower():
                logger.info(f"Domain {domain} already exists in Vercel")
                return {
                    'id': domain,
                    'domain': domain,
                    'status': 'existing',
                    'message': 'Domain already exists in Vercel'
                }
            
            # Handle other errors
            logger.error(f"Failed to add domain {domain}: {error_msg}")
            raise
    
    def verify_domain(self, domain: str) -> Dict[str, Any]:
        """
        Check domain verification status
        
        Args:
            domain: The domain to check
            
        Returns:
            Dict containing verification status
        """
        endpoint = f"/v9/projects/{self.project_id}/domains/{domain}/verify"
        
        try:
            result = self._make_request("POST", endpoint)
            
            return {
                'verified': result.get('verified', False),
                'verification': result.get('verification', [])
            }
            
        except Exception as e:
            logger.error(f"Failed to verify domain {domain}: {e}")
            raise
    
    def remove_custom_domain(self, domain: str) -> bool:
        """
        Remove a custom domain from Vercel project
        
        Args:
            domain: The domain to remove
            
        Returns:
            True if successful
        """
        endpoint = f"/v9/projects/{self.project_id}/domains/{domain}"
        
        try:
            self._make_request("DELETE", endpoint)
            logger.info(f"Successfully removed domain {domain} from Vercel")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove domain {domain}: {e}")
            return False
    
    def list_domains(self) -> Dict[str, Any]:
        """
        List all domains for the project
        
        Returns:
            Dict containing domains list
        """
        endpoint = f"/v9/projects/{self.project_id}/domains"
        
        try:
            result = self._make_request("GET", endpoint)
            return result
            
        except Exception as e:
            logger.error(f"Failed to list domains: {e}")
            raise

# Singleton instance for easy import
vercel_manager = None

def get_vercel_manager() -> VercelDomainManager:
    """Get or create Vercel manager instance"""
    global vercel_manager
    if vercel_manager is None:
        vercel_manager = VercelDomainManager()
    return vercel_manager