import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
from data_fetcher import read_historical_data

def validate_date(df, input_date):
    """
    Validate if the input date and required historical data is available.
    
    Args:
        df (pandas.DataFrame): DataFrame containing historical data
        input_date (str): Input date in YYYY-MM-DD format
        
    Returns:
        tuple: (bool, DataFrame) - (True if validation passes and filtered DataFrame, False and None otherwise)
    """
    try:
        # Convert input date to timezone-naive datetime
        input_date = pd.to_datetime(input_date).tz_localize(None)
        six_months_ago = input_date - timedelta(days=180)
        
        # Ensure df['Date'] is timezone-naive
        if df['Date'].dt.tz is not None:
            df['Date'] = df['Date'].dt.tz_localize(None)
        
        # Get all available dates
        available_dates = df['Date'].unique()
        
        # Find the most recent date that's not in the future
        current_date = pd.Timestamp.now().tz_localize(None)
        valid_dates = available_dates[available_dates <= current_date]
        
        if len(valid_dates) == 0:
            print(f"Error: No historical data available")
            return False, None
            
        # Use the most recent available date
        most_recent_date = valid_dates.max()
        if most_recent_date < input_date:
            print(f"Using most recent available date: {most_recent_date.strftime('%Y-%m-%d')} instead of {input_date.strftime('%Y-%m-%d')}")
            input_date = most_recent_date
            six_months_ago = input_date - timedelta(days=180)
        
        # Filter data for the required period
        filtered_df = df[(df['Date'] >= six_months_ago) & (df['Date'] <= input_date)]
        
        if len(filtered_df) == 0:
            print(f"Error: No data available for the period {six_months_ago.strftime('%Y-%m-%d')} to {input_date.strftime('%Y-%m-%d')}")
            return False, None
            
        print(f"Using data from {filtered_df['Date'].min().strftime('%Y-%m-%d')} to {filtered_df['Date'].max().strftime('%Y-%m-%d')}")
        print(f"Total records: {len(filtered_df)}")
        
        # Get the column name for stock symbols
        symbol_column = 'Stock' if 'Stock' in filtered_df.columns else 'Symbol'
        print(f"Unique stocks: {filtered_df[symbol_column].nunique()}")
        
        return True, filtered_df
    except Exception as e:
        print(f"Error in date validation: {str(e)}")
        return False, None

def calculate_moving_averages(df, stock_data):
    """
    Calculate 20-day moving averages for price and volume.
    
    Args:
        df (pandas.DataFrame): Complete historical data
        stock_data (pandas.DataFrame): Data for a specific stock
        
    Returns:
        tuple: (20_MA, 20_MAV, liquidity)
    """
    # Calculate 20-day moving averages
    stock_data['20_MA'] = stock_data['Close'].rolling(window=20).mean()
    stock_data['20_MAV'] = stock_data['Volume'].rolling(window=20).mean()
    
    # Calculate liquidity
    stock_data['Liquidity'] = stock_data['20_MA'] * stock_data['20_MAV']
    
    # Get the latest values
    latest_ma = stock_data['20_MA'].iloc[-1]
    latest_mav = stock_data['20_MAV'].iloc[-1]
    latest_liquidity = stock_data['Liquidity'].iloc[-1]
    
    return latest_ma, latest_mav, latest_liquidity

