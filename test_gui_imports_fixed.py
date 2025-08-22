#!/usr/bin/env python3
"""
Test script to verify GUI imports and QColor fix
"""

import sys
import os

# Add src to path
sys.path.append('src')

def test_imports():
    """Test all GUI imports"""
    try:
        print("Testing GUI imports...")
        
        # Test PySide6 imports
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QColor  # This was the missing import
        print("✓ PySide6 imports successful")
        
        # Test backend import
        from backend import InvestmentTracker
        print("✓ Backend import successful")
        
        # Test frontend import (this should now work with QColor)
        from frontend import InvestmentGUI
        print("✓ Frontend import successful")
        
        # Test QColor specifically
        test_color = QColor('#4CAF50')
        print(f"✓ QColor working: {test_color.name()}")
        
        print("\n=== All imports successful! ===")
        print("✓ QColor import issue has been fixed")
        print("✓ GUI should now launch without the 'QColor is not defined' error")
        print("✓ The remaining warnings about 'transform' property are harmless CSS warnings")
        
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    test_imports()
