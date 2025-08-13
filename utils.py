"""
Utility Functions
Common utilities for logging, configuration, and helper functions
"""

import os
import json
import logging
import logging.handlers
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

def setup_logging(config: Dict[str, Any]) -> logging.Logger:
    """
    Set up logging configuration
    
    Args:
        config (Dict[str, Any]): Logging configuration
        
    Returns:
        logging.Logger: Configured logger
    """
    try:
        # Get logging parameters
        log_level = config.get('level', 'INFO').upper()
        log_file = config.get('file', 'trading_bot.log')
        max_file_size = config.get('max_file_size', '10MB')
        backup_count = config.get('backup_count', 5)
        
        # Convert max_file_size to bytes
        size_multipliers = {'KB': 1024, 'MB': 1024*1024, 'GB': 1024*1024*1024}
        max_bytes = 10 * 1024 * 1024  # Default 10MB
        
        if isinstance(max_file_size, str):
            for suffix, multiplier in size_multipliers.items():
                if max_file_size.upper().endswith(suffix):
                    size_str = max_file_size[:-len(suffix)]
                    max_bytes = int(float(size_str) * multiplier)
                    break
        
        # Create logs directory if it doesn't exist
        log_dir = os.path.dirname(log_file) if os.path.dirname(log_file) else 'logs'
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        # Configure logging
        logger = logging.getLogger('trading_bot')
        logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Remove existing handlers
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        
        # File handler with rotation
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=max_bytes, backupCount=backup_count
            )
            file_handler.setFormatter(detailed_formatter)
            logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
        
        logger.info("Logging configured successfully")
        return logger
        
    except Exception as e:
        # Fallback logging configuration
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error setting up logging: {e}")
        return logger

def load_config(config_file: str) -> Dict[str, Any]:
    """
    Load configuration from JSON file
    
    Args:
        config_file (str): Path to configuration file
        
    Returns:
        Dict[str, Any]: Configuration dictionary
    """
    try:
        if not os.path.exists(config_file):
            logger = logging.getLogger('trading_bot')
            logger.warning(f"Config file {config_file} not found, using defaults")
            return get_default_config()
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Merge with defaults for missing keys
        default_config = get_default_config()
        merged_config = merge_configs(default_config, config)
        
        return merged_config
        
    except json.JSONDecodeError as e:
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error parsing config file {config_file}: {e}")
        return get_default_config()
    except Exception as e:
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error loading config file {config_file}: {e}")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """
    Get default configuration
    
    Returns:
        Dict[str, Any]: Default configuration
    """
    return {
        "flattrade": {
            "user_id": "",
            "password": "",
            "totp_key": "",
            "api_key": "",
            "api_secret": "",
            "base_url": "https://piconnect.flattrade.in/PiConnectTP"
        },
        "trading": {
            "max_positions": 5,
            "max_risk_per_trade": 0.02,
            "stop_loss_percentage": 0.05,
            "take_profit_percentage": 0.10,
            "position_size_percentage": 0.20,
            "trading_enabled": False,
            "paper_trading": True
        },
        "symbols": [
            "NIFTY50", "BANKNIFTY", "RELIANCE", "TCS", "INFY"
        ],
        "strategy": {
            "name": "simple_momentum",
            "parameters": {
                "rsi_period": 14,
                "rsi_oversold": 30,
                "rsi_overbought": 70,
                "sma_fast": 10,
                "sma_slow": 20,
                "volume_threshold": 1.5
            }
        },
        "risk_management": {
            "max_drawdown": 0.10,
            "daily_loss_limit": 0.05,
            "max_open_positions": 3,
            "position_timeout_hours": 24
        },
        "logging": {
            "level": "INFO",
            "file": "trading_bot.log",
            "max_file_size": "10MB",
            "backup_count": 5
        },
        "web_interface": {
            "host": "0.0.0.0",
            "port": 5000,
            "debug": False
        },
        "backtesting": {
            "start_date": "2024-01-01",
            "end_date": "2024-12-31",
            "initial_capital": 100000,
            "commission": 0.001
        }
    }

def merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge user config with default config
    
    Args:
        default (Dict[str, Any]): Default configuration
        user (Dict[str, Any]): User configuration
        
    Returns:
        Dict[str, Any]: Merged configuration
    """
    merged = default.copy()
    
    for key, value in user.items():
        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
            merged[key] = merge_configs(merged[key], value)
        else:
            merged[key] = value
    
    return merged

