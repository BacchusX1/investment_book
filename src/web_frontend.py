"""
Modern Web Frontend for Investment Portfolio Tracker
Flask-based web application with a clean, responsive HTML/CSS/JS interface
"""

import os
import sys
import glob
import webbrowser
from threading import Timer
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Import our backend
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.backend import InvestmentTracker

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'),
            static_folder=os.path.join(os.path.dirname(__file__), '..', 'static'))
CORS(app)

# Project root directory for database discovery
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Initialize tracker with database (use absolute path)
current_db_name = "my_assets.db"
tracker = InvestmentTracker(os.path.join(PROJECT_ROOT, current_db_name))


# Disable caching for development
@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


# ============== Page Routes ==============

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


# ============== API Routes ==============

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """Get portfolio summary"""
    try:
        portfolio = tracker.get_portfolio_summary()
        return jsonify({'success': True, 'data': portfolio})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist', methods=['GET'])
def get_watchlist():
    """Get watchlist"""
    try:
        watchlist = tracker.get_watchlist()
        return jsonify({'success': True, 'data': watchlist})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist', methods=['POST'])
def add_to_watchlist():
    """Add asset to watchlist"""
    try:
        data = request.json
        symbol = data.get('symbol')
        notes = data.get('notes', '')
        
        if not symbol:
            return jsonify({'success': False, 'error': 'Symbol is required'}), 400
        
        success = tracker.add_to_watchlist(symbol, notes)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/watchlist/<symbol>', methods=['DELETE'])
def remove_from_watchlist(symbol):
    """Remove asset from watchlist"""
    try:
        success = tracker.remove_from_watchlist(symbol)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets', methods=['GET'])
def get_assets():
    """Get all assets"""
    try:
        assets = tracker.get_all_assets()
        # Add watchlist status to each asset
        for asset in assets:
            asset['in_watchlist'] = tracker.is_in_watchlist(asset['symbol'])
        return jsonify({'success': True, 'data': assets})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets', methods=['POST'])
def add_asset():
    """Add a new asset"""
    try:
        data = request.json
        symbol = data.get('symbol')
        name = data.get('name')
        asset_type = data.get('asset_type')
        platform = data.get('platform', '')
        
        if not all([symbol, name, asset_type]):
            return jsonify({'success': False, 'error': 'Symbol, name, and asset_type are required'}), 400
        
        success = tracker.add_asset(symbol, name, asset_type, platform)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets/<symbol>', methods=['DELETE'])
def delete_asset(symbol):
    """Delete an asset"""
    try:
        success = tracker.delete_asset(symbol)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/assets/<symbol>/price', methods=['PUT'])
def update_asset_price(symbol):
    """Manually update asset price"""
    try:
        data = request.json
        price = data.get('price')
        
        if price is None or price <= 0:
            return jsonify({'success': False, 'error': 'Valid price is required'}), 400
        
        success = tracker.update_asset_values_manually(symbol, price)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions', methods=['GET'])
