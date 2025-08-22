import datetime
import sqlite3
import yfinance as yf
import requests
import pandas as pd
import time
from typing import Optional, List, Dict, Tuple

#This script holds all my backend functions for the investment book

class InvestmentTracker:
    def __init__(self, db_path: str = "my_assets.db"):
        self.db_path = db_path
        self._crypto_symbols_cache = None
        self._cache_timestamp = None
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
            self.update_single_asset_price(symbol.upper(), asset_type)
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
            
            # Validate that the asset exists
            cursor.execute("SELECT symbol FROM assets WHERE symbol = ?", (asset_symbol.upper(),))
            if not cursor.fetchone():
                print(f"Error: Asset {asset_symbol} does not exist. Please add the asset first.")
                conn.close()
                return False
            
            # Validate input data
            if amount <= 0:
                print(f"Error: Amount must be positive, got {amount}")
                conn.close()
                return False
                
            if price_per_unit <= 0:
                print(f"Error: Price per unit must be positive, got {price_per_unit}")
                conn.close()
                return False
            
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
        crypto_count = 0
        
        for symbol, asset_type in assets:
            # Add extra delay between crypto API calls to avoid rate limiting
            if asset_type == 'crypto':
                crypto_count += 1
                if crypto_count > 1:  # Add delay after the first crypto call
                    print(f"Waiting to avoid rate limits... ({crypto_count} crypto assets)")
                    time.sleep(2)  # 2 second delay between crypto calls
            
            results[symbol] = self.update_single_asset_price(symbol, asset_type)
        
        return results
    
    def get_available_crypto_symbols(self) -> Dict[str, str]:
        """Fetch available cryptocurrency symbols and their CoinGecko IDs from API"""
        # Cache for 1 hour to avoid too many API calls
        if (self._crypto_symbols_cache is not None and 
            self._cache_timestamp is not None and
            (datetime.datetime.now() - self._cache_timestamp).seconds < 3600):
            return self._crypto_symbols_cache
            
        try:
            print("Fetching available cryptocurrency symbols from CoinGecko API...")
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                coins = response.json()
                
                # Priority mapping for well-known cryptocurrencies to avoid conflicts
                priority_mapping = {
                    'BTC': 'bitcoin',
                    'ETH': 'ethereum', 
                    'BNB': 'binancecoin',
                    'ADA': 'cardano',
                    'SOL': 'solana',
                    'DOT': 'polkadot',
                    'MATIC': 'matic-network',
                    'AVAX': 'avalanche-2',
                    'LINK': 'chainlink',
                    'UNI': 'uniswap',
                    'LTC': 'litecoin',
                    'XRP': 'ripple',
                    'DOGE': 'dogecoin',
                    'ATOM': 'cosmos',
                    'VET': 'vechain',
                    'ALGO': 'algorand',
                    'ICP': 'internet-computer',
                    'FIL': 'filecoin',
                    'TRX': 'tron',
                    'ETC': 'ethereum-classic',
                    'XLM': 'stellar',
                    'SHIB': 'shiba-inu'
                }
                
                # Start with priority mapping
                crypto_map = priority_mapping.copy()
                
                # Add other coins, but don't override priority ones
                for coin in coins:
                    symbol = coin['symbol'].upper()
                    # Only include coins with reasonable symbols (not too long, alphanumeric)
                    if (len(symbol) <= 10 and symbol.isalnum() and 
                        symbol not in crypto_map):  # Don't override priority mapping
                        crypto_map[symbol] = coin['id']
                
                # Cache the results
                self._crypto_symbols_cache = crypto_map
                self._cache_timestamp = datetime.datetime.now()
                print(f"Successfully fetched {len(crypto_map)} cryptocurrency symbols")
                return crypto_map
        except Exception as e:
            print(f"Error fetching crypto symbols from API: {e}")
        
        # Fallback to basic list if API fails
        fallback_map = {
            'BTC': 'bitcoin', 'ETH': 'ethereum', 'ADA': 'cardano', 'DOT': 'polkadot',
            'LTC': 'litecoin', 'XRP': 'ripple', 'DOGE': 'dogecoin', 'BNB': 'binancecoin',
            'SOL': 'solana', 'MATIC': 'matic-network', 'AVAX': 'avalanche-2'
        }
        print("Using fallback cryptocurrency list")
        return fallback_map

    def update_single_asset_price(self, symbol: str, asset_type: str = None) -> bool:
        """Update price for a single asset based on its type"""
        try:
            price = None
            
            # Route to appropriate API based on asset type
            if asset_type == 'crypto':
                # Use CoinGecko API for cryptocurrencies
                crypto_map = self.get_available_crypto_symbols()
                if symbol in crypto_map:
                    try:
                        coin_id = crypto_map[symbol]
                        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=eur"
                        
                        # Add delay to avoid rate limiting
                        time.sleep(1.2)  # CoinGecko free tier allows ~30 calls per minute
                        
                        response = requests.get(url, timeout=15)
                        if response.status_code == 200:
                            data = response.json()
                            if coin_id in data and 'eur' in data[coin_id]:
                                price = data[coin_id]['eur']
                        elif response.status_code == 429:
                            print(f"Rate limit hit for {symbol}. Waiting and retrying...")
                            time.sleep(5)  # Wait 5 seconds and try once more
                            response = requests.get(url, timeout=15)
                            if response.status_code == 200:
                                data = response.json()
                                if coin_id in data and 'eur' in data[coin_id]:
                                    price = data[coin_id]['eur']
                            else:
                                print(f"Still rate limited for {symbol}")
                        else:
                            print(f"CoinGecko API error for {symbol}: {response.status_code}")
                    except Exception as e:
                        print(f"Error fetching crypto price for {symbol}: {e}")
            else:
                # Use yfinance for stocks, ETFs, bonds, commodities
                try:
                    ticker = yf.Ticker(symbol)
                    # Extract currency from ticker info
                    currency = ticker.info.get('currency')

                    # Get historical data to get the most recent price
                    hist = ticker.history(period="1d")
                    if not hist.empty:
                        # Use the most recent close price
                        price_original = hist['Close'].iloc[-1]
                        
                        # Only convert to EUR if currency is not already EUR
                        if price_original is not None and price_original > 0:
                            if currency and currency.upper() == 'EUR':
                                # Price is already in EUR, no conversion needed
                                price = price_original
                                print(f"Price for {symbol} already in EUR: €{price:.2f}")
                            else:
                                # Convert to EUR (assume USD if currency not specified)
                                try:
                                    if currency and currency.upper() == 'USD':
                                        conversion_pair = "EURUSD=X"
                                    elif currency and currency.upper() == 'GBP':
                                        conversion_pair = "EURGBP=X"
                                    elif currency and currency.upper() == 'CHF':
                                        conversion_pair = "EURCHF=X"
                                    elif currency and currency.upper() == 'JPY':
                                        conversion_pair = "EURJPY=X"
                                    else:
                                        # Default to USD conversion if currency unknown
                                        conversion_pair = "EURUSD=X"
                                        print(f"Unknown currency {currency} for {symbol}, assuming USD")
                                    
                                    # Get exchange rate
                                    eur_rate_ticker = yf.Ticker(conversion_pair)
                                    eur_rate_hist = eur_rate_ticker.history(period="1d")
                                    
                                    if not eur_rate_hist.empty:
                                        exchange_rate = eur_rate_hist['Close'].iloc[-1]
                                        if conversion_pair in ["EURGBP=X", "EURCHF=X"]:
                                            # For EUR base pairs, multiply
                                            price = price_original * exchange_rate
                                        elif conversion_pair == "EURJPY=X":
                                            # For JPY, divide by the rate
                                            price = price_original / exchange_rate
                                        else:
                                            # For USD (EURUSD=X), divide to convert USD to EUR
                                            price = price_original / exchange_rate
                                        print(f"Converted {symbol} from {currency} to EUR: {price_original:.2f} -> €{price:.2f}")
                                    else:
                                        # Fallback conversion rates if API fails
                                        if currency and currency.upper() == 'USD':
                                            price = price_original * 0.92  # Approximate USD to EUR
                                        elif currency and currency.upper() == 'GBP':
                                            price = price_original * 1.17  # Approximate GBP to EUR
                                        else:
                                            price = price_original * 0.92  # Default USD conversion
                                        print(f"Using fallback conversion for {symbol}: €{price:.2f}")
                                except Exception as conv_error:
                                    print(f"Currency conversion failed for {symbol}: {conv_error}")
                                    price = price_original  # Use original price if conversion fails
                    
                    # Fallback to ticker info if history doesn't work
                    if price is None:
                        info = ticker.info
                        if 'currentPrice' in info and info['currentPrice'] is not None:
                            price_raw = info['currentPrice']
                        elif 'regularMarketPrice' in info and info['regularMarketPrice'] is not None:
                            price_raw = info['regularMarketPrice']
                        elif 'bid' in info and info['bid'] is not None and info['bid'] > 0:
                            price_raw = info['bid']
                        else:
                            price_raw = None
                        
                        # Convert to EUR if we got a price and it's not already EUR
                        if price_raw is not None:
                            if currency and currency.upper() == 'EUR':
                                price = price_raw  # Already in EUR
                            else:
                                # Apply same conversion logic as above
                                try:
                                    if currency and currency.upper() == 'USD':
                                        conversion_pair = "EURUSD=X"
                                    else:
                                        conversion_pair = "EURUSD=X"  # Default to USD
                                    
                                    eur_rate_ticker = yf.Ticker(conversion_pair)
                                    eur_rate_hist = eur_rate_ticker.history(period="1d")
                                    if not eur_rate_hist.empty:
                                        exchange_rate = eur_rate_hist['Close'].iloc[-1]
                                        price = price_raw / exchange_rate
                                    else:
                                        price = price_raw * 0.92  # Fallback conversion
                                except:
                                    price = price_raw
                                
                except Exception as e:
                    print(f"Error fetching stock/ETF price for {symbol}: {e}")
            
            # Save price to database if we got one
            if price is not None and price > 0:
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
