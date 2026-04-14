#!/usr/bin/env python3
"""
Unit tests for the Investment Portfolio Tracker backend.
All external API calls (yfinance, CoinGecko) are mocked.
"""

import unittest
import tempfile
import os
import sqlite3
import datetime
from unittest.mock import patch, MagicMock
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend import (
    InvestmentTracker,
    VALID_ASSET_TYPES,
    VALID_TRANSACTION_TYPES,
    PRIORITY_CRYPTO_MAPPING,
)


def _make_tracker():
    """Create a tracker with a temp database and mocked price update."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    tmp.close()
    with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
        tracker = InvestmentTracker(tmp.name)
    return tracker, tmp.name


class TestDatabaseInitialization(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_tables_created(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cur.fetchall()}
        conn.close()
        for t in ('assets', 'transactions', 'price_history', 'watchlist'):
            self.assertIn(t, tables)

    def test_indexes_created(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='index'")
        indexes = {row[0] for row in cur.fetchall()}
        conn.close()
        for idx in ('idx_transactions_asset', 'idx_price_history_asset',
                     'idx_price_history_date', 'idx_watchlist_asset'):
            self.assertIn(idx, indexes)

    def test_foreign_keys_enabled(self):
        conn = self.tracker._get_connection()
        cur = conn.cursor()
        cur.execute("PRAGMA foreign_keys")
        self.assertEqual(cur.fetchone()[0], 1)
        conn.close()


class TestInputValidation(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_validate_symbol_valid(self):
        self.assertEqual(self.tracker._validate_symbol('aapl'), 'AAPL')
        self.assertEqual(self.tracker._validate_symbol('VWCE.DE'), 'VWCE.DE')
        self.assertEqual(self.tracker._validate_symbol('BTC-USD'), 'BTC-USD')

    def test_validate_symbol_empty(self):
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol('')
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol(None)

    def test_validate_symbol_too_long(self):
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol('A' * 21)

    def test_validate_symbol_bad_chars(self):
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol('AA PL')
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol('AA/PL')
        with self.assertRaises(ValueError):
            self.tracker._validate_symbol('../etc')

    def test_validate_name(self):
        self.assertEqual(self.tracker._validate_name('Apple Inc.'), 'Apple Inc.')
        with self.assertRaises(ValueError):
            self.tracker._validate_name('')
        with self.assertRaises(ValueError):
            self.tracker._validate_name('A' * 101)

    def test_validate_asset_type(self):
        for t in VALID_ASSET_TYPES:
            self.assertEqual(self.tracker._validate_asset_type(t), t)
        with self.assertRaises(ValueError):
            self.tracker._validate_asset_type('invalid')

    def test_validate_transaction_type(self):
        for t in VALID_TRANSACTION_TYPES:
            self.assertEqual(self.tracker._validate_transaction_type(t), t)
        with self.assertRaises(ValueError):
            self.tracker._validate_transaction_type('invalid')

    def test_validate_platform_optional(self):
        self.assertIsNone(self.tracker._validate_platform(None))
        self.assertIsNone(self.tracker._validate_platform(''))
        self.assertEqual(self.tracker._validate_platform('Binance'), 'Binance')

    def test_validate_notes_optional(self):
        self.assertIsNone(self.tracker._validate_notes(None))
        self.assertIsNone(self.tracker._validate_notes(''))
        self.assertEqual(self.tracker._validate_notes('Some note'), 'Some note')
        with self.assertRaises(ValueError):
            self.tracker._validate_notes('N' * 501)


class TestAssetOperations(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_add_asset(self, mock_price):
        self.assertTrue(self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock', 'IB'))
        assets = self.tracker.get_all_assets()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets[0]['symbol'], 'AAPL')
        self.assertEqual(assets[0]['asset_type'], 'stock')

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_add_asset_normalizes_symbol(self, mock_price):
        self.assertTrue(self.tracker.add_asset('aapl', 'Apple Inc.', 'stock'))
        assets = self.tracker.get_all_assets()
        self.assertEqual(assets[0]['symbol'], 'AAPL')

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_add_asset_invalid_type(self, mock_price):
        self.assertFalse(self.tracker.add_asset('AAPL', 'Apple', 'invalid_type'))

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_delete_asset_cascades(self, mock_price):
        self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock')
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.tracker.add_to_watchlist('AAPL')
        self.assertTrue(self.tracker.delete_asset('AAPL'))
        self.assertEqual(len(self.tracker.get_all_assets()), 0)
        self.assertEqual(len(self.tracker.get_transactions()), 0)
        self.assertEqual(len(self.tracker.get_watchlist()), 0)

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_get_all_assets_empty(self, mock_price):
        self.assertEqual(self.tracker.get_all_assets(), [])


class TestTransactionOperations(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()
        with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
            self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock')
            self.tracker.add_asset('BTC', 'Bitcoin', 'crypto')

    def tearDown(self):
        os.unlink(self.db_path)

    def test_add_buy_transaction(self):
        self.assertTrue(self.tracker.add_transaction('AAPL', 'buy', 10, 150.0, 5.0, 'IB'))
        txns = self.tracker.get_transactions()
        self.assertEqual(len(txns), 1)
        self.assertEqual(txns[0]['amount'], 10.0)
        self.assertAlmostEqual(txns[0]['total_value'], 1500.0)

    def test_add_sell_transaction(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.assertTrue(self.tracker.add_transaction('AAPL', 'sell', 5, 160.0))

    def test_sell_more_than_held_rejected(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.assertFalse(self.tracker.add_transaction('AAPL', 'sell', 11, 160.0))

    def test_sell_without_holdings_rejected(self):
        self.assertFalse(self.tracker.add_transaction('AAPL', 'sell', 1, 160.0))

    def test_sell_exact_holdings_allowed(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.assertTrue(self.tracker.add_transaction('AAPL', 'sell', 10, 160.0))

    def test_transaction_nonexistent_asset(self):
        self.assertFalse(self.tracker.add_transaction('NOPE', 'buy', 1, 100.0))

    def test_transaction_invalid_amount(self):
        self.assertFalse(self.tracker.add_transaction('AAPL', 'buy', -5, 150.0))
        self.assertFalse(self.tracker.add_transaction('AAPL', 'buy', 0, 150.0))

    def test_transaction_invalid_price(self):
        self.assertFalse(self.tracker.add_transaction('AAPL', 'buy', 10, 0))
        self.assertFalse(self.tracker.add_transaction('AAPL', 'buy', 10, -5))

    def test_transaction_negative_fees_rejected(self):
        self.assertFalse(self.tracker.add_transaction('AAPL', 'buy', 10, 150.0, -1))

    def test_transaction_with_date_and_notes(self):
        self.assertTrue(self.tracker.add_transaction(
            'AAPL', 'buy', 10, 150.0, 5.0, 'IB', '2024-01-15', 'Test note'
        ))
        txns = self.tracker.get_transactions()
        self.assertEqual(txns[0]['notes'], 'Test note')

    def test_get_transactions_by_asset(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.tracker.add_transaction('BTC', 'buy', 1, 50000.0)
        apple_txns = self.tracker.get_transactions('AAPL')
        self.assertEqual(len(apple_txns), 1)
        self.assertEqual(apple_txns[0]['asset_symbol'], 'AAPL')

    def test_delete_transaction(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        txns = self.tracker.get_transactions()
        self.assertTrue(self.tracker.delete_transaction(txns[0]['id']))
        self.assertEqual(len(self.tracker.get_transactions()), 0)

    def test_dividend_and_fee_transactions(self):
        self.assertTrue(self.tracker.add_transaction('AAPL', 'dividend', 50, 1.0))
        self.assertTrue(self.tracker.add_transaction('AAPL', 'fee', 1, 10.0))
        txns = self.tracker.get_transactions()
        self.assertEqual(len(txns), 2)


class TestPortfolioSummary(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()
        with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
            self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock')
            self.tracker.add_asset('BTC', 'Bitcoin', 'crypto')

    def tearDown(self):
        os.unlink(self.db_path)

    def test_empty_portfolio(self):
        self.assertEqual(self.tracker.get_portfolio_summary(), [])

    def test_portfolio_pnl_calculation(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0, 5.0)
        self.tracker._save_price('AAPL', 160.0)
        portfolio = self.tracker.get_portfolio_summary()
        self.assertEqual(len(portfolio), 1)
        a = portfolio[0]
        self.assertEqual(a['symbol'], 'AAPL')
        self.assertEqual(a['total_amount'], 10.0)
        self.assertAlmostEqual(a['total_invested'], 1505.0)
        self.assertAlmostEqual(a['current_value'], 1600.0)
        self.assertAlmostEqual(a['profit_loss'], 95.0)

    def test_portfolio_buy_and_sell(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0, 5.0)
        self.tracker.add_transaction('AAPL', 'sell', 4, 160.0, 3.0)
        self.tracker._save_price('AAPL', 170.0)
        portfolio = self.tracker.get_portfolio_summary()
        self.assertEqual(portfolio[0]['total_amount'], 6.0)
        self.assertAlmostEqual(portfolio[0]['total_invested'], 868.0)

    def test_portfolio_excludes_zero_holdings(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.tracker.add_transaction('AAPL', 'sell', 10, 160.0)
        self.assertEqual(len(self.tracker.get_portfolio_summary()), 0)

    def test_multiple_assets(self):
        self.tracker.add_transaction('AAPL', 'buy', 10, 150.0)
        self.tracker.add_transaction('BTC', 'buy', 0.5, 50000.0)
        self.tracker._save_price('AAPL', 160.0)
        self.tracker._save_price('BTC', 55000.0)
        portfolio = self.tracker.get_portfolio_summary()
        self.assertEqual(len(portfolio), 2)


class TestWatchlist(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()
        with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
            self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock')
            self.tracker.add_asset('BTC', 'Bitcoin', 'crypto')

    def tearDown(self):
        os.unlink(self.db_path)

    def test_add_to_watchlist(self):
        self.assertTrue(self.tracker.add_to_watchlist('AAPL'))
        self.assertTrue(self.tracker.is_in_watchlist('AAPL'))

    def test_add_nonexistent_to_watchlist(self):
        self.assertFalse(self.tracker.add_to_watchlist('NOPE'))

    def test_remove_from_watchlist(self):
        self.tracker.add_to_watchlist('AAPL')
        self.assertTrue(self.tracker.remove_from_watchlist('AAPL'))
        self.assertFalse(self.tracker.is_in_watchlist('AAPL'))

    def test_get_watchlist_with_notes(self):
        self.tracker.add_to_watchlist('AAPL', 'Watching Apple')
        wl = self.tracker.get_watchlist()
        self.assertEqual(len(wl), 1)
        self.assertEqual(wl[0]['symbol'], 'AAPL')
        self.assertEqual(wl[0]['watchlist_notes'], 'Watching Apple')

    def test_watchlist_empty(self):
        self.assertEqual(self.tracker.get_watchlist(), [])


class TestPriceOperations(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()
        with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
            self.tracker.add_asset('AAPL', 'Apple Inc.', 'stock')

    def tearDown(self):
        os.unlink(self.db_path)

    def test_save_price(self):
        self.tracker._save_price('AAPL', 155.50)
        assets = self.tracker.get_all_assets()
        self.assertAlmostEqual(assets[0]['current_price'], 155.50)

    def test_manual_price_update_valid(self):
        self.assertTrue(self.tracker.update_asset_values_manually('AAPL', 200.0))
        assets = self.tracker.get_all_assets()
        self.assertAlmostEqual(assets[0]['current_price'], 200.0)

    def test_manual_price_update_invalid(self):
        self.assertFalse(self.tracker.update_asset_values_manually('AAPL', -10))
        self.assertFalse(self.tracker.update_asset_values_manually('AAPL', 0))

    def test_price_history_recorded(self):
        self.tracker._save_price('AAPL', 150.0)
        self.tracker._save_price('AAPL', 155.0)
        history = self.tracker.get_price_history('AAPL')
        self.assertEqual(len(history), 2)

    def test_cleanup_old_price_history(self):
        conn = self.tracker._get_connection()
        cur = conn.cursor()
        old_date = (datetime.datetime.now() - datetime.timedelta(days=400)).isoformat()
        cur.execute("INSERT INTO price_history (asset_symbol, price, date) VALUES (?, ?, ?)",
                    ('AAPL', 100.0, old_date))
        cur.execute("INSERT INTO price_history (asset_symbol, price, date) VALUES (?, ?, ?)",
                    ('AAPL', 150.0, datetime.datetime.now().isoformat()))
        conn.commit()
        conn.close()
        self.tracker._cleanup_price_history()
        history = self.tracker.get_price_history('AAPL')
        self.assertEqual(len(history), 1)
        self.assertAlmostEqual(history[0]['price'], 150.0)

    @patch.object(InvestmentTracker, '_fetch_stock_price', return_value=175.0)
    def test_update_single_asset_stock(self, mock_fetch):
        result = InvestmentTracker.update_single_asset_price(self.tracker, 'AAPL', 'stock')
        self.assertTrue(result)
        mock_fetch.assert_called_once_with('AAPL')

    @patch.object(InvestmentTracker, '_fetch_crypto_price', return_value=50000.0)
    def test_update_single_asset_crypto(self, mock_fetch):
        with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
            self.tracker.add_asset('BTC', 'Bitcoin', 'crypto')
        result = InvestmentTracker.update_single_asset_price(self.tracker, 'BTC', 'crypto')
        self.assertTrue(result)
        mock_fetch.assert_called_once_with('BTC')


class TestCurrencyConversion(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_eur_passthrough(self):
        self.assertAlmostEqual(self.tracker._convert_to_eur(100.0, 'EUR'), 100.0)
        self.assertAlmostEqual(self.tracker._convert_to_eur(100.0, None), 100.0)

    def test_zero_or_negative(self):
        self.assertAlmostEqual(self.tracker._convert_to_eur(0.0, 'USD'), 0.0)
        self.assertAlmostEqual(self.tracker._convert_to_eur(-5.0, 'USD'), 0.0)

    @patch.object(InvestmentTracker, '_get_exchange_rate', return_value=0.92)
    def test_conversion_with_rate(self, mock_rate):
        self.assertAlmostEqual(self.tracker._convert_to_eur(100.0, 'USD'), 92.0)


class TestCryptoSymbols(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    @patch.object(InvestmentTracker, '_fetch_with_backoff')
    def test_fetches_from_api(self, mock_fetch):
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {'symbol': 'btc', 'id': 'bitcoin'},
            {'symbol': 'xyz', 'id': 'some-coin'},
        ]
        mock_fetch.return_value = mock_response
        self.tracker._crypto_symbols_cache = None
        result = self.tracker.get_available_crypto_symbols()
        self.assertIn('BTC', result)
        self.assertEqual(result['BTC'], 'bitcoin')  # priority mapping
        self.assertIn('XYZ', result)

    def test_uses_cache(self):
        self.tracker._crypto_symbols_cache = {'BTC': 'bitcoin'}
        self.tracker._cache_timestamp = datetime.datetime.now()
        result = self.tracker.get_available_crypto_symbols()
        self.assertEqual(result, {'BTC': 'bitcoin'})

    @patch.object(InvestmentTracker, '_fetch_with_backoff', return_value=None)
    def test_fallback_on_api_failure(self, mock_fetch):
        self.tracker._crypto_symbols_cache = None
        result = self.tracker.get_available_crypto_symbols()
        self.assertIn('BTC', result)
        self.assertEqual(result['BTC'], 'bitcoin')


class TestFetchWithBackoff(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    @patch('backend.requests.get')
    def test_success_first_try(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp
        result = self.tracker._fetch_with_backoff('http://example.com', max_retries=3, initial_delay=0.01)
        self.assertEqual(result, mock_resp)
        self.assertEqual(mock_get.call_count, 1)

    @patch('backend.time.sleep')
    @patch('backend.requests.get')
    def test_retries_on_429(self, mock_get, mock_sleep):
        rate_limited = MagicMock(status_code=429)
        success = MagicMock(status_code=200)
        mock_get.side_effect = [rate_limited, success]
        result = self.tracker._fetch_with_backoff('http://example.com', max_retries=3, initial_delay=0.01)
        self.assertEqual(result, success)
        self.assertEqual(mock_get.call_count, 2)

    @patch('backend.requests.get')
    def test_returns_none_on_server_error(self, mock_get):
        mock_get.return_value = MagicMock(status_code=500)
        result = self.tracker._fetch_with_backoff('http://example.com', max_retries=1, initial_delay=0.01)
        self.assertIsNone(result)


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.tracker, self.db_path = _make_tracker()

    def tearDown(self):
        os.unlink(self.db_path)

    def test_popular_assets(self):
        popular = self.tracker.get_popular_assets()
        self.assertGreater(len(popular), 0)
        symbols = [a['symbol'] for a in popular]
        self.assertIn('AAPL', symbols)
        self.assertIn('BTC', symbols)

    @patch.object(InvestmentTracker, 'get_available_crypto_symbols',
                  return_value={'BTC': 'bitcoin', 'ETH': 'ethereum'})
    def test_search_crypto(self, mock_crypto):
        results = self.tracker.search_available_assets('BTC', 'crypto')
        self.assertTrue(any(r['symbol'] == 'BTC' for r in results))


if __name__ == '__main__':
    unittest.main()
