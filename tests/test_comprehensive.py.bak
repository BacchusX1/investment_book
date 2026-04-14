#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite for Investment Portfolio Tracker

This script creates a realistic portfolio with diverse assets and demonstrates:
- Multi-currency asset support with automatic EUR conversion
- Dynamic cryptocurrency fetching from CoinGecko API
- Asset type-based API routing
- Transaction management and portfolio analytics
- GUI-ready database creation
"""

import sys
import os
import time
import unittest
from datetime import datetime, timedelta

# Add the src directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from backend import InvestmentTracker

class TestComprehensivePortfolio(unittest.TestCase):
    """Test suite for comprehensive portfolio functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.test_db = 'test_comprehensive.db'
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
        self.tracker = InvestmentTracker(self.test_db)
    
    def tearDown(self):
        """Clean up test database"""
        try:
            if os.path.exists(self.test_db):
                os.remove(self.test_db)
        except:
            pass
    
    def test_multi_currency_portfolio(self):
        """Test portfolio with assets from different currencies"""
        # Add assets from different markets
        assets = [
            ("AAPL", "Apple Inc.", "stock"),     # USD
            ("ASML.AS", "ASML Holding", "stock"), # EUR
            ("VOD.L", "Vodafone", "stock"),      # GBP
            ("BTC", "Bitcoin", "crypto"),        # EUR (via CoinGecko)
        ]
        
        for symbol, name, asset_type in assets:
            result = self.tracker.add_asset(symbol, name, asset_type)
            self.assertTrue(result, f"Failed to add {symbol}")
        
        # Add transactions
        transactions = [
            ("AAPL", "buy", 10, 150.0, 5.0, "Test"),
            ("ASML.AS", "buy", 2, 600.0, 7.5, "Test"),
            ("BTC", "buy", 0.1, 45000.0, 25.0, "Test"),
        ]
        
        for symbol, t_type, amount, price, fees, platform in transactions:
            result = self.tracker.add_transaction(symbol, t_type, amount, price, fees, platform)
            self.assertTrue(result, f"Failed to add transaction for {symbol}")
        
        # Check portfolio
        portfolio = self.tracker.get_portfolio_summary()
        self.assertGreaterEqual(len(portfolio), 3)
    
    def test_asset_type_distribution(self):
        """Test portfolio with different asset types"""
        assets = [
            ("AAPL", "Apple Inc.", "stock"),
            ("VWCE.DE", "Vanguard All-World ETF", "etf"),
            ("BTC", "Bitcoin", "crypto"),
        ]
        
        for symbol, name, asset_type in assets:
            self.tracker.add_asset(symbol, name, asset_type)
            self.tracker.add_transaction(symbol, "buy", 1.0, 100.0, 1.0)
        
        portfolio = self.tracker.get_portfolio_summary()
        asset_types = {asset['asset_type'] for asset in portfolio}
        
        self.assertIn('stock', asset_types)
        self.assertIn('etf', asset_types)
        self.assertIn('crypto', asset_types)

