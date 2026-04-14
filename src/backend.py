import datetime
import sqlite3
import yfinance as yf
import requests
import pandas as pd
import time
import logging
import re
from typing import Optional, List, Dict, Tuple

# This script holds all backend functions for the investment book

# Configure logging to avoid I/O errors when stdout is unavailable
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Safe print function that won't crash on I/O errors
def safe_print(msg):
    try:
        print(msg)
    except (IOError, OSError):
        logger.info(msg)


# ============== Constants ==============

VALID_ASSET_TYPES = ('stock', 'etf', 'crypto', 'bond', 'commodity')
VALID_TRANSACTION_TYPES = ('buy', 'sell', 'dividend', 'fee')
MAX_SYMBOL_LENGTH = 20
MAX_NAME_LENGTH = 100
MAX_PLATFORM_LENGTH = 100
MAX_NOTES_LENGTH = 500
SYMBOL_PATTERN = re.compile(r'^[A-Za-z0-9._\-]{1,20}$')
PRICE_HISTORY_RETENTION_DAYS = 365
CRYPTO_CACHE_TTL_SECONDS = 3600

# Fallback exchange rates (approximate, used only when API fails)
FALLBACK_RATES = {
    'USD': 0.92,
    'GBP': 1.17,
    'CHF': 1.05,
    'JPY': 0.0061,
}

PRIORITY_CRYPTO_MAPPING = {
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
    'SHIB': 'shiba-inu',
}


