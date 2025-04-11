import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from data_fetcher import read_historical_data, clear_historical_data, fetch_all_stocks_data

def calculate_strength_scores(df):
    """
    Calculate strength scores for all stocks with additional metrics.
    
    Args:
        df (pandas.DataFrame): DataFrame containing historical data
        
    Returns:
        pandas.DataFrame: DataFrame with strength scores and additional metrics (top 50 only)
    """
    # Create a results DataFrame
    results = pd.DataFrame()
    
    # Calculate performance metrics for each stock
    for stock in df['Stock'].unique():
        stock_data = df[df['Stock'] == stock].sort_values('Date')
        
        if len(stock_data) < 20:  # Need at least 20 days for moving averages
            continue
            
        # Get the latest price
        latest_price = stock_data.iloc[-1]['Close']
        
        # Calculate returns for different periods
        try:
            # 1-month return
            one_month_ago = stock_data['Date'].max() - timedelta(days=30)
            one_month_data = stock_data[stock_data['Date'] >= one_month_ago]
            if len(one_month_data) > 0:
                one_month_return = (latest_price / one_month_data.iloc[0]['Close'] - 1) * 100
            else:
                one_month_return = 0
                
            # 3-month return
            three_months_ago = stock_data['Date'].max() - timedelta(days=90)
            three_month_data = stock_data[stock_data['Date'] >= three_months_ago]
            if len(three_month_data) > 0:
                three_month_return = (latest_price / three_month_data.iloc[0]['Close'] - 1) * 100
            else:
                three_month_return = 0
                
            # 6-month return
            six_months_ago = stock_data['Date'].max() - timedelta(days=180)
            six_month_data = stock_data[stock_data['Date'] >= six_months_ago]
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
        'Stock', 'Rank', 'Latest_Price',
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
    # File paths
    data_file = '/Users/kunalsaxena/stocks/stock_data/historical_data_20250410.csv'
    scores_file = 'stock_data/strength_scores.csv'
    
    # Clear and fetch new data
    clear_historical_data(data_file)
    fetch_all_stocks_data(data_file, days=730)
    
    # Read the saved data and calculate strength scores
    df = read_historical_data(data_file)
    
    if df is not None:
        # Calculate strength scores
        strength_scores = calculate_strength_scores(df)
        
        # Save results to CSV
        strength_scores.to_csv(scores_file, index=False)
        print(f"\nStrength scores saved to {scores_file}")
        
        # Print top 30 stocks with pretty formatting
        print("\nTop 30 Stocks by Strength Score:")
        print("=" * 120)  # Header separator
        print(f"{'Index':<6} {'Stock':<12} {'Rank':<6} {'Price':<10} {'1M':<6} {'3M':<6} {'6M':<6} {'Score':<8}")
        print("-" * 120)  # Row separator
        
        # Print each row with formatted columns
        for idx, (_, row) in enumerate(strength_scores.head(30).iterrows(), 1):
            print(f"{idx:<6} {row['Stock']:<12} {row['Rank']:<6} {row['Latest_Price']:<10.2f} "
                  f"{row['1M_Return_Normalized']:<6.0f} {row['3M_Return_Normalized']:<6.0f} "
                  f"{row['6M_Return_Normalized']:<6.0f} {row['Strength_Score_Normalized']:<8.0f}")
        
        print("=" * 120)  # Footer separator
        
        # Print summary statistics
        print("\nSummary Statistics:")
        print(f"Average 1M Return: {strength_scores['1M_Return_Normalized'].mean():.2f}")
        print(f"Average 3M Return: {strength_scores['3M_Return_Normalized'].mean():.2f}")
        print(f"Average 6M Return: {strength_scores['6M_Return_Normalized'].mean():.2f}")
        print(f"Average Strength Score: {strength_scores['Strength_Score_Normalized'].mean():.2f}")

if __name__ == "__main__":
    main()