def create_demo_portfolio():
    """Create a comprehensive demonstration portfolio"""
    
    # Clean slate
    demo_db = 'comprehensive_demo.db'
    if os.path.exists(demo_db):
        os.remove(demo_db)
    
    tracker = InvestmentTracker(demo_db)
    
    print("🚀 Investment Portfolio Tracker - Comprehensive Demo")
    print("=" * 65)
    print("Creating realistic portfolio with diverse assets...")
    
    # Comprehensive asset selection across markets and currencies
    demo_assets = [
        # US Tech Stocks (USD → EUR)
        ('AAPL', 'Apple Inc.', 'stock'),
        ('MSFT', 'Microsoft Corporation', 'stock'),
        ('GOOGL', 'Alphabet Inc.', 'stock'),
        ('NVDA', 'NVIDIA Corporation', 'stock'),
        
        # European Stocks (EUR)
        ('ASML.AS', 'ASML Holding N.V.', 'stock'),
        ('SAP.DE', 'SAP SE', 'stock'),
        
        # UK Stocks (GBP → EUR)
        ('VOD.L', 'Vodafone Group Plc', 'stock'),
        ('BP.L', 'BP p.l.c.', 'stock'),
        
        # Swiss Stocks (CHF → EUR)
        ('NESN.SW', 'Nestlé S.A.', 'stock'),
        
        # ETFs (Mixed currencies)
        ('VWCE.DE', 'Vanguard FTSE All-World UCITS ETF', 'etf'),
        ('SPY', 'SPDR S&P 500 ETF Trust', 'etf'),
        ('QQQ', 'Invesco QQQ Trust', 'etf'),
        
        # Major Cryptocurrencies (EUR via CoinGecko)
        ('BTC', 'Bitcoin', 'crypto'),
        ('ETH', 'Ethereum', 'crypto'),
        ('ADA', 'Cardano', 'crypto'),
        ('SOL', 'Solana', 'crypto'),
        ('DOT', 'Polkadot', 'crypto'),
    ]
    
    print(f"\n📊 Adding {len(demo_assets)} Demo Assets...")
    print("-" * 45)
    
    added_count = 0
    for symbol, name, asset_type in demo_assets:
        print(f"Adding {symbol:12} ({asset_type:6})...", end=" ")
        try:
            success = tracker.add_asset(symbol, name, asset_type)
            if success:
                print("✅")
                added_count += 1
            else:
                print("❌")
            
            # Rate limiting for crypto APIs
            if asset_type == 'crypto':
                time.sleep(1.2)
                
        except Exception as e:
            print(f"❌ ({str(e)[:30]}...)")
    
    print(f"\n✅ Successfully added {added_count}/{len(demo_assets)} assets")
    
    # Realistic transaction history
    demo_transactions = [
        # Initial stock investments
        ('AAPL', 'buy', 25, 145.50, 9.99, 'Interactive Brokers'),
        ('MSFT', 'buy', 15, 295.20, 9.99, 'Interactive Brokers'),
        ('GOOGL', 'buy', 8, 2750.00, 9.99, 'Interactive Brokers'),
        
        # European stocks
        ('ASML.AS', 'buy', 5, 580.30, 7.50, 'DeGiro'),
        ('SAP.DE', 'buy', 12, 125.40, 5.00, 'DeGiro'),
        
        # ETF investments (regular monthly investments)
        ('VWCE.DE', 'buy', 50, 82.15, 2.50, 'DeGiro'),
        ('VWCE.DE', 'buy', 55, 84.20, 2.50, 'DeGiro'),
        ('VWCE.DE', 'buy', 48, 86.75, 2.50, 'DeGiro'),
        ('SPY', 'buy', 20, 415.60, 9.99, 'Interactive Brokers'),
        
        # Crypto investments
        ('BTC', 'buy', 0.25, 42000.00, 35.00, 'Binance'),
        ('BTC', 'buy', 0.15, 47500.00, 28.50, 'Binance'),
        ('ETH', 'buy', 2.5, 2850.00, 22.00, 'Binance'),
        ('ADA', 'buy', 2500, 0.95, 18.75, 'Binance'),
        ('SOL', 'buy', 35, 145.20, 15.50, 'Binance'),
        
        # Some profit-taking
        ('AAPL', 'sell', 5, 175.80, 9.99, 'Interactive Brokers'),
        ('BTC', 'sell', 0.05, 52000.00, 15.60, 'Binance'),
        
        # Dividend payments
        ('AAPL', 'dividend', 20, 0.24, 0.00, 'Interactive Brokers'),
        ('MSFT', 'dividend', 15, 0.68, 0.00, 'Interactive Brokers'),
        ('VWCE.DE', 'dividend', 153, 0.47, 0.00, 'DeGiro'),
        ('SAP.DE', 'dividend', 12, 1.85, 0.00, 'DeGiro'),
    ]
    
    print(f"\n💰 Adding {len(demo_transactions)} Demo Transactions...")
    print("-" * 50)
    
    transaction_count = 0
    for asset, tx_type, amount, price, fees, platform in demo_transactions:
        print(f"{tx_type:8} {amount:8.2f} {asset:12} @ €{price:8.2f}...", end=" ")
        try:
            success = tracker.add_transaction(asset, tx_type, amount, price, fees, platform)
            if success:
                print("✅")
                transaction_count += 1
            else:
                print("❌")
        except Exception as e:
            print(f"❌ ({str(e)[:20]}...)")
    
    print(f"\n✅ Successfully added {transaction_count}/{len(demo_transactions)} transactions")
    
    return tracker, demo_db

