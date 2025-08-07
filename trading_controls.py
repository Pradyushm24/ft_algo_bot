"""
Trading Controls Module
Provides utilities for manual control of the trading bot
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class TradingControls:
    """
    Manages manual trading controls like pause/resume functionality
    """
    
    def __init__(self, pause_file: str = 'trading_pause.txt'):
        """
        Initialize trading controls
        
        Args:
            pause_file (str): Path to pause control file
        """
        self.pause_file = pause_file
        self.status_file = 'trading_status.json'
        
    def pause_trading(self, reason: str = "Manual pause") -> bool:
        """
        Pause trading by creating pause file
        
        Args:
            reason (str): Reason for pausing
            
        Returns:
            bool: True if successful
        """
        try:
            pause_info = {
                'timestamp': datetime.now().isoformat(),
                'reason': reason,
                'paused_by': 'manual'
            }
            
            with open(self.pause_file, 'w') as f:
                json.dump(pause_info, f, indent=2)
            
            logger.info(f"Trading paused: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error pausing trading: {e}")
            return False
    
    def resume_trading(self) -> bool:
        """
        Resume trading by removing pause file
        
        Returns:
            bool: True if successful
        """
        try:
            if os.path.exists(self.pause_file):
                os.remove(self.pause_file)
                logger.info("Trading resumed")
                return True
            else:
                logger.warning("Trading was not paused")
                return True
                
        except Exception as e:
            logger.error(f"Error resuming trading: {e}")
            return False
    
    def is_trading_paused(self) -> bool:
        """
        Check if trading is currently paused
        
        Returns:
            bool: True if paused
        """
        return os.path.exists(self.pause_file)
    
    def get_pause_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about current pause status
        
        Returns:
            Optional[Dict[str, Any]]: Pause information or None
        """
        try:
            if not self.is_trading_paused():
                return None
            
            with open(self.pause_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error reading pause info: {e}")
            return None
    
    def save_trading_status(self, status: Dict[str, Any]) -> bool:
        """
        Save current trading status to file
        
        Args:
            status (Dict[str, Any]): Status information
            
        Returns:
            bool: True if successful
        """
        try:
            status['last_updated'] = datetime.now().isoformat()
            
            with open(self.status_file, 'w') as f:
                json.dump(status, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving trading status: {e}")
            return False
    
    def load_trading_status(self) -> Optional[Dict[str, Any]]:
        """
        Load trading status from file
        
        Returns:
            Optional[Dict[str, Any]]: Status information or None
        """
        try:
            if not os.path.exists(self.status_file):
                return None
            
            with open(self.status_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error loading trading status: {e}")
            return None


def create_emergency_stop():
    """
    Create emergency stop file to immediately halt all trading
    """
    try:
        controls = TradingControls()
        controls.pause_trading("EMERGENCY STOP - Manual intervention required")
        
        # Also create a more obvious emergency file
        with open('EMERGENCY_STOP.txt', 'w') as f:
            f.write(f"EMERGENCY STOP ACTIVATED\n")
            f.write(f"Time: {datetime.now().isoformat()}\n")
            f.write(f"Action: All trading halted immediately\n")
            f.write(f"To resume: Delete this file and trading_pause.txt\n")
        
        print("EMERGENCY STOP ACTIVATED - All trading halted")
        return True
        
    except Exception as e:
        print(f"Error creating emergency stop: {e}")
        return False


def remove_emergency_stop():
    """
    Remove emergency stop and resume normal trading
    """
    try:
        files_to_remove = ['EMERGENCY_STOP.txt', 'trading_pause.txt']
        
        for file_path in files_to_remove:
            if os.path.exists(file_path):
                os.remove(file_path)
        
        print("Emergency stop removed - Trading can resume")
        return True
        
    except Exception as e:
        print(f"Error removing emergency stop: {e}")
        return False


if __name__ == "__main__":
    # Command line interface for trading controls
    import sys
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python trading_controls.py pause [reason]")
        print("  python trading_controls.py resume")
        print("  python trading_controls.py status")
        print("  python trading_controls.py emergency_stop")
        print("  python trading_controls.py remove_emergency")
        sys.exit(1)
    
    controls = TradingControls()
    command = sys.argv[1].lower()
    
    if command == 'pause':
        reason = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else "Manual pause"
        if controls.pause_trading(reason):
            print(f"Trading paused: {reason}")
        else:
            print("Failed to pause trading")
    
    elif command == 'resume':
        if controls.resume_trading():
            print("Trading resumed")
        else:
            print("Failed to resume trading")
    
    elif command == 'status':
        if controls.is_trading_paused():
            pause_info = controls.get_pause_info()
            print("Trading Status: PAUSED")
            if pause_info:
                print(f"  Paused at: {pause_info.get('timestamp', 'Unknown')}")
                print(f"  Reason: {pause_info.get('reason', 'Unknown')}")
        else:
            print("Trading Status: ACTIVE")
    
    elif command == 'emergency_stop':
        create_emergency_stop()
    
    elif command == 'remove_emergency':
        remove_emergency_stop()
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)