#!/usr/bin/env python3
"""
Test script to verify that all GUI imports work correctly
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

def test_imports():
    """Test that all required modules can be imported"""
    print("=== Testing GUI Imports ===")
    
    try:
        from PySide6.QtWidgets import QApplication
        print("✓ PySide6.QtWidgets imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import PySide6.QtWidgets: {e}")
        return False
    
    try:
        import matplotlib.pyplot as plt
        print("✓ matplotlib imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import matplotlib: {e}")
        return False
    
    try:
        import pandas as pd
        print("✓ pandas imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import pandas: {e}")
        return False
    
    try:
        from backend import InvestmentTracker
        print("✓ backend module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import backend: {e}")
        return False
    
    try:
        from frontend import InvestmentGUI
        print("✓ frontend module imported successfully")
    except ImportError as e:
        print(f"✗ Failed to import frontend: {e}")
        return False
    
    print("✓ All imports successful!")
    return True

def test_gui_creation():
    """Test that we can create the GUI class without display"""
    print("\n=== Testing GUI Creation (without display) ===")
    
    try:
        # Set QT_QPA_PLATFORM to offscreen to avoid display issues
        os.environ['QT_QPA_PLATFORM'] = 'offscreen'
        
        from PySide6.QtWidgets import QApplication
        from frontend import InvestmentGUI
        
        app = QApplication([])
        
        # Create GUI with test database
        gui = InvestmentGUI("test_assets.db")
        print("✓ GUI object created successfully")
        
        # Test that methods exist
        assert hasattr(gui, 'refresh_all_data'), "refresh_all_data method missing"
        assert hasattr(gui, 'load_portfolio_data'), "load_portfolio_data method missing"
        assert hasattr(gui, 'add_asset'), "add_asset method missing"
        assert hasattr(gui, 'add_transaction'), "add_transaction method missing"
        print("✓ All required methods exist")
        
        app.quit()
        print("✓ GUI test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ GUI creation failed: {e}")
        return False

if __name__ == "__main__":
    success = test_imports()
    if success:
        success = test_gui_creation()
    
    if success:
        print("\n✅ All tests passed! The GUI should work correctly.")
    else:
        print("\n❌ Some tests failed. Check the errors above.")
    
    sys.exit(0 if success else 1)
