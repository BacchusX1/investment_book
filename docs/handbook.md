# Investment Portfolio Tracker - User Handbook

A comprehensive guide to using the Investment Portfolio Tracker application.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Managing Assets](#managing-assets)
4. [Recording Transactions](#recording-transactions)
5. [Using the Watchlist](#using-the-watchlist)
6. [Database Management](#database-management)
7. [Server Management](#server-management)
8. [Troubleshooting](#troubleshooting)

---

## Getting Started

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/BacchusX1/investment_book.git
   cd investment_book
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Launch the application:
   ```bash
   python demo.py
   ```

4. Select option `[1]` to launch the web interface. Your browser will open automatically to `http://127.0.0.1:5000`.

### First Run

On first run, an empty database (`my_assets.db`) is created. You can start by:
- Adding assets to track
- Recording buy transactions
- Adding items to your watchlist

---

## Dashboard Overview

The **Dashboard** is your portfolio home page, showing:

### Stats Cards
- **Total Value**: Current portfolio value in EUR
- **Total P&L**: Profit/Loss across all holdings
- **Holdings**: Number of unique assets
- **Total Invested**: Sum of all buy transactions

### Charts
- **Allocation Chart**: Pie chart showing portfolio distribution by asset
- **Performance Chart**: Line chart showing portfolio value over time

### Portfolio Table
Lists all your assets with:
- Symbol and name
- Current price
- Quantity held
- Current value
- Profit/Loss (amount and percentage)
- Actions (refresh price, delete)

### Quick Actions
- **Refresh Prices**: Update all asset prices from Yahoo Finance/CoinGecko
- **Add Asset**: Add a new asset to your portfolio

---

## Managing Assets

### Adding an Asset

1. Click **Add Asset** button
2. In the search box, type the asset name or symbol
3. Select from the dropdown:
   - **Stocks/ETFs**: Searched via Yahoo Finance (e.g., AAPL, MSFT, VWCE.DE)
   - **Crypto**: Searched via CoinGecko (e.g., BTC, ETH, SOL)
4. The asset type and name are auto-filled
5. Optionally add a platform (e.g., "Coinbase", "Trade Republic")
6. Click **Add Asset**

### Supported Asset Types

| Type | Example Symbols | Data Source |
|------|-----------------|-------------|
| Stock | AAPL, MSFT, GOOGL | Yahoo Finance |
| ETF | VWCE.DE, SPY, QQQ | Yahoo Finance |
| Crypto | BTC, ETH, SOL | CoinGecko |
| Bond | Various | Yahoo Finance |
| Commodity | GC=F (Gold) | Yahoo Finance |

### Deleting an Asset

1. Find the asset in the Portfolio table
2. Click the **trash icon** in the Actions column
3. Confirm deletion

> **Warning**: Deleting an asset also removes all associated transactions.

### Refreshing Prices

- **All assets**: Click **Refresh Prices** button in the header
- **Single asset**: Click the **refresh icon** next to an asset in the table

Prices are automatically converted to EUR using current exchange rates.

---

## Recording Transactions

### Adding a Transaction

1. Go to **Assets & Transactions** page (click in sidebar)
2. Click **Add Transaction**
3. Fill in the form:
   - **Asset**: Select from your existing assets
   - **Type**: Buy, Sell, Dividend, or Fee
   - **Amount**: Number of units
   - **Price per Unit**: Price at time of transaction (in EUR)
   - **Fees**: Any transaction fees
   - **Date**: Transaction date
   - **Notes**: Optional notes
4. Click **Add Transaction**

### Transaction Types

| Type | Description | Effect on Holdings |
|------|-------------|-------------------|
| **Buy** | Purchase of asset | Increases quantity |
| **Sell** | Sale of asset | Decreases quantity |
| **Dividend** | Dividend payment | No effect on quantity |
| **Fee** | Platform/transaction fee | No effect on quantity |

### Viewing Transaction History

The transaction table shows:
- Date
- Asset symbol
- Type (color-coded)
- Amount
- Price per unit
- Total value
- Fees
- Notes

You can filter transactions by asset using the dropdown filter.

### Deleting a Transaction

Click the **trash icon** next to any transaction to delete it. This will recalculate your portfolio holdings.

---

## Using the Watchlist

The **Watchlist** lets you track assets you're interested in without buying them.

### Adding to Watchlist

**Method 1**: From the Watchlist page
1. Go to **Watchlist** page
2. Click **Add to Watchlist**
3. Search and select an asset
4. Add optional notes
5. Click **Add**

**Method 2**: From the Portfolio table
- Click the **eye icon** next to any asset to add/remove from watchlist

### Watchlist Features

- View current prices of watched assets
- See price changes
- One-click to add to portfolio
- Remove items when no longer interested

---

## Database Management

The application supports multiple database files, allowing you to maintain separate portfolios.

### Switching Databases

1. Look at the **bottom of the sidebar** for the Database selector
2. Click the dropdown to see available databases
3. Select a different database to switch
4. All data (portfolio, transactions, watchlist) will reload

### Creating a New Database

1. Click the **+** button next to the database dropdown
2. Enter a name for the new database (e.g., "retirement_portfolio")
3. Click **Create**
4. The app switches to the new empty database

### Database Location

Databases are stored as SQLite files (`.db`) in the project root directory:
- `my_assets.db` - Default database
- `comprehensive_demo.db` - Demo database with sample data
- Any custom databases you create

---

## Server Management

The web interface runs on a Flask server. Here's how to manage it:

### Starting the Server

```bash
cd investment_book
python demo.py
# Select option [1] to launch
```

The server runs at `http://127.0.0.1:5000`.

### Stopping the Server

**If running in foreground**: Press `Ctrl+C`

**If running in background**:
```bash
# Kill by port
kill $(lsof -t -i:5000)

# Or kill by process name
pkill -f "python.*demo.py"
```

### Checking if Server is Running

```bash
# Check process
ps aux | grep python | grep demo

# Check port
lsof -i :5000
```

### Development Mode

For auto-reload when code changes:
```bash
FLASK_DEBUG=1 python -c "from src.web_frontend import main; main()"
```

---

## Troubleshooting

### Web interface won't load

1. Check if server is running: `lsof -i :5000`
2. Kill any stale processes: `kill $(lsof -t -i:5000)`
3. Restart: `python demo.py`

### Database selector not visible

1. Kill old server process
2. Restart the application
3. Hard refresh browser: `Ctrl+Shift+R`

### Price updates failing

- **Rate limits**: CoinGecko free tier limits requests. Wait a minute and try again.
- **Network issues**: Check your internet connection
- **Invalid symbol**: Verify the asset symbol is correct

### "Input/Output Error" when adding assets

This was fixed in the latest version. If you see this:
1. Update to latest code
2. Restart the server

### Database errors

- Ensure write permissions in the project directory
- Check disk space
- Don't open the `.db` file while the server is running

### Browser shows old interface

1. Hard refresh: `Ctrl+Shift+R`
2. Clear browser cache
3. Try incognito mode
4. Make sure you restarted the server after code changes

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+R` | Hard refresh (bypass cache) |
| `Escape` | Close modal dialogs |

---

## Support

For issues and feature requests, please open an issue on the GitHub repository.
