from nsetools import Nse
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os
import time

nse = Nse()

# Create stock_data directory if it doesn't exist
os.makedirs('stock_data', exist_ok=True)

def get_stock_info(stock_symbol):
    """Get industry and sector information for a stock.
    
    Args:
        stock_symbol (str): Stock symbol to fetch info for
    
    Returns:
        dict: Dictionary containing industry and sector information
    """
    try:
        # Add .NS suffix for NSE stocks in yfinance
        ticker = yf.Ticker(f"{stock_symbol}.NS")
        info = ticker.info
        
        return {
            'Industry': info.get('industry', 'Unknown'),
            'Sector': info.get('sector', 'Unknown')
        }
    except Exception as e:
        print(f"Error fetching info for {stock_symbol}: {str(e)}")
        return {
            'Industry': 'Unknown',
            'Sector': 'Unknown'
        }

def get_all_stocks():
    """Get all stock codes from NSE."""
    all_stocks = nse.get_stock_codes()
    return all_stocks

def get_historical_data(stock_symbol, days=730):
    """Fetch historical data for a given stock symbol.
    
    Args:
        stock_symbol (str): Stock symbol to fetch data for
        days (int): Number of days of historical data to fetch (default: 730)
    
    Returns:
        pandas.DataFrame: Historical data for the stock
    """
    try:
        # Add .NS suffix for NSE stocks in yfinance
        ticker = yf.Ticker(f"{stock_symbol}.NS")
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        hist = ticker.history(start=start_date, end=end_date)
        if not hist.empty:
            # Add stock symbol as a column
            hist['Stock'] = stock_symbol
            
            # Get industry and sector information
            stock_info = get_stock_info(stock_symbol)
            hist['Industry'] = stock_info['Industry']
            hist['Sector'] = stock_info['Sector']
            
            # Add Date column from the index and format it
            hist['Date'] = hist.index.strftime('%Y-%m-%d')
            
            # Ensure Volume and Close columns are included
            hist['Volume'] = hist['Volume']
            hist['Close'] = hist['Close']
            
            return hist
        return None
    except Exception as e:
        print(f"Error fetching data for {stock_symbol}: {str(e)}")
        return None

def read_historical_data(file_path):
    """
    Read historical data from CSV file and create a DataFrame with specific columns.
    
    Args:
        file_path (str): Path to the CSV file
        
    Returns:
        pandas.DataFrame: DataFrame containing Date, Open, Close, Volume, Stock, Industry, and Sector columns
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Select and rename columns
        df = df[['Date', 'Open', 'Close', 'Volume', 'Stock', 'Industry', 'Sector']]
        
        # Convert Date column to datetime
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Sort by Date and Stock
        df = df.sort_values(['Date', 'Stock'])
        
        print(f"Successfully read data from {file_path}")
        print(f"Total records: {len(df)}")
        print(f"Date range: {df['Date'].min()} to {df['Date'].max()}")
        print(f"Number of unique stocks: {df['Stock'].nunique()}")
        
        return df
    except Exception as e:
        print(f"Error reading file {file_path}: {str(e)}")
        return None

def fetch_all_stocks_data(output_file, days=730, append=False):
    """Fetch historical data for all stocks and save to a file.
    
    Args:
        output_file (str): Path to save the output CSV file
        days (int): Number of days of historical data to fetch (default: 730)
        append (bool): Whether to append to existing file (default: False)
    """
    # Get all stocks
    all_stocks = get_all_stocks()
    print(f"Total stocks found: {len(all_stocks)}")
    
    # Initialize an empty DataFrame to store all data
    all_data = pd.DataFrame()
    
    # Get historical data for each stock
    for i, symbol in enumerate(all_stocks, 1):
        print(f"\nFetching {days}-day data for {symbol} ({i}/{len(all_stocks)})")
        hist_data = get_historical_data(symbol, days=days)
        if hist_data is not None:
            # Add stock symbol as a column
            hist_data['Stock'] = symbol
            
            # Get industry and sector information
            stock_info = get_stock_info(symbol)
            hist_data['Industry'] = stock_info['Industry']
            hist_data['Sector'] = stock_info['Sector']
            
            # Add Date column from the index and format it
            hist_data['Date'] = hist_data.index.strftime('%Y-%m-%d')
            
            # Append to the main DataFrame
            all_data = pd.concat([all_data, hist_data])
            # Save intermediate results every 50 stocks
            if i % 50 == 0:
                temp_filename = f'stock_data/historical_data_intermediate_{i}.csv'
                all_data.to_csv(temp_filename, index=False)
                print(f"Saved intermediate results to {temp_filename}")
    
    # Save final data to CSV
    if not all_data.empty:
        if append and os.path.exists(output_file):
            # Read existing data and append new data
            existing_data = pd.read_csv(output_file)
            all_data = pd.concat([existing_data, all_data])
            # Remove duplicates based on Date and Stock
            all_data = all_data.drop_duplicates(subset=['Date', 'Stock'])
        
        # Ensure Date column is in the correct format
        all_data['Date'] = pd.to_datetime(all_data['Date']).dt.strftime('%Y-%m-%d')
        
        # Save to CSV with Date column
        all_data.to_csv(output_file, index=False)
        print(f"\nFinal data saved to {output_file}")
        print(f"Total records saved: {len(all_data)}")
        print(f"Total stocks processed: {len(all_stocks)}")
    else:
        print("No data was fetched successfully")

def clear_historical_data(file_path):
    """Clear the contents of the historical data file.
    
    Args:
        file_path (str): Path to the CSV file
    """
    try:
        # Create an empty DataFrame with the same columns
        empty_df = pd.DataFrame(columns=['Date', 'Open', 'Close', 'Volume', 'Stock', 'Industry', 'Sector'])
        
        # Save the empty DataFrame to the file
        empty_df.to_csv(file_path, index=False)
        print(f"Successfully cleared data in {file_path}")
    except Exception as e:
        print(f"Error clearing file {file_path}: {str(e)}")

if __name__ == "__main__":
    # Example usage
    output_file = os.path.join('stock_data', 'historical_data.csv')
    clear_historical_data(output_file)
    fetch_all_stocks_data(output_file, days=730) 