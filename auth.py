"""
Flattrade API Authentication Module
Handles authentication and session management for Flattrade API
"""

import requests
import json
import hashlib
import logging
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FlattradeAuth:
    """
    Flattrade API Authentication class
    Manages login, session tokens, and API request authentication
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize Flattrade authentication
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config = self._load_config(config_file)
        self.session_token = None
        self.request_token = None
        self.access_token = None
        self.feed_token = None
        self.session = requests.Session()
        self.base_url = "https://piconnect.flattrade.in/PiConnectTP"
        
        # Get credentials from environment or config
        self.user_id = os.getenv('FLATTRADE_USER_ID', self.config.get('FT040233', ''))
        self.password = os.getenv('FLATTRADE_PASSWORD', self.config.get('Vinit2@', ''))
        self.totp_key = os.getenv('FLATTRADE_TOTP_KEY', self.config.get('5A5A34TP43CU74G6VHJ5IA6ILAA7442N', ''))
        self.api_key = os.getenv('FLATTRADE_API_KEY', self.config.get('a2f996137c6941d1a548abe55908afb9', ''))
        self.api_secret = os.getenv('FLATTRADE_API_SECRET', self.config.get('2025.c5a03507a5a34b1e9bb831c0135c9b8e87ae869115d01229', ''))
        
        logger.info("Flattrade authentication initialized")

    def _load_config(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file
        
        Args:
            config_file (str): Path to config file
            
        Returns:
            Dict[str, Any]: Configuration dictionary
        """
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(f"Config file {config_file} not found, using environment variables")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing config file: {e}")
            return {}

    def generate_checksum(self, data: Dict[str, str]) -> str:
        """
        Generate checksum for API requests
        
        Args:
            data (Dict[str, str]): Request data
            
        Returns:
            str: Generated checksum
        """
        # Create string from sorted data values + api_secret
        values = [str(data[key]) for key in sorted(data.keys())]
        values.append(self.api_secret)
        checksum_string = '|'.join(values)
        
        # Generate SHA256 hash
        return hashlib.sha256(checksum_string.encode()).hexdigest()

    def get_totp(self) -> str:
        """
        Generate TOTP for two-factor authentication
        
        Returns:
            str: TOTP code
        """
        try:
            import pyotp
            totp = pyotp.TOTP(self.totp_key)
            return totp.now()
        except ImportError:
            logger.error("pyotp library not installed. Install with: pip install pyotp")
            return ""
        except Exception as e:
            logger.error(f"Error generating TOTP: {e}")
            return ""

    def login(self) -> bool:
        """
        Perform login to Flattrade API
        
        Returns:
            bool: True if login successful, False otherwise
        """
        try:
            # Step 1: Get session token
            if not self._get_session_token():
                return False
            
            # Step 2: Login with credentials
            if not self._authenticate_user():
                return False
            
            # Step 3: Get access tokens
            if not self._get_access_tokens():
                return False
            
            logger.info("Login successful")
            return True
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def _get_session_token(self) -> bool:
        """
        Get session token from Flattrade
        
        Returns:
            bool: True if successful
        """
        try:
            url = f"{self.base_url}/QuickAuth"
            
            data = {
                'apkversion': '1.0.0',
                'uid': self.user_id,
                'pwd': hashlib.sha256(self.password.encode()).hexdigest(),
                'factor2': self.get_totp(),
                'vc': self.user_id + "_" + self.password,
                'appkey': self.api_key,
                'imei': 'flattrade_python_api',
                'source': 'API'
            }
            
            # Add checksum
            data['checksum'] = self.generate_checksum(data)
            
            response = self.session.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('stat') == 'Ok':
                self.session_token = result.get('susertoken')
                logger.info("Session token obtained successfully")
                return True
            else:
                logger.error(f"Failed to get session token: {result.get('emsg', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error getting session token: {e}")
            return False

    def _authenticate_user(self) -> bool:
        """
        Authenticate user with session token
        
        Returns:
            bool: True if successful
        """
        try:
            url = f"{self.base_url}/UserDetails"
            
            data = {
                'uid': self.user_id,
                'actid': self.user_id
            }
            
            headers = {
                'Authorization': f'Bearer {self.session_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('stat') == 'Ok':
                logger.info("User authentication successful")
                return True
            else:
                logger.error(f"User authentication failed: {result.get('emsg', 'Unknown error')}")
                return False
                
        except Exception as e:
            logger.error(f"Error in user authentication: {e}")
            return False

    def _get_access_tokens(self) -> bool:
        """
        Get access and feed tokens
        
        Returns:
            bool: True if successful
        """
        try:
            # For this implementation, we'll use the session token as access token
            # In a real implementation, you might need additional API calls
            self.access_token = self.session_token
            self.feed_token = self.session_token
            
            logger.info("Access tokens obtained successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error getting access tokens: {e}")
            return False

    def is_authenticated(self) -> bool:
        """
        Check if user is authenticated
        
        Returns:
            bool: True if authenticated
        """
        return self.session_token is not None and self.access_token is not None

    def make_authenticated_request(self, endpoint: str, method: str = 'POST', 
                                 data: Optional[Dict] = None) -> Optional[Dict]:
        """
        Make an authenticated API request
        
        Args:
            endpoint (str): API endpoint
            method (str): HTTP method
            data (Optional[Dict]): Request data
            
        Returns:
            Optional[Dict]: API response or None if failed
        """
        if not self.is_authenticated():
            logger.error("Not authenticated. Please login first.")
            return None
        
        try:
            url = f"{self.base_url}/{endpoint}"
            
            headers = {
                'Authorization': f'Bearer {self.access_token}',
                'Content-Type': 'application/json'
            }
            
            if method.upper() == 'GET':
                response = self.session.get(url, params=data, headers=headers)
            else:
                response = self.session.post(url, json=data or {}, headers=headers)
            
            response.raise_for_status()
            result = response.json()
            
            if result.get('stat') == 'Ok':
                return result
            else:
                logger.error(f"API request failed: {result.get('emsg', 'Unknown error')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error in API request: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error in API response: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
            return None

    def logout(self) -> bool:
        """
        Logout from Flattrade API
        
        Returns:
            bool: True if successful
        """
        try:
            if not self.is_authenticated():
                return True
            
            # Clear tokens
            self.session_token = None
            self.access_token = None
            self.feed_token = None
            
            logger.info("Logged out successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during logout: {e}")
            return False

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information
        
        Returns:
            Dict[str, Any]: Session information
        """
        return {
            'authenticated': self.is_authenticated(),
            'user_id': self.user_id,
            'session_token': bool(self.session_token),
            'access_token': bool(self.access_token),
            'feed_token': bool(self.feed_token)
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize authentication
    auth = FlattradeAuth()
    
    # Test login
    if auth.login():
        print("Login successful!")
        
        # Print session info
        print("Session Info:", auth.get_session_info())
        
        # Test API call (get user details)
        user_details = auth.make_authenticated_request('UserDetails', data={'uid': auth.user_id})
        if user_details:
            print("User details retrieved successfully")
        
        # Logout
        auth.logout()
    else:
        print("Login failed!")