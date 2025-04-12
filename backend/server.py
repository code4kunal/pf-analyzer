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
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)

# Get the base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # Go up one level to get the root directory

# Cache directory
CACHE_DIR = os.path.join(BASE_DIR, 'backend', 'stock_data', 'cache')
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
    logger.info(f"Sample of filtered data:\n{filtered_data[['Stock', 'Date', 'Close', 'Volume']].head()}")

    try:
        # Create a results DataFrame
        results = pd.DataFrame()
        
        # Calculate performance metrics for each stock
        for stock in filtered_data['Stock'].unique():
            stock_data = filtered_data[filtered_data['Stock'] == stock].sort_values('Date')
            
            if len(stock_data) < 20:  # Need at least 20 days for moving averages
                logger.debug(f"Skipping {stock}: insufficient data points ({len(stock_data)})")
                continue
                
            # Get the latest price
            latest_price = stock_data.iloc[-1]['Close']
            logger.debug(f"Processing {stock}: Latest price = {latest_price}")
            
            # Calculate returns for different periods
            try:
                # 1-month return
                one_month_ago = date - timedelta(days=30)
                one_month_data = stock_data[stock_data['Date'] >= one_month_ago]
                if len(one_month_data) > 0:
                    one_month_return = (latest_price / one_month_data.iloc[0]['Close'] - 1) * 100
                    logger.debug(f"{stock} 1M return: {one_month_return}")
                else:
                    one_month_return = 0
                    logger.debug(f"{stock} 1M return: No data available")
                    
                # 3-month return
                three_months_ago = date - timedelta(days=90)
                three_month_data = stock_data[stock_data['Date'] >= three_months_ago]
                if len(three_month_data) > 0:
                    three_month_return = (latest_price / three_month_data.iloc[0]['Close'] - 1) * 100
                    logger.debug(f"{stock} 3M return: {three_month_return}")
                else:
                    three_month_return = 0
                    logger.debug(f"{stock} 3M return: No data available")
                    
                # 6-month return
                six_months_ago = date - timedelta(days=180)
                six_month_data = stock_data[stock_data['Date'] >= six_months_ago]
                if len(six_month_data) > 0:
                    six_month_return = (latest_price / six_month_data.iloc[0]['Close'] - 1) * 100
                    logger.debug(f"{stock} 6M return: {six_month_return}")
                else:
                    six_month_return = 0
                    logger.debug(f"{stock} 6M return: No data available")
                
                # Calculate moving averages and liquidity
                ma_20 = stock_data['Close'].rolling(20).mean().iloc[-1]
                mav_20 = stock_data['Volume'].rolling(20).mean().iloc[-1]
                liquidity = ma_20 * mav_20
                logger.debug(f"{stock} MA20: {ma_20}, MAV20: {mav_20}, Liquidity: {liquidity}")
                
                # Calculate weighted strength score
                strength_score = (one_month_return * 0.5) + (three_month_return * 0.3) + (six_month_return * 0.2)
                logger.debug(f"{stock} Strength score: {strength_score}")
                
                # Get industry and sector information
                industry = stock_data.iloc[-1]['Industry']
                sector = stock_data.iloc[-1]['Sector']
                logger.debug(f"{stock} Industry: {industry}, Sector: {sector}")
                
                # Check for NaN values before adding to results
                if pd.isna(ma_20) or pd.isna(mav_20) or pd.isna(liquidity) or pd.isna(strength_score):
                    logger.error(f"NaN values detected for {stock}: MA20={ma_20}, MAV20={mav_20}, Liquidity={liquidity}, Strength={strength_score}")
                    continue
                
                # Add to results
                results = pd.concat([results, pd.DataFrame({
                    'Stock': [stock],
                    'Latest_Price': [latest_price],
                    '1M_Return': [one_month_return],
                    '3M_Return': [three_month_return],
                    '6M_Return': [six_month_return],
                    'Strength_Score': [strength_score],
                    '20_MA': [ma_20],
                    '20_MAV': [mav_20],
                    'Liquidity': [liquidity],
                    'Industry': [industry],
                    'Sector': [sector]
                })])
                
            except Exception as e:
                logger.error(f"Error calculating metrics for {stock}: {str(e)}")
                continue
        
        if results.empty:
            logger.error("No valid results after processing")
            return None
            
        # Log results before normalization
        logger.info(f"Results before normalization:\n{results[['Stock', '1M_Return', '3M_Return', '6M_Return', 'Strength_Score']].head()}")
            
        # Normalize scores to 100
        def normalize_to_100(series):
            min_val = series.min()
            max_val = series.max()
            if max_val == min_val:
                logger.warning(f"All values are the same in series: {series.name}")
                return series * 0  # Return zeros if all values are the same
            normalized = ((series - min_val) / (max_val - min_val) * 100).apply(np.ceil)
            logger.debug(f"Normalized {series.name}: min={min_val}, max={max_val}, sample={normalized.head()}")
            return normalized
        
        # Normalize all return columns and strength score
        results['1M_Return_Normalized'] = normalize_to_100(results['1M_Return'])
        results['3M_Return_Normalized'] = normalize_to_100(results['3M_Return'])
        results['6M_Return_Normalized'] = normalize_to_100(results['6M_Return'])
        results['Strength_Score_Normalized'] = normalize_to_100(results['Strength_Score'])
        
        # Log results after normalization
        logger.info(f"Results after normalization:\n{results[['Stock', '1M_Return_Normalized', '3M_Return_Normalized', '6M_Return_Normalized', 'Strength_Score_Normalized']].head()}")
        
        # Sort by strength score and add rank
        results = results.sort_values('Strength_Score_Normalized', ascending=False)
        results['Rank'] = range(1, len(results) + 1)
        logger.debug(f"Final ranks sample:\n{results[['Stock', 'Rank', 'Strength_Score_Normalized']].head()}")
        
        # Filter for stocks with sufficient liquidity (e.g., > 10M)
        results = results[results['Liquidity'] >= 10000000]
        logger.info(f"After liquidity filter: {len(results)} stocks remaining")
        
        # Take top 50 stocks by strength score
        top_50_stocks = results.head(50).copy()
        logger.info(f"Top 50 stocks by strength score:\n{top_50_stocks[['Stock', 'Strength_Score_Normalized', 'Industry']]}")
        
        # Calculate industry metrics in top 50
        industry_metrics = {}
        for industry in top_50_stocks['Industry'].unique():
            industry_stocks = top_50_stocks[top_50_stocks['Industry'] == industry]
            count = len(industry_stocks)
            strength_sum = industry_stocks['Strength_Score_Normalized'].sum()
            avg_strength = strength_sum / count if count > 0 else 0
            industry_metrics[industry] = {
                'count': count,
                'strength_sum': strength_sum,
                'avg_strength': avg_strength,
                'stocks': industry_stocks['Stock'].tolist()
            }
            logger.info(f"\nIndustry: {industry}")
            logger.info(f"Count in top 50: {count}")
            logger.info(f"Total strength: {strength_sum:.2f}")
            logger.info(f"Average strength: {avg_strength:.2f}")
            logger.info(f"Stocks: {', '.join(industry_stocks['Stock'].tolist())}")
        
        # Sort industries first by count (descending), then by total strength (descending)
        sorted_industries = sorted(
            industry_metrics.items(),
            key=lambda x: (x[1]['count'], x[1]['strength_sum']),
            reverse=True
        )
        
        # Log the sorted industries
        logger.info("\nIndustries sorted by count and strength:")
        for i, (industry, metrics) in enumerate(sorted_industries, 1):
            logger.info(f"{i}. {industry}: {metrics['count']} stocks, total strength: {metrics['strength_sum']:.2f}, avg strength: {metrics['avg_strength']:.2f}")
            logger.info(f"   Stocks: {', '.join(metrics['stocks'])}")
        
        # Assign ranks based on the sorted order
        industry_ranks = {}
        current_rank = 1
        prev_metrics = None
        
        for industry, metrics in sorted_industries:
            # If this industry has different metrics than the previous one, increment the rank
            if prev_metrics and (prev_metrics['count'] != metrics['count'] or 
                               prev_metrics['strength_sum'] != metrics['strength_sum']):
                current_rank += 1
            
            industry_ranks[industry] = current_rank
            prev_metrics = metrics
            logger.info(f"Assigned rank {current_rank} to {industry} (count: {metrics['count']}, strength: {metrics['strength_sum']:.2f})")
        
        # Initialize Industry_Group column with 0
        results['Industry_Group'] = 0
        
        # Map the industry ranks back to the full results
        results['Industry_Rank'] = results['Industry'].map(industry_ranks)
        
        # Set industry rank and group to 0 for stocks not in top 50
        results.loc[results['Rank'] > 50, ['Industry_Rank', 'Industry_Group']] = 0
        
        # Log final rankings
        logger.info("\nFinal Industry Rankings:")
        for rank in sorted(set(industry_ranks.values())):
            industries = [ind for ind, r in industry_ranks.items() if r == rank]
            logger.info(f"Rank {rank}: {', '.join(industries)}")
            for industry in industries:
                metrics = industry_metrics[industry]
                logger.info(f"  {industry}: {metrics['count']} stocks, total strength: {metrics['strength_sum']:.2f}")
                logger.info(f"  Stocks: {', '.join(metrics['stocks'])}")
        
        # Convert to dictionary format
        stock_list = []
        
        # Read sector counts from JSON file
        try:
            with open('/Users/kunalsaxena/stocks/backend/stock_data/sector_count.json', 'r') as f:
                sector_counts = json.load(f)
        except Exception as e:
            logger.error(f"Error reading sector counts: {str(e)}")
            sector_counts = {}
        
        # Only process top 50 stocks
        top_50_results = results[results['Rank'] <= 50]
        
        for _, row in top_50_results.iterrows():
            try:
                # Convert all numeric values to float and check for infinite/NaN values
                stock_data = {
                    'Stock': row['Stock'],
                    'Rank': int(row['Rank']),
                    'Latest_Price': float(row['Latest_Price']),
                    '1M_Return_Normalized': float(row['1M_Return_Normalized']),
                    '3M_Return_Normalized': float(row['3M_Return_Normalized']),
                    '6M_Return_Normalized': float(row['6M_Return_Normalized']),
                    'Strength_Score_Normalized': float(row['Strength_Score_Normalized']),
                    'Industry': row['Industry'],
                    'Industry_Rank': int(row['Industry_Rank']),
                    'Industry_Group': int(sector_counts.get(row['Industry'], 0)),  # Get group size from sector_counts
                    'Liquidity': float(row['Liquidity'])
                }
                
                # Validate all numeric values
                for key, value in stock_data.items():
                    if isinstance(value, (int, float)):
                        if not np.isfinite(value):
                            logger.error(f"Invalid value found for {row['Stock']} - {key}: {value}")
                            raise ValueError(f"Invalid value in {key}")
                
                stock_list.append(stock_data)
            except Exception as e:
                logger.error(f"Error converting row to dict for {row['Stock']}: {str(e)}")
                logger.error(f"Problematic row data: {row.to_dict()}")
                continue
        
        if not stock_list:
            logger.error("No valid stock data after processing")
            return None
            
        return {
            'date': date.strftime('%Y-%m-%d'),
            'results': stock_list
        }
        
    except Exception as e:
        logger.error(f"Error in calculate_strength_scores: {str(e)}")
        return None

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
        
        if result is None:
            logger.error("No valid results from calculate_strength_scores")
            raise HTTPException(status_code=500, detail="Failed to calculate strength scores")
            
        # Only save to cache if we have valid results
        if result and 'results' in result and len(result['results']) > 0:
            save_to_cache(f"{today}.pkl", result)
        else:
            logger.error("Empty results from calculate_strength_scores")
            raise HTTPException(status_code=500, detail="No valid stock data available")
        
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
        
        if result is None:
            logger.error("No valid results from calculate_strength_scores")
            raise HTTPException(status_code=500, detail="Failed to calculate strength scores")
            
        # Only save to cache if we have valid results
        if result and 'results' in result and len(result['results']) > 0:
            save_to_cache(f"{backtest_date}.pkl", result)
        else:
            logger.error("Empty results from calculate_strength_scores")
            raise HTTPException(status_code=500, detail="No valid stock data available")
        
        return result

    except ValueError as e:
        logger.error(f"Invalid date format: {e}")
        raise HTTPException(status_code=400, detail="Invalid date format. Please use YYYY-MM-DD format.")
    except Exception as e:
        logger.error(f"Error in run_backtest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/add-todays-data")
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

