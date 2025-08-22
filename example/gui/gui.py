#!/usr/bin/env python3
"""
💰 Investment Portfolio Tracker - Main GUI Application

This application helps you track your investment portfolio with real-time price updates,
transaction management, and comprehensive analytics. It supports stocks, ETFs, cryptocurrencies,
bonds, and commodities with automatic currency conversion to EUR.

Features:
- 📊 Real-time portfolio dashboard with charts
- 💰 Transaction tracking (buy, sell, dividend, fees)
- 🎯 Asset management with automatic price updates
- 🌍 Multi-currency support with auto EUR conversion
- 📈 Historical price tracking and analytics
"""

import sys
import os
from PySide6.QtWidgets import QApplication, QFileDialog, QMessageBox
from PySide6.QtCore import Qt

# Add the src directory to the path so we can import our modules
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'src'))

from frontend import InvestmentGUI

def select_database():
    """Allow user to select or create a database file"""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    
    # Ask user if they want to create new or open existing database
    msg = QMessageBox()
    msg.setWindowTitle("Investment Portfolio Tracker")
    msg.setText("<span style='color: #e2e8f0;'>Welcome! Would you like to open an existing database or create a new one?</span>")
    msg.setInformativeText("<span style='color: #e2e8f0;'>Choose 'Open Existing' to load your portfolio data, or 'Create New' to start fresh.</span>")
    msg.setStandardButtons(QMessageBox.Open | QMessageBox.Save | QMessageBox.Cancel)
    msg.button(QMessageBox.Open).setText("Open Existing")
    msg.button(QMessageBox.Save).setText("Create New")
    msg.button(QMessageBox.Cancel).setText("Cancel")
    
    # Style the message box
    msg.setStyleSheet("""
        QMessageBox {
            background-color: #2d3748;
            color: #e2e8f0;
        }
        QMessageBox QPushButton {
            background-color: #0078d4;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 600;
            min-width: 100px;
        }
        QMessageBox QPushButton:hover {
            background-color: #106ebe;
        }
    """)
    
    choice = msg.exec()
    
    if choice == QMessageBox.Cancel:
        return None
    elif choice == QMessageBox.Open:
        # Open existing database
        db_path, _ = QFileDialog.getOpenFileName(
            None,
            "Select Investment Database",
            os.getcwd(),
            "Database Files (*.db);;All Files (*)"
        )
        return db_path if db_path else None
    else:
        # Create new database
        db_path, _ = QFileDialog.getSaveFileName(
            None,
            "Create New Investment Database",
            os.path.join(os.getcwd(), "my_assets.db"),
            "Database Files (*.db);;All Files (*)"
        )
        return db_path if db_path else None

def main():
    """Main function to launch the Investment Portfolio Tracker"""
    # Handle display issues gracefully
    try:
        app = QApplication(sys.argv)
    except Exception as e:
        print(f"Failed to initialize Qt application: {e}")
        print("This might be due to display/X11 issues.")
        print("Try running with: export QT_QPA_PLATFORM=offscreen")
        print("Or ensure you have a proper display environment.")
        return 1
    
    # Set application properties
    app.setApplicationName("Investment Portfolio Tracker")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Personal Finance")
    
    # Set application icon (if you have one)
    # app.setWindowIcon(QIcon("icon.png"))
    
    print("=== Investment Portfolio Tracker ===")
    print("Welcome to your personal investment tracking application!")
    print("")
    
    # Select database
    try:
        db_path = select_database()
    except Exception as e:
        print(f"Failed to show database selection dialog: {e}")
        print("Using default database: my_assets.db")
        db_path = "my_assets.db"
    
    if db_path is None:
        print("No database selected. Exiting...")
        return 0
    
    try:
        # Create and show the main window
        print(f"Loading database: {db_path}")
        window = InvestmentGUI(db_path)
        window.show()
        
        print("GUI launched successfully!")
        print("Features available:")
        print("  📊 Dashboard - View portfolio overview and performance")
        print("  💰 Transactions - Add buy/sell/dividend transactions")
        print("  🎯 Asset Management - Add new assets and update prices")
        print("")
        print("💡 Tips:")
        print("  • All prices are automatically converted to EUR")
        print("  • Crypto assets use CoinGecko API (13,000+ supported)")
        print("  • Stocks/ETFs use Yahoo Finance with currency detection")
        print("  • The application auto-updates prices every 5 minutes")
        print("  • Use the refresh button for manual price updates")
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        print(f"Error launching application: {e}")
        print("You can still use the backend functionality by running:")
        print("  python tests/test_backend.py")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)