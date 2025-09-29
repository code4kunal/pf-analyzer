# Production Deployment Guide

## Option 1: Railway (Recommended - Easiest)

### Prerequisites
- GitHub account
- Railway account (free at https://railway.app)

### Steps

1. **Push code to GitHub**
```bash
git init
git add .
git commit -m "Initial commit - Portfolio Analyzer"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/portfolio-analyzer.git
git push -u origin main
```

2. **Deploy to Railway**
- Go to https://railway.app
- Click "New Project"
- Select "Deploy from GitHub repo"
- Connect your GitHub account
- Select your repository
- Railway will auto-detect the Python app

3. **Configure Environment Variables**
In Railway dashboard, go to Variables tab and add:
```
DATABASE_URL=sqlite:///./portfolio.db
SECRET_KEY=<click-generate-to-create-a-secure-key>
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
```

4. **Get your app URL**
- Go to Settings tab
- Under Domains, click "Generate Domain"
- You'll get a URL like: `portfolio-analyzer.up.railway.app`

5. **Update Zerodha Kite App**
- Go to https://developers.kite.trade/
- Update your app with:
  - Redirect URL: `https://your-app.up.railway.app/api/kite/callback`
  - Postback URL: `https://your-app.up.railway.app/api/kite/postback`

## Option 2: Render

### Steps

1. **Push code to GitHub** (same as above)

2. **Deploy to Render**
- Go to https://render.com
- Click "New +"
- Select "Web Service"
- Connect GitHub repository
- Configure:
  - Name: `portfolio-analyzer`
  - Environment: `Python 3`
  - Build Command: `pip install -r requirements.txt`
  - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

3. **Add Environment Variables**
```
DATABASE_URL=sqlite:///./portfolio.db
SECRET_KEY=your-secret-key-here
KITE_API_KEY=your_kite_api_key
KITE_API_SECRET=your_kite_api_secret
```

4. **Update Zerodha URLs**
- Use your Render URL: `https://portfolio-analyzer.onrender.com`

## Option 3: Replit (Alternative)

1. **Create new Repl**
- Go to https://replit.com
- Create new Python repl
- Upload all files

2. **Configure**
- Add secrets in Secrets tab
- Run the app

## Free Tier Limitations

### Railway
- $5 free credits per month
- Sleeps after inactivity
- Perfect for personal use

### Render
- Spins down after 15 min inactivity
- Limited build minutes
- Good for testing

### Recommendations
- **Railway** for personal portfolio tracking
- **Render** for testing
- Consider paid tier ($5-7/month) for always-on service

## Post-Deployment Checklist

- [ ] Test Zerodha connection
- [ ] Verify portfolio sync works
- [ ] Check performance metrics calculation
- [ ] Test journal entry creation
- [ ] Verify daily scheduler runs
- [ ] Set up monitoring (optional)

## Monitoring (Optional)

Add these free monitoring services:
- **UptimeRobot**: Monitor uptime
- **Sentry**: Error tracking (add to requirements.txt: `sentry-sdk[fastapi]`)

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Use strong passwords
- [ ] Enable HTTPS (automatic on Railway/Render)
- [ ] Don't commit .env file
- [ ] Regularly update dependencies

## Troubleshooting

### App crashes on startup
- Check logs in Railway/Render dashboard
- Verify all environment variables are set
- Check Python version compatibility

### Database issues
- For production, consider PostgreSQL (free on Railway)
- SQLite works fine for single-user

### Zerodha connection fails
- Verify redirect URLs match exactly
- Check API credentials
- Ensure app is active on Kite Connect

## Support

- Railway Discord: https://discord.gg/railway
- Render Community: https://community.render.com
- Create issue on GitHub for app-specific problems