def display_comprehensive_analytics(tracker):
    """Display detailed portfolio analytics"""
    
    print("\n📈 Comprehensive Portfolio Analytics")
    print("=" * 65)
    
    # Update prices first
    print("\n🔄 Updating current market prices...")
    try:
        results = tracker.update_prices()
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        print(f"✅ Updated {success_count}/{total_count} asset prices")
    except Exception as e:
        print(f"⚠️  Price update limited due to: {str(e)[:50]}...")
    
    # Portfolio Summary
    portfolio = tracker.get_portfolio_summary()
    if not portfolio:
        print("❌ No portfolio data available")
        return
    
    print(f"\n💼 Portfolio Holdings ({len(portfolio)} assets):")
    print("-" * 90)
    print(f"{'Asset':<12} {'Type':<8} {'Amount':<12} {'Price':<12} {'Value':<12} {'Invested':<12} {'P&L':<20}")
    print("-" * 90)
    
    total_value = 0
    total_invested = 0
    type_totals = {}
    
    for asset in portfolio:
        total_value += asset['current_value']
        total_invested += asset['total_invested']
        
        # Track by asset type
        asset_type = asset['asset_type']
        if asset_type not in type_totals:
            type_totals[asset_type] = {'value': 0, 'invested': 0, 'count': 0}
        type_totals[asset_type]['value'] += asset['current_value']
        type_totals[asset_type]['invested'] += asset['total_invested']
        type_totals[asset_type]['count'] += 1
        
        # Format P&L with color indicators
        pnl = asset['profit_loss']
        pnl_pct = asset['profit_loss_percent']
        pnl_indicator = "🟢" if pnl > 0 else "🔴" if pnl < 0 else "⚪"
        pnl_text = f"{pnl_indicator} €{pnl:+.2f} ({pnl_pct:+.1f}%)"
        
        print(f"{asset['symbol']:<12} {asset_type:<8} {asset['total_amount']:<12.4f} "
              f"€{asset['current_price']:<11.2f} €{asset['current_value']:<11.2f} "
              f"€{asset['total_invested']:<11.2f} {pnl_text:<20}")
    
    print("-" * 90)
    total_pnl = total_value - total_invested
    total_pnl_pct = (total_pnl / total_invested * 100) if total_invested > 0 else 0
    total_indicator = "🟢" if total_pnl > 0 else "🔴" if total_pnl < 0 else "⚪"
    
    print(f"{'TOTAL':<12} {'':<8} {'':<12} {'':<12} €{total_value:<11.2f} "
          f"€{total_invested:<11.2f} {total_indicator} €{total_pnl:+.2f} ({total_pnl_pct:+.1f}%)")
    
    # Asset Type Breakdown
    print(f"\n📊 Asset Allocation by Type:")
    print("-" * 55)
    print(f"{'Type':<12} {'Value':<12} {'Invested':<12} {'Count':<8} {'Weight':<10}")
    print("-" * 55)
    
    for asset_type, data in sorted(type_totals.items()):
        weight_pct = (data['value'] / total_value * 100) if total_value > 0 else 0
        type_pnl = data['value'] - data['invested']
        type_indicator = "🟢" if type_pnl > 0 else "🔴" if type_pnl < 0 else "⚪"
        
        print(f"{asset_type.capitalize():<12} €{data['value']:<11.2f} "
              f"€{data['invested']:<11.2f} {data['count']:<8} {weight_pct:>6.1f}% {type_indicator}")
    
    # Recent Transactions
    transactions = tracker.get_transactions()
    if transactions:
        print(f"\n📋 Recent Transactions (Last 10):")
        print("-" * 75)
        print(f"{'Date':<12} {'Asset':<10} {'Type':<8} {'Amount':<12} {'Price':<12} {'Platform':<15}")
        print("-" * 75)
        
        for tx in transactions[:10]:
            date_str = tx['transaction_date'][:10] if tx['transaction_date'] else "Unknown"
            print(f"{date_str:<12} {tx['asset_symbol']:<10} {tx['transaction_type']:<8} "
                  f"{tx['amount']:<12.4f} €{tx['price_per_unit']:<11.2f} "
                  f"{tx.get('platform', 'N/A'):<15}")
    
    # Summary Statistics
    print(f"\n💡 Portfolio Summary:")
    print(f"   📈 Total Value: €{total_value:,.2f}")
    print(f"   💰 Total Invested: €{total_invested:,.2f}")
    print(f"   🎯 Total P&L: €{total_pnl:+,.2f} ({total_pnl_pct:+.1f}%)")
    print(f"   📊 Asset Types: {len(type_totals)}")
    print(f"   🏢 Total Assets: {len(portfolio)}")
    print(f"   📝 Total Transactions: {len(transactions)}")

def main():
    """Main demonstration function"""
    
    if len(sys.argv) > 1 and sys.argv[1] == "--unittest":
        # Run unit tests
        unittest.main(argv=[''])
        return
    
    print("🎯 Creating comprehensive demonstration portfolio...")
    
    try:
        tracker, demo_db = create_demo_portfolio()
        display_comprehensive_analytics(tracker)
        
        print(f"\n🎉 Comprehensive demo completed successfully!")
        print(f"📁 Database saved as: {demo_db}")
        print(f"🚀 Ready for GUI testing:")
        print(f"   python example/gui/gui.py")
        print(f"   (Select '{demo_db}' when prompted)")
        print(f"\n✨ This portfolio demonstrates:")
        print(f"   • Multi-currency support (USD, EUR, GBP, CHF)")
        print(f"   • Real-time price updates")
        print(f"   • Diverse asset types (stocks, ETFs, crypto)")
        print(f"   • Realistic transaction history")
        print(f"   • Comprehensive analytics")
        
    except KeyboardInterrupt:
        print("\n\n👋 Demo cancelled by user")
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
