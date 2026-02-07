#!/usr/bin/env python3
"""
Investment Portfolio Tracker - Main Launcher
Modern web interface (HTML/CSS/JS + Flask backend)
"""

import sys
import os
import subprocess
import traceback
import signal

def print_banner():
    """Print application banner"""
    print("=" * 75)
    print("    Investment Portfolio Tracker")
    print("=" * 75)
    print("Features:")
    print("   - Multi-currency support (EUR, USD, GBP, CHF, JPY)")
    print("   - Real-time prices (13,000+ crypto assets)")
    print("   - Modern web interface (opens in browser)")
    print("   - Searchable asset dropdown")
    print("   - Watchlist functionality")
    print("   - Portfolio composition charts")
    print("   - Transaction management")
    print("=" * 75)


def kill_existing_servers():
    """Kill any existing Flask servers running on port 5000"""
    try:
        # Find processes using port 5000
        result = subprocess.run(
            ['lsof', '-t', '-i:5000'],
            capture_output=True, text=True, timeout=5
        )
        
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                try:
                    pid_int = int(pid)
                    # Don't kill ourselves
                    if pid_int != os.getpid():
                        os.kill(pid_int, signal.SIGTERM)
                        print(f"   Killed old server process (PID: {pid})")
                except (ValueError, ProcessLookupError):
                    pass
            return True
        return False
    except FileNotFoundError:
        # lsof not available, try alternative method
        try:
            result = subprocess.run(
                ['fuser', '-k', '5000/tcp'],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                print("   Killed old server process")
                return True
        except FileNotFoundError:
            pass
        return False
    except Exception:
        return False


def test_dependencies():
    """Test core dependencies"""
    print("\nTesting Dependencies...")
    
    try:
        sys.path.append('src')
        
        from backend import InvestmentTracker
        print("+ Backend module")
        
        from flask import Flask
        print("+ Flask")
        
        import requests
        import yfinance
        import pandas
        print("+ All dependencies available")
        
        return True
    except ImportError as e:
        print(f"- Missing: {e}")
        return False


def launch_web_interface():
    """Launch the web interface"""
    print("\nStarting Web Server...")
    print("=" * 75)
    
    # Kill any existing server first
    if kill_existing_servers():
        print("   (Cleaned up old server)")
    
    try:
        sys.path.append('src')
        from web_frontend import main
        main()
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return False
    
    return True

def run_test_suite():
    """Run the test suite"""
    print("\nRunning Tests...")
    print("-" * 50)
    
    try:
        test_runner = os.path.join('tests', 'run_all_tests.py')
        if not os.path.exists(test_runner):
            print("Test runner not found")
            return False
        
        result = subprocess.run([sys.executable, test_runner], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("Test suite timed out")
        return False
    except Exception as e:
        print(f"Test suite failed: {e}")
        return False


def create_demo_portfolio():
    """Create a demonstration portfolio"""
    print("\nCreating Demo Portfolio...")
    
    try:
        demo_script = os.path.join('tests', 'test_comprehensive.py')
        result = subprocess.run([sys.executable, demo_script], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("Demo portfolio created!")
            print(result.stdout)
            return True
        else:
            print("Demo portfolio creation failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"Demo creation failed: {e}")
        return False

def main():
    """Main launcher"""
    print_banner()
    
    if not test_dependencies():
        print("\nMissing dependencies!")
        print("Run: pip install Flask Flask-CORS pandas yfinance requests")
        return 1
    
    print("\n+ Ready!")
    
    while True:
        print("\nOptions:")
        print("   [1] Launch Web Interface")
        print("   [2] Run Tests")
        print("   [3] Create Demo Portfolio")
        print("   [0] Exit")
        
        try:
            choice = input("\nChoice (0-3): ").strip()
            
            if choice == '1':
                launch_web_interface()
            
            elif choice == '2':
                run_test_suite()
            
            elif choice == '3':
                create_demo_portfolio()
            
            elif choice == '0':
                print("\nGoodbye!")
                break
            
            else:
                print("Invalid choice.")
                
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
