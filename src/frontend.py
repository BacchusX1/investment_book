import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QLineEdit, 
                               QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit,
                               QGroupBox, QFormLayout, QMessageBox, QHeaderView,
                               QSplitter, QFrame)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QPalette
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import pandas as pd
from datetime import datetime, timedelta

# Import our backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.backend import InvestmentTracker

class InvestmentGUI(QMainWindow):
    def __init__(self, db_path="my_assets.db"):
        super().__init__()
        self.tracker = InvestmentTracker(db_path)
        self.init_ui()
        
        # Setup auto-refresh timer (every 5 minutes)
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all_data)
        self.timer.start(300000)  # 5 minutes
    
    def init_ui(self):
        self.setWindowTitle("Investment Portfolio Tracker")
        self.setGeometry(100, 100, 1400, 900)
        
        # Apply dark theme
        self.setStyleSheet("""
            QMainWindow {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QWidget {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QTabWidget::pane {
                border: 1px solid #555555;
                background-color: #2b2b2b;
            }
            QTabBar::tab {
                background-color: #404040;
                color: #ffffff;
                padding: 10px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background-color: #606060;
            }
            QTableWidget {
                background-color: #353535;
                alternate-background-color: #404040;
                gridline-color: #555555;
                selection-background-color: #0078d4;
                color: #ffffff;
            }
            QTableWidget::item {
                color: #ffffff;
                padding: 5px;
            }
            QHeaderView::section {
                background-color: #404040;
                color: #ffffff;
                padding: 8px;
                border: 1px solid #555555;
            }
            QPushButton {
                background-color: #0078d4;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QLineEdit, QDoubleSpinBox, QComboBox, QDateEdit, QTextEdit {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 5px;
                border-radius: 3px;
            }
            QComboBox::drop-down {
                border: none;
                background-color: #555555;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #ffffff;
                margin-right: 5px;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #555555;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                color: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
                color: #ffffff;
            }
            QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QFormLayout QLabel {
                color: #ffffff;
            }
        """)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Create tabs
        self.dashboard_tab = self.create_dashboard_tab()
        self.transactions_tab = self.create_transactions_tab()
        self.assets_tab = self.create_assets_tab()
        
        # Add tabs to widget
        self.tab_widget.addTab(self.dashboard_tab, "Dashboard")
        self.tab_widget.addTab(self.transactions_tab, "Transactions")
        self.tab_widget.addTab(self.assets_tab, "Assets Management")
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.tab_widget)
        central_widget.setLayout(main_layout)
        
        # Load initial data
        self.refresh_all_data()
    
    def create_dashboard_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Header with portfolio summary
        header_group = QGroupBox("Portfolio Overview")
        header_layout = QHBoxLayout()
        
        self.total_value_label = QLabel("Total Value: €0.00")
        self.total_invested_label = QLabel("Total Invested: €0.00")
        self.total_pnl_label = QLabel("P&L: €0.00 (0.00%)")
        
        # Style the summary labels
        for label in [self.total_value_label, self.total_invested_label, self.total_pnl_label]:
            label.setFont(QFont("Arial", 12, QFont.Bold))
            label.setStyleSheet("padding: 10px; border: 1px solid #555555; border-radius: 5px; margin: 5px;")
        
        header_layout.addWidget(self.total_value_label)
        header_layout.addWidget(self.total_invested_label)
        header_layout.addWidget(self.total_pnl_label)
        header_group.setLayout(header_layout)
        
        # Refresh button
        refresh_btn = QPushButton("Refresh Prices")
        refresh_btn.clicked.connect(self.update_all_prices)
        
        layout.addWidget(header_group)
        layout.addWidget(refresh_btn)
        
        # Create splitter for charts and table
        splitter = QSplitter(Qt.Horizontal)
        
        # Charts widget
        charts_widget = QWidget()
        charts_layout = QVBoxLayout()
        
        # Portfolio composition chart
        self.portfolio_figure = Figure(figsize=(8, 6), facecolor='#2b2b2b')
        self.portfolio_canvas = FigureCanvas(self.portfolio_figure)
        charts_layout.addWidget(self.portfolio_canvas)
        
        # Portfolio value over time chart
        self.timeline_figure = Figure(figsize=(8, 4), facecolor='#2b2b2b')
        self.timeline_canvas = FigureCanvas(self.timeline_figure)
        charts_layout.addWidget(self.timeline_canvas)
        
        charts_widget.setLayout(charts_layout)
        
        # Portfolio table
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(8)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Type", "Amount", "Price", "Value", "Invested", "P&L (%)"
        ])
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.portfolio_table.setAlternatingRowColors(True)
        
        splitter.addWidget(charts_widget)
        splitter.addWidget(self.portfolio_table)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        widget.setLayout(layout)
        return widget
    
    def create_transactions_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add transaction form
        form_group = QGroupBox("Add New Transaction")
        form_layout = QFormLayout()
        
        self.asset_combo = QComboBox()
        self.transaction_type_combo = QComboBox()
        self.transaction_type_combo.addItems(["buy", "sell", "dividend", "fee"])
        self.amount_spin = QDoubleSpinBox()
        self.amount_spin.setMaximum(999999999.99)
        self.amount_spin.setDecimals(8)
        self.price_spin = QDoubleSpinBox()
        self.price_spin.setMaximum(999999999.99)
        self.price_spin.setDecimals(2)
        self.fees_spin = QDoubleSpinBox()
        self.fees_spin.setMaximum(999999999.99)
        self.fees_spin.setDecimals(2)
        self.platform_edit = QLineEdit()
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(60)
        
        form_layout.addRow("Asset:", self.asset_combo)
        form_layout.addRow("Type:", self.transaction_type_combo)
        form_layout.addRow("Amount:", self.amount_spin)
        form_layout.addRow("Price per Unit:", self.price_spin)
        form_layout.addRow("Fees:", self.fees_spin)
        form_layout.addRow("Platform:", self.platform_edit)
        form_layout.addRow("Date:", self.date_edit)
        form_layout.addRow("Notes:", self.notes_edit)
        
        add_transaction_btn = QPushButton("Add Transaction")
        add_transaction_btn.clicked.connect(self.add_transaction)
        form_layout.addRow(add_transaction_btn)
        
        form_group.setLayout(form_layout)
        
        # Transactions table
        self.transactions_table = QTableWidget()
        self.transactions_table.setColumnCount(9)
        self.transactions_table.setHorizontalHeaderLabels([
            "Asset", "Type", "Amount", "Price", "Total", "Fees", "Platform", "Date", "Notes"
        ])
        self.transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.transactions_table.setAlternatingRowColors(True)
        
        layout.addWidget(form_group)
        layout.addWidget(QLabel("Recent Transactions"))
        layout.addWidget(self.transactions_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_assets_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Add asset form
        form_group = QGroupBox("Add New Asset")
        form_layout = QFormLayout()
        
        self.new_symbol_edit = QLineEdit()
        self.new_name_edit = QLineEdit()
        self.new_type_combo = QComboBox()
        self.new_type_combo.addItems(["stock", "etf", "crypto", "bond", "commodity"])
        self.new_platform_edit = QLineEdit()
        
        form_layout.addRow("Symbol:", self.new_symbol_edit)
        form_layout.addRow("Name:", self.new_name_edit)
        form_layout.addRow("Type:", self.new_type_combo)
        form_layout.addRow("Platform:", self.new_platform_edit)
        
        add_asset_btn = QPushButton("Add Asset")
        add_asset_btn.clicked.connect(self.add_asset)
        form_layout.addRow(add_asset_btn)
        
        form_group.setLayout(form_layout)
        
        # Manual price update
        price_group = QGroupBox("Manual Price Update")
        price_layout = QFormLayout()
        
        self.price_asset_combo = QComboBox()
        self.manual_price_spin = QDoubleSpinBox()
        self.manual_price_spin.setMaximum(999999999.99)
        self.manual_price_spin.setDecimals(2)
        
        price_layout.addRow("Asset:", self.price_asset_combo)
        price_layout.addRow("New Price:", self.manual_price_spin)
        
        update_price_btn = QPushButton("Update Price")
        update_price_btn.clicked.connect(self.update_manual_price)
        price_layout.addRow(update_price_btn)
        
        price_group.setLayout(price_layout)
        
        # Assets table
        self.assets_table = QTableWidget()
        self.assets_table.setColumnCount(6)
        self.assets_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Type", "Platform", "Current Price", "Last Updated"
        ])
        self.assets_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.assets_table.setAlternatingRowColors(True)
        
        # Control buttons
        control_layout = QHBoxLayout()
        delete_asset_btn = QPushButton("Delete Selected Asset")
        delete_asset_btn.clicked.connect(self.delete_selected_asset)
        control_layout.addWidget(delete_asset_btn)
        control_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addWidget(price_group)
        layout.addWidget(QLabel("Assets"))
        layout.addLayout(control_layout)
        layout.addWidget(self.assets_table)
        
        widget.setLayout(layout)
        return widget
    
    def refresh_all_data(self):
        """Refresh all data in the GUI"""
        self.load_portfolio_data()
        self.load_transactions_data()
        self.load_assets_data()
        self.update_asset_combos()
        self.update_charts()
    
    def load_portfolio_data(self):
        """Load and display portfolio data"""
        portfolio = self.tracker.get_portfolio_summary()
        
        self.portfolio_table.setRowCount(len(portfolio))
        
        total_value = 0
        total_invested = 0
        
        for row, asset in enumerate(portfolio):
            self.portfolio_table.setItem(row, 0, QTableWidgetItem(str(asset['symbol'])))
            self.portfolio_table.setItem(row, 1, QTableWidgetItem(str(asset['name'])))
            self.portfolio_table.setItem(row, 2, QTableWidgetItem(str(asset['asset_type'])))
            self.portfolio_table.setItem(row, 3, QTableWidgetItem(f"{asset['total_amount']:.4f}"))
            self.portfolio_table.setItem(row, 4, QTableWidgetItem(f"€{asset['current_price']:.2f}"))
            self.portfolio_table.setItem(row, 5, QTableWidgetItem(f"€{asset['current_value']:.2f}"))
            self.portfolio_table.setItem(row, 6, QTableWidgetItem(f"€{asset['total_invested']:.2f}"))
            
            pnl_text = f"€{asset['profit_loss']:.2f} ({asset['profit_loss_percent']:.1f}%)"
            pnl_item = QTableWidgetItem(pnl_text)
            
            # Color coding for profit/loss
            if asset['profit_loss'] > 0:
                pnl_item.setBackground(Qt.darkGreen)
            elif asset['profit_loss'] < 0:
                pnl_item.setBackground(Qt.darkRed)
            
            self.portfolio_table.setItem(row, 7, pnl_item)
            
            total_value += asset['current_value']
            total_invested += asset['total_invested']
        
        # Update summary labels
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        self.total_value_label.setText(f"Total Value: €{total_value:.2f}")
        self.total_invested_label.setText(f"Total Invested: €{total_invested:.2f}")
        self.total_pnl_label.setText(f"P&L: €{total_pnl:.2f} ({total_pnl_percent:.1f}%)")
        
        # Color code the P&L label
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet("padding: 10px; border: 1px solid #555555; border-radius: 5px; margin: 5px; background-color: #1a4a1a; color: #4ade80;")
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet("padding: 10px; border: 1px solid #555555; border-radius: 5px; margin: 5px; background-color: #4a1a1a; color: #f87171;")
        else:
            self.total_pnl_label.setStyleSheet("padding: 10px; border: 1px solid #555555; border-radius: 5px; margin: 5px;")
    
    def load_transactions_data(self):
        """Load and display transactions data"""
        transactions = self.tracker.get_transactions()
        
        self.transactions_table.setRowCount(len(transactions))
        
        for row, transaction in enumerate(transactions):
            self.transactions_table.setItem(row, 0, QTableWidgetItem(str(transaction['asset_symbol'])))
            self.transactions_table.setItem(row, 1, QTableWidgetItem(str(transaction['transaction_type'])))
            self.transactions_table.setItem(row, 2, QTableWidgetItem(f"{transaction['amount']:.4f}"))
            self.transactions_table.setItem(row, 3, QTableWidgetItem(f"€{transaction['price_per_unit']:.2f}"))
            self.transactions_table.setItem(row, 4, QTableWidgetItem(f"€{transaction['total_value']:.2f}"))
            self.transactions_table.setItem(row, 5, QTableWidgetItem(f"€{transaction['fees']:.2f}"))
            self.transactions_table.setItem(row, 6, QTableWidgetItem(str(transaction.get('platform', ''))))
            self.transactions_table.setItem(row, 7, QTableWidgetItem(str(transaction['transaction_date'])[:16]))
            self.transactions_table.setItem(row, 8, QTableWidgetItem(str(transaction.get('notes', ''))))
    
    def load_assets_data(self):
        """Load and display assets data"""
        assets = self.tracker.get_all_assets()
        
        self.assets_table.setRowCount(len(assets))
        
        for row, asset in enumerate(assets):
            self.assets_table.setItem(row, 0, QTableWidgetItem(str(asset['symbol'])))
            self.assets_table.setItem(row, 1, QTableWidgetItem(str(asset['name'])))
            self.assets_table.setItem(row, 2, QTableWidgetItem(str(asset['asset_type'])))
            self.assets_table.setItem(row, 3, QTableWidgetItem(str(asset.get('platform', ''))))
            self.assets_table.setItem(row, 4, QTableWidgetItem(f"€{asset['current_price']:.2f}"))
            self.assets_table.setItem(row, 5, QTableWidgetItem(str(asset.get('last_updated', ''))[:16]))
    
    def update_asset_combos(self):
        """Update asset combo boxes with current assets"""
        assets = self.tracker.get_all_assets()
        asset_symbols = [asset['symbol'] for asset in assets]
        
        # Clear and populate asset combo
        self.asset_combo.clear()
        self.asset_combo.addItems(asset_symbols)
        
        # Clear and populate price update combo
        self.price_asset_combo.clear()
        self.price_asset_combo.addItems(asset_symbols)
    
    def update_charts(self):
        """Update the portfolio charts"""
        portfolio = self.tracker.get_portfolio_summary()
        
        if not portfolio:
            # Clear charts if no portfolio data
            self.portfolio_figure.clear()
            self.timeline_figure.clear()
            self.portfolio_canvas.draw()
            self.timeline_canvas.draw()
            return
        
        # Portfolio composition pie chart
        self.portfolio_figure.clear()
        ax1 = self.portfolio_figure.add_subplot(111)
        
        symbols = [asset['symbol'] for asset in portfolio]
        values = [asset['current_value'] for asset in portfolio]
        colors = plt.cm.Set3(range(len(symbols)))
        
        wedges, texts, autotexts = ax1.pie(values, labels=symbols, autopct='%1.1f%%', colors=colors)
        
        # Set text colors to white for better visibility
        for text in texts:
            text.set_color('white')
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax1.set_title('Portfolio Composition', color='white', fontsize=14, fontweight='bold')
        ax1.set_facecolor('#2b2b2b')
        
        self.portfolio_figure.patch.set_facecolor('#2b2b2b')
        self.portfolio_canvas.draw()
        
        # Portfolio value timeline (simplified - using dummy data for now)
        self.timeline_figure.clear()
        ax2 = self.timeline_figure.add_subplot(111)
        
        # This is a simplified timeline - in a real app you'd track portfolio value over time
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')[-30:]
        total_value = sum(values) if values else 0
        # Simulate some price movement
        portfolio_values = [total_value * (1 + (i % 10 - 5) * 0.01) for i in range(len(dates))]
        
        ax2.plot(dates, portfolio_values, color='#4ade80', linewidth=2)
        ax2.set_title('Portfolio Value (Last 30 Days)', color='white', fontsize=12, fontweight='bold')
        ax2.set_facecolor('#2b2b2b')
        ax2.tick_params(colors='white')
        ax2.grid(True, alpha=0.3, color='white')
        
        # Set axis labels color
        ax2.xaxis.label.set_color('white')
        ax2.yaxis.label.set_color('white')
        
        self.timeline_figure.patch.set_facecolor('#2b2b2b')
        self.timeline_canvas.draw()
    
    def add_asset(self):
        """Add a new asset"""
        symbol = self.new_symbol_edit.text().strip().upper()
        name = self.new_name_edit.text().strip()
        asset_type = self.new_type_combo.currentText()
        platform = self.new_platform_edit.text().strip()
        
        if not symbol or not name:
            QMessageBox.warning(self, "Error", "Symbol and Name are required!")
            return
        
        if self.tracker.add_asset(symbol, name, asset_type, platform):
            QMessageBox.information(self, "Success", f"Asset {symbol} added successfully!")
            self.new_symbol_edit.clear()
            self.new_name_edit.clear()
            self.new_platform_edit.clear()
            self.refresh_all_data()
        else:
            QMessageBox.warning(self, "Error", "Failed to add asset!")
    
    def add_transaction(self):
        """Add a new transaction"""
        if self.asset_combo.currentText() == "":
            QMessageBox.warning(self, "Error", "Please select an asset!")
            return
        
        asset_symbol = self.asset_combo.currentText()
        transaction_type = self.transaction_type_combo.currentText()
        amount = self.amount_spin.value()
        price = self.price_spin.value()
        fees = self.fees_spin.value()
        platform = self.platform_edit.text().strip()
        date = self.date_edit.date().toString("yyyy-MM-dd")
        notes = self.notes_edit.toPlainText().strip()
        
        if amount <= 0 or price <= 0:
            QMessageBox.warning(self, "Error", "Amount and Price must be greater than 0!")
            return
        
        if self.tracker.add_transaction(asset_symbol, transaction_type, amount, price, fees, platform, date, notes):
            QMessageBox.information(self, "Success", "Transaction added successfully!")
            self.amount_spin.setValue(0)
            self.price_spin.setValue(0)
            self.fees_spin.setValue(0)
            self.platform_edit.clear()
            self.notes_edit.clear()
            self.refresh_all_data()
        else:
            QMessageBox.warning(self, "Error", "Failed to add transaction!")
    
    def update_manual_price(self):
        """Update asset price manually"""
        if self.price_asset_combo.currentText() == "":
            QMessageBox.warning(self, "Error", "Please select an asset!")
            return
        
        symbol = self.price_asset_combo.currentText()
        price = self.manual_price_spin.value()
        
        if price <= 0:
            QMessageBox.warning(self, "Error", "Price must be greater than 0!")
            return
        
        if self.tracker.update_asset_values_manually(symbol, price):
            QMessageBox.information(self, "Success", f"Price for {symbol} updated successfully!")
            self.manual_price_spin.setValue(0)
            self.refresh_all_data()
        else:
            QMessageBox.warning(self, "Error", "Failed to update price!")
    
    def update_all_prices(self):
        """Update all asset prices from APIs"""
        QMessageBox.information(self, "Info", "Updating prices... This may take a moment.")
        
        results = self.tracker.update_asset_prices()
        
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        QMessageBox.information(self, "Price Update Complete", 
                               f"Successfully updated {success_count}/{total_count} asset prices.")
        
        self.refresh_all_data()
    
    def delete_selected_asset(self):
        """Delete the selected asset"""
        current_row = self.assets_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Error", "Please select an asset to delete!")
            return
        
        symbol = self.assets_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(self, "Confirm Delete", 
                                   f"Are you sure you want to delete asset {symbol} and all its transactions?",
                                   QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            if self.tracker.delete_asset(symbol):
                QMessageBox.information(self, "Success", f"Asset {symbol} deleted successfully!")
                self.refresh_all_data()
            else:
                QMessageBox.warning(self, "Error", "Failed to delete asset!")

def main():
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Investment Portfolio Tracker")
    app.setApplicationVersion("1.0")
    
    # Create and show the main window
    window = InvestmentGUI()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()