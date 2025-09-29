# Portfolio Analyzer

A comprehensive portfolio analysis tool with Zerodha Kite integration, built with FastAPI and vanilla JavaScript.

## Features

- **Portfolio Tracking**: Real-time portfolio monitoring with automatic Zerodha Kite sync
- **Performance Metrics**: XIRR, CAGR, Win Rate, Max Drawdown calculations
- **Trading Journal**: Document trades with entry/exit reasons, strategies, and learnings
- **Time-based Filters**: View performance for 1M, 3M, 6M, 1Y, or all-time periods
- **Daily Updates**: Automatic portfolio sync and performance calculations
- **Professional UI**: Clean, minimalist dark-themed interface
- **Free Deployment**: Configured for Railway, Render, or Heroku

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Authentication**: JWT
- **Integration**: Zerodha Kite Connect API
- **Deployment**: Railway/Render/Heroku ready

## Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd portfolio-analyzer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Run the application:
```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000` to access the application.

## Zerodha Kite Setup

1. Register for Kite Connect API at https://developers.kite.trade/
2. Get your API Key and Secret
3. Add them to your `.env` file
4. Use the Settings page to connect your Zerodha account

## Deployment

### Railway

1. Connect your GitHub repository to Railway
2. Railway will auto-detect the configuration
3. Add environment variables in Railway dashboard
4. Deploy!

### Render

1. Connect your GitHub repository to Render
2. Choose "Web Service"
3. Render will use `render.yaml` configuration
4. Add environment variables
5. Deploy!

### Heroku (Alternative)

1. Install Heroku CLI
2. Run:
```bash
heroku create your-app-name
heroku config:set SECRET_KEY=your-secret-key
git push heroku main
```

## API Endpoints

- `GET /`: Dashboard
- `GET /journal`: Trading Journal
- `GET /settings`: Settings

### REST API
- `POST /api/register`: Register new user
- `POST /api/login`: User login
- `GET /api/trades`: Get all trades
- `POST /api/trades`: Add new trade
- `GET /api/journal`: Get journal entries
- `POST /api/journal`: Add journal entry
- `GET /api/holdings`: Get current holdings
- `GET /api/performance`: Get performance metrics
- `GET /api/kite/sync`: Sync with Zerodha

## Database Schema

- **Users**: User accounts with Kite credentials
- **Trades**: Buy/sell transactions
- **JournalEntries**: Trade documentation and learnings
- **Holdings**: Current portfolio positions
- **PerformanceSnapshots**: Daily performance metrics

## Security

- Passwords are hashed using bcrypt
- JWT tokens for authentication
- Environment variables for sensitive data
- HTTPS recommended for production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

MIT License

## Support

For issues or questions, please create an issue on GitHub.