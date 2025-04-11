from nsetools import Nse
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

nse = Nse()

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
        pandas.DataFrame: DataFrame containing Date, Open, Close, Volume, and Stock columns
    """
    try:
        # Read the CSV file
        df = pd.read_csv(file_path)
        
        # Select and rename columns
        df = df[['Date', 'Open', 'Close', 'Volume', 'Stock']]
        
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

def fetch_all_stocks_data(output_file, days=730):
    """Fetch historical data for all stocks and save to a file.
    
    Args:
        output_file (str): Path to save the output CSV file
        days (int): Number of days of historical data to fetch (default: 730)
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
            # Append to the main DataFrame
            all_data = pd.concat([all_data, hist_data])
            # Save intermediate results every 50 stocks
            if i % 50 == 0:
                temp_filename = f'stock_data/historical_data_intermediate_{i}.csv'
                all_data.to_csv(temp_filename)
                print(f"Saved intermediate results to {temp_filename}")
    
    # Save final data to CSV
    if not all_data.empty:
        all_data.to_csv(output_file)
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
        empty_df = pd.DataFrame(columns=['Date', 'Open', 'Close', 'Volume', 'Stock'])
        
        # Save the empty DataFrame to the file
        empty_df.to_csv(file_path, index=False)
        print(f"Successfully cleared data in {file_path}")
    except Exception as e:
        print(f"Error clearing file {file_path}: {str(e)}")

if __name__ == "__main__":
    # Example usage
    output_file = '/Users/kunalsaxena/stocks/stock_data/historical_data_20250410.csv'
    clear_historical_data(output_file)
    fetch_all_stocks_data(output_file, days=730) 