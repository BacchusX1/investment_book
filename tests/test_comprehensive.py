#!/usr/bin/env python3
"""
Integration tests for the Flask API routes.
Tests all endpoints with a Flask test client and mocked backend.
"""

import unittest
import tempfile
import os
import json
import sys
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from backend import InvestmentTracker

# We need to set up the Flask app for testing
import web_frontend
from web_frontend import app, _set_current_db_name, _validate_db_name, _safe_error


def _make_tracker():
    """Create a tracker with a temp database."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
    tmp.close()
    with patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True):
        tracker = InvestmentTracker(tmp.name)
    return tracker, tmp.name


class FlaskTestBase(unittest.TestCase):
    """Base class for Flask API tests."""

    def setUp(self):
        self.tracker, self.db_path = _make_tracker()
        app.config['TESTING'] = True
        self.client = app.test_client()

        # Point the app at our temp database
        self.db_name = os.path.basename(self.db_path)
        # Override PROJECT_ROOT and current db for tests
        self._orig_root = web_frontend.PROJECT_ROOT
        web_frontend.PROJECT_ROOT = os.path.dirname(self.db_path)
        _set_current_db_name(self.db_name)

    def tearDown(self):
        web_frontend.PROJECT_ROOT = self._orig_root
        try:
            os.unlink(self.db_path)
        except OSError:
            pass

    def _add_asset(self, symbol='AAPL', name='Apple Inc.', asset_type='stock'):
        return self.client.post('/api/assets', json={
            'symbol': symbol, 'name': name, 'asset_type': asset_type
        })

    def _add_transaction(self, symbol='AAPL', tx_type='buy', amount=10, price=150.0, fees=5.0):
        return self.client.post('/api/transactions', json={
            'asset_symbol': symbol, 'transaction_type': tx_type,
            'amount': amount, 'price_per_unit': price, 'fees': fees
        })


class TestIndexRoute(FlaskTestBase):
    def test_index_returns_html(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)


class TestAssetEndpoints(FlaskTestBase):
    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_add_asset(self, mock_price):
        resp = self._add_asset()
        data = resp.get_json()
        self.assertTrue(data['success'])

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_get_assets(self, mock_price):
        self._add_asset()
        resp = self.client.get('/api/assets')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['symbol'], 'AAPL')

    def test_add_asset_missing_fields(self):
        resp = self.client.post('/api/assets', json={'symbol': 'AAPL'})
        data = resp.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(resp.status_code, 400)

    def test_add_asset_no_body(self):
        resp = self.client.post('/api/assets', content_type='application/json', data='')
        self.assertIn(resp.status_code, (400, 415))

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_delete_asset(self, mock_price):
        self._add_asset()
        resp = self.client.delete('/api/assets/AAPL')
        self.assertTrue(resp.get_json()['success'])
        resp = self.client.get('/api/assets')
        self.assertEqual(len(resp.get_json()['data']), 0)

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_update_asset_price(self, mock_price):
        self._add_asset()
        resp = self.client.put('/api/assets/AAPL/price', json={'price': 175.0})
        self.assertTrue(resp.get_json()['success'])

    def test_update_asset_price_invalid(self):
        resp = self.client.put('/api/assets/AAPL/price', json={'price': -10})
        data = resp.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(resp.status_code, 400)

    def test_update_asset_price_no_body(self):
        resp = self.client.put('/api/assets/AAPL/price', content_type='application/json', data='')
        self.assertIn(resp.status_code, (400, 415))


class TestTransactionEndpoints(FlaskTestBase):
    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_add_and_get_transactions(self, mock_price):
        self._add_asset()
        resp = self._add_transaction()
        self.assertTrue(resp.get_json()['success'])

        resp = self.client.get('/api/transactions')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)

    def test_add_transaction_missing_fields(self):
        resp = self.client.post('/api/transactions', json={'asset_symbol': 'AAPL'})
        self.assertFalse(resp.get_json()['success'])
        self.assertEqual(resp.status_code, 400)

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_delete_transaction(self, mock_price):
        self._add_asset()
        self._add_transaction()
        txns = self.client.get('/api/transactions').get_json()['data']
        resp = self.client.delete(f"/api/transactions/{txns[0]['id']}")
        self.assertTrue(resp.get_json()['success'])

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_get_transactions_by_symbol(self, mock_price):
        self._add_asset()
        self._add_asset('BTC', 'Bitcoin', 'crypto')
        self._add_transaction('AAPL')
        self._add_transaction('BTC', 'buy', 0.1, 50000.0)
        resp = self.client.get('/api/transactions?symbol=AAPL')
        data = resp.get_json()
        self.assertEqual(len(data['data']), 1)
        self.assertEqual(data['data'][0]['asset_symbol'], 'AAPL')


class TestPortfolioEndpoint(FlaskTestBase):
    def test_empty_portfolio(self):
        resp = self.client.get('/api/portfolio')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_portfolio_with_data(self, mock_price):
        self._add_asset()
        self._add_transaction()
        resp = self.client.get('/api/portfolio')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['data']), 1)


class TestWatchlistEndpoints(FlaskTestBase):
    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_watchlist_crud(self, mock_price):
        self._add_asset()

        # Add to watchlist
        resp = self.client.post('/api/watchlist', json={'symbol': 'AAPL'})
        self.assertTrue(resp.get_json()['success'])

        # Get watchlist
        resp = self.client.get('/api/watchlist')
        data = resp.get_json()
        self.assertEqual(len(data['data']), 1)

        # Remove from watchlist
        resp = self.client.delete('/api/watchlist/AAPL')
        self.assertTrue(resp.get_json()['success'])

        resp = self.client.get('/api/watchlist')
        self.assertEqual(len(resp.get_json()['data']), 0)

    def test_watchlist_no_body(self):
        resp = self.client.post('/api/watchlist', content_type='application/json', data='')
        self.assertIn(resp.status_code, (400, 415))


class TestPriceRefreshEndpoints(FlaskTestBase):
    @patch.object(InvestmentTracker, 'update_asset_prices', return_value={'AAPL': True})
    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_refresh_all_prices(self, mock_single, mock_all):
        self._add_asset()
        resp = self.client.post('/api/prices/refresh')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['updated'], 1)

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_refresh_single_price(self, mock_price):
        self._add_asset()
        resp = self.client.post('/api/prices/refresh/AAPL')
        self.assertTrue(resp.get_json()['success'])

    @patch.object(InvestmentTracker, 'update_single_asset_price', return_value=True)
    def test_refresh_nonexistent_asset(self, mock_price):
        resp = self.client.post('/api/prices/refresh/NOPE')
        data = resp.get_json()
        self.assertFalse(data['success'])
        self.assertEqual(resp.status_code, 404)


class TestSearchEndpoints(FlaskTestBase):
    def test_popular_assets(self):
        resp = self.client.get('/api/popular-assets')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']), 0)

    def test_search_empty_query(self):
        resp = self.client.get('/api/search/assets?q=')
        data = resp.get_json()
        self.assertTrue(data['success'])

    @patch.object(InvestmentTracker, 'get_available_crypto_symbols',
                  return_value={'BTC': 'bitcoin'})
    def test_crypto_symbols(self, mock_crypto):
        resp = self.client.get('/api/crypto-symbols')
        data = resp.get_json()
        self.assertTrue(data['success'])


class TestPriceHistoryEndpoint(FlaskTestBase):
    def test_price_history_empty(self):
        resp = self.client.get('/api/price-history')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data'], [])


class TestDatabaseEndpoints(FlaskTestBase):
    def test_list_databases(self):
        resp = self.client.get('/api/databases')
        data = resp.get_json()
        self.assertTrue(data['success'])
        self.assertIsInstance(data['data'], list)

    def test_get_current_database(self):
        resp = self.client.get('/api/databases/current')
        data = resp.get_json()
        self.assertTrue(data['success'])

    def test_create_database(self):
        resp = self.client.post('/api/databases/create', json={'name': 'test_new'})
        data = resp.get_json()
        self.assertTrue(data['success'])
        # Cleanup
        new_db = os.path.join(os.path.dirname(self.db_path), 'test_new.db')
        if os.path.exists(new_db):
            os.unlink(new_db)

    def test_create_database_no_name(self):
        resp = self.client.post('/api/databases/create', json={'name': ''})
        self.assertFalse(resp.get_json()['success'])

    def test_load_database_not_found(self):
        resp = self.client.post('/api/databases/load', json={'database': 'nonexistent.db'})
        data = resp.get_json()
        self.assertFalse(data['success'])


class TestDbNameValidation(unittest.TestCase):
    def test_valid_names(self):
        self.assertEqual(_validate_db_name('my_portfolio.db'), 'my_portfolio.db')
        self.assertEqual(_validate_db_name('test-db.db'), 'test-db.db')

    def test_path_traversal_blocked(self):
        with self.assertRaises(ValueError):
            _validate_db_name('../etc/passwd.db')
        with self.assertRaises(ValueError):
            _validate_db_name('../../secrets.db')

    def test_deep_path_blocked(self):
        with self.assertRaises(ValueError):
            _validate_db_name('a/b/c.db')

    def test_non_data_prefix_blocked(self):
        with self.assertRaises(ValueError):
            _validate_db_name('other/test.db')

    def test_data_prefix_allowed(self):
        self.assertEqual(_validate_db_name('data/test.db'), 'data/test.db')

    def test_empty_name_rejected(self):
        with self.assertRaises(ValueError):
            _validate_db_name('')
        with self.assertRaises(ValueError):
            _validate_db_name(None)

    def test_bad_extension_rejected(self):
        with self.assertRaises(ValueError):
            _validate_db_name('test.txt')


class TestSafeError(unittest.TestCase):
    def test_normal_message(self):
        self.assertEqual(_safe_error(Exception('Something failed')), 'Something failed')

    def test_filters_paths(self):
        self.assertEqual(_safe_error(Exception('/home/user/secret.py failed')), 'An internal error occurred')

    def test_truncates_long_message(self):
        msg = 'x' * 300
        result = _safe_error(Exception(msg))
        self.assertEqual(len(result), 200)


if __name__ == '__main__':
    unittest.main()
