# Environment Configuration

## How It Works

Your application is **already configured** to work in both local development and production (Railway).

The `config.py` setup automatically:
- ✅ Reads environment variables first (Railway)
- ✅ Falls back to `.env` file (local development)
- ✅ Uses sensible defaults as last resort

**No conflicts** - Railway environment variables take priority over local `.env` file.

---

## Local Development

### Setup (One-time)

```bash
# Copy template
cp .env.example .env

# Edit .env with your local settings
nano .env
```

### Your `.env` File

```bash
# Database (local PostgreSQL)
DATABASE_URL=postgresql://localhost/growfolio

# Security (dev key is fine for local)
SECRET_KEY=dev-secret-key-for-local-testing

# App Settings
DEBUG=True
ENVIRONMENT=development
PORT=8000
FRONTEND_URL=http://localhost:8000

# Email (optional - for testing invitations)
SMTP_USERNAME=help@grow-folio.in
SMTP_PASSWORD=your-gmail-app-password
```

### Run

```bash
uvicorn main:app --reload
```

Visit: `http://localhost:8000`

---

## Production (Railway)

Railway uses **environment variables** set in the dashboard (NOT a .env file).

### Required Variables

Set these in Railway Dashboard → Variables:

```bash
# REQUIRED
SECRET_KEY=<generate-secure-key>
FRONTEND_URL=https://cms.grow-folio.in
DEBUG=False
ENVIRONMENT=production

# OPTIONAL (for emails)
SMTP_USERNAME=help@grow-folio.in
SMTP_PASSWORD=<gmail-app-password>

# AUTO-SET by Railway
DATABASE_URL=<postgresql-connection-string>
```

### Generate Secure SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and paste as `SECRET_KEY` in Railway.

---

## How Priority Works

When the app looks for `SECRET_KEY`:

1. **Environment variable** (Railway dashboard or system env)
2. **`.env` file** (local development)
3. **Default value** (from config.py)

Example:
- **On Railway:** Uses `SECRET_KEY` from Railway dashboard
- **On your laptop:** Uses `SECRET_KEY` from `.env` file
- **No conflict!**

---

## Verification

### Local Development
```bash
# Check .env exists
ls .env

# Run app
uvicorn main:app --reload

# Should show: Running on http://127.0.0.1:8000
```

### Production (Railway)
```bash
# Check variables are set
# Go to Railway Dashboard → Your Project → Variables

# Deploy
git push origin main

# Should deploy to: https://cms.grow-folio.in
```

---

## Important Notes

✅ **`.env` file:**
- Only for local development
- Already in `.gitignore`
- Never deployed to Railway

✅ **Railway:**
- Uses environment variables (dashboard)
- `DATABASE_URL` automatically set when you add PostgreSQL
- No `.env` file needed or used

✅ **No Conflicts:**
- Your setup was already correct!
- Environment variables take priority
- Each environment uses its own config

---

## Quick Reference

| Setting | Local | Production |
|---------|-------|------------|
| Configuration | `.env` file | Railway dashboard |
| Database | `postgresql://localhost/growfolio` | Auto-set by Railway |
| Debug | `True` | `False` |
| SECRET_KEY | Dev key (any string) | Secure random string |
| FRONTEND_URL | `http://localhost:8000` | `https://cms.grow-folio.in` |

---

## Troubleshooting

### Local: Can't connect to database
**Solution:** Check `.env` has correct `DATABASE_URL`

### Production: App not working
**Solution:** Check Railway Variables are set correctly

### Email not sending
**Solution:**
1. Use Gmail App Password (not account password)
2. Enable 2FA on Gmail first
3. Generate App Password in Google Account settings

---

**Need More Help?**
- Deployment: `DEPLOYMENT.md`
- Quick start: `QUICK_START.md`
