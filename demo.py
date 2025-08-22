#!/usr/bin/env python3
"""
Investment Portfolio Tracker - Main Demo & Launcher
Fixed: QColor import issue resolved, Unicode icons removed, dashboard improved
Features: Clean GUI, asset-type charts, separate P&L columns, comprehensive testing
"""

import sys
import os
import subprocess
import traceback

def print_banner():
    """Print application banner"""
    print("=" * 75)
    print("    🚀 Investment Portfolio Tracker - Demo & Launcher 💰")
    print("=" * 75)
    print("✨ Features:")
    print("   📊 Multi-currency support (EUR, USD, GBP, CHF, JPY)")
    print("   🔄 Real-time prices (13,000+ crypto assets)")
    print("   🎨 Clean GUI without problematic Unicode icons")
    print("   📈 Asset-type pie charts (Stock/ETF/Crypto)")
    print("   💰 Separate P&L (EUR) and P&L (%) columns")
    print("   🧪 Comprehensive test suite")
    print("=" * 75)

def test_dependencies():
    """Test core dependencies without imports"""
    print("\n� Testing Core Dependencies...")
    
    try:
        import sys
        sys.path.append('src')
        
        # Test backend
        from backend import InvestmentTracker
        print("✓ Backend module available")
        
        # Test PySide6
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor
        print("✓ PySide6 available")
        
        # Test matplotlib
        import matplotlib.pyplot as plt
        print("✓ Matplotlib available")
        
        # Test frontend (including QColor fix)
        from frontend import InvestmentGUI
        print("✓ Frontend module available (QColor fixed)")
        
        return True
        
    except ImportError as e:
        print(f"✗ Missing dependency: {e}")
        return False
    except Exception as e:
        print(f"✗ Dependency error: {e}")
        return False

def run_test_suite():
    """Run the complete test suite"""
    print("\n🧪 Running Comprehensive Test Suite...")
    print("-" * 50)
    
    try:
        test_runner = os.path.join('tests', 'run_all_tests.py')
        if not os.path.exists(test_runner):
            print("❌ Test runner not found")
            return False
        
        result = subprocess.run([sys.executable, test_runner], 
                              capture_output=True, text=True, timeout=300)
        
        print(result.stdout)
        if result.stderr:
            print("Warnings/Errors:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print("⏰ Test suite timed out (>5 minutes)")
        return False
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        return False

def launch_gui():
    """Launch the GUI application"""
    print("\n🚀 Launching GUI Application...")
    
    try:
        # Set environment variables for better Qt compatibility
        env = os.environ.copy()
        env['QT_QPA_PLATFORM'] = 'xcb'
        
        gui_launcher = os.path.join('example', 'gui', 'gui.py')
        if not os.path.exists(gui_launcher):
            print("❌ GUI launcher not found")
            return False
        
        print("✓ Starting GUI (this may take a moment)...")
        print("ℹ️  GUI Features:")
        print("   - No problematic Unicode icons")
        print("   - Asset-type pie charts") 
        print("   - Separate P&L columns (EUR and %)")
        print("   - Modern dark theme")
        
        # Launch GUI
        subprocess.run([sys.executable, gui_launcher], env=env)
        return True
        
    except Exception as e:
        print(f"❌ GUI launch failed: {e}")
        print("\nPossible solutions:")
        print("1. Check display system (X11/Wayland)")
        print("2. Verify PySide6 installation")
        print("3. Run: python tests/test_gui_imports.py")
        return False

def create_demo_portfolio():
    """Create a demonstration portfolio"""
    print("\n📊 Creating Demo Portfolio...")
    
    try:
        demo_script = os.path.join('tests', 'test_comprehensive.py')
        result = subprocess.run([sys.executable, demo_script], 
                              capture_output=True, text=True, timeout=120)
        
        if result.returncode == 0:
            print("✅ Demo portfolio created successfully!")
            print(result.stdout)
            return True
        else:
            print("❌ Demo portfolio creation failed")
            if result.stderr:
                print(result.stderr)
            return False
            
    except Exception as e:
        print(f"💥 Demo creation failed: {e}")
        return False

def main():
    """Main demo launcher"""
    print_banner()
    
    # Quick dependency check
    if not test_dependencies():
        print("\n❌ Dependency issues detected!")
        print("Please install required packages:")
        print("   pip install PySide6 matplotlib pandas yfinance requests")
        return 1
    
    print("\n✅ All dependencies available!")
    
    while True:
        print("\n🎯 Choose an option:")
        print("   [1] Launch GUI Application")
        print("   [2] Run Tests")
        print("   [3] Create Demo Portfolio")
        print("   [0] Exit")
        
        try:
            choice = input("\nEnter choice (0-3): ").strip()
            
            if choice == '1':
                success = launch_gui()
                if not success:
                    print("\n💡 Try running tests first to diagnose issues")
            
            elif choice == '2':
                print("\n🧪 Running All Tests...")
                success = run_test_suite()
                if success:
                    print("\n🎉 All tests passed! System ready for use.")
                else:
                    print("\n⚠️ Some tests failed. Please review output above.")
            
            elif choice == '3':
                success = create_demo_portfolio()
                if success:
                    print("\n💡 Demo portfolio ready! Launch GUI to view it.")
            
            elif choice == '0':
                print("\n👋 Thanks for using Investment Portfolio Tracker!")
                break
            
            else:
                print("❌ Invalid choice. Please select 0-3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n💥 Error: {e}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
