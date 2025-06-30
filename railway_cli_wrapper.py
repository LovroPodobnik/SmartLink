"""
Railway CLI wrapper for domain management
Uses the Railway CLI as a fallback when API fails
"""
import subprocess
import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class RailwayCliManager:
    """Manages Railway domains using the CLI"""
    
    def __init__(self):
        self.project_id = os.environ.get('RAILWAY_PROJECT_ID')
        self.service_id = os.environ.get('RAILWAY_SERVICE_ID')
        self.environment_id = os.environ.get('RAILWAY_ENVIRONMENT_ID')
        
        # Check if Railway CLI is available
        self.cli_available = self._check_cli()
    
    def _check_cli(self) -> bool:
        """Check if Railway CLI is installed"""
        try:
            result = subprocess.run(['railway', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            logger.warning("Railway CLI not found")
            return False
    
    def _run_cli_command(self, args: list) -> Dict[str, Any]:
        """Run a Railway CLI command"""
        if not self.cli_available:
            raise Exception("Railway CLI is not available")
        
        # Add project context
        if self.project_id:
            args.extend(['--project', self.project_id])
        
        try:
            result = subprocess.run(
                ['railway'] + args,
                capture_output=True,
                text=True,
                env={**os.environ, 'RAILWAY_TOKEN': os.environ.get('RAILWAY_API_TOKEN', '')}
            )
            
            if result.returncode != 0:
                logger.error(f"Railway CLI error: {result.stderr}")
                raise Exception(f"Railway CLI command failed: {result.stderr}")
            
            return {
                'success': True,
                'output': result.stdout,
                'error': result.stderr
            }
            
        except Exception as e:
            logger.error(f"Failed to run Railway CLI: {e}")
            raise
    
    def add_custom_domain_cli(self, domain: str) -> Dict[str, Any]:
        """Add a custom domain using Railway CLI"""
        logger.info(f"Attempting to add domain {domain} via Railway CLI")
        
        # Railway CLI command format: railway domain add <domain>
        args = ['domain', 'add', domain]
        
        if self.service_id:
            args.extend(['--service', self.service_id])
        
        try:
            result = self._run_cli_command(args)
            
            if result['success']:
                logger.info(f"Successfully added domain {domain} via CLI")
                return {
                    'id': f'cli-{domain}',
                    'domain': domain,
                    'status': 'success',
                    'message': 'Domain added via Railway CLI'
                }
            
        except Exception as e:
            logger.error(f"Failed to add domain via CLI: {e}")
            # Return a partial success to allow manual configuration
            return {
                'id': f'manual-{domain}',
                'domain': domain,
                'status': 'manual_required',
                'message': f'CLI failed: {str(e)}. Please add domain manually in Railway dashboard.'
            }