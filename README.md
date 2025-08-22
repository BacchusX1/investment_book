# Investment Portfolio Tracker

A comprehensive investment portfolio tracking application built with Python and PySide6. This application helps you track your investments across different asset classes including stocks, ETFs, cryptocurrencies, bonds, and commodities.

## Features

### 📊 Dashboard
- **Portfolio Overview**: Real-time portfolio value, total invested amount, and profit/loss
- **Visual Charts**: Portfolio composition pie chart and value timeline
- **Asset Performance**: Detailed view of each asset's performance with color-coded profit/loss indicators
- **Automatic Price Updates**: Updates prices every 5 minutes using online APIs

### 💰 Transaction Management
- **Add Transactions**: Record buy, sell, dividend, and fee transactions
- **Transaction History**: View all historical transactions with filtering options
- **Platform Tracking**: Track which platform each transaction was made on
- **Notes Support**: Add custom notes to transactions for better record keeping

### 🎯 Asset Management
- **Multi-Asset Support**: Stocks, ETFs, cryptocurrencies, bonds, commodities
- **Automatic Price Updates**: Fetches current prices from Yahoo Finance and CoinGecko APIs
- **Manual Price Updates**: Override prices manually when needed
- **Platform Integration**: Track assets across multiple trading platforms

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Install Dependencies
```bash
pip install -r requirements.txt
```

Or install manually:
```bash
pip install PySide6 requests yfinance pandas matplotlib
```

## Usage

### Method 1: GUI Application (Recommended)
Run the main GUI application:
```bash
python example/gui/gui.py
```

This will:
1. Ask you to select an existing database or create a new one
2. Launch the full GUI interface
3. Provide three main tabs: Dashboard, Transactions, and Asset Management

### Method 2: Direct GUI Launch
If you want to use a specific database file:
```bash
python src/frontend.py
```

### Method 3: Backend Testing
Test the backend functionality:
```bash
python example/test_backend.py
```

This creates a test database with sample data to verify everything works correctly.

## Supported Assets

### Stocks & ETFs
- Any stock or ETF with a Yahoo Finance ticker symbol
- Examples: AAPL, MSFT, VWCE.DE, SPY

### Cryptocurrencies
- Major cryptocurrencies supported via CoinGecko API
- Supported: BTC, ETH, ADA, DOT, LTC, XRP, DOGE
- Prices in EUR (can be modified in backend.py)

### Adding New Assets
1. Go to the "Assets Management" tab
2. Enter the symbol (e.g., AAPL, BTC, VWCE.DE)
3. Enter the full name
4. Select the asset type
5. Optionally specify the trading platform
6. Click "Add Asset"

## Database Structure

The application uses SQLite to store data in three main tables:

### Assets Table
- Asset symbol, name, type, platform
- Current price and last update timestamp

### Transactions Table
- All buy/sell/dividend/fee transactions
- Amount, price, total value, fees
- Transaction date and notes

### Price History Table
- Historical price data for all assets
- Automatic tracking of price changes over time

## Configuration

### Price Update APIs
- **Stocks/ETFs**: Yahoo Finance (via yfinance library)
- **Cryptocurrencies**: CoinGecko API (free tier)
- **Manual Override**: Always available for any asset

### Auto-Refresh
- Portfolio data refreshes every 5 minutes
- Can be manually triggered with the refresh button
- Price updates are stored in the database for historical tracking

## File Structure

```
investment_book/
├── src/
│   ├── backend.py          # Core backend functionality
│   └── frontend.py         # GUI application
├── example/
│   ├── gui/
│   │   └── gui.py         # Main entry point
│   └── test_backend.py    # Backend testing script
├── data/                  # Data storage directory
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Troubleshooting

### Price Updates Not Working
1. Check your internet connection
2. Verify the asset symbol is correct
3. For stocks/ETFs, ensure the symbol exists on Yahoo Finance
4. For cryptocurrencies, check if it's in the supported list

### Database Issues
1. Ensure you have write permissions in the selected directory
2. If database appears corrupted, create a new one
3. The application will automatically create required tables

### GUI Not Loading
1. Verify PySide6 is properly installed: `pip install PySide6`
2. Check that all dependencies are installed: `pip install -r requirements.txt`
3. Try running the test backend script first to verify core functionality

## Contributing

This is a personal investment tracking tool. Feel free to modify the code to suit your needs:

1. **Adding New Asset Types**: Modify the asset_type dropdown in frontend.py
2. **Adding New Exchanges**: Extend the price update logic in backend.py
3. **Custom Reports**: Add new tabs or charts to frontend.py
4. **Currency Support**: Modify the price fetching APIs for different currencies

## Security Note

- Database files contain sensitive financial information
- Store database files securely and consider encryption for sensitive environments
- The application does not connect to trading platforms for execution - it's read-only for tracking purposes

## License

This project is for personal use. Modify and distribute as needed for your own investment tracking requirements.