def save_config(config: Dict[str, Any], config_file: str) -> bool:
    """
    Save configuration to JSON file
    
    Args:
        config (Dict[str, Any]): Configuration to save
        config_file (str): Path to configuration file
        
    Returns:
        bool: True if successful
    """
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)
        return True
    except Exception as e:
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error saving config file {config_file}: {e}")
        return False

def format_currency(amount: float, currency: str = '₹') -> str:
    """
    Format amount as currency
    
    Args:
        amount (float): Amount to format
        currency (str): Currency symbol
        
    Returns:
        str: Formatted currency string
    """
    if abs(amount) >= 10000000:  # 1 crore
        return f"{currency}{amount/10000000:.2f}Cr"
    elif abs(amount) >= 100000:  # 1 lakh
        return f"{currency}{amount/100000:.2f}L"
    elif abs(amount) >= 1000:  # 1 thousand
        return f"{currency}{amount/1000:.2f}K"
    else:
        return f"{currency}{amount:.2f}"

def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format value as percentage
    
    Args:
        value (float): Value to format (0.05 = 5%)
        decimals (int): Number of decimal places
        
    Returns:
        str: Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"

def calculate_returns(prices: List[float]) -> List[float]:
    """
    Calculate returns from price series
    
    Args:
        prices (List[float]): Price series
        
    Returns:
        List[float]: Returns series
    """
    if len(prices) < 2:
        return []
    
    returns = []
    for i in range(1, len(prices)):
        if prices[i-1] != 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
        else:
            returns.append(0.0)
    
    return returns

def calculate_sharpe_ratio(returns: List[float], risk_free_rate: float = 0.0) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns (List[float]): Returns series
        risk_free_rate (float): Risk-free rate
        
    Returns:
        float: Sharpe ratio
    """
    if not returns:
        return 0.0
    
    excess_returns = [r - risk_free_rate for r in returns]
    mean_return = np.mean(excess_returns)
    std_return = np.std(excess_returns)
    
    if std_return == 0:
        return 0.0
    
    return mean_return / std_return

def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """
    Calculate maximum drawdown
    
    Args:
        equity_curve (List[float]): Equity curve values
        
    Returns:
        float: Maximum drawdown as decimal (0.1 = 10%)
    """
    if not equity_curve:
        return 0.0
    
    peak = equity_curve[0]
    max_drawdown = 0.0
    
    for value in equity_curve:
        if value > peak:
            peak = value
        
        drawdown = (peak - value) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)
    
    return max_drawdown

def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    """
    Calculate win rate from trades
    
    Args:
        trades (List[Dict[str, Any]]): List of trade dictionaries
        
    Returns:
        float: Win rate as decimal (0.6 = 60%)
    """
    if not trades:
        return 0.0
    
    winning_trades = 0
    for trade in trades:
        pnl = trade.get('pnl', 0)
        if pnl > 0:
            winning_trades += 1
    
    return winning_trades / len(trades)

def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate configuration and return list of errors
    
    Args:
        config (Dict[str, Any]): Configuration to validate
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Check required sections
    required_sections = ['flattrade', 'trading', 'symbols', 'strategy', 'risk_management']
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: {section}")
    
    # Validate Flattrade config
    if 'flattrade' in config:
        flattrade_config = config['flattrade']
        required_fields = ['user_id', 'api_key', 'api_secret']
        for field in required_fields:
            if not flattrade_config.get(field):
                errors.append(f"Missing Flattrade field: {field}")
    
    # Validate trading config
    if 'trading' in config:
        trading_config = config['trading']
        
        # Check percentage values
        percentage_fields = ['max_risk_per_trade', 'stop_loss_percentage', 
                           'take_profit_percentage', 'position_size_percentage']
        for field in percentage_fields:
            value = trading_config.get(field, 0)
            if not 0 < value <= 1:
                errors.append(f"Invalid {field}: must be between 0 and 1")
    
    # Validate symbols
    if 'symbols' in config:
        symbols = config['symbols']
        if not isinstance(symbols, list) or len(symbols) == 0:
            errors.append("Symbols must be a non-empty list")
    
    # Validate risk management
    if 'risk_management' in config:
        risk_config = config['risk_management']
        
        max_drawdown = risk_config.get('max_drawdown', 0)
        if not 0 < max_drawdown <= 1:
            errors.append("max_drawdown must be between 0 and 1")
        
        daily_loss_limit = risk_config.get('daily_loss_limit', 0)
        if not 0 < daily_loss_limit <= 1:
            errors.append("daily_loss_limit must be between 0 and 1")
    
    return errors

def is_market_open() -> bool:
    """
    Check if Indian stock market is open
    
    Returns:
        bool: True if market is open
    """
    now = datetime.now()
    
    # Check if it's a weekday
    if now.weekday() >= 5:  # Saturday or Sunday
        return False
    
    # Check market hours (9:15 AM to 3:30 PM IST)
    market_start = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_end = now.replace(hour=15, minute=30, second=0, microsecond=0)
    
    return market_start <= now <= market_end

def get_next_market_open() -> datetime:
    """
    Get next market open time
    
    Returns:
        datetime: Next market open time
    """
    now = datetime.now()
    
    # If it's before market open today and it's a weekday
    if now.weekday() < 5:
        market_open_today = now.replace(hour=9, minute=15, second=0, microsecond=0)
        if now < market_open_today:
            return market_open_today
    
    # Find next weekday
    days_ahead = 1
    while (now + timedelta(days=days_ahead)).weekday() >= 5:
        days_ahead += 1
    
    next_market_day = now + timedelta(days=days_ahead)
    return next_market_day.replace(hour=9, minute=15, second=0, microsecond=0)

def sanitize_symbol(symbol: str) -> str:
    """
    Sanitize symbol name for file/database usage
    
    Args:
        symbol (str): Symbol to sanitize
        
    Returns:
        str: Sanitized symbol
    """
    return ''.join(c for c in symbol if c.isalnum() or c in '-_').upper()

def create_directories(paths: List[str]):
    """
    Create directories if they don't exist
    
    Args:
        paths (List[str]): List of directory paths to create
    """
    for path in paths:
        try:
            os.makedirs(path, exist_ok=True)
        except Exception as e:
            logger = logging.getLogger('trading_bot')
            logger.error(f"Error creating directory {path}: {e}")

def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """
    Safely divide two numbers
    
    Args:
        numerator (float): Numerator
        denominator (float): Denominator
        default (float): Default value if division by zero
        
    Returns:
        float: Division result or default
    """
    return numerator / denominator if denominator != 0 else default

def round_to_tick_size(price: float, tick_size: float = 0.05) -> float:
    """
    Round price to nearest tick size
    
    Args:
        price (float): Price to round
        tick_size (float): Tick size
        
    Returns:
        float: Rounded price
    """
    return round(price / tick_size) * tick_size

def get_business_days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Get number of business days between two dates
    
    Args:
        start_date (datetime): Start date
        end_date (datetime): End date
        
    Returns:
        int: Number of business days
    """
    business_days = 0
    current_date = start_date
    
    while current_date <= end_date:
        if current_date.weekday() < 5:  # Monday to Friday
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days

