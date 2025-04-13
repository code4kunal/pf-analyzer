@app.get("/api/analytics/price-trends")
async def get_price_trends(date: str, stocks: str):
    """Get price trends for specified stocks from the backtest date to today with 5-day intervals."""
    try:
        # Parse the input parameters
        start_date = datetime.strptime(date, "%Y-%m-%d").date()
        end_date = datetime.now().date()
        stock_list = stocks.split(',')
        
        logger.info(f"Requested date range: {start_date} to {end_date}")
        logger.info(f"Requested stocks: {stock_list}")
        
        # Read historical data
        df = read_historical_data(HISTORICAL_DATA_PATH)
        if df is None or df.empty:
            logger.error("No historical data available")
            raise HTTPException(status_code=404, detail="No historical data available")
            
        # Convert Date column to date type
        df['Date'] = pd.to_datetime(df['Date']).dt.date
            
        logger.info(f"Data loaded successfully. Date range: {df['Date'].min()} to {df['Date'].max()}")
        logger.info(f"Available stocks: {df['Stock'].unique().tolist()}")
            
        # Filter data for the specified stocks and date range
        filtered_data = df[
            (df['Stock'].isin(stock_list)) & 
            (df['Date'] >= start_date) & 
            (df['Date'] <= end_date)
        ]
        
        if filtered_data.empty:
            logger.error(f"No data found for stocks: {stock_list} and date range: {start_date} to {end_date}")
            raise HTTPException(status_code=404, detail="No data found for the specified stocks and date range")
            
        logger.info(f"Found {len(filtered_data)} records for the specified criteria")
            
        # Create a list of dates with 5-day intervals
        all_dates = []
        current_date = start_date
        while current_date <= end_date:
            all_dates.append(current_date)
            current_date += timedelta(days=5)
        
        # Prepare data for chart
        chart_data = {
            'labels': [d.strftime('%Y-%m-%d') for d in all_dates],
            'datasets': []
        }
        
        # Create a dataset for each stock
        for stock in stock_list:
            stock_data = filtered_data[filtered_data['Stock'] == stock].sort_values('Date')
            if not stock_data.empty:
                # Create a complete series with 5-day intervals
                price_series = []
                last_available_price = None
                
                for date in all_dates:
                    # Find the closest date in the data (within 2 days)
                    date_data = stock_data[
                        (stock_data['Date'] >= date - timedelta(days=2)) & 
                        (stock_data['Date'] <= date + timedelta(days=2))
                    ]
                    
                    if not date_data.empty:
                        # Use the closest date's closing price
                        closest_date = date_data.iloc[0]['Date']
                        closest_price = date_data[date_data['Date'] == closest_date].iloc[0]['Close']
                        price_series.append(closest_price)
                        last_available_price = closest_price
                    else:
                        # If no data found, use the last available price
                        if last_available_price is not None:
                            price_series.append(last_available_price)
                            logger.info(f"Using last available price {last_available_price} for {stock} on {date}")
                        else:
                            # If this is the first date and no data is available, use the first available price
                            future_data = stock_data[stock_data['Date'] > date]
                            if not future_data.empty:
                                first_future_price = future_data.iloc[0]['Close']
                                price_series.append(first_future_price)
                                last_available_price = first_future_price
                                logger.info(f"Using first future price {first_future_price} for {stock} on {date}")
                            else:
                                price_series.append(None)
                                logger.warning(f"No data available for {stock} on {date} and no future data found")
                
                chart_data['datasets'].append({
                    'label': stock,
                    'data': price_series,
                    'borderColor': f'rgb({np.random.randint(0, 255)}, {np.random.randint(0, 255)}, {np.random.randint(0, 255)})',
                    'tension': 0.1,
                    'spanGaps': True  # This allows the line to continue through missing data points
                })
            else:
                logger.warning(f"No data found for stock: {stock}")
        
        return chart_data
        
    except ValueError as e:
        logger.error(f"Invalid date format: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        logger.error(f"Error in get_price_trends: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/sector-data")
async def get_sector_data(date: str, industries: str):