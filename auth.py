': 'application/json'
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
            logger.error(f"Error in user authentication: {d(self) -> bool:
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