def calculate_strength_scores(df, input_date):
    """
    Calculate strength scores for a specific date with additional metrics.
    
    Args:
        df (pandas.DataFrame): DataFrame containing historical data
        input_date (str): Date for which to calculate scores
        
    Returns:
        pandas.DataFrame: DataFrame with strength scores and additional metrics (top 50 only)
    """
    # Convert input date to timezone-aware datetime
    input_date = pd.to_datetime(input_date).tz_localize('Asia/Kolkata')
    
    # Calculate time periods
    one_month_ago = input_date - timedelta(days=30)
    three_months_ago = input_date - timedelta(days=90)
    six_months_ago = input_date - timedelta(days=180)
    
    # Create a results DataFrame
    results = pd.DataFrame()
    
    # Get the column name for stock symbols
    symbol_column = 'Stock' if 'Stock' in df.columns else 'Symbol'
    
    # Calculate performance metrics for each stock
    for stock in df[symbol_column].unique():
        stock_data = df[df[symbol_column] == stock].sort_values('Date')
        
        if len(stock_data) < 20:  # Need at least 20 days for moving averages
            continue
            
        # Get the latest price (at input date)
        latest_data = stock_data[stock_data['Date'].dt.date <= input_date.date()]
        if latest_data.empty:
            continue
        latest_price = latest_data.iloc[-1]['Close']
        
        # Calculate returns for different periods
        try:
            # 1-month return
            one_month_data = stock_data[stock_data['Date'].dt.date >= one_month_ago.date()]
            if len(one_month_data) > 0:
                one_month_return = (latest_price / one_month_data.iloc[0]['Close'] - 1) * 100
            else:
                one_month_return = 0
                
            # 3-month return
            three_month_data = stock_data[stock_data['Date'].dt.date >= three_months_ago.date()]
            if len(three_month_data) > 0:
                three_month_return = (latest_price / three_month_data.iloc[0]['Close'] - 1) * 100
            else:
                three_month_return = 0
                
            # 6-month return
            six_month_data = stock_data[stock_data['Date'].dt.date >= six_months_ago.date()]
            if len(six_month_data) > 0:
                six_month_return = (latest_price / six_month_data.iloc[0]['Close'] - 1) * 100
            else:
                six_month_return = 0
            
            # Calculate moving averages and liquidity
            ma_20, mav_20, liquidity = calculate_moving_averages(df, stock_data)
            
            # Calculate weighted strength score
            strength_score = (one_month_return * 0.5) + (three_month_return * 0.3) + (six_month_return * 0.2)
            
            # Add to results
            results = pd.concat([results, pd.DataFrame({
                symbol_column: [stock],
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
            print(f"Error calculating returns for {stock}: {str(e)}")
            continue
    
    # Normalize scores to 100
    def normalize_to_100(series):
        min_val = series.min()
        max_val = series.max()
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
    
    # Select and reorder columns
    final_columns = [
        symbol_column, 'Rank', 'Latest_Price',
        '1M_Return_Normalized', '3M_Return_Normalized', '6M_Return_Normalized',
        'Strength_Score_Normalized', '20_MA', '20_MAV', 'Liquidity'
    ]
    
    # Format all numeric columns to 2 decimal places
    numeric_columns = ['Latest_Price', '1M_Return_Normalized', '3M_Return_Normalized', 
                      '6M_Return_Normalized', 'Strength_Score_Normalized', 
                      '20_MA', '20_MAV', 'Liquidity']
    
    for col in numeric_columns:
        results[col] = results[col].round(2)
    
    return results[final_columns]

def main():
    # Test date (January 1, 2024)
    input_date = "2024-01-01"
    
    # File paths
    data_file = '/Users/kunalsaxena/stocks/stock_data/historical_data_20250410.csv'
    print(f"\nReading data from: {data_file}")
    
    # Read historical data
    df = read_historical_data(data_file)
    print(f"Data read successfully: {df is not None}")
    
    if df is not None:
        print(f"\nValidating date: {input_date}")
        # Validate input date and get filtered data
        is_valid, filtered_df = validate_date(df, input_date)
        print(f"Date validation result: {is_valid}")
        
        if not is_valid:
            return
            
        print("\nCalculating strength scores...")
        # Calculate strength scores using filtered data
        strength_scores = calculate_strength_scores(filtered_df, input_date)
        print(f"Strength scores calculated for {len(strength_scores)} stocks")
        
        # Create backtest directory if it doesn't exist
        os.makedirs('backtest', exist_ok=True)
        
        # Save results to CSV with date in filename
        output_file = f'backtest/strength_scores_{input_date}.csv'
        strength_scores.to_csv(output_file, index=False)
        print(f"\nStrength scores saved to {output_file}")
        
        # Print filtered stocks with their metrics
        print("\nFiltered Stocks (Liquidity >= 10,000,000):")
        print("=" * 120)
        print(f"{'Stock':<12} {'20_MA':<10} {'20_MAV':<15} {'Liquidity':<15}")
        print("-" * 120)
        
        for _, row in strength_scores.iterrows():
            print(f"{row['Stock']:<12} {row['20_MA']:<10.2f} {row['20_MAV']:<15.2f} {row['Liquidity']:<15.2f}")
        
        print("=" * 120)
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Average 1M Return: {strength_scores['1M_Return_Normalized'].mean():.2f}")
        print(f"Average 3M Return: {strength_scores['3M_Return_Normalized'].mean():.2f}")
        print(f"Average 6M Return: {strength_scores['6M_Return_Normalized'].mean():.2f}")
        print(f"Average Strength Score: {strength_scores['Strength_Score_Normalized'].mean():.2f}")
        print(f"Total Stocks Filtered: {len(strength_scores)}")

if __name__ == "__main__":
    main() 