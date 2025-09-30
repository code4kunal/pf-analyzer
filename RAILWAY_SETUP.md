# Railway PostgreSQL Setup Guide

This guide explains how to migrate from SQLite to PostgreSQL on Railway for persistent data storage.

## Why PostgreSQL?

Railway uses ephemeral storage, which means SQLite databases get erased on every deployment. PostgreSQL provides persistent storage that survives deployments.

## Setup Steps

### 1. Add PostgreSQL Service in Railway

1. Go to your Railway project dashboard
2. Click "Add Service" → "Database" → "PostgreSQL"
3. Railway will automatically create a PostgreSQL database and set the `DATABASE_URL` environment variable

### 2. Environment Variables

Railway automatically provides:
- `DATABASE_URL` - PostgreSQL connection string

Manually set these environment variables in Railway:
- `KITE_API_KEY` - Your Zerodha Kite API key
- `KITE_API_SECRET` - Your Zerodha Kite API secret
- `SECRET_KEY` - A secure secret key for JWT tokens

### 3. Deploy

The application will automatically:
- Detect the PostgreSQL `DATABASE_URL`
- Create all necessary database tables
- Initialize a default user on first startup

### 4. Verify Deployment

After deployment, check:
- Health endpoint: `https://your-app.railway.app/health`
- Portfolio analyzer: `https://your-app.railway.app/dashboard`

## Features

✅ **Persistent Data**: User accounts, trades, and portfolio data survive deployments
✅ **Automatic Initialization**: Default user created on first startup
✅ **Database Migration**: Seamless transition from SQLite to PostgreSQL
✅ **Connection Pooling**: Optimized for production workloads

## Local Development

For local development, the app continues to use SQLite:
```bash
# Local development uses SQLite
DATABASE_URL=sqlite:///./portfolio.db

# Production on Railway uses PostgreSQL automatically
DATABASE_URL=postgresql://user:password@host:port/database
```

## Database Schema

The application automatically creates these tables:
- `users` - User accounts and Kite credentials
- `trades` - Trading history and transactions
- `holdings` - Portfolio holdings
- `journal_entries` - Trading journal entries
- `performance_snapshots` - Portfolio performance history

## Troubleshooting

### Database Connection Issues
- Check that PostgreSQL service is running in Railway
- Verify `DATABASE_URL` environment variable is set
- Check application logs for connection errors

### Missing Data After Deployment
- This is expected when migrating from SQLite
- Re-authenticate with Kite Connect to sync current data
- Previous SQLite data is not automatically migrated

### User Authentication
- Default user is created automatically: `testuser`
- Use Kite Connect integration for portfolio sync
- No manual user creation needed in production