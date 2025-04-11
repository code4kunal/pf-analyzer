# Stock Analysis Backend

A FastAPI backend for stock analysis and backtesting.

## Features

- Real-time stock data analysis
- Historical backtesting
- Caching system for performance optimization
- RESTful API endpoints

## API Endpoints

- `GET /api/stock-data`: Get current stock data with strength scores
- `GET /api/run-backtest?date=YYYY-MM-DD`: Run backtest for a specific date

## Environment Variables

- `PORT`: Server port (default: 8000)
- `DATA_DIR`: Directory containing stock data (default: current directory)
- `CACHE_DIR`: Directory for cache files (default: DATA_DIR/stock_data/cache)

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run the server:
```bash
python server.py
```

## Deployment

This application is configured for deployment on Railway.app. The `Procfile` specifies how to run the application in production. 