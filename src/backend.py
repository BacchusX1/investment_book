import datetime
import sqlite3
import yfinance as yf
import requests
import pandas as pd
from typing import Optional, List, Dict, Tuple

#This script holds all my backend functions for the investment book

class InvestmentTracker:
    def __init__(self, db_path: str = "my_assets.db"):
        self.db_path = db_path
        self.initialize_database()
    
    def initialize_database(self):
        """Initialize a SQL-based database to track investments"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create assets table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                asset_type TEXT NOT NULL,
                platform TEXT,
                current_price REAL DEFAULT 0.0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create transactions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_symbol TEXT NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                price_per_unit REAL NOT NULL,
                total_value REAL NOT NULL,
                fees REAL DEFAULT 0.0,
                platform TEXT,
                transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (asset_symbol) REFERENCES assets (symbol)
            )
        ''')
        
        # Create price_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_symbol TEXT NOT NULL,
                price REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_symbol) REFERENCES assets (symbol)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_asset(self, symbol: str, name: str, asset_type: str, platform: str = None) -> bool:
        """Add a new asset to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO assets (symbol, name, asset_type, platform)
                VALUES (?, ?, ?, ?)
            ''', (symbol.upper(), name, asset_type, platform))
            
            conn.commit()
            conn.close()
            
            # Update price immediately after adding
            self.update_single_asset_price(symbol.upper())
            return True
        except Exception as e:
            print(f"Error adding asset: {e}")
            return False
    
    def add_transaction(self, asset_symbol: str, transaction_type: str, amount: float, 
                       price_per_unit: float, fees: float = 0.0, platform: str = None, 
                       transaction_date: str = None, notes: str = None) -> bool:
        """Add a transaction to the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            total_value = amount * price_per_unit
            if transaction_date is None:
                transaction_date = datetime.datetime.now().isoformat()
            
            cursor.execute('''
                INSERT INTO transactions 
                (asset_symbol, transaction_type, amount, price_per_unit, total_value, fees, platform, transaction_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (asset_symbol.upper(), transaction_type, amount, price_per_unit, total_value, fees, platform, transaction_date, notes))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding transaction: {e}")
            return False
    
    def update_asset_prices(self) -> Dict[str, bool]:
        """Update all asset prices automatically using yfinance and crypto APIs"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT symbol, asset_type FROM assets")
        assets = cursor.fetchall()
        conn.close()
        
        results = {}
        for symbol, asset_type in assets:
            results[symbol] = self.update_single_asset_price(symbol)
        
        return results
    
    def update_single_asset_price(self, symbol: str) -> bool:
        """Update price for a single asset"""
        try:
            price = None
            
            # Try to get price using yfinance first (works for stocks, ETFs, some crypto)
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                if 'currentPrice' in info:
                    price = info['currentPrice']
                elif 'regularMarketPrice' in info:
                    price = info['regularMarketPrice']
                elif 'bid' in info and info['bid'] > 0:
                    price = info['bid']
            except:
                pass
            
            # If yfinance failed, try crypto API for common crypto symbols
            if price is None and symbol in ['BTC', 'ETH', 'ADA', 'DOT', 'LTC', 'XRP', 'DOGE']:
                try:
                    # Using CoinGecko API (free)
                    crypto_map = {
                        'BTC': 'bitcoin',
                        'ETH': 'ethereum',
                        'ADA': 'cardano',
                        'DOT': 'polkadot',
                        'LTC': 'litecoin',
                        'XRP': 'ripple',
                        'DOGE': 'dogecoin'
                    }
                    
                    if symbol in crypto_map:
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={crypto_map[symbol]}&vs_currencies=eur"
                        response = requests.get(url)
                        if response.status_code == 200:
                            data = response.json()
                            price = data[crypto_map[symbol]]['eur']
                except:
                    pass
            
            if price is not None:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()
                
                # Update current price
                cursor.execute('''
                    UPDATE assets SET current_price = ?, last_updated = CURRENT_TIMESTAMP 
                    WHERE symbol = ?
                ''', (price, symbol))
                
                # Add to price history
                cursor.execute('''
                    INSERT INTO price_history (asset_symbol, price) VALUES (?, ?)
                ''', (symbol, price))
                
                conn.commit()
                conn.close()
                return True
            
        except Exception as e:
            print(f"Error updating price for {symbol}: {e}")
        
        return False
    
    def update_asset_values_manually(self, symbol: str, price: float) -> bool:
        """Manually update the value of an asset"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE assets SET current_price = ?, last_updated = CURRENT_TIMESTAMP 
                WHERE symbol = ?
            ''', (price, symbol.upper()))
            
            # Add to price history
            cursor.execute('''
                INSERT INTO price_history (asset_symbol, price) VALUES (?, ?)
            ''', (symbol.upper(), price))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error manually updating price for {symbol}: {e}")
            return False
    
    def get_portfolio_summary(self) -> Dict:
        """Get a summary of the current portfolio"""
        conn = sqlite3.connect(self.db_path)
        
        # Get portfolio holdings
        query = '''
            SELECT 
                a.symbol, a.name, a.asset_type, a.platform, a.current_price,
                COALESCE(SUM(CASE WHEN t.transaction_type = 'buy' THEN t.amount 
                                 WHEN t.transaction_type = 'sell' THEN -t.amount 
                                 ELSE 0 END), 0) as total_amount,
                COALESCE(SUM(CASE WHEN t.transaction_type = 'buy' THEN t.total_value + t.fees
                                 WHEN t.transaction_type = 'sell' THEN -(t.total_value - t.fees)
                                 ELSE 0 END), 0) as total_invested
            FROM assets a
            LEFT JOIN transactions t ON a.symbol = t.asset_symbol
            GROUP BY a.symbol, a.name, a.asset_type, a.platform, a.current_price
            HAVING total_amount > 0
        '''
        
        df = pd.read_sql_query(query, conn)
        
        if not df.empty:
            df['current_value'] = df['total_amount'] * df['current_price']
            df['profit_loss'] = df['current_value'] - df['total_invested']
            df['profit_loss_percent'] = (df['profit_loss'] / df['total_invested'] * 100).round(2)
        
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def get_transactions(self, asset_symbol: str = None) -> List[Dict]:
        """Get all transactions or transactions for a specific asset"""
        conn = sqlite3.connect(self.db_path)
        
        if asset_symbol:
            query = '''
                SELECT * FROM transactions 
                WHERE asset_symbol = ? 
                ORDER BY transaction_date DESC
            '''
            df = pd.read_sql_query(query, conn, params=(asset_symbol.upper(),))
        else:
            query = '''
                SELECT * FROM transactions 
                ORDER BY transaction_date DESC
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def get_price_history(self, asset_symbol: str = None) -> List[Dict]:
        """Get price history for all assets or a specific asset"""
        conn = sqlite3.connect(self.db_path)
        
        if asset_symbol:
            query = '''
                SELECT * FROM price_history 
                WHERE asset_symbol = ? 
                ORDER BY date ASC
            '''
            df = pd.read_sql_query(query, conn, params=(asset_symbol.upper(),))
        else:
            query = '''
                SELECT ph.*, a.name as asset_name FROM price_history ph
                JOIN assets a ON ph.asset_symbol = a.symbol
                ORDER BY ph.date ASC
            '''
            df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def get_all_assets(self) -> List[Dict]:
        """Get all assets in the database"""
        conn = sqlite3.connect(self.db_path)
        
        query = "SELECT * FROM assets ORDER BY symbol"
        df = pd.read_sql_query(query, conn)
        
        conn.close()
        return df.to_dict('records') if not df.empty else []
    
    def delete_asset(self, symbol: str) -> bool:
        """Delete an asset and all its transactions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete transactions first (foreign key constraint)
            cursor.execute("DELETE FROM transactions WHERE asset_symbol = ?", (symbol.upper(),))
            cursor.execute("DELETE FROM price_history WHERE asset_symbol = ?", (symbol.upper(),))
            cursor.execute("DELETE FROM assets WHERE symbol = ?", (symbol.upper(),))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error deleting asset {symbol}: {e}")
            return False