@app.post("/api/load-historical-data")
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

@app.post("/api/refresh-data")
async def refresh_daily_data():
    """
    Scheduled job to refresh daily data at 8 PM IST.
    """
    try:
        # Get current date in IST
        current_time = datetime.now(IST)
        logger.info(f"Running daily data refresh at {current_time}")
        
        # Add today's data
        await add_todays_data(HISTORICAL_DATA_PATH)
        logger.info(f"Daily data refresh completed at {current_time}")
        
        return {
            "status": "success",
            "message": "Successfully refreshed daily data",
            "timestamp": current_time.isoformat()
        }
    except Exception as e:
        logger.error(f"Error in daily data refresh: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Schedule daily data refresh at 8 PM IST
scheduler.add_job(
    refresh_daily_data,
    trigger=CronTrigger(hour=20, minute=0, timezone=IST),
    id='daily_data_refresh',
    name='Refresh daily stock data',
    replace_existing=True
)

# Add these after the existing scheduler initialization
scheduler.configure(timezone=IST)

@app.get("/api/scheduler-status")
async def get_scheduler_status():
    """
    Get the status of the data refresh scheduler.
    """
    try:
        jobs = []
        for job in scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'timezone': str(job.trigger.timezone),
                'status': 'running' if scheduler.running else 'stopped'
            })
        
        return {
            "status": "success",
            "scheduler_running": scheduler.running,
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/pause")
async def pause_scheduler():
    """
    Pause the data refresh scheduler.
    """
    try:
        if scheduler.running:
            scheduler.pause()
            return {"status": "success", "message": "Scheduler paused successfully"}
        return {"status": "success", "message": "Scheduler is already paused"}
    except Exception as e:
        logger.error(f"Error pausing scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/resume")
async def resume_scheduler():
    """
    Resume the data refresh scheduler.
    """
    try:
        if not scheduler.running:
            scheduler.resume()
            return {"status": "success", "message": "Scheduler resumed successfully"}
        return {"status": "success", "message": "Scheduler is already running"}
    except Exception as e:
        logger.error(f"Error resuming scheduler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduler/reschedule")
async def reschedule_job(hour: int = 20, minute: int = 0):
    """
    Reschedule the data refresh job to run at a different time.
    
    Args:
        hour (int): Hour in 24-hour format (0-23)
        minute (int): Minute (0-59)
    """
    try:
        if not 0 <= hour <= 23:
            raise HTTPException(status_code=400, detail="Hour must be between 0 and 23")
        if not 0 <= minute <= 59:
            raise HTTPException(status_code=400, detail="Minute must be between 0 and 59")
            
        job = scheduler.get_job('daily_data_refresh')
        if job:
            job.reschedule(trigger=CronTrigger(hour=hour, minute=minute, timezone=IST))
            return {
                "status": "success",
                "message": f"Job rescheduled to run at {hour:02d}:{minute:02d} IST",
                "next_run": job.next_run_time.isoformat()
            }
        else:
            raise HTTPException(status_code=404, detail="Refresh job not found")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rescheduling job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Configure scheduler with error handling
try:
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started successfully")
except Exception as e:
    logger.error(f"Error starting scheduler: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 