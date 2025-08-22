import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                               QHBoxLayout, QTabWidget, QLabel, QPushButton, 
                               QTableWidget, QTableWidgetItem, QLineEdit, 
                               QComboBox, QDoubleSpinBox, QDateEdit, QTextEdit,
                               QGroupBox, QFormLayout, QMessageBox, QHeaderView,
                               QSplitter, QFrame)
from PySide6.QtCore import Qt, QDate, QTimer
from PySide6.QtGui import QFont, QPalette, QColor
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
        self.setWindowTitle("💰 Investment Portfolio Tracker")
        self.setGeometry(100, 100, 1600, 1000)
        
        # Set window icon (if available)
        # self.setWindowIcon(QIcon("assets/icon.png"))
        
        # Apply modern dark theme with improved aesthetics
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2d3748, stop: 1 #1a202c);
                color: #e2e8f0;
            }
            QWidget {
                background-color: transparent;
                color: #e2e8f0;
                font-family: 'Segoe UI', 'San Francisco', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 2px solid #4a5568;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #2d3748, stop: 1 #1a202c);
                border-radius: 8px;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4a5568, stop: 1 #2d3748);
                color: #cbd5e0;
                padding: 12px 20px;
                margin-right: 3px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border: 1px solid #4a5568;
                font-weight: 600;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0078d4, stop: 1 #0056b3);
                color: #ffffff;
                border-bottom: none;
            }
            QTabBar::tab:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5a6578, stop: 1 #3d4852);
            }
            QTableWidget {
                background-color: #2d3748;
                alternate-background-color: #374151;
                gridline-color: #4a5568;
                selection-background-color: #0078d4;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 8px;
                font-size: 11px;
            }
            QTableWidget::item {
                color: #e2e8f0;
                padding: 8px;
                border-bottom: 1px solid #374151;
            }
            QTableWidget::item:selected {
                background-color: #0078d4;
                color: #ffffff;
            }
            QHeaderView::section {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4a5568, stop: 1 #374151);
                color: #f7fafc;
                padding: 10px;
                border: 1px solid #2d3748;
                font-weight: 600;
                font-size: 12px;
            }
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #0078d4, stop: 1 #0056b3);
                color: #ffffff;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: 600;
                font-size: 12px;
                min-height: 16px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #106ebe, stop: 1 #0056b3);
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #004494, stop: 1 #003d82);
            }
            QLineEdit, QDoubleSpinBox, QComboBox, QDateEdit, QTextEdit {
                background-color: #374151;
                color: #e2e8f0;
                border: 2px solid #4a5568;
                padding: 8px 12px;
                border-radius: 6px;
                font-size: 12px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, 
            QDateEdit:focus, QTextEdit:focus {
                border-color: #0078d4;
                background-color: #2d3748;
            }
            QComboBox::drop-down {
                border: none;
                background-color: transparent;
                width: 20px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 6px solid transparent;
                border-right: 6px solid transparent;
                border-top: 6px solid #cbd5e0;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #374151;
                color: #e2e8f0;
                border: 1px solid #4a5568;
                border-radius: 6px;
                selection-background-color: #0078d4;
            }
            QSpinBox, QDoubleSpinBox {
                background-color: #374151;
                color: #e2e8f0;
                border: 2px solid #4a5568;
                border-radius: 6px;
                padding: 8px;
            }
            QGroupBox {
                font-weight: 600;
                font-size: 14px;
                border: 2px solid #4a5568;
                border-radius: 8px;
                margin-top: 16px;
                padding-top: 12px;
                color: #f7fafc;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #374151, stop: 1 #2d3748);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 16px;
                padding: 0 8px 0 8px;
                color: #0078d4;
                font-weight: 700;
            }
            QLabel {
                color: #e2e8f0;
                background-color: transparent;
                font-size: 12px;
            }
            QFormLayout QLabel {
                color: #cbd5e0;
                font-weight: 500;
            }
            QScrollBar:vertical {
                background-color: #374151;
                width: 12px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: #4a5568;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #5a6578;
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
        
        # Style the summary labels with improved design
        summary_style = """
            QLabel {
                padding: 16px;
                border: 2px solid #4a5568;
                border-radius: 12px;
                margin: 8px;
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #374151, stop: 1 #2d3748);
                font-size: 14px;
                font-weight: 600;
                min-height: 20px;
            }
        """
        
        for label in [self.total_value_label, self.total_invested_label, self.total_pnl_label]:
            label.setFont(QFont("Segoe UI", 12, QFont.Bold))
            label.setStyleSheet(summary_style)
        
        header_layout.addWidget(self.total_value_label)
        header_layout.addWidget(self.total_invested_label)
        header_layout.addWidget(self.total_pnl_label)
        header_group.setLayout(header_layout)
        
        # Refresh button with improved styling
        refresh_btn = QPushButton("Refresh Prices")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #48bb78, stop: 1 #38a169);
                font-size: 13px;
                padding: 12px 24px;
                border-radius: 8px;
                margin: 8px;
            }
            QPushButton:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4fd180, stop: 1 #48bb78);
            }
        """)
        refresh_btn.clicked.connect(self.update_all_prices)
        
        layout.addWidget(header_group)
        layout.addWidget(refresh_btn)
        
        # Create splitter for chart and table
        splitter = QSplitter(Qt.Horizontal)
        
        # Portfolio composition chart (by asset type)
        chart_widget = QWidget()
        chart_layout = QVBoxLayout()
        
        self.portfolio_figure = Figure(figsize=(8, 8), facecolor='#2b2b2b')
        self.portfolio_canvas = FigureCanvas(self.portfolio_figure)
        chart_layout.addWidget(self.portfolio_canvas)
        chart_widget.setLayout(chart_layout)
        
        # Portfolio table with profit % column
        self.portfolio_table = QTableWidget()
        self.portfolio_table.setColumnCount(9)
        self.portfolio_table.setHorizontalHeaderLabels([
            "Symbol", "Name", "Type", "Amount", "Price", "Value", "Invested", "P&L (EUR)", "P&L (%)"
        ])
        self.portfolio_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.portfolio_table.setAlternatingRowColors(True)
        
        splitter.addWidget(chart_widget)
        splitter.addWidget(self.portfolio_table)
        splitter.setSizes([400, 600])
        
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
        self.platform_edit.setPlaceholderText("e.g., Binance, eToro, Interactive Brokers")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.notes_edit = QTextEdit()
        self.notes_edit.setMaximumHeight(80)
        self.notes_edit.setPlaceholderText("Optional notes about this transaction...")
        
        form_layout.addRow("Asset:", self.asset_combo)
        form_layout.addRow("Type:", self.transaction_type_combo)
        form_layout.addRow("Amount:", self.amount_spin)
        form_layout.addRow("Price per Unit:", self.price_spin)
        form_layout.addRow("Fees:", self.fees_spin)
        form_layout.addRow("Platform:", self.platform_edit)
        form_layout.addRow("Date:", self.date_edit)
        form_layout.addRow("Notes:", self.notes_edit)
        
        add_transaction_btn = QPushButton("Add Transaction")
        add_transaction_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #48bb78, stop: 1 #38a169);
                font-size: 13px;
                padding: 12px 24px;
                margin: 8px 0px;
            }
        """)
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
        self.new_symbol_edit.setPlaceholderText("e.g., AAPL, BTC, VWCE.DE")
        self.new_name_edit = QLineEdit()
        self.new_name_edit.setPlaceholderText("e.g., Apple Inc., Bitcoin")
        self.new_type_combo = QComboBox()
        self.new_type_combo.addItems(["stock", "etf", "crypto", "bond", "commodity"])
        self.new_platform_edit = QLineEdit()
        self.new_platform_edit.setPlaceholderText("e.g., Interactive Brokers, Binance")
        
        form_layout.addRow("Symbol:", self.new_symbol_edit)
        form_layout.addRow("Name:", self.new_name_edit)
        form_layout.addRow("Type:", self.new_type_combo)
        form_layout.addRow("Platform:", self.new_platform_edit)
        
        add_asset_btn = QPushButton("Add Asset")
        add_asset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #48bb78, stop: 1 #38a169);
                font-size: 13px;
                padding: 12px 24px;
                margin: 8px 0px;
            }
        """)
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
        # Note: QDoubleSpinBox doesn't support placeholder text
        
        price_layout.addRow("Asset:", self.price_asset_combo)
        price_layout.addRow("New Price (EUR):", self.manual_price_spin)
        
        update_price_btn = QPushButton("Update Price")
        update_price_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #ed8936, stop: 1 #dd6b20);
                font-size: 13px;
                padding: 12px 24px;
                margin: 8px 0px;
            }
        """)
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
        delete_asset_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f56565, stop: 1 #e53e3e);
                font-size: 12px;
                padding: 10px 16px;
            }
        """)
        delete_asset_btn.clicked.connect(self.delete_selected_asset)
        control_layout.addWidget(delete_asset_btn)
        control_layout.addStretch()
        
        layout.addWidget(form_group)
        layout.addWidget(price_group)
        layout.addWidget(QLabel("Assets Portfolio"))
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
            
            # P&L in EUR
            pnl_eur_item = QTableWidgetItem(f"€{asset['profit_loss']:.2f}")
            if asset['profit_loss'] > 0:
                pnl_eur_item.setForeground(QColor('#4CAF50'))  # Green for profit
            elif asset['profit_loss'] < 0:
                pnl_eur_item.setForeground(QColor('#F44336'))  # Red for loss
            self.portfolio_table.setItem(row, 7, pnl_eur_item)
            
            # P&L in %
            pnl_pct_item = QTableWidgetItem(f"{asset['profit_loss_percent']:.1f}%")
            if asset['profit_loss_percent'] > 0:
                pnl_pct_item.setForeground(QColor('#4CAF50'))  # Green for profit
            elif asset['profit_loss_percent'] < 0:
                pnl_pct_item.setForeground(QColor('#F44336'))  # Red for loss
            self.portfolio_table.setItem(row, 8, pnl_pct_item)
            
            total_value += asset['current_value']
            total_invested += asset['total_invested']
        
        # Update summary labels
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        
        self.total_value_label.setText(f"Total Value: €{total_value:.2f}")
        self.total_invested_label.setText(f"Total Invested: €{total_invested:.2f}")
        self.total_pnl_label.setText(f"P&L: €{total_pnl:.2f} ({total_pnl_percent:.1f}%)")
        
        # Color code the P&L label with improved styling
        if total_pnl > 0:
            self.total_pnl_label.setStyleSheet("""
                QLabel {
                    padding: 16px;
                    border: 2px solid #48bb78;
                    border-radius: 12px;
                    margin: 8px;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #2f855a, stop: 1 #276749);
                    color: #9ae6b4;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 20px;
                }
            """)
        elif total_pnl < 0:
            self.total_pnl_label.setStyleSheet("""
                QLabel {
                    padding: 16px;
                    border: 2px solid #f56565;
                    border-radius: 12px;
                    margin: 8px;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #c53030, stop: 1 #9b2c2c);
                    color: #feb2b2;
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 20px;
                }
            """)
        else:
            self.total_pnl_label.setStyleSheet("""
                QLabel {
                    padding: 16px;
                    border: 2px solid #4a5568;
                    border-radius: 12px;
                    margin: 8px;
                    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                        stop: 0 #374151, stop: 1 #2d3748);
                    font-size: 14px;
                    font-weight: 600;
                    min-height: 20px;
                }
            """)
    
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
            # Clear chart if no portfolio data
            self.portfolio_figure.clear()
            self.portfolio_canvas.draw()
            return
        
        # Portfolio composition by asset type pie chart
        self.portfolio_figure.clear()
        ax1 = self.portfolio_figure.add_subplot(111)
        
        # Group by asset type
        type_values = {}
        for asset in portfolio:
            asset_type = asset['asset_type'].lower()
            if asset_type not in type_values:
                type_values[asset_type] = 0
            type_values[asset_type] += asset['current_value']
        
        # Filter out zero values
        type_values = {k: v for k, v in type_values.items() if v > 0}
        
        if type_values:
            types = list(type_values.keys())
            values = list(type_values.values())
            
            # Color mapping for asset types
            color_map = {
                'stock': '#FF6B6B',
                'etf': '#4ECDC4', 
                'crypto': '#45B7D1',
                'bond': '#FFA726',
                'commodity': '#AB47BC'
            }
            colors = [color_map.get(asset_type, '#95A5A6') for asset_type in types]
            
            # Create labels with values
            labels = [f"{asset_type.upper()}\n€{value:.2f}" for asset_type, value in zip(types, values)]
            
            wedges, texts, autotexts = ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors, startangle=90)
            
            # Set text colors to white for better visibility
            for text in texts:
                text.set_color('white')
                text.set_fontsize(10)
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontweight('bold')
                autotext.set_fontsize(9)
        
        ax1.set_title('Portfolio Composition by Asset Type', color='white', fontsize=14, fontweight='bold')
        ax1.set_facecolor('#2b2b2b')
        
        self.portfolio_figure.patch.set_facecolor('#2b2b2b')
        self.portfolio_figure.tight_layout()
        self.portfolio_canvas.draw()
    
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