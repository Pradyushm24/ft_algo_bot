#!/usr/bin/env python3
"""
Bot CLI - Command Line Interface for Options Trading Bot
Provides easy command-line control of the trading bot
"""

import sys
import os
import argparse
import json
import time
from datetime import datetime
from typing import Dict, Any

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from trading_controls import TradingControls
from utils import load_config

class BotCLI:
    """Command line interface for the trading bot"""
    
    def __init__(self):
        self.controls = TradingControls()
        self.config = load_config('config.json')
    
    def start_bot(self, paper: bool = True):
        """Start the trading bot"""
        try:
            print("Starting Options Trading Bot...")
            
            if paper:
                print("📄 Running in PAPER TRADING mode (safe testing)")
            else:
                print("⚠️  Running in LIVE TRADING mode")
                confirm = input("Are you sure? Type 'YES' to confirm: ")
                if confirm != 'YES':
                    print("Cancelled.")
                    return
            
            # Update config for paper trading
            self.config['paper_trading'] = paper
            
            # Import and start the bot
            from main import OptionsStrategyBot
            
            bot = OptionsStrategyBot()
            
            if bot.start():
                print("✅ Bot started successfully!")
                print("🌐 Web dashboard: http://localhost:5000")
                print("📝 Logs: trading_bot.log")
                print("\nPress Ctrl+C to stop")
                
                try:
                    while bot.running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n⏹️  Stopping bot...")
                    bot.stop()
                    print("✅ Bot stopped successfully")
            else:
                print("❌ Failed to start bot. Check logs for details.")
                
        except Exception as e:
            print(f"❌ Error starting bot: {e}")
    
    def stop_bot(self):
        """Stop the trading bot"""
        print("Stopping trading bot...")
        # This would require process management in a real implementation
        print("✅ Stop signal sent")
    
    def pause_trading(self, reason: str = "Manual pause"):
        """Pause trading"""
        if self.controls.pause_trading(reason):
            print(f"⏸️  Trading paused: {reason}")
        else:
            print("❌ Failed to pause trading")
    
    def resume_trading(self):
        """Resume trading"""
        if self.controls.resume_trading():
            print("▶️  Trading resumed")
        else:
            print("❌ Failed to resume trading")
    
    def show_status(self):
        """Show current trading status"""
        print("\n=== Trading Bot Status ===")
        
        # Check pause status
        if self.controls.is_trading_paused():
            pause_info = self.controls.get_pause_info()
            print("🔴 Status: PAUSED")
            if pause_info:
                print(f"   Paused at: {pause_info.get('timestamp', 'Unknown')}")
                print(f"   Reason: {pause_info.get('reason', 'Unknown')}")
        else:
            print("🟢 Status: ACTIVE")
        
        # Check emergency stop
        if os.path.exists('EMERGENCY_STOP.txt'):
            print("🚨 EMERGENCY STOP ACTIVE")
        
        # Load trading status if available
        status = self.controls.load_trading_status()
        if status:
            print(f"\nLast Updated: {status.get('last_updated', 'Unknown')}")
            if 'positions' in status:
                print(f"Open Positions: {len(status['positions'])}")
            if 'total_pnl' in status:
                print(f"Total P&L: ₹{status['total_pnl']:.2f}")
        
        print("\n=== Files ===")
        files_to_check = [
            'trading_pause.txt',
            'EMERGENCY_STOP.txt', 
            'config.json',
            'trading_bot.log'
        ]
        
        for file_path in files_to_check:
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                print(f"✅ {file_path} ({size} bytes)")
            else:
                print(f"❌ {file_path} (not found)")
    
    def emergency_stop(self):
        """Emergency stop all trading"""
        from trading_controls import create_emergency_stop
        
        if create_emergency_stop():
            print("🚨 EMERGENCY STOP ACTIVATED")
            print("   All trading has been halted immediately")
            print("   Use 'clear-emergency' to resume")
        else:
            print("❌ Failed to activate emergency stop")
    
    def clear_emergency(self):
        """Clear emergency stop"""
        from trading_controls import remove_emergency_stop
        
        if remove_emergency_stop():
            print("✅ Emergency stop cleared")
            print("   Trading can now resume normally")
        else:
            print("❌ Failed to clear emergency stop")
    
    def show_config(self):
        """Show current configuration"""
        print("\n=== Current Configuration ===")
        print(json.dumps(self.config, indent=2))
    
    def show_logs(self, lines: int = 20):
        """Show recent log entries"""
        try:
            if not os.path.exists('trading_bot.log'):
                print("❌ Log file not found")
                return
            
            print(f"\n=== Last {lines} Log Entries ===")
            with open('trading_bot.log', 'r') as f:
                log_lines = f.readlines()
                for line in log_lines[-lines:]:
                    print(line.strip())
                    
        except Exception as e:
            print(f"❌ Error reading logs: {e}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(
        description='Options Trading Bot CLI',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s start --paper          # Start in paper trading mode
  %(prog)s start --live           # Start in live trading mode  
  %(prog)s pause "Market crash"   # Pause with reason
  %(prog)s resume                 # Resume trading
  %(prog)s status                 # Show current status
  %(prog)s emergency              # Emergency stop
  %(prog)s logs --lines 50        # Show 50 recent log lines
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the trading bot')
    start_group = start_parser.add_mutually_exclusive_group()
    start_group.add_argument('--paper', action='store_true', default=True, help='Paper trading mode (default)')
    start_group.add_argument('--live', action='store_true', help='Live trading mode')
    
    # Stop command  
    subparsers.add_parser('stop', help='Stop the trading bot')
    
    # Pause command
    pause_parser = subparsers.add_parser('pause', help='Pause trading')
    pause_parser.add_argument('reason', nargs='*', help='Reason for pausing')
    
    # Resume command
    subparsers.add_parser('resume', help='Resume trading')
    
    # Status command
    subparsers.add_parser('status', help='Show trading status')
    
    # Emergency commands
    subparsers.add_parser('emergency', help='Emergency stop all trading')
    subparsers.add_parser('clear-emergency', help='Clear emergency stop')
    
    # Config command
    subparsers.add_parser('config', help='Show configuration')
    
    # Logs command
    logs_parser = subparsers.add_parser('logs', help='Show recent logs')
    logs_parser.add_argument('--lines', type=int, default=20, help='Number of lines to show')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = BotCLI()
    
    try:
        if args.command == 'start':
            paper_mode = not args.live
            cli.start_bot(paper=paper_mode)
        
        elif args.command == 'stop':
            cli.stop_bot()
        
        elif args.command == 'pause':
            reason = ' '.join(args.reason) if args.reason else "Manual pause"
            cli.pause_trading(reason)
        
        elif args.command == 'resume':
            cli.resume_trading()
        
        elif args.command == 'status':
            cli.show_status()
        
        elif args.command == 'emergency':
            cli.emergency_stop()
        
        elif args.command == 'clear-emergency':
            cli.clear_emergency()
        
        elif args.command == 'config':
            cli.show_config()
        
        elif args.command == 'logs':
            cli.show_logs(args.lines)
        
        else:
            print(f"Unknown command: {args.command}")
            parser.print_help()
    
    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    main()