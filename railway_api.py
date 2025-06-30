"""
Railway API integration for automated custom domain management
"""
import os
import requests
import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)

class RailwayDomainManager:
    """Manages custom domains via Railway GraphQL API"""
    
    def __init__(self, api_token: str = None):
        self.api_token = api_token or os.environ.get('RAILWAY_API_TOKEN')
        self.endpoint = "https://backboard.railway.com/graphql/v2"
        self.project_id = os.environ.get('RAILWAY_PROJECT_ID')
        self.service_id = os.environ.get('RAILWAY_SERVICE_ID') 
        self.environment_id = os.environ.get('RAILWAY_ENVIRONMENT_ID')
        
        if not self.api_token:
            raise ValueError("RAILWAY_API_TOKEN environment variable is required")
    
    def _make_request(self, query: str, variables: Dict = None) -> Dict[str, Any]:
        """Make GraphQL request to Railway API"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Railway API request failed: {e}")
            raise Exception(f"Railway API error: {str(e)}")
    
    def add_custom_domain(self, domain: str) -> Dict[str, Any]:
        """
        Add a custom domain to Railway service
        
        Args:
            domain: The custom domain to add (e.g., 'links.customer.com')
            
        Returns:
            Dict containing the result of the domain creation
        """
        mutation = """
        mutation CustomDomainCreate($input: CustomDomainCreateInput!) {
            customDomainCreate(input: $input) {
                id
                domain
                status
                cnameCheck {
                    status
                    message
                    link
                }
            }
        }
        """
        
        variables = {
            "input": {
                "projectId": self.project_id,
                "serviceId": self.service_id,
                "environmentId": self.environment_id,
                "domain": domain
            }
        }
        
        logger.info(f"Adding custom domain {domain} to Railway")
        result = self._make_request(mutation, variables)
        
        if result.get('errors'):
            error_msg = result['errors'][0].get('message', 'Unknown error')
            logger.error(f"Failed to add domain {domain}: {error_msg}")
            logger.error(f"Full error response: {result}")
            
            # Handle specific domain conflicts
            if 'already exists' in error_msg.lower():
                logger.info(f"Domain {domain} already exists in Railway")
                # Return success for domains that are already configured
                return {
                    'id': f'existing-{domain}',
                    'domain': domain,
                    'status': 'existing',
                    'message': 'Domain already exists in Railway'
                }
            
            # Handle invalid domain errors
            if 'invalid domain' in error_msg.lower():
                logger.warning(f"Domain {domain} is invalid or has DNS conflicts")
                # Still return a partial success to allow manual configuration
                return {
                    'id': f'manual-{domain}',
                    'domain': domain,
                    'status': 'manual_required',
                    'message': 'Domain requires manual configuration - CNAME may not be set correctly'
                }
            
            # Handle permission errors
            if 'permission' in error_msg.lower() or 'forbidden' in error_msg.lower():
                logger.error(f"Permission denied when adding domain {domain}")
                raise Exception(f"Railway API permission denied. Please check your API token permissions.")
            
            raise Exception(f"Railway domain creation failed: {error_msg}")
        
        domain_data = result.get('data', {}).get('customDomainCreate')
        if domain_data:
            logger.info(f"Successfully added domain {domain} with ID {domain_data.get('id')}")
            return domain_data
        else:
            raise Exception("No domain data returned from Railway API")
    
    def delete_custom_domain(self, domain_id: str) -> bool:
        """
        Delete a custom domain from Railway service
        
        Args:
            domain_id: Railway domain ID to delete
            
        Returns:
            True if successful, False otherwise
        """
        mutation = """
        mutation CustomDomainDelete($id: String!) {
            customDomainDelete(id: $id)
        }
        """
        
        variables = {"id": domain_id}
        
        logger.info(f"Deleting custom domain {domain_id} from Railway")
        result = self._make_request(mutation, variables)
        
        if result.get('errors'):
            error_msg = result['errors'][0].get('message', 'Unknown error')
            logger.error(f"Failed to delete domain {domain_id}: {error_msg}")
            return False
        
        success = result.get('data', {}).get('customDomainDelete', False)
        if success:
            logger.info(f"Successfully deleted domain {domain_id}")
        
        return success
    
    def list_custom_domains(self) -> Dict[str, Any]:
        """
        List all custom domains for the service
        
        Returns:
            Dict containing domains data
        """
        # Note: Domain listing query structure may vary
        # For now, we'll rely on Railway MCP or dashboard for domain listing
        # The create/delete operations work correctly
        logger.info("Domain listing not implemented - use Railway dashboard or MCP")
        return {"customDomains": [], "serviceDomains": []}
    
    def check_domain_status(self, domain_id: str) -> Dict[str, Any]:
        """
        Check the status of a specific custom domain
        
        Args:
            domain_id: Railway domain ID to check
            
        Returns:
            Dict containing domain status information
        """
        domains_data = self.list_custom_domains()
        custom_domains = domains_data.get('customDomains', [])
        
        for domain in custom_domains:
            if domain.get('id') == domain_id:
                return domain
        
        raise Exception(f"Domain {domain_id} not found")

# Singleton instance for easy import
railway_manager = None

def get_railway_manager() -> RailwayDomainManager:
    """Get or create Railway manager instance"""
    global railway_manager
    if railway_manager is None:
        railway_manager = RailwayDomainManager()
    return railway_manager