class InvestmentTracker:
    def __init__(self, db_path: str = "my_assets.db"):
        self.db_path = db_path
        self._crypto_symbols_cache: Optional[Dict[str, str]] = None
        self._cache_timestamp: Optional[datetime.datetime] = None
        self.initialize_database()

    # ============== Database Setup ==============

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection with foreign keys enabled."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    def initialize_database(self):
        """Initialize a SQL-based database to track investments."""
        conn = self._get_connection()
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
                FOREIGN KEY (asset_symbol) REFERENCES assets (symbol) ON DELETE CASCADE
            )
        ''')

        # Create price_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_symbol TEXT NOT NULL,
                price REAL NOT NULL,
                date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (asset_symbol) REFERENCES assets (symbol) ON DELETE CASCADE
            )
        ''')

        # Create watchlist table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_symbol TEXT UNIQUE NOT NULL,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (asset_symbol) REFERENCES assets (symbol) ON DELETE CASCADE
            )
        ''')

        # Create indexes for commonly queried columns
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_transactions_asset ON transactions(asset_symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_asset ON price_history(asset_symbol)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_price_history_date ON price_history(date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_asset ON watchlist(asset_symbol)')

        conn.commit()
        conn.close()

    # ============== Input Validation ==============

    def _validate_symbol(self, symbol: str) -> str:
        """Validate and normalize an asset symbol. Returns uppercased symbol."""
        if not symbol or not isinstance(symbol, str):
            raise ValueError("Symbol is required")
        symbol = symbol.strip().upper()
        if len(symbol) > MAX_SYMBOL_LENGTH:
            raise ValueError(f"Symbol must be at most {MAX_SYMBOL_LENGTH} characters")
        if not SYMBOL_PATTERN.match(symbol):
            raise ValueError("Symbol may only contain letters, digits, dots, hyphens, and underscores")
        return symbol

    def _validate_name(self, name: str) -> str:
        """Validate an asset name."""
        if not name or not isinstance(name, str):
            raise ValueError("Name is required")
        name = name.strip()
        if len(name) > MAX_NAME_LENGTH:
            raise ValueError(f"Name must be at most {MAX_NAME_LENGTH} characters")
        return name

    def _validate_asset_type(self, asset_type: str) -> str:
        """Validate asset type."""
        if not asset_type or asset_type not in VALID_ASSET_TYPES:
            raise ValueError(f"Asset type must be one of: {', '.join(VALID_ASSET_TYPES)}")
        return asset_type

    def _validate_transaction_type(self, tx_type: str) -> str:
        """Validate transaction type."""
        if not tx_type or tx_type not in VALID_TRANSACTION_TYPES:
            raise ValueError(f"Transaction type must be one of: {', '.join(VALID_TRANSACTION_TYPES)}")
        return tx_type

    def _validate_platform(self, platform: Optional[str]) -> Optional[str]:
        """Validate platform name."""
        if platform is None:
            return None
        platform = str(platform).strip()
        if len(platform) > MAX_PLATFORM_LENGTH:
            raise ValueError(f"Platform must be at most {MAX_PLATFORM_LENGTH} characters")
        return platform if platform else None

    def _validate_notes(self, notes: Optional[str]) -> Optional[str]:
        """Validate notes field."""
        if notes is None:
            return None
        notes = str(notes).strip()
        if len(notes) > MAX_NOTES_LENGTH:
            raise ValueError(f"Notes must be at most {MAX_NOTES_LENGTH} characters")
        return notes if notes else None

    # ============== Currency Conversion ==============

    def _get_exchange_rate(self, currency: str) -> Optional[float]:
        """Get the exchange rate from a given currency to EUR.
        Returns the multiplier to convert from currency to EUR, or None on failure.
        """
        if not currency or currency.upper() == 'EUR':
            return 1.0

        currency = currency.upper()
        conversion_pairs = {
            'USD': 'EURUSD=X',
            'GBP': 'EURGBP=X',
            'CHF': 'EURCHF=X',
            'JPY': 'EURJPY=X',
        }

        pair = conversion_pairs.get(currency, 'EURUSD=X')
        if currency not in conversion_pairs:
            safe_print(f"Unknown currency {currency}, assuming USD")

        try:
            eur_rate_ticker = yf.Ticker(pair)
            eur_rate_hist = eur_rate_ticker.history(period="1d")
            if not eur_rate_hist.empty:
                exchange_rate = eur_rate_hist['Close'].iloc[-1]
                if exchange_rate and exchange_rate > 0:
                    # For all EUR-based pairs, divide the original price by the rate
                    return 1.0 / exchange_rate
        except Exception as e:
            safe_print(f"Exchange rate fetch failed for {currency}: {e}")

        # Fallback to approximate rates
        fallback = FALLBACK_RATES.get(currency, FALLBACK_RATES['USD'])
        safe_print(f"Using fallback conversion rate for {currency}: {fallback}")
        return fallback

    def _convert_to_eur(self, price: float, currency: Optional[str]) -> float:
        """Convert a price from the given currency to EUR."""
        if price is None or price <= 0:
            return 0.0
        if not currency or currency.upper() == 'EUR':
            return price
        rate = self._get_exchange_rate(currency)
        if rate is None:
            return price
        converted = price * rate
        safe_print(f"Converted from {currency} to EUR: {price:.2f} -> EUR {converted:.2f}")
        return converted

    # ============== API Helpers ==============

    def _fetch_with_backoff(self, url: str, max_retries: int = 3, initial_delay: float = 2.0,
                            timeout: int = 10) -> Optional[requests.Response]:
        """Fetch a URL with exponential backoff on 429 (rate limit) responses."""
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=timeout)
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    safe_print(f"Rate limited (attempt {attempt + 1}/{max_retries}), waiting {delay:.1f}s...")
                    time.sleep(delay)
                    delay *= 2  # exponential backoff
                else:
                    safe_print(f"API error: HTTP {response.status_code} for {url}")
                    return None
            except requests.exceptions.Timeout:
                safe_print(f"Timeout fetching {url} (attempt {attempt + 1}/{max_retries})")
                time.sleep(delay)
                delay *= 2
            except requests.exceptions.RequestException as e:
                safe_print(f"Request failed for {url}: {e}")
                return None
        safe_print(f"All {max_retries} attempts failed for {url}")
        return None

    # ============== Asset Operations ==============

    def add_asset(self, symbol: str, name: str, asset_type: str, platform: str = None) -> bool:
        """Add a new asset to the database."""
        try:
            symbol = self._validate_symbol(symbol)
            name = self._validate_name(name)
            asset_type = self._validate_asset_type(asset_type)
            platform = self._validate_platform(platform)
        except ValueError as e:
            safe_print(f"Validation error adding asset: {e}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO assets (symbol, name, asset_type, platform)
                VALUES (?, ?, ?, ?)
            ''', (symbol, name, asset_type, platform))
            conn.commit()
            conn.close()

            # Update price immediately after adding
            self.update_single_asset_price(symbol, asset_type)
            return True
        except Exception as e:
            safe_print(f"Error adding asset: {e}")
            return False

    def get_all_assets(self) -> List[Dict]:
        """Get all assets in the database."""
        conn = self._get_connection()
        query = "SELECT * FROM assets ORDER BY symbol"
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df.to_dict('records') if not df.empty else []

    def delete_asset(self, symbol: str) -> bool:
        """Delete an asset and all its related data atomically."""
        try:
            symbol = self._validate_symbol(symbol)
        except ValueError as e:
            safe_print(f"Validation error: {e}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            # Use a transaction for atomicity
            cursor.execute("BEGIN")
            try:
                cursor.execute("DELETE FROM transactions WHERE asset_symbol = ?", (symbol,))
                cursor.execute("DELETE FROM price_history WHERE asset_symbol = ?", (symbol,))
                cursor.execute("DELETE FROM watchlist WHERE asset_symbol = ?", (symbol,))
                cursor.execute("DELETE FROM assets WHERE symbol = ?", (symbol,))
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            conn.close()
            return True
        except Exception as e:
            safe_print(f"Error deleting asset {symbol}: {e}")
            return False

    # ============== Transaction Operations ==============

    def _get_current_holdings(self, cursor, symbol: str) -> float:
        """Get current net holdings for an asset (buys - sells)."""
        cursor.execute('''
            SELECT COALESCE(SUM(
                CASE WHEN transaction_type = 'buy' THEN amount
                     WHEN transaction_type = 'sell' THEN -amount
                     ELSE 0 END
            ), 0) FROM transactions WHERE asset_symbol = ?
        ''', (symbol,))
        return cursor.fetchone()[0]

    def add_transaction(self, asset_symbol: str, transaction_type: str, amount: float,
                        price_per_unit: float, fees: float = 0.0, platform: str = None,
                        transaction_date: str = None, notes: str = None) -> bool:
        """Add a transaction to the database with full validation."""
        try:
            asset_symbol = self._validate_symbol(asset_symbol)
            transaction_type = self._validate_transaction_type(transaction_type)
            platform = self._validate_platform(platform)
            notes = self._validate_notes(notes)
        except ValueError as e:
            safe_print(f"Validation error: {e}")
            return False

        if not isinstance(amount, (int, float)) or amount <= 0:
            safe_print(f"Error: Amount must be positive, got {amount}")
            return False

        if not isinstance(price_per_unit, (int, float)) or price_per_unit <= 0:
            safe_print(f"Error: Price per unit must be positive, got {price_per_unit}")
            return False

        if fees is None:
            fees = 0.0
        if not isinstance(fees, (int, float)) or fees < 0:
            safe_print(f"Error: Fees must be non-negative, got {fees}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            # Validate that the asset exists
            cursor.execute("SELECT symbol FROM assets WHERE symbol = ?", (asset_symbol,))
            if not cursor.fetchone():
                safe_print(f"Error: Asset {asset_symbol} does not exist. Please add the asset first.")
                conn.close()
                return False

            # Validate sell does not exceed holdings
            if transaction_type == 'sell':
                current_holdings = self._get_current_holdings(cursor, asset_symbol)
                if amount > current_holdings + 1e-9:  # small epsilon for float comparison
                    safe_print(f"Error: Cannot sell {amount} of {asset_symbol}, only {current_holdings:.8f} held")
                    conn.close()
                    return False

            total_value = amount * price_per_unit
            if transaction_date is None:
                transaction_date = datetime.datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO transactions
                (asset_symbol, transaction_type, amount, price_per_unit, total_value, fees, platform, transaction_date, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (asset_symbol, transaction_type, amount, price_per_unit, total_value, fees, platform, transaction_date, notes))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            safe_print(f"Error adding transaction: {e}")
            return False

    def get_transactions(self, asset_symbol: str = None) -> List[Dict]:
        """Get all transactions or transactions for a specific asset."""
        conn = self._get_connection()

        if asset_symbol:
            try:
                asset_symbol = self._validate_symbol(asset_symbol)
            except ValueError:
                conn.close()
                return []
            query = '''
                SELECT * FROM transactions
                WHERE asset_symbol = ?
                ORDER BY transaction_date DESC
            '''
            df = pd.read_sql_query(query, conn, params=(asset_symbol,))
        else:
            query = '''
                SELECT * FROM transactions
                ORDER BY transaction_date DESC
            '''
            df = pd.read_sql_query(query, conn)

        conn.close()
        return df.to_dict('records') if not df.empty else []

    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete a specific transaction by ID."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            safe_print(f"Error deleting transaction {transaction_id}: {e}")
            return False

    # ============== Price Updates ==============

    def update_asset_prices(self) -> Dict[str, bool]:
        """Update all asset prices using yfinance and CoinGecko APIs."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT symbol, asset_type FROM assets")
        assets = cursor.fetchall()
        conn.close()

        results = {}
        crypto_count = 0

        for symbol, asset_type in assets:
            if asset_type == 'crypto':
                crypto_count += 1
                if crypto_count > 1:
                    safe_print(f"Waiting to avoid rate limits... ({crypto_count} crypto assets)")
                    time.sleep(2)

            results[symbol] = self.update_single_asset_price(symbol, asset_type)

        # Clean up old price history
        self._cleanup_price_history()

        return results

    def update_single_asset_price(self, symbol: str, asset_type: str = None) -> bool:
        """Update price for a single asset based on its type."""
        try:
            price = None

            if asset_type == 'crypto':
                price = self._fetch_crypto_price(symbol)
            else:
                price = self._fetch_stock_price(symbol)

            if price is not None and price > 0:
                self._save_price(symbol, price)
                return True

        except Exception as e:
            safe_print(f"Error updating price for {symbol}: {e}")

        return False

    def _fetch_crypto_price(self, symbol: str) -> Optional[float]:
        """Fetch cryptocurrency price from CoinGecko API in EUR."""
        crypto_map = self.get_available_crypto_symbols()
        if symbol not in crypto_map:
            safe_print(f"No CoinGecko mapping for {symbol}")
            return None

        coin_id = crypto_map[symbol]
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=eur"

        # Rate-limit CoinGecko free tier
        time.sleep(1.2)

        response = self._fetch_with_backoff(url, max_retries=3, initial_delay=5.0)
        if response is not None:
            data = response.json()
            if coin_id in data and 'eur' in data[coin_id]:
                return data[coin_id]['eur']
            else:
                safe_print(f"Unexpected CoinGecko response for {symbol}")
        return None

    def _fetch_stock_price(self, symbol: str) -> Optional[float]:
        """Fetch stock/ETF/bond/commodity price via yfinance, converted to EUR."""
        try:
            ticker = yf.Ticker(symbol)
            currency = ticker.info.get('currency')

            # Try historical data first
            hist = ticker.history(period="1d")
            if not hist.empty:
                price_original = hist['Close'].iloc[-1]
                if price_original is not None and price_original > 0:
                    return self._convert_to_eur(price_original, currency)

            # Fallback to ticker info
            info = ticker.info
            price_raw = None
            for key in ('currentPrice', 'regularMarketPrice', 'bid'):
                val = info.get(key)
                if val is not None and val > 0:
                    price_raw = val
                    break

            if price_raw is not None:
                return self._convert_to_eur(price_raw, currency)

        except Exception as e:
            safe_print(f"Error fetching stock/ETF price for {symbol}: {e}")
        return None

    def _save_price(self, symbol: str, price: float):
        """Save updated price to the database."""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE assets SET current_price = ?, last_updated = CURRENT_TIMESTAMP
            WHERE symbol = ?
        ''', (price, symbol))
        cursor.execute('''
            INSERT INTO price_history (asset_symbol, price) VALUES (?, ?)
        ''', (symbol, price))
        conn.commit()
        conn.close()

    def _cleanup_price_history(self):
        """Remove price history older than the retention period."""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cutoff = (datetime.datetime.now() - datetime.timedelta(days=PRICE_HISTORY_RETENTION_DAYS)).isoformat()
            cursor.execute("DELETE FROM price_history WHERE date < ?", (cutoff,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            if deleted > 0:
                safe_print(f"Cleaned up {deleted} old price history records")
        except Exception as e:
            safe_print(f"Error cleaning up price history: {e}")

    def update_asset_values_manually(self, symbol: str, price: float) -> bool:
        """Manually update the value of an asset."""
        try:
            symbol = self._validate_symbol(symbol)
        except ValueError as e:
            safe_print(f"Validation error: {e}")
            return False

        if not isinstance(price, (int, float)) or price <= 0:
            safe_print(f"Error: Price must be positive, got {price}")
            return False

        try:
            self._save_price(symbol, price)
            return True
        except Exception as e:
            safe_print(f"Error manually updating price for {symbol}: {e}")
            return False

    # ============== Crypto Symbols ==============

    def get_available_crypto_symbols(self) -> Dict[str, str]:
        """Fetch available cryptocurrency symbols and their CoinGecko IDs from API."""
        # Return cache if still valid
        if (self._crypto_symbols_cache is not None
                and self._cache_timestamp is not None
                and (datetime.datetime.now() - self._cache_timestamp).total_seconds() < CRYPTO_CACHE_TTL_SECONDS):
            return self._crypto_symbols_cache

        try:
            safe_print("Fetching available cryptocurrency symbols from CoinGecko API...")
            url = "https://api.coingecko.com/api/v3/coins/list"
            response = self._fetch_with_backoff(url, max_retries=2, initial_delay=3.0)
            if response is not None:
                coins = response.json()

                # Start with priority mapping
                crypto_map = PRIORITY_CRYPTO_MAPPING.copy()

                # Add other coins, but don't override priority ones
                for coin in coins:
                    sym = coin['symbol'].upper()
                    if (len(sym) <= 10 and sym.isalnum() and sym not in crypto_map):
                        crypto_map[sym] = coin['id']

                self._crypto_symbols_cache = crypto_map
                self._cache_timestamp = datetime.datetime.now()
                safe_print(f"Successfully fetched {len(crypto_map)} cryptocurrency symbols")
                return crypto_map
        except Exception as e:
            safe_print(f"Error fetching crypto symbols from API: {e}")

        # Fallback to priority list
        safe_print("Using fallback cryptocurrency list")
        return PRIORITY_CRYPTO_MAPPING.copy()

    # ============== Portfolio ==============

    def get_portfolio_summary(self) -> List[Dict]:
        """Get a summary of the current portfolio with P&L calculations."""
        conn = self._get_connection()

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
            # Guard against division by zero
            df['profit_loss_percent'] = df.apply(
                lambda row: round((row['profit_loss'] / row['total_invested']) * 100, 2)
                if row['total_invested'] != 0 else 0.0,
                axis=1
            )

        conn.close()
        return df.to_dict('records') if not df.empty else []

    # ============== Price History ==============

    def get_price_history(self, asset_symbol: str = None) -> List[Dict]:
        """Get price history for all assets or a specific asset."""
        conn = self._get_connection()

        if asset_symbol:
            try:
                asset_symbol = self._validate_symbol(asset_symbol)
            except ValueError:
                conn.close()
                return []
            query = '''
                SELECT * FROM price_history
                WHERE asset_symbol = ?
                ORDER BY date ASC
            '''
            df = pd.read_sql_query(query, conn, params=(asset_symbol,))
        else:
            query = '''
                SELECT ph.*, a.name as asset_name FROM price_history ph
                JOIN assets a ON ph.asset_symbol = a.symbol
                ORDER BY ph.date ASC
            '''
            df = pd.read_sql_query(query, conn)

        conn.close()
        return df.to_dict('records') if not df.empty else []

    # ============== Watchlist ==============

    def add_to_watchlist(self, symbol: str, notes: str = None) -> bool:
        """Add an asset to the watchlist."""
        try:
            symbol = self._validate_symbol(symbol)
            notes = self._validate_notes(notes)
        except ValueError as e:
            safe_print(f"Validation error: {e}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()

            cursor.execute("SELECT symbol FROM assets WHERE symbol = ?", (symbol,))
            if not cursor.fetchone():
                safe_print(f"Asset {symbol} does not exist. Please add the asset first.")
                conn.close()
                return False

            cursor.execute('''
                INSERT OR REPLACE INTO watchlist (asset_symbol, notes)
                VALUES (?, ?)
            ''', (symbol, notes))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            safe_print(f"Error adding {symbol} to watchlist: {e}")
            return False

    def remove_from_watchlist(self, symbol: str) -> bool:
        """Remove an asset from the watchlist."""
        try:
            symbol = self._validate_symbol(symbol)
        except ValueError as e:
            safe_print(f"Validation error: {e}")
            return False

        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM watchlist WHERE asset_symbol = ?", (symbol,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            safe_print(f"Error removing {symbol} from watchlist: {e}")
            return False

    def get_watchlist(self) -> List[Dict]:
        """Get all assets in the watchlist with current prices."""
        conn = self._get_connection()

        query = '''
            SELECT
                a.symbol, a.name, a.asset_type, a.platform, a.current_price, a.last_updated,
                w.added_date, w.notes as watchlist_notes
            FROM watchlist w
            JOIN assets a ON w.asset_symbol = a.symbol
            ORDER BY w.added_date DESC
        '''
        df = pd.read_sql_query(query, conn)

        conn.close()
        return df.to_dict('records') if not df.empty else []

    def is_in_watchlist(self, symbol: str) -> bool:
        """Check if an asset is in the watchlist."""
        try:
            symbol = self._validate_symbol(symbol)
        except ValueError:
            return False

        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM watchlist WHERE asset_symbol = ?", (symbol,))
        result = cursor.fetchone() is not None
        conn.close()
        return result

    # ============== Search ==============

    def search_available_assets(self, query: str, asset_type: str = None) -> List[Dict]:
        """Search for available assets from APIs based on query."""
        results = []
        query_upper = query.upper()
        query_lower = query.lower()

        # Search cryptocurrencies
        if asset_type is None or asset_type == 'crypto':
            crypto_map = self.get_available_crypto_symbols()
            for symbol, coin_id in crypto_map.items():
                if query_upper in symbol or query_lower in coin_id:
                    results.append({
                        'symbol': symbol,
                        'name': coin_id.replace('-', ' ').title(),
                        'asset_type': 'crypto',
                        'source': 'coingecko'
                    })

        # For stocks/ETFs, try yfinance
        if asset_type is None or asset_type in ('stock', 'etf'):
            try:
                ticker = yf.Ticker(query_upper)
                info = ticker.info
                if info and 'shortName' in info:
                    type_guess = 'etf' if 'ETF' in info.get('shortName', '').upper() else 'stock'
                    results.append({
                        'symbol': query_upper,
                        'name': info.get('shortName', query_upper),
                        'asset_type': type_guess,
                        'source': 'yfinance'
                    })
            except Exception:
                pass

        return results[:50]

    def get_popular_assets(self) -> List[Dict]:
        """Get a list of popular assets for quick selection."""
        return [
            # Popular Stocks
            {'symbol': 'AAPL', 'name': 'Apple Inc.', 'asset_type': 'stock'},
            {'symbol': 'MSFT', 'name': 'Microsoft Corporation', 'asset_type': 'stock'},
            {'symbol': 'GOOGL', 'name': 'Alphabet Inc.', 'asset_type': 'stock'},
            {'symbol': 'AMZN', 'name': 'Amazon.com Inc.', 'asset_type': 'stock'},
            {'symbol': 'TSLA', 'name': 'Tesla Inc.', 'asset_type': 'stock'},
            {'symbol': 'NVDA', 'name': 'NVIDIA Corporation', 'asset_type': 'stock'},
            {'symbol': 'META', 'name': 'Meta Platforms Inc.', 'asset_type': 'stock'},
            # Popular ETFs
            {'symbol': 'VWCE.DE', 'name': 'Vanguard FTSE All-World UCITS ETF', 'asset_type': 'etf'},
            {'symbol': 'SPY', 'name': 'SPDR S&P 500 ETF Trust', 'asset_type': 'etf'},
            {'symbol': 'QQQ', 'name': 'Invesco QQQ Trust', 'asset_type': 'etf'},
            {'symbol': 'VTI', 'name': 'Vanguard Total Stock Market ETF', 'asset_type': 'etf'},
            {'symbol': 'IWDA.AS', 'name': 'iShares Core MSCI World UCITS ETF', 'asset_type': 'etf'},
            # Popular Cryptos
            {'symbol': 'BTC', 'name': 'Bitcoin', 'asset_type': 'crypto'},
            {'symbol': 'ETH', 'name': 'Ethereum', 'asset_type': 'crypto'},
            {'symbol': 'SOL', 'name': 'Solana', 'asset_type': 'crypto'},
            {'symbol': 'ADA', 'name': 'Cardano', 'asset_type': 'crypto'},
            {'symbol': 'DOT', 'name': 'Polkadot', 'asset_type': 'crypto'},
            {'symbol': 'AVAX', 'name': 'Avalanche', 'asset_type': 'crypto'},
            {'symbol': 'MATIC', 'name': 'Polygon', 'asset_type': 'crypto'},
            {'symbol': 'LINK', 'name': 'Chainlink', 'asset_type': 'crypto'},
        ]