def get_transactions():
    """Get all transactions"""
    try:
        symbol = request.args.get('symbol')
        transactions = tracker.get_transactions(symbol)
        return jsonify({'success': True, 'data': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions', methods=['POST'])
def add_transaction():
    """Add a new transaction"""
    try:
        data = request.json
        asset_symbol = data.get('asset_symbol')
        transaction_type = data.get('transaction_type')
        amount = data.get('amount')
        price_per_unit = data.get('price_per_unit')
        fees = data.get('fees', 0)
        platform = data.get('platform', '')
        transaction_date = data.get('transaction_date')
        notes = data.get('notes', '')
        
        if not all([asset_symbol, transaction_type, amount, price_per_unit]):
            return jsonify({'success': False, 'error': 'Required fields missing'}), 400
        
        success = tracker.add_transaction(
            asset_symbol, transaction_type, float(amount), float(price_per_unit),
            float(fees), platform, transaction_date, notes
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/transactions/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    """Delete a transaction"""
    try:
        success = tracker.delete_transaction(transaction_id)
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prices/refresh', methods=['POST'])
def refresh_prices():
    """Refresh all asset prices"""
    try:
        results = tracker.update_asset_prices()
        success_count = sum(1 for s in results.values() if s)
        return jsonify({
            'success': True, 
            'updated': success_count, 
            'total': len(results),
            'details': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/prices/refresh/<symbol>', methods=['POST'])
def refresh_single_price(symbol):
    """Refresh price for a single asset"""
    try:
        # Get asset type
        assets = tracker.get_all_assets()
        asset = next((a for a in assets if a['symbol'] == symbol.upper()), None)
        
        if not asset:
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        
        success = tracker.update_single_asset_price(symbol.upper(), asset['asset_type'])
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/search/assets', methods=['GET'])
def search_assets():
    """Search for available assets"""
    try:
        query = request.args.get('q', '')
        asset_type = request.args.get('type')
        
        if len(query) < 1:
            # Return popular assets if no query
            popular = tracker.get_popular_assets()
            return jsonify({'success': True, 'data': popular})
        
        results = tracker.search_available_assets(query, asset_type)
        return jsonify({'success': True, 'data': results})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/popular-assets', methods=['GET'])
def get_popular_assets():
    """Get popular assets for quick selection"""
    try:
        popular = tracker.get_popular_assets()
        return jsonify({'success': True, 'data': popular})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/crypto-symbols', methods=['GET'])
def get_crypto_symbols():
    """Get all available crypto symbols"""
    try:
        crypto_map = tracker.get_available_crypto_symbols()
        # Convert to list of dicts for frontend
        cryptos = [{'symbol': sym, 'name': name.replace('-', ' ').title(), 'asset_type': 'crypto'} 
                   for sym, name in crypto_map.items()]
        return jsonify({'success': True, 'data': cryptos})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/price-history', methods=['GET'])
def get_price_history():
    """Get price history"""
    try:
        symbol = request.args.get('symbol')
        history = tracker.get_price_history(symbol)
        return jsonify({'success': True, 'data': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============== Database Management Routes ==============

@app.route('/api/databases', methods=['GET'])
def list_databases():
    """List all available database files"""
    try:
        # Search for .db files in project root and data folder
        db_files = []
        
        # Check project root
        for db_path in glob.glob(os.path.join(PROJECT_ROOT, '*.db')):
            db_name = os.path.basename(db_path)
            db_files.append({
                'name': db_name,
                'path': db_name,
                'size': os.path.getsize(db_path),
                'is_current': db_name == current_db_name
            })
        
        # Check data folder
        data_folder = os.path.join(PROJECT_ROOT, 'data')
        for db_path in glob.glob(os.path.join(data_folder, '*.db')):
            db_name = os.path.basename(db_path)
            relative_path = os.path.join('data', db_name)
            db_files.append({
                'name': db_name,
                'path': relative_path,
                'size': os.path.getsize(db_path),
                'is_current': relative_path == current_db_name
            })
        
        return jsonify({'success': True, 'data': db_files, 'current': current_db_name})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/databases/current', methods=['GET'])
def get_current_database():
    """Get the currently loaded database"""
    return jsonify({'success': True, 'data': {'name': current_db_name}})


@app.route('/api/databases/load', methods=['POST'])
def load_database():
    """Load a different database file"""
    global tracker, current_db_name
    try:
        data = request.json
        db_name = data.get('database')
        
        if not db_name:
            return jsonify({'success': False, 'error': 'Database name is required'}), 400
        
        # Validate the database path
        db_path = os.path.join(PROJECT_ROOT, db_name)
        if not os.path.exists(db_path):
            return jsonify({'success': False, 'error': f'Database file not found: {db_name}'}), 404
        
        # Load the new database
        tracker = InvestmentTracker(db_path)
        current_db_name = db_name
        
        return jsonify({'success': True, 'message': f'Successfully loaded database: {db_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/databases/create', methods=['POST'])
def create_database():
    """Create a new database file"""
    global tracker, current_db_name
    try:
        data = request.json
        db_name = data.get('name')
        
        if not db_name:
            return jsonify({'success': False, 'error': 'Database name is required'}), 400
        
        # Ensure it has .db extension
        if not db_name.endswith('.db'):
            db_name += '.db'
        
        # Sanitize filename
        db_name = os.path.basename(db_name)
        db_path = os.path.join(PROJECT_ROOT, db_name)
        
        if os.path.exists(db_path):
            return jsonify({'success': False, 'error': f'Database already exists: {db_name}'}), 400
        
        # Create and load the new database
        tracker = InvestmentTracker(db_path)
        current_db_name = db_name
        
        return jsonify({'success': True, 'message': f'Successfully created database: {db_name}'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


def open_browser():
    """Open the web browser after server starts"""
    webbrowser.open('http://127.0.0.1:5000')


def main():
    """Run the Flask application"""
    print("=" * 50)
    print("💰 Investment Portfolio Tracker")
    print("=" * 50)
    print("Starting web server...")
    print("Opening browser at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print("=" * 50)
    
    # Open browser after a short delay
    Timer(1.5, open_browser).start()
    
    # Run Flask app
    app.run(host='127.0.0.1', port=5000, debug=False)


if __name__ == '__main__':
    main()
