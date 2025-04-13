import pandas as pd
import os

# Read the CSV file
df = pd.read_csv('stock_data/historical_data.csv')

# Save as PKL
df.to_pickle('stock_data/historical_data.pkl')

# Print sizes
csv_size = os.path.getsize('stock_data/historical_data.csv')
pkl_size = os.path.getsize('stock_data/historical_data.pkl')

print(f"CSV size: {csv_size / (1024*1024):.2f} MB")
print(f"PKL size: {pkl_size / (1024*1024):.2f} MB")
print(f"Size reduction: {(1 - pkl_size/csv_size)*100:.2f}%") 