"""
Options Trading Bot - Flattrade Integration
Implements specific options strategy with trailing SL and re-entry logic
"""

import logging
import threading
import time
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import signal
import sys

from auth import FlattradeAuth
from market_data import MarketDataManager
from risk_manager import RiskManager
from portfolio import PortfolioManager
from web_interface import WebInterface
from utils import setup_logging, load_config

# Configure logging
setup_logging({'logging': {'level': 'INFO'}})
logger = logging.getLogger(__name__)

class OptionsStrategyBot:
    """
    Options trading bot implementing specific strategy:
    - Buy 5th OTM CE, Sell 3rd OTM CE
    - Buy 5th OTM PE, Sell 3rd OTM PE
    - Lot size: 65
    - Start after 9:20 AM
    - Trailing SL with ₹300 profit threshold, ₹50 buffer, ₹1 trail
    - Re-entry after 5 mins if SL hit
    - Exit on SL hit or forcibly at 2:00 PM on expiry day
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """Initialize the options trading bot"""
        self.config = load_config(config_file)
        self.running = False
        self.trading_enabled = True
        self.paper_trading = self.config.get('paper_trading', True)
        
        # Strategy parameters
        self.lot_size = 65
        self.start_time_hour = 9
        self.start_time_minute = 20
        self.profit_threshold = 300  # ₹300 profit to start trailing SL
        self.trailing_buffer = 50    # ₹50 buffer
        self.trailing_step = 1       # ₹1 trail step
        self.re_entry_delay = 5      # 5 minutes before re-entry
        self.expiry_exit_hour = 14   # 2:00 PM
        self.expiry_exit_minute = 0
        
        # Position tracking
        self.positions = {}
        self.last_sl_hit_time = None
        self.highest_profit = 0
        self.trailing_sl_active = False
        self.current_sl_level = 0
        
        # Pause/Resume control file
        self.pause_file = 'trading_pause.txt'
        
        # Initialize components
        self._initialize_components()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("Options strategy bot initialized")

    def _initialize_components(self):
        """Initialize all bot components"""
        try:
            # Initialize authentication
            self.auth = FlattradeAuth()
            
            # Initialize market data manager
            self.market_data = MarketDataManager(
                auth=self.auth,
                config=self.config.get('market_data', {})
            )
            
            # Initialize risk manager
            self.risk_manager = RiskManager(self.config.get('risk_management', {}))
            
            # Initialize portfolio manager
            self.portfolio = PortfolioManager(
                auth=self.auth,
                config=self.config.get('portfolio', {})
            )
            
            # Initialize web interface
            self.web_interface = WebInterface(
                trading_bot=self,
                config=self.config.get('web_interface', {})
            )
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {e}")
            raise

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info(f"Received signal {signum}, shutting down...")
        self.stop()
        sys.exit(0)

    def start(self) -> bool:
        """Start the trading bot"""
        try:
            logger.info("Starting options trading bot...")
            
            # Authenticate with Flattrade
            if not self.auth.login():
                logger.error("Authentication failed. Cannot start bot.")
                return False
            
            # Start market data feed
            if not self.market_data.start():
                logger.error("Failed to start market data feed")
                return False
            
            # Start web interface in separate thread
            web_thread = threading.Thread(target=self.web_interface.run, daemon=True)
            web_thread.start()
            
            self.running = True
            
            # Start main trading loop
            trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
            trading_thread.start()
            
            logger.info("Options trading bot started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            return False

    def stop(self):
        """Stop the trading bot"""
        logger.info("Stopping options trading bot...")
        
        self.running = False
        
        # Stop market data feed
        if hasattr(self, 'market_data'):
            self.market_data.stop()
        
        # Close all positions if needed
        if hasattr(self, 'portfolio'):
            self.portfolio.close_all_positions()
        
        logger.info("Options trading bot stopped successfully")

    def _trading_loop(self):
        """Main trading loop"""
        logger.info("Trading loop started")
        
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check if trading is paused
                if self._is_trading_paused():
                    time.sleep(10)
                    continue
                
                # Check if we're in trading hours
                if not self._is_trading_time(current_time):
                    time.sleep(30)
                    continue
                
                # Check if it's expiry day and past exit time
                if self._should_force_exit(current_time):
                    self._force_exit_all_positions()
                    continue
                
                # Get current Nifty price for option chain
                nifty_ltp = self._get_nifty_ltp()
                if not nifty_ltp:
                    time.sleep(5)
                    continue
                
                # Check existing positions
                self._monitor_existing_positions()
                
                # Check for new entry opportunity
                if self._should_enter_new_position(current_time):
                    self._enter_options_strategy(nifty_ltp)
                
                # Update trailing stop loss
                self._update_trailing_stop_loss()
                
                time.sleep(1)  # 1-second loop interval
                
            except Exception as e:
                logger.error(f"Error in trading loop: {e}")
                time.sleep(5)
        
        logger.info("Trading loop ended")

    def _is_trading_paused(self) -> bool:
        """Check if trading is paused via file control"""
        return os.path.exists(self.pause_file)

    def _is_trading_time(self, current_time: datetime) -> bool:
        """Check if current time is within trading hours"""
        # Market is open 9:15 AM to 3:30 PM, but we start at 9:20 AM
        start_time = current_time.replace(
            hour=self.start_time_hour, 
            minute=self.start_time_minute, 
            second=0, 
            microsecond=0
        )
        end_time = current_time.replace(hour=15, minute=30, second=0, microsecond=0)
        
        return start_time <= current_time <= end_time

    def _should_force_exit(self, current_time: datetime) -> bool:
        """Check if we should force exit on expiry day"""
        # Check if today is expiry day (Thursday)
        if current_time.weekday() != 3:  # 3 = Thursday
            return False
        
        # Check if past 2:00 PM
        exit_time = current_time.replace(
            hour=self.expiry_exit_hour,
            minute=self.expiry_exit_minute,
            second=0,
            microsecond=0
        )
        
        return current_time >= exit_time

    def _get_nifty_ltp(self) -> Optional[float]:
        """Get current Nifty 50 price"""
        try:
            # Subscribe to Nifty 50 if not already subscribed
            nifty_symbol = "NSE:NIFTY 50"
            market_data = self.market_data.get_symbol_data(nifty_symbol)
            
            if market_data and 'ltp' in market_data:
                return float(market_data['ltp'])
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting Nifty LTP: {e}")
            return None

    def _should_enter_new_position(self, current_time: datetime) -> bool:
        """Check if we should enter a new position"""
        # Don't enter if we already have positions
        if self.positions:
            return False
        
        # Check re-entry delay if SL was hit recently
        if self.last_sl_hit_time:
            time_since_sl = current_time - self.last_sl_hit_time
            if time_since_sl < timedelta(minutes=self.re_entry_delay):
                return False
        
        return True

    def _enter_options_strategy(self, nifty_ltp: float):
        """Enter the options strategy positions"""
        try:
            logger.info(f"Entering options strategy at Nifty LTP: {nifty_ltp}")
            
            # Calculate strike prices
            strikes = self._calculate_option_strikes(nifty_ltp)
            
            # Get option symbols for current expiry
            option_symbols = self._get_option_symbols(strikes)
            
            if not option_symbols:
                logger.error("Could not get option symbols")
                return
            
            # Place orders for the strategy
            orders = [
                # Buy 5th OTM CE
                {
                    'symbol': option_symbols['buy_ce'],
                    'action': 'BUY',
                    'quantity': self.lot_size,
                    'product': 'MIS'
                },
                # Sell 3rd OTM CE
                {
                    'symbol': option_symbols['sell_ce'],
                    'action': 'SELL',
                    'quantity': self.lot_size,
                    'product': 'MIS'
                },
                # Buy 5th OTM PE
                {
                    'symbol': option_symbols['buy_pe'],
                    'action': 'BUY',
                    'quantity': self.lot_size,
                    'product': 'MIS'
                },
                # Sell 3rd OTM PE
                {
                    'symbol': option_symbols['sell_pe'],
                    'action': 'SELL',
                    'quantity': self.lot_size,
                    'product': 'MIS'
                }
            ]
            
            # Execute orders
            order_ids = []
            for order in orders:
                order_id = self.portfolio.place_order(
                    symbol=order['symbol'],
                    action=order['action'],
                    quantity=order['quantity'],
                    price=0.0,  # Market orders use 0 price
                    order_type='MARKET'
                )
                
                if order_id:
                    order_ids.append(order_id)
                    logger.info(f"Placed {order['action']} order for {order['symbol']}")
                else:
                    logger.error(f"Failed to place {order['action']} order for {order['symbol']}")
            
            # Track positions
            if len(order_ids) == 4:  # All orders successful
                self.positions = {
                    'entry_time': datetime.now(),
                    'orders': orders,
                    'order_ids': order_ids,
                    'entry_nifty': nifty_ltp
                }
                
                # Reset trailing SL parameters
                self.highest_profit = 0
                self.trailing_sl_active = False
                self.current_sl_level = 0
                
                logger.info("Options strategy positions entered successfully")
            else:
                logger.error("Not all orders were successful, strategy entry incomplete")
                
        except Exception as e:
            logger.error(f"Error entering options strategy: {e}")

    def _calculate_option_strikes(self, nifty_ltp: float) -> Dict[str, float]:
        """Calculate option strike prices based on Nifty LTP"""
        # Round to nearest 50 for Nifty options
        atm_strike = round(nifty_ltp / 50) * 50
        
        strikes = {
            'sell_ce': float(atm_strike + 150),  # 3rd OTM CE (3 * 50)
            'buy_ce': float(atm_strike + 250),   # 5th OTM CE (5 * 50)
            'sell_pe': float(atm_strike - 150),  # 3rd OTM PE (3 * 50)
            'buy_pe': float(atm_strike - 250)    # 5th OTM PE (5 * 50)
        }
        
        logger.info(f"Calculated strikes - ATM: {atm_strike}, Strikes: {strikes}")
        return strikes

    def _get_option_symbols(self, strikes: Dict[str, float]) -> Optional[Dict[str, str]]:
        """Get option symbols for the calculated strikes"""
        try:
            # Get current expiry date (next Thursday)
            current_date = datetime.now()
            days_until_thursday = (3 - current_date.weekday()) % 7
            if days_until_thursday == 0 and current_date.hour >= 15:  # After 3 PM on Thursday
                days_until_thursday = 7
            
            expiry_date = current_date + timedelta(days=days_until_thursday)
            expiry_str = expiry_date.strftime("%d%b%y").upper()
            
            # Format option symbols (Flattrade format)
            symbols = {
                'buy_ce': f"NSE:NIFTY{expiry_str}{int(strikes['buy_ce'])}CE",
                'sell_ce': f"NSE:NIFTY{expiry_str}{int(strikes['sell_ce'])}CE",
                'buy_pe': f"NSE:NIFTY{expiry_str}{int(strikes['buy_pe'])}PE",
                'sell_pe': f"NSE:NIFTY{expiry_str}{int(strikes['sell_pe'])}PE"
            }
            
            logger.info(f"Option symbols: {symbols}")
            return symbols
            
        except Exception as e:
            logger.error(f"Error getting option symbols: {e}")
            return None

    def _monitor_existing_positions(self):
        """Monitor existing positions for P&L and SL"""
        if not self.positions:
            return
        
        try:
            # Calculate current P&L
            current_pnl = self._calculate_strategy_pnl()
            
            if current_pnl is None:
                return
            
            # Update highest profit for trailing SL
            if current_pnl > self.highest_profit:
                self.highest_profit = current_pnl
            
            # Check if we should activate trailing SL
            if not self.trailing_sl_active and current_pnl >= self.profit_threshold:
                self.trailing_sl_active = True
                self.current_sl_level = current_pnl - self.trailing_buffer
                logger.info(f"Trailing SL activated at profit: ₹{current_pnl}, SL level: ₹{self.current_sl_level}")
            
            # Update trailing SL if active
            if self.trailing_sl_active:
                new_sl_level = self.highest_profit - self.trailing_buffer
                if new_sl_level > self.current_sl_level:
                    self.current_sl_level = new_sl_level
                    logger.info(f"Trailing SL updated to: ₹{self.current_sl_level}")
                
                # Check if SL is hit
                if current_pnl <= self.current_sl_level:
                    logger.info(f"Trailing SL hit at P&L: ₹{current_pnl}, closing positions")
                    self._close_all_strategy_positions("Trailing SL hit")
                    self.last_sl_hit_time = datetime.now()
            
            logger.debug(f"Strategy P&L: ₹{current_pnl}, Highest: ₹{self.highest_profit}, SL: ₹{self.current_sl_level}")
            
        except Exception as e:
            logger.error(f"Error monitoring positions: {e}")

    def _calculate_strategy_pnl(self) -> Optional[float]:
        """Calculate current P&L of the strategy"""
        try:
            total_pnl = 0
            
            for order in self.positions.get('orders', []):
                symbol = order['symbol']
                action = order['action']
                quantity = order['quantity']
                
                # Get current market price
                market_data = self.market_data.get_symbol_data(symbol)
                if not market_data or 'ltp' not in market_data:
                    continue
                
                current_price = float(market_data['ltp'])
                
                # Get entry price from portfolio
                position_info = self.portfolio.get_position(symbol)
                if not position_info:
                    continue
                
                entry_price = position_info.get('avg_price', 0)
                
                # Calculate P&L
                if action == 'BUY':
                    pnl = (current_price - entry_price) * quantity
                else:  # SELL
                    pnl = (entry_price - current_price) * quantity
                
                total_pnl += pnl
            
            return total_pnl
            
        except Exception as e:
            logger.error(f"Error calculating strategy P&L: {e}")
            return None

    def _close_all_strategy_positions(self, reason: str):
        """Close all positions in the strategy"""
        try:
            logger.info(f"Closing all strategy positions - Reason: {reason}")
            
            for order in self.positions.get('orders', []):
                symbol = order['symbol']
                action = order['action']
                quantity = order['quantity']
                
                # Place opposite order to close position
                close_action = 'SELL' if action == 'BUY' else 'BUY'
                
                order_id = self.portfolio.place_order(
                    symbol=symbol,
                    action=close_action,
                    quantity=quantity,
                    price=0.0,  # Market orders use 0 price
                    order_type='MARKET'
                )
                
                if order_id:
                    logger.info(f"Placed {close_action} order to close {symbol}")
                else:
                    logger.error(f"Failed to close position in {symbol}")
            
            # Clear positions tracking
            self.positions = {}
            self.highest_profit = 0
            self.trailing_sl_active = False
            self.current_sl_level = 0
            
            logger.info("All strategy positions closed")
            
        except Exception as e:
            logger.error(f"Error closing strategy positions: {e}")

    def _force_exit_all_positions(self):
        """Force exit all positions on expiry day"""
        if self.positions:
            logger.info("Force exiting all positions - Expiry day 2:00 PM")
            self._close_all_strategy_positions("Expiry day force exit")

    def _update_trailing_stop_loss(self):
        """Update trailing stop loss based on current profit"""
        # This is handled in _monitor_existing_positions
        pass

    def get_status(self) -> Dict[str, Any]:
        """Get current bot status"""
        return {
            'running': self.running,
            'trading_enabled': self.trading_enabled,
            'paper_trading': self.paper_trading,
            'has_positions': bool(self.positions),
            'trailing_sl_active': self.trailing_sl_active,
            'current_profit':