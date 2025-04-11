from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json
import hashlib
from typing import List, Dict, Any
import logging
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = FastAPI()

# Add CORS middleware with development configuration
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Add a middleware to set CORS headers for all responses
@app.middleware("http")
async def add_cors_header(request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:3000"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Get base directory from environment variable or use current directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to /Users/kunalsaxena/stocks
CACHE_DIR = os.path.join(BASE_DIR, 'stock_data', 'cache')

def get_cache_path(date):
    """Generate cache file path based on date"""
    date_str = date.strftime('%Y-%m-%d')
    hash_object = hashlib.md5(date_str.encode())
    filename = f"strength_scores_{hash_object.hexdigest()}.json"
    return os.path.join(CACHE_DIR, filename)

def load_from_cache(date):
    """Load data from cache if available"""
    cache_path = get_cache_path(date)
    if os.path.exists(cache_path):
        try:
            with open(cache_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading cache: {e}")
    return None

def save_to_cache(date, data):
    """Save data to cache"""
    cache_path = get_cache_path(date)
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    try:
        with open(cache_path, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving cache: {e}")

@app.get("/api/stock-data")
async def get_stock_data():
    try:
        # Get today's date
        today = datetime.now().date()
        logger.info(f"Today's date: {today}")

        # Check cache first
        cached_data = load_from_cache(today)
        if cached_data:
            logger.info("Using cached data")
            return cached_data

        # Read historical data
        csv_path = os.path.join(BASE_DIR, 'stock_data', 'historical_data.csv')
        logger.info(f"Looking for CSV file at: {csv_path}")
        logger.info("Reading CSV file...")
        try:
            df = pd.read_csv(csv_path)
            logger.info(f"CSV loaded with {len(df)} rows")
        except FileNotFoundError:
            logger.error(f"File not found at: {csv_path}")
            raise HTTPException(status_code=500, detail=f"Historical data file not found at {csv_path}")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])

        # Get the latest date in the data (up to today)
        latest_date = df['Date'].max().date()
        if latest_date > today:
            latest_date = today
        logger.info(f"Latest available date in data (up to today): {latest_date}")

        # Get data for the latest date
        latest_data = df[df['Date'].dt.date == latest_date]
        logger.info("Sample of 5 records from latest date:")
        logger.info(latest_data[['Date', 'Stock', 'Close']].head())

        # Calculate strength scores
        start_date = latest_date - timedelta(days=180)  # 6 months
        filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= latest_date)]
        
        logger.info(f"Using data from {start_date.strftime('%Y-%m-%d')} to {latest_date.strftime('%Y-%m-%d')}")
        logger.info(f"Total records: {len(filtered_data)}")
        logger.info(f"Unique stocks: {len(filtered_data['Stock'].unique())}")
        
        # Calculate returns
        filtered_data['Returns'] = filtered_data.groupby('Stock')['Close'].pct_change()
        
        # Calculate normalized returns
        for period in [20, 60, 120]:  # 1M, 3M, 6M
            filtered_data[f'{period}D_Return'] = filtered_data.groupby('Stock')['Returns'].rolling(period).sum().reset_index(0, drop=True)
        
        # Normalize returns
        for period in [20, 60, 120]:
            filtered_data[f'{period}D_Return_Normalized'] = (
                (filtered_data[f'{period}D_Return'] - filtered_data[f'{period}D_Return'].mean()) /
                filtered_data[f'{period}D_Return'].std()
            )
        
        # Calculate strength score
        filtered_data['Strength_Score'] = (
            filtered_data['20D_Return_Normalized'] * 0.4 +
            filtered_data['60D_Return_Normalized'] * 0.3 +
            filtered_data['120D_Return_Normalized'] * 0.3
        )
        
        # Get top 50 stocks by strength score
        top_stocks = filtered_data[filtered_data['Date'] == latest_date].nlargest(50, 'Strength_Score')
        
        # Prepare response
        result = {
            "date": latest_date.strftime('%Y-%m-%d'),
            "stocks": []
        }
        
        for _, stock in top_stocks.iterrows():
            result["stocks"].append({
                "Stock": stock['Stock'],
                "Rank": len(result["stocks"]) + 1,
                "Latest_Price": stock['Close'],
                "1M_Return_Normalized": stock['20D_Return_Normalized'],
                "3M_Return_Normalized": stock['60D_Return_Normalized'],
                "6M_Return_Normalized": stock['120D_Return_Normalized'],
                "Strength_Score_Normalized": stock['Strength_Score'],
                "20_MA": stock['Close'],  # Using latest price as MA for now
                "20_MAV": stock['Close'],  # Using latest price as MAV for now
                "Liquidity": 1000000  # Placeholder value
            })
        
        # Save to cache
        save_to_cache(today, result)
        logger.info("Saved results to cache")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in get_stock_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/run-backtest")
async def run_backtest(date: str):
    try:
        logger.info(f"Running backtest for date: {date}")
        
        # Parse the date
        backtest_date = datetime.strptime(date, '%Y-%m-%d').date()
        
        # Check cache first
        cached_data = load_from_cache(backtest_date)
        if cached_data:
            logger.info("Using cached backtest data")
            return cached_data
        
        # Read historical data
        csv_path = os.path.join(BASE_DIR, 'stock_data', 'historical_data.csv')
        logger.info(f"Reading CSV file for backtest: {csv_path}")
        
        df = pd.read_csv(csv_path)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Filter data for the backtest date
        backtest_data = df[df['Date'].dt.date == backtest_date]
        
        if backtest_data.empty:
            raise HTTPException(status_code=404, detail=f"No data found for date {date}")
        
        # Calculate strength scores (similar to get_stock_data)
        start_date = backtest_date - timedelta(days=180)
        filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= backtest_date)]
        
        # Calculate returns and normalized returns
        filtered_data['Returns'] = filtered_data.groupby('Stock')['Close'].pct_change()
        
        for period in [20, 60, 120]:
            filtered_data[f'{period}D_Return'] = filtered_data.groupby('Stock')['Returns'].rolling(period).sum().reset_index(0, drop=True)
            filtered_data[f'{period}D_Return_Normalized'] = (
                (filtered_data[f'{period}D_Return'] - filtered_data[f'{period}D_Return'].mean()) /
                filtered_data[f'{period}D_Return'].std()
            )
        
        # Calculate strength score
        filtered_data['Strength_Score'] = (
            filtered_data['20D_Return_Normalized'] * 0.4 +
            filtered_data['60D_Return_Normalized'] * 0.3 +
            filtered_data['120D_Return_Normalized'] * 0.3
        )
        
        # Get top 50 stocks by strength score
        top_stocks = filtered_data[filtered_data['Date'] == backtest_date].nlargest(50, 'Strength_Score')
        
        # Prepare response
        result = {
            "date": date,
            "stocks": []
        }
        
        for _, stock in top_stocks.iterrows():
            result["stocks"].append({
                "Stock": stock['Stock'],
                "Rank": len(result["stocks"]) + 1,
                "Latest_Price": stock['Close'],
                "1M_Return_Normalized": stock['20D_Return_Normalized'],
                "3M_Return_Normalized": stock['60D_Return_Normalized'],
                "6M_Return_Normalized": stock['120D_Return_Normalized'],
                "Strength_Score_Normalized": stock['Strength_Score'],
                "20_MA": stock['Close'],
                "20_MAV": stock['Close'],
                "Liquidity": 1000000
            })
        
        # Save to cache
        save_to_cache(backtest_date, result)
        logger.info("Saved backtest results to cache")
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error in run_backtest: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv('PORT', 8000))
    uvicorn.run(app, host="0.0.0.0", port=port) 