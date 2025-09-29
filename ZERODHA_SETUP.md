# Zerodha Kite Connect Setup Guide

## Step 1: Create Kite Connect App

1. Go to https://developers.kite.trade/
2. Sign up/Login with your Zerodha account
3. Create a new app
4. Choose app type: **Connect**
5. App name: `Portfolio Analyzer` (or any name you prefer)

## Step 2: Configure App URLs

In your Kite Connect app settings, set these URLs:

### For Local Development:
- **Redirect URL**: `http://127.0.0.1:8000/api/kite/callback`
- **Postback URL**: `http://127.0.0.1:8000/api/kite/postback`

### For Production:

#### Railway:
- **Redirect URL**: `https://your-app-name.up.railway.app/api/kite/callback`
- **Postback URL**: `https://your-app-name.up.railway.app/api/kite/postback`

#### Render:
- **Redirect URL**: `https://your-app-name.onrender.com/api/kite/callback`
- **Postback URL**: `https://your-app-name.onrender.com/api/kite/postback`

## Step 3: Get API Credentials

After creating the app, you'll receive:
- **API Key**: (32 character string)
- **API Secret**: (32 character string)

## Step 4: Configure Application

1. Copy `.env.example` to `.env`
2. Add your credentials:
```env
KITE_API_KEY=your_api_key_here
KITE_API_SECRET=your_api_secret_here
```

## Step 5: Connect Your Account

1. Run the application
2. Go to Settings page
3. Click "Connect to Kite"
4. You'll be redirected to Zerodha login
5. Enter your credentials and PIN
6. Approve the app access
7. You'll be redirected back to Settings with success message

## API Endpoints Explained

### `/api/kite/callback`
- **Purpose**: Handles the redirect after user logs in to Zerodha
- **Parameters**:
  - `request_token`: Token to exchange for access token
  - `status`: Success or cancelled
- **Flow**: Exchanges request token for access token and stores it

### `/api/kite/postback`
- **Purpose**: Receives real-time order updates from Zerodha
- **When triggered**: When you place/modify/cancel orders
- **Data received**: Order details, execution status, etc.

## Important Notes

1. **Access Token Validity**: Access token is valid for one day. You need to re-login daily.
2. **API Limits**:
   - 3 requests per second
   - 200 requests per minute
3. **Charges**: Kite Connect API has monthly charges (₹2000/month as of 2024)
4. **Testing**: Use Kite Connect sandbox for testing (free)

## Troubleshooting

### Error: "Token is invalid or has expired"
- Access token has expired
- Solution: Reconnect from Settings page

### Error: "Invalid API key or access token"
- Check if API key and secret are correct in `.env`
- Ensure app is active in Kite Connect dashboard

### Error: "Redirect URI mismatch"
- Ensure the redirect URL in Kite app exactly matches your application URL
- Check for http vs https
- Check for trailing slashes

### Cannot connect to Kite
1. Check if your Kite Connect app is active
2. Verify API credentials in `.env`
3. Ensure redirect URLs match exactly
4. Try clearing browser cookies and cache

## Security Best Practices

1. **Never commit `.env` file** to git
2. **Use environment variables** in production
3. **Enable HTTPS** in production
4. **Rotate API credentials** periodically
5. **Store access tokens securely** (encrypted in production)
6. **Implement rate limiting** to avoid API limits

## Production Deployment URLs

After deploying to Railway/Render, update your Kite Connect app with production URLs:

1. Go to https://developers.kite.trade/
2. Edit your app
3. Update Redirect and Postback URLs with your production domain
4. Save changes

The application will automatically use the correct URLs based on the HOST environment.