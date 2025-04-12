import os
import pandas as pd
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import logging
import json
import pickle
from pathlib import Path
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from data_fetcher import read_historical_data, clear_historical_data, fetch_all_stocks_data
from typing import List, Dict, Any

# Define IST timezone
IST = pytz.timezone('Asia/Kolkata')

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
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
    allow_methods=["GET", "POST", "OPTIONS"],
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

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to get the root directory

# Cache directory
CACHE_DIR = os.path.join('backend', 'stock_data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

# Historical data file path
HISTORICAL_DATA_PATH = '/Users/kunalsaxena/stocks/backend/stock_data/historical_data.csv'

# Initialize scheduler
scheduler = BackgroundScheduler()

def save_to_cache(filename: str, data: Any) -> None:
    """Save data to cache file."""
    try:
        filepath = os.path.join(CACHE_DIR, filename)
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Data saved to cache: {filepath}")
    except Exception as e:
        logger.error(f"Error saving to cache: {str(e)}")

def load_from_cache(filename: str) -> Any:
    """Load data from cache file."""
    try:
        filepath = os.path.join(CACHE_DIR, filename)
        if os.path.exists(filepath):
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            logger.info(f"Data loaded from cache: {filepath}")
            return data
        return None
    except Exception as e:
        logger.error(f"Error loading from cache: {str(e)}")
        return None

def calculate_strength_scores(df, date):
    """
    Calculate strength scores for stocks based on their returns over different time periods.
    
    Args:
        df (pd.DataFrame): DataFrame containing stock data
        date (datetime.date): The date for which to calculate strength scores
        
    Returns:
        dict: Dictionary containing the date and list of top stocks with their metrics
    """
    # Filter data for the specified date range
    start_date = date - timedelta(days=180)  # 6 months
    filtered_data = df[(df['Date'] >= start_date) & (df['Date'] <= date)]
    
    logger.info(f"Using data from {start_date.strftime('%Y-%m-%d')} to {date.strftime('%Y-%m-%d')}")
    logger.info(f"Total records: {len(filtered_data)}")
    logger.info(f"Unique stocks: {len(filtered_data['Stock'].unique())}")

    try:
        # Create a results DataFrame
        results = pd.DataFrame()
        
        # Calculate performance metrics for each stock
        for stock in filtered_data['Stock'].unique():
            stock_data = filtered_data[filtered_data['Stock'] == stock].sort_values('Date')
            
            if len(stock_data) < 20:  # Need at least 20 days for moving averages
                continue
                
            # Get the latest price
            latest_price = stock_data.iloc[-1]['Close']
            
            # Calculate returns for different periods
            try:
                # 1-month return
                one_month_ago = date - timedelta(days=30)
                one_month_data = stock_data[stock_data['Date'] >= one_month_ago]
                if len(one_month_data) > 0:
                    one_month_return = (latest_price / one_month_data.iloc[0]['Close'] - 1) * 100
                else:
                    one_month_return = 0
                    
                # 3-month return
                three_months_ago = date - timedelta(days=90)
                three_month_data = stock_data[stock_data['Date'] >= three_months_ago]
                if len(three_month_data) > 0:
                    three_month_return = (latest_price / three_month_data.iloc[0]['Close'] - 1) * 100
                else:
                    three_month_return = 0
                    
                # 6-month return
                six_months_ago = date - timedelta(days=180)
                six_month_data = stock_data[stock_data['Date'] >= six_months_ago]
                if len(six_month_data) > 0:
                    six_month_return = (latest_price / six_month_data.iloc[0]['Close'] - 1) * 100
                else:
                    six_month_return = 0
                
                # Calculate moving averages and liquidity
                ma_20 = stock_data['Close'].rolling(20).mean().iloc[-1]
                mav_20 = stock_data['Volume'].rolling(20).mean().iloc[-1]
                liquidity = ma_20 * mav_20
                
                # Calculate weighted strength score
                strength_score = (one_month_return * 0.5) + (three_month_return * 0.3) + (six_month_return * 0.2)
                
                # Add to results
                results = pd.concat([results, pd.DataFrame({
                    'Stock': [stock],
                    '1M_Return': [one_month_return],
                    '3M_Return': [three_month_return],
                    '6M_Return': [six_month_return],
                    'Strength_Score': [strength_score],
                    'Latest_Price': [latest_price],
                    '20_MA': [ma_20],
                    '20_MAV': [mav_20],
                    'Liquidity': [liquidity]
                })])
                
            except Exception as e:
                logger.error(f"Error calculating returns for {stock}: {str(e)}")
                continue
        
        # Normalize scores to 100
        def normalize_to_100(series):
            min_val = series.min()
            max_val = series.max()
            if max_val == min_val:
                return series * 0  # Return zeros if all values are the same
            return ((series - min_val) / (max_val - min_val) * 100).apply(np.ceil)
        
        # Normalize all return columns and strength score
        results['1M_Return_Normalized'] = normalize_to_100(results['1M_Return'])
        results['3M_Return_Normalized'] = normalize_to_100(results['3M_Return'])
        results['6M_Return_Normalized'] = normalize_to_100(results['6M_Return'])
        results['Strength_Score_Normalized'] = normalize_to_100(results['Strength_Score'])
        
        # Filter stocks with liquidity >= 10,000,000
        results = results[results['Liquidity'] >= 10000000]
        
        # Sort by normalized strength score and take top 50
        results = results.sort_values('Strength_Score_Normalized', ascending=False).head(50)
        
        # Add rank
        results['Rank'] = range(1, len(results) + 1)
        
        # Format all numeric columns to 2 decimal places
        numeric_columns = ['Latest_Price', '1M_Return_Normalized', '3M_Return_Normalized', 
                          '6M_Return_Normalized', 'Strength_Score_Normalized', 
                          '20_MA', '20_MAV', 'Liquidity']
        
        for col in numeric_columns:
            results[col] = results[col].round(2)
        
        # Prepare the response
        result = {
            "date": date.strftime("%Y-%m-%d"),
            "stocks": []
        }
        
        for _, stock in results.iterrows():
            result["stocks"].append({
                "Stock": stock['Stock'],
                "Rank": stock['Rank'],
                "Latest_Price": stock['Latest_Price'],
                "1M_Return_Normalized": stock['1M_Return_Normalized'],
                "3M_Return_Normalized": stock['3M_Return_Normalized'],
                "6M_Return_Normalized": stock['6M_Return_Normalized'],
                "Strength_Score_Normalized": stock['Strength_Score_Normalized'],
                "20_MA": stock['20_MA'],
                "20_MAV": stock['20_MAV'],
                "Liquidity": stock['Liquidity']
            })
            
        return result
    except Exception as e:
        logger.error(f"Error calculating strength scores: {e}")
        return {"error": "An error occurred while calculating strength scores"}

@app.get("/api/stock-data")
async def get_stock_data():
    try:
        # Get today's date
        today = datetime.now().date()
        logger.info(f"Today's date: {today}")

        # Check cache first
        cached_data = load_from_cache(f"{today}.pkl")
        if cached_data:
            logger.info("Using cached data")
            return cached_data

        # Read historical data
        logger.info(f"Looking for CSV file at: {HISTORICAL_DATA_PATH}")
        logger.info("Reading CSV file...")
        try:
            df = pd.read_csv(HISTORICAL_DATA_PATH)
            logger.info(f"CSV loaded with {len(df)} rows")
        except FileNotFoundError:
            logger.error(f"File not found at: {HISTORICAL_DATA_PATH}")
            raise HTTPException(status_code=500, detail=f"Historical data file not found at {HISTORICAL_DATA_PATH}")
        except Exception as e:
            logger.error(f"Error reading CSV file: {e}")
            raise HTTPException(status_code=500, detail=str(e))

        # Convert Date column to date only (no timezone)
        df['Date'] = pd.to_datetime(df['Date']).dt.date

        # Get the latest date in the data (up to today)
        latest_date = df['Date'].max()
        if latest_date > today:
            latest_date = today
        logger.info(f"Latest available date in data (up to today): {latest_date}")

        # Calculate strength scores using the helper function
        result = calculate_strength_scores(df, latest_date)
        
        # Save to cache
        save_to_cache(f"{today}.pkl", result)
        
        return result

    except Exception as e:
        logger.error(f"Error in get_stock_data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/run-backtest")
async def run_backtest(date: str):
    try:
        # Parse the date
        backtest_date = datetime.strptime(date, '%Y-%m-%d').date()
        logger.info(f"Running backtest for date: {backtest_date}")
        
        # Check if the date is in the future
        today = datetime.now(IST).date()
        if backtest_date > today:
            error_msg = f"Cannot backtest future dates. Selected date: {backtest_date}, Today: {today}"
            logger.error(error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Check cache first
        cached_data = load_from_cache(f"{backtest_date}.pkl")
        if cached_data:
            logger.info("Using cached backtest data")
            return cached_data
        
        # Read historical data
        logger.info(f"Reading CSV file for backtest: {HISTORICAL_DATA_PATH}")
        
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        # Convert Date column to date only (no timezone)
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        
        # Check if we have data for the requested date
        if backtest_date not in df['Date'].values:
            error_msg = f"No data available for the selected date: {backtest_date}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)
        
        # Calculate strength scores using the helper function
        result = calculate_strength_scores(df, backtest_date)
        
        # Save to cache
        save_to_cache(f"{backtest_date}.pkl", result)
        
        return result

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD format.")
    except Exception as e:
        logger.error(f"Error in run_backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-todays-data")
async def add_todays_data(file_path: str = HISTORICAL_DATA_PATH):
    """
    Add today's data to existing historical data file.
    If data for today already exists, it will be overwritten with the latest data.
    
    Args:
        file_path (str): Path to the existing data file
        
    Returns:
        dict: Status message
    """
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
            
        # Read existing data
        df = read_historical_data(file_path)
        if df is None:
            raise HTTPException(status_code=500, detail="Failed to read existing data")
            
        # Get today's date in IST
        today = datetime.now(IST).date()
        
        # Remove existing data for today if it exists
        df = df[df['Date'].dt.date != today]
        
        # Fetch today's data
        fetch_all_stocks_data(file_path, days=1, append=True)
        
        return {
            "status": "success",
            "message": "Successfully updated today's data"
        }
    except Exception as e:
        logger.error(f"Error adding today's data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/load-historical-data")
async def load_historical_data(days: int):
    """
    Load historical data for specified number of days.
    
    Args:
        days (int): Number of days of historical data to fetch
        
    Returns:
        dict: Status message and file path
    """
    try:
        # Clear existing data and fetch new data
        clear_historical_data(HISTORICAL_DATA_PATH)
        fetch_all_stocks_data(HISTORICAL_DATA_PATH, days=days)
        
        return {
            "status": "success",
            "message": f"Successfully loaded {days} days of historical data",
            "file_path": HISTORICAL_DATA_PATH
        }
    except Exception as e:
        logger.error(f"Error loading historical data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def refresh_daily_data():
    """
    Scheduled job to refresh daily data at 8 PM IST.
    """
    try:
        # Get current date in IST
        current_time = datetime.now(IST)
        logger.info(f"Running daily data refresh at {current_time}")
        
        # Add today's data
        add_todays_data(HISTORICAL_DATA_PATH)
        logger.info(f"Daily data refresh completed at {current_time}")
    except Exception as e:
        logger.error(f"Error in daily data refresh: {str(e)}")

# Schedule daily data refresh at 8 PM IST
scheduler.add_job(
    refresh_daily_data,
    trigger=CronTrigger(hour=20, minute=0, timezone=IST),
    id='daily_data_refresh',
    name='Refresh daily stock data',
    replace_existing=True
)

# Start the scheduler
scheduler.start()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 