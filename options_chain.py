"""
Options Chain Module
Handles options data retrieval and strike price calculations
"""

import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json

logger = logging.getLogger(__name__)

class OptionsChain:
    """
    Manages options chain data and strike price calculations
    """
    
    def __init__(self, auth, config: Dict[str, Any] = None):
        """
        Initialize options chain manager
        
        Args:
            auth: Authentication instance
            config: Configuration dictionary
        """
        self.auth = auth
        self.config = config or {}
        self.options_cache = {}
        self.expiry_dates = []
        
    def get_nifty_option_chain(self, expiry_date: str = None) -> Optional[Dict[str, Any]]:
        """
        Get Nifty option chain data
        
        Args:
            expiry_date (str): Expiry date in YYYY-MM-DD format
            
        Returns:
            Optional[Dict[str, Any]]: Option chain data
        """
        try:
            # Use current weekly expiry if not specified
            if not expiry_date:
                expiry_date = self.get_current_weekly_expiry()
            
            # API call to get option chain
            endpoint = "/OptionChain"
            data = {
                'uid': self.auth.user_id,
                'exch': 'NSE',
                'tsym': 'NIFTY',
                'strprc': '',  # Will get all strikes
                'cnt': '20'    # Number of strikes each side
            }
            
            response = self.auth.make_authenticated_request(endpoint, 'POST', data)
            
            if response and response.get('stat') == 'Ok':
                return response
            else:
                logger.error(f"Failed to get option chain: {response}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting option chain: {e}")
            return None
    
    def get_current_weekly_expiry(self) -> str:
        """
        Get current weekly expiry date (next Thursday)
        
        Returns:
            str: Expiry date in DD-MMM-YY format
        """
        try:
            current_date = datetime.now()
            
            # Find next Thursday
            days_until_thursday = (3 - current_date.weekday()) % 7
            if days_until_thursday == 0 and current_date.hour >= 15:  # After 3 PM on Thursday
                days_until_thursday = 7
            
            expiry_date = current_date + timedelta(days=days_until_thursday)
            return expiry_date.strftime("%d%b%y").upper()
            
        except Exception as e:
            logger.error(f"Error calculating expiry date: {e}")
            return datetime.now().strftime("%d%b%y").upper()
    
    def calculate_option_strikes(self, nifty_price: float, otm_levels: List[int]) -> Dict[str, float]:
        """
        Calculate option strike prices based on Nifty price
        
        Args:
            nifty_price (float): Current Nifty price
            otm_levels (List[int]): OTM levels (e.g., [3, 5] for 3rd and 5th OTM)
            
        Returns:
            Dict[str, float]: Strike prices for different options
        """
        try:
            # Round to nearest 50 for Nifty options
            atm_strike = round(nifty_price / 50) * 50
            
            strikes = {}
            
            for level in otm_levels:
                ce_strike = atm_strike + (level * 50)
                pe_strike = atm_strike - (level * 50)
                
                strikes[f'ce_{level}otm'] = ce_strike
                strikes[f'pe_{level}otm'] = pe_strike
            
            strikes['atm'] = atm_strike
            
            logger.info(f"Calculated strikes for Nifty {nifty_price}: ATM={atm_strike}, Strikes={strikes}")
            return strikes
            
        except Exception as e:
            logger.error(f"Error calculating option strikes: {e}")
            return {}
    
    def get_option_symbols(self, strikes: Dict[str, float], expiry: str = None) -> Dict[str, str]:
        """
        Generate option symbols for given strikes
        
        Args:
            strikes (Dict[str, float]): Strike prices
            expiry (str): Expiry date
            
        Returns:
            Dict[str, str]: Option symbols
        """
        try:
            if not expiry:
                expiry = self.get_current_weekly_expiry()
            
            symbols = {}
            
            for key, strike in strikes.items():
                if 'ce' in key.lower():
                    symbol = f"NSE:NIFTY{expiry}{int(strike)}CE"
                elif 'pe' in key.lower():
                    symbol = f"NSE:NIFTY{expiry}{int(strike)}PE"
                else:
                    continue
                
                symbols[key] = symbol
            
            logger.info(f"Generated option symbols: {symbols}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error generating option symbols: {e}")
            return {}
    
    def get_option_price(self, symbol: str) -> Optional[float]:
        """
        Get current option price
        
        Args:
            symbol (str): Option symbol
            
        Returns:
            Optional[float]: Current price
        """
        try:
            endpoint = "/GetQuotes"
            data = {
                'uid': self.auth.user_id,
                'exch': 'NSE',
                'token': self._get_token_for_symbol(symbol)
            }
            
            response = self.auth.make_authenticated_request(endpoint, 'POST', data)
            
            if response and response.get('stat') == 'Ok':
                return float(response.get('lp', 0))
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting option price for {symbol}: {e}")
            return None
    
    def _get_token_for_symbol(self, symbol: str) -> str:
        """
        Get token for symbol (simplified implementation)
        
        Args:
            symbol (str): Symbol name
            
        Returns:
            str: Token
        """
        # This is a simplified implementation
        # In practice, you'd need to map symbols to tokens using the symbol master
        return symbol.replace("NSE:", "").replace("NIFTY", "26000")
    
    def get_strategy_legs(self, nifty_price: float) -> List[Dict[str, Any]]:
        """
        Get the specific strategy legs for Iron Condor
        
        Args:
            nifty_price (float): Current Nifty price
            
        Returns:
            List[Dict[str, Any]]: Strategy legs
        """
        try:
            # Calculate strikes for 3rd and 5th OTM
            strikes = self.calculate_option_strikes(nifty_price, [3, 5])
            symbols = self.get_option_symbols(strikes)
            
            # Define strategy legs
            legs = [
                {
                    'action': 'BUY',
                    'option_type': 'CE',
                    'strike': strikes['ce_5otm'],
                    'symbol': symbols['ce_5otm'],
                    'description': 'Buy 5th OTM Call'
                },
                {
                    'action': 'SELL',
                    'option_type': 'CE', 
                    'strike': strikes['ce_3otm'],
                    'symbol': symbols['ce_3otm'],
                    'description': 'Sell 3rd OTM Call'
                },
                {
                    'action': 'BUY',
                    'option_type': 'PE',
                    'strike': strikes['pe_5otm'],
                    'symbol': symbols['pe_5otm'],
                    'description': 'Buy 5th OTM Put'
                },
                {
                    'action': 'SELL',
                    'option_type': 'PE',
                    'strike': strikes['pe_3otm'],
                    'symbol': symbols['pe_3otm'],
                    'description': 'Sell 3rd OTM Put'
                }
            ]
            
            logger.info(f"Generated strategy legs for Nifty {nifty_price}")
            return legs
            
        except Exception as e:
            logger.error(f"Error generating strategy legs: {e}")
            return []
    
    def validate_option_symbol(self, symbol: str) -> bool:
        """
        Validate option symbol format
        
        Args:
            symbol (str): Option symbol to validate
            
        Returns:
            bool: True if valid
        """
        try:
            # Basic validation for Nifty option symbol
            if not symbol.startswith('NSE:NIFTY'):
                return False
            
            if not (symbol.endswith('CE') or symbol.endswith('PE')):
                return False
            
            # Extract and validate strike price
            parts = symbol.replace('NSE:NIFTY', '').replace('CE', '').replace('PE', '')
            
            # Should have date and strike
            if len(parts) < 7:  # DDMmmYY + strike
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating option symbol {symbol}: {e}")
            return False


def get_nifty_current_price() -> Optional[float]:
    """
    Get current Nifty 50 price (fallback implementation)
    
    Returns:
        Optional[float]: Current Nifty price
    """
    try:
        # This is a fallback implementation
        # In practice, you'd get this from your market data feed
        
        # For testing, return a reasonable Nifty price
        # You should replace this with actual market data
        return 19500.0  # Example price
        
    except Exception as e:
        logger.error(f"Error getting Nifty price: {e}")
        return None


if __name__ == "__main__":
    # Test the options chain functionality
    print("Testing Options Chain Module")
    
    # Test strike calculation
    nifty_price = 19500.0
    chain = OptionsChain(None)
    
    strikes = chain.calculate_option_strikes(nifty_price, [3, 5])
    print(f"Strikes for Nifty {nifty_price}: {strikes}")
    
    symbols = chain.get_option_symbols(strikes)
    print(f"Option symbols: {symbols}")
    
    legs = chain.get_strategy_legs(nifty_price)
    print(f"Strategy legs:")
    for leg in legs:
        print(f"  {leg['action']} {leg['description']} - {leg['symbol']}")