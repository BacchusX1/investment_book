#!/usr/bin/env python3
"""
Test script to demonstrate the investment tracker backend functionality
"""

import sys
import os

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from backend import InvestmentTracker

def test_backend():
    """Test the backend functionality"""
    print("=== Testing Investment Tracker Backend ===")
    
    # Initialize tracker with test database
    tracker = InvestmentTracker("test_assets.db")
    print("✓ Database initialized")
    
    # Add some test assets
    assets_to_add = [
        ("BTC", "Bitcoin", "crypto", "Bitpanda"),
        ("ETH", "Ethereum", "crypto", "Bitpanda"),
        ("AAPL", "Apple Inc.", "stock", "Trade Republic"),
        ("MSFT", "Microsoft Corporation", "stock", "Trade Republic"),
        ("VWCE.DE", "Vanguard FTSE All-World UCITS ETF", "etf", "Trade Republic")
    ]
    
    for symbol, name, asset_type, platform in assets_to_add:
        success = tracker.add_asset(symbol, name, asset_type, platform)
        if success:
            print(f"✓ Added asset: {symbol} ({name})")
        else:
            print(f"✗ Failed to add asset: {symbol}")
    
    # Add some test transactions
    transactions_to_add = [
        ("BTC", "buy", 0.5, 45000.0, 25.0, "Bitpanda"),
        ("BTC", "buy", 0.3, 50000.0, 20.0, "Bitpanda"),
        ("ETH", "buy", 2.0, 3000.0, 15.0, "Bitpanda"),
        ("AAPL", "buy", 10, 150.0, 5.0, "Trade Republic"),
        ("MSFT", "buy", 5, 300.0, 5.0, "Trade Republic"),
        ("VWCE.DE", "buy", 50, 85.0, 2.5, "Trade Republic")
    ]
    
    for symbol, t_type, amount, price, fees, platform in transactions_to_add:
        success = tracker.add_transaction(symbol, t_type, amount, price, fees, platform)
        if success:
            print(f"✓ Added transaction: {t_type} {amount} {symbol} @ €{price}")
        else:
            print(f"✗ Failed to add transaction for {symbol}")
    
    # Update prices
    print("\n=== Updating Prices ===")
    results = tracker.update_asset_prices()
    for symbol, success in results.items():
        if success:
            print(f"✓ Updated price for {symbol}")
        else:
            print(f"✗ Failed to update price for {symbol}")
    
    # Get portfolio summary
    print("\n=== Portfolio Summary ===")
    portfolio = tracker.get_portfolio_summary()
    
    if portfolio:
        total_value = 0
        total_invested = 0
        
        print(f"{'Symbol':<10} {'Amount':<12} {'Price':<10} {'Value':<12} {'Invested':<12} {'P&L':<12}")
        print("-" * 70)
        
        for asset in portfolio:
            print(f"{asset['symbol']:<10} {asset['total_amount']:<12.4f} €{asset['current_price']:<9.2f} €{asset['current_value']:<11.2f} €{asset['total_invested']:<11.2f} €{asset['profit_loss']:<11.2f}")
            total_value += asset['current_value']
            total_invested += asset['total_invested']
        
        print("-" * 70)
        total_pnl = total_value - total_invested
        total_pnl_percent = (total_pnl / total_invested * 100) if total_invested > 0 else 0
        print(f"{'TOTAL':<10} {'':<12} {'':<10} €{total_value:<11.2f} €{total_invested:<11.2f} €{total_pnl:<11.2f} ({total_pnl_percent:.1f}%)")
        
    else:
        print("No portfolio data available")
    
    # Get recent transactions
    print("\n=== Recent Transactions ===")
    transactions = tracker.get_transactions()
    
    if transactions:
        print(f"{'Asset':<8} {'Type':<6} {'Amount':<12} {'Price':<10} {'Total':<12} {'Date':<12}")
        print("-" * 62)
        
        for i, trans in enumerate(transactions[:10]):  # Show last 10 transactions
            date_str = trans['transaction_date'][:10] if trans['transaction_date'] else ""
            print(f"{trans['asset_symbol']:<8} {trans['transaction_type']:<6} {trans['amount']:<12.4f} €{trans['price_per_unit']:<9.2f} €{trans['total_value']:<11.2f} {date_str:<12}")
    else:
        print("No transactions found")
    
    print(f"\n✓ Backend test completed successfully!")
    print(f"Test database created at: test_assets.db")
    print(f"You can now run the GUI with this database for testing.")

if __name__ == "__main__":
    test_backend()
