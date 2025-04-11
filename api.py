from fastapi import FastAPI, HTTPException
from datetime import datetime, timedelta
import pandas as pd
import os
from data_fetcher import read_historical_data, clear_historical_data, fetch_all_stocks_data
from backtester import calculate_strength_scores
import pytz
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

app = FastAPI(title="Stock Analysis API",
             description="API for stock data management and analysis",
             version="1.0.0")

# Configuration
IST = pytz.timezone('Asia/Kolkata')
DEFAULT_DATA_FILE = '/Users/kunalsaxena/stocks/stock_data/historical_data.csv'

# Initialize scheduler
scheduler = BackgroundScheduler()

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
        # Generate filename with current date
        current_date = datetime.now(IST).strftime("%Y%m%d")
        data_file = f'/Users/kunalsaxena/stocks/stock_data/historical_data_{current_date}.csv'
        
        # Clear existing data and fetch new data
        clear_historical_data(data_file)
        fetch_all_stocks_data(data_file, days=days)
        
        return {
            "status": "success",
            "message": f"Successfully loaded {days} days of historical data",
            "file_path": data_file
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/add-todays-data")
async def add_todays_data(file_path: str):
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/run-backtest")
async def run_backtest(date: str):
    """
    Run backtest for a specific date.
    
    Args:
        date (str): Date in YYYY-MM-DD format
        
    Returns:
        dict: Backtest results
    """
    try:
        # Convert input date to datetime
        input_date = pd.to_datetime(date)
        
        # Read historical data
        df = read_historical_data(DEFAULT_DATA_FILE)
        if df is None:
            raise HTTPException(status_code=500, detail="Failed to read historical data")
            
        # Calculate strength scores
        results = calculate_strength_scores(df, input_date)
        
        # Convert results to dict
        results_dict = results.to_dict(orient='records')
        
        return {
            "status": "success",
            "date": date,
            "results": results_dict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def refresh_daily_data():
    """
    Scheduled job to refresh daily data at 8 PM IST.
    """
    try:
        # Get current date in IST
        current_time = datetime.now(IST)
        print(f"Running daily data refresh at {current_time}")
        
        # Add today's data
        add_todays_data(DEFAULT_DATA_FILE)
        print(f"Daily data refresh completed at {current_time}")
    except Exception as e:
        print(f"Error in daily data refresh: {str(e)}")

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