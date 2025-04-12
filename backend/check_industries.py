import pandas as pd
import os
import json

# Path to historical data
HISTORICAL_DATA_PATH = '/Users/kunalsaxena/stocks/backend/stock_data/historical_data.csv'
SECTOR_DATA_PATH = '/Users/kunalsaxena/stocks/backend/stock_data/sector_data.json'

def analyze_sectors():
    try:
        # Read the CSV file
        df = pd.read_csv(HISTORICAL_DATA_PATH)
        
        # Convert Sector column to string and handle NaN values
        df['Sector'] = df['Sector'].astype(str).replace('nan', 'Unknown')
        
        # Get unique stocks per sector
        sector_stocks = df.groupby('Sector')['Stock'].nunique().sort_values(ascending=False)
        
        # Print the results
        print("\nNumber of stocks per sector:")
        print("-" * 30)
        for sector, count in sector_stocks.items():
            print(f"{sector}: {count} stocks")
        
        # Save to JSON
        result = {
            "sector_counts": sector_stocks.to_dict(),
            "total_stocks": len(df['Stock'].unique()),
            "total_sectors": len(sector_stocks)
        }
        
        with open(SECTOR_DATA_PATH, 'w') as f:
            json.dump(result, f, indent=2)
        
        print(f"\nTotal number of stocks: {result['total_stocks']}")
        print(f"Total number of sectors: {result['total_sectors']}")
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    analyze_sectors() 