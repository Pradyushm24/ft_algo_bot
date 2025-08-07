"""
Portfolio Management Module
Handles portfolio tracking, position management, and order execution
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json

logger = logging.getLogger(__name__)

class PortfolioManager:
    """
    Manages portfolio positions, orders, and P&L tracking
    """
    
    def __init__(self, auth, config: Dict[str, Any]):
        """
        Initialize portfolio manager
        
        Args:
            auth: FlattradeAuth instance
            config (Dict[str, Any]): Configuration dictionary
        """
        self.auth = auth
        self.config = config
        
        # Portfolio state
        self.positions = {}  # Open positions
        self.orders = {}     # Order history
        self.cash_balance = 0.0
        self.initial_capital = 100000.0  # Default ₹1 lakh
        self.total_value = self.initial_capital
        
        # Trading configuration
        self.paper_trading = config.get('trading', {}).get('paper_trading', True)
        
        # P&L tracking
        self.realized_pnl = 0.0
        self.unrealized_pnl = 0.0
        self.daily_pnl = 0.0
        self.total_pnl = 0.0
        
        # Order management
        self.order_counter = 0
        self.pending_orders = {}
        
        # Performance tracking
        self.trades_history = []
        self.equity_curve = []
        
        logger.info("Portfolio manager initialized")

    def initialize(self) -> bool:
        """
        Initialize portfolio with current positions and balance
        
        Returns:
            bool: True if initialization successful
        """
        try:
            if not self.auth.is_authenticated():
                logger.error("Authentication required for portfolio initialization")
                return False
            
            # Get initial capital from config
            self.initial_capital = self.config.get('backtesting', {}).get('initial_capital', 100000.0)
            self.cash_balance = self.initial_capital
            self.total_value = self.initial_capital
            
            if not self.paper_trading:
                # Get actual positions and balance from API
                if not self._fetch_live_portfolio():
                    logger.warning("Failed to fetch live portfolio, using paper trading mode")
                    self.paper_trading = True
            
            # Initialize equity curve
            self.equity_curve.append({
                'timestamp': datetime.now(),
                'value': self.total_value,
                'pnl': 0.0
            })
            
            logger.info(f"Portfolio initialized with ₹{self.total_value:,.2f}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing portfolio: {e}")
            return False

    def _fetch_live_portfolio(self) -> bool:
        """
        Fetch live portfolio data from Flattrade API
        
        Returns:
            bool: True if successful
        """
        try:
            # Get positions
            positions_response = self.auth.make_authenticated_request(
                'PositionBook',
                data={'uid': self.auth.user_id}
            )
            
            if positions_response:
                self._process_positions_response(positions_response)
            
            # Get account balance
            balance_response = self.auth.make_authenticated_request(
                'Limits',
                data={'uid': self.auth.user_id, 'actid': self.auth.user_id}
            )
            
            if balance_response:
                self._process_balance_response(balance_response)
            
            return True
            
        except Exception as e:
            logger.error(f"Error fetching live portfolio: {e}")
            return False

    def _process_positions_response(self, response: Dict[str, Any]):
        """Process positions response from API"""
        try:
            # Process actual positions from Flattrade API
            # This is a simplified implementation
            if 'positions' in response:
                for pos in response['positions']:
                    symbol = pos.get('tsym', '')
                    if symbol:
                        self.positions[symbol] = {
                            'symbol': symbol,
                            'quantity': int(pos.get('netqty', 0)),
                            'entry_price': float(pos.get('avgprc', 0)),
                            'current_price': float(pos.get('lp', 0)),
                            'side': 'LONG' if int(pos.get('netqty', 0)) > 0 else 'SHORT',
                            'entry_time': datetime.now(),  # You'd parse actual time
                            'pnl': float(pos.get('rpnl', 0))
                        }
            
        except Exception as e:
            logger.error(f"Error processing positions response: {e}")

    def _process_balance_response(self, response: Dict[str, Any]):
        """Process balance response from API"""
        try:
            # Process account balance from API response
            if 'cash' in response:
                self.cash_balance = float(response['cash'])
            
            if 'marginused' in response:
                margin_used = float(response['marginused'])
                self.total_value = self.cash_balance + margin_used
            
        except Exception as e:
            logger.error(f"Error processing balance response: {e}")

    def place_order(self, symbol: str, action: str, quantity: int, 
                   price: float, order_type: str = 'LIMIT') -> Optional[str]:
        """
        Place a trading order
        
        Args:
            symbol (str): Symbol to trade
            action (str): BUY or SELL
            quantity (int): Quantity to trade
            price (float): Order price
            order_type (str): Order type (LIMIT, MARKET)
            
        Returns:
            Optional[str]: Order ID if successful, None otherwise
        """
        try:
            if quantity <= 0 or price <= 0:
                logger.error("Invalid order parameters")
                return None
            
            # Generate order ID
            self.order_counter += 1
            order_id = f"ORD_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.order_counter:04d}"
            
            # Create order object
            order = {
                'order_id': order_id,
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_type': order_type,
                'status': 'PENDING',
                'timestamp': datetime.now(),
                'filled_quantity': 0,
                'remaining_quantity': quantity,
                'avg_fill_price': 0.0
            }
            
            if self.paper_trading:
                # Simulate order execution
                return self._execute_paper_order(order)
            else:
                # Place real order via API
                return self._place_live_order(order)
                
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return None

    def _execute_paper_order(self, order: Dict[str, Any]) -> str:
        """
        Execute order in paper trading mode
        
        Args:
            order (Dict[str, Any]): Order to execute
            
        Returns:
            str: Order ID
        """
        try:
            order_id = order['order_id']
            symbol = order['symbol']
            action = order['action']
            quantity = order['quantity']
            price = order['price']
            
            # Calculate order value
            order_value = quantity * price
            
            # Check available balance for buy orders
            if action.upper() == 'BUY':
                if order_value > self.cash_balance:
                    order['status'] = 'REJECTED'
                    order['reject_reason'] = 'Insufficient funds'
                    logger.warning(f"Order rejected: Insufficient funds for {order_id}")
                    return order_id
            
            # Execute the order immediately (simplified)
            order['status'] = 'FILLED'
            order['filled_quantity'] = quantity
            order['remaining_quantity'] = 0
            order['avg_fill_price'] = price
            order['fill_time'] = datetime.now()
            
            # Update positions and cash
            self._update_position_from_order(order)
            
            # Store order
            self.orders[order_id] = order
            
            # Add to trades history
            self.trades_history.append({
                'timestamp': order['fill_time'],
                'symbol': symbol,
                'action': action,
                'quantity': quantity,
                'price': price,
                'order_id': order_id
            })
            
            logger.info(f"Paper order executed: {action} {quantity} {symbol} at ₹{price:.2f}")
            return order_id
            
        except Exception as e:
            logger.error(f"Error executing paper order: {e}")
            return order['order_id']

    def _place_live_order(self, order: Dict[str, Any]) -> Optional[str]:
        """
        Place live order via Flattrade API
        
        Args:
            order (Dict[str, Any]): Order to place
            
        Returns:
            Optional[str]: Order ID if successful
        """
        try:
            # Prepare order data for Flattrade API
            order_data = {
                'uid': self.auth.user_id,
                'actid': self.auth.user_id,
                'exch': 'NSE',  # Default exchange
                'tsym': order['symbol'],
                'qty': str(order['quantity']),
                'prc': str(order['price']),
                'prd': 'I',  # Intraday
                'trantype': order['action'],
                'prctyp': 'LMT' if order['order_type'] == 'LIMIT' else 'MKT',
                'ordersource': 'API'
            }
            
            # Place order via API
            response = self.auth.make_authenticated_request('PlaceOrder', data=order_data)
            
            if response and response.get('stat') == 'Ok':
                # Update order with API response
                order['api_order_id'] = response.get('norenordno')
                order['status'] = 'PLACED'
                
                # Store in pending orders
                self.pending_orders[order['order_id']] = order
                
                logger.info(f"Live order placed: {order['order_id']}")
                return order['order_id']
            else:
                error_msg = response.get('emsg', 'Unknown error') if response else 'API call failed'
                order['status'] = 'REJECTED'
                order['reject_reason'] = error_msg
                logger.error(f"Order placement failed: {error_msg}")
                return order['order_id']
                
        except Exception as e:
            logger.error(f"Error placing live order: {e}")
            return None

    def _update_position_from_order(self, order: Dict[str, Any]):
        """
        Update positions based on executed order
        
        Args:
            order (Dict[str, Any]): Executed order
        """
        try:
            symbol = order['symbol']
            action = order['action']
            quantity = order['filled_quantity']
            price = order['avg_fill_price']
            
            if symbol not in self.positions:
                # New position
                self.positions[symbol] = {
                    'symbol': symbol,
                    'quantity': 0,
                    'entry_price': 0.0,
                    'current_price': price,
                    'side': None,
                    'entry_time': order['fill_time'],
                    'pnl': 0.0,
                    'unrealized_pnl': 0.0
                }
            
            position = self.positions[symbol]
            
            if action.upper() == 'BUY':
                if position['quantity'] >= 0:
                    # Adding to long position or new long position
                    total_value = (position['quantity'] * position['entry_price']) + (quantity * price)
                    total_quantity = position['quantity'] + quantity
                    position['entry_price'] = total_value / total_quantity if total_quantity > 0 else price
                    position['quantity'] = total_quantity
                    position['side'] = 'LONG'
                    
                    # Update cash
                    self.cash_balance -= quantity * price
                else:
                    # Covering short position
                    if abs(position['quantity']) >= quantity:
                        # Partial or full cover
                        position['quantity'] += quantity
                        self.cash_balance -= quantity * price
                        
                        # Calculate realized P&L for covered portion
                        realized_pnl = quantity * (position['entry_price'] - price)
                        self.realized_pnl += realized_pnl
                        
                        if position['quantity'] == 0:
                            # Position fully closed
                            del self.positions[symbol]
                    else:
                        # Cover all short and go long
                        cover_quantity = abs(position['quantity'])
                        long_quantity = quantity - cover_quantity
                        
                        # Realized P&L from covering short
                        realized_pnl = cover_quantity * (position['entry_price'] - price)
                        self.realized_pnl += realized_pnl
                        
                        # New long position
                        position['quantity'] = long_quantity
                        position['entry_price'] = price
                        position['side'] = 'LONG'
                        
                        self.cash_balance -= quantity * price
            
            else:  # SELL
                if position['quantity'] <= 0:
                    # Adding to short position or new short position
                    total_value = (abs(position['quantity']) * position['entry_price']) + (quantity * price)
                    total_quantity = abs(position['quantity']) + quantity
                    position['entry_price'] = total_value / total_quantity if total_quantity > 0 else price
                    position['quantity'] = -total_quantity
                    position['side'] = 'SHORT'
                    
                    # Update cash
                    self.cash_balance += quantity * price
                else:
                    # Selling long position
                    if position['quantity'] >= quantity:
                        # Partial or full sale
                        position['quantity'] -= quantity
                        self.cash_balance += quantity * price
                        
                        # Calculate realized P&L for sold portion
                        realized_pnl = quantity * (price - position['entry_price'])
                        self.realized_pnl += realized_pnl
                        
                        if position['quantity'] == 0:
                            # Position fully closed
                            del self.positions[symbol]
                    else:
                        # Sell all long and go short
                        sell_quantity = position['quantity']
                        short_quantity = quantity - sell_quantity
                        
                        # Realized P&L from selling long
                        realized_pnl = sell_quantity * (price - position['entry_price'])
                        self.realized_pnl += realized_pnl
                        
                        # New short position
                        position['quantity'] = -short_quantity
                        position['entry_price'] = price
                        position['side'] = 'SHORT'
                        
                        self.cash_balance += quantity * price
            
            # Update position current price
            if symbol in self.positions:
                self.positions[symbol]['current_price'] = price
            
        except Exception as e:
            logger.error(f"Error updating position from order: {e}")

    def update(self):
        """Update portfolio with current market prices"""
        try:
            # Update unrealized P&L for all positions
            total_unrealized_pnl = 0.0
            
            for symbol, position in self.positions.items():
                # Get current market price (you'd get this from market data manager)
                # For now, we'll use the stored current price
                current_price = position.get('current_price', position['entry_price'])
                
                # Calculate unrealized P&L
                quantity = position['quantity']
                entry_price = position['entry_price']
                
                if quantity > 0:  # Long position
                    unrealized_pnl = quantity * (current_price - entry_price)
                else:  # Short position
                    unrealized_pnl = abs(quantity) * (entry_price - current_price)
                
                position['unrealized_pnl'] = unrealized_pnl
                total_unrealized_pnl += unrealized_pnl
            
            self.unrealized_pnl = total_unrealized_pnl
            
            # Calculate total portfolio value
            positions_value = sum(
                abs(pos['quantity']) * pos['current_price'] 
                for pos in self.positions.values()
            )
            
            self.total_value = self.cash_balance + positions_value + self.unrealized_pnl
            self.total_pnl = self.realized_pnl + self.unrealized_pnl
            
            # Update equity curve
            self.equity_curve.append({
                'timestamp': datetime.now(),
                'value': self.total_value,
                'pnl': self.total_pnl
            })
            
            # Keep only recent equity curve data (last 1000 points)
            if len(self.equity_curve) > 1000:
                self.equity_curve = self.equity_curve[-1000:]
                
        except Exception as e:
            logger.error(f"Error updating portfolio: {e}")

    def get_open_positions(self) -> List[Dict[str, Any]]:
        """
        Get all open positions
        
        Returns:
            List[Dict[str, Any]]: List of open positions
        """
        return list(self.positions.values())

    def get_position(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get position for specific symbol
        
        Args:
            symbol (str): Symbol to get position for
            
        Returns:
            Optional[Dict[str, Any]]: Position data or None
        """
        return self.positions.get(symbol)

    def close_position(self, symbol: str) -> bool:
        """
        Close position for a symbol
        
        Args:
            symbol (str): Symbol to close position for
            
        Returns:
            bool: True if successful
        """
        try:
            if symbol not in self.positions:
                logger.warning(f"No position found for {symbol}")
                return False
            
            position = self.positions[symbol]
            quantity = abs(position['quantity'])
            current_price = position['current_price']
  