def export_data_to_csv(data: List[Dict[str, Any]], filename: str) -> bool:
    """
    Export data to CSV file
    
    Args:
        data (List[Dict[str, Any]]): Data to export
        filename (str): Output filename
        
    Returns:
        bool: True if successful
    """
    try:
        if not data:
            return False
        
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        return True
    except Exception as e:
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error exporting data to CSV {filename}: {e}")
        return False

def import_data_from_csv(filename: str) -> List[Dict[str, Any]]:
    """
    Import data from CSV file
    
    Args:
        filename (str): Input filename
        
    Returns:
        List[Dict[str, Any]]: Imported data
    """
    try:
        if not os.path.exists(filename):
            return []
        
        df = pd.read_csv(filename)
        return df.to_dict('records')
    except Exception as e:
        logger = logging.getLogger('trading_bot')
        logger.error(f"Error importing data from CSV {filename}: {e}")
        return []

# Example usage and testing
if __name__ == "__main__":
    # Test logging setup
    config = {
        'level': 'DEBUG',
        'file': 'test.log',
        'max_file_size': '1MB',
        'backup_count': 3
    }
    
    logger = setup_logging(config)
    logger.info("Testing logging setup")
    
    # Test configuration loading
    test_config = load_config('config.json')
    print(f"Loaded config sections: {list(test_config.keys())}")
    
    # Test utility functions
    print(f"Market open: {is_market_open()}")
    print(f"Next market open: {get_next_market_open()}")
    print(f"Currency format: {format_currency(1234567.89)}")
    print(f"Percentage format: {format_percentage(0.1234)}")
    
    # Test validation
    errors = validate_config(test_config)
    if errors:
        print(f"Configuration errors: {errors}")
    else:
        print("Configuration is valid")