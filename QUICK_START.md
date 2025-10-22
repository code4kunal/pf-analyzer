# GrowFolio CMS - Quick Start Guide

## Configuration

- **Local:** Uses `.env` file (copy from `.env.example`)
- **Railway:** Uses environment variables (dashboard)
- Already configured to work in both environments!

---

## 🚀 Deploy to Railway (5 Steps)

### 1. Push to GitHub
```bash
git add .
git commit -m "Initial commit"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. "New Project" → "Deploy from GitHub"
3. Select your repository
4. Add PostgreSQL database (click "New" → "Database")

### 3. Set Environment Variables

In Railway dashboard → Your Project → Variables tab, add:

```bash
ENVIRONMENT=production
SECRET_KEY=<generate-with-command-below>
FRONTEND_URL=https://cms.grow-folio.in
DEBUG=False
SMTP_USERNAME=help@grow-folio.in
SMTP_PASSWORD=<your-gmail-app-password>
```

**Note:** `DATABASE_URL` is auto-set by Railway.

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 4. Custom Domain (Squarespace)

In Railway:
- Settings → Domains → "Add Custom Domain"
- Enter: `cms.grow-folio.in`
- Copy the CNAME value shown

In Squarespace DNS:
- Add CNAME record:
  - Host: `cms`
  - Points to: `your-app.railway.app` (from Railway)

Wait 15-30 minutes for DNS propagation.

### 5. Create Admin User

Connect to Railway PostgreSQL and run:
```sql
INSERT INTO users (email, full_name, hashed_password, role, is_active, is_temp_password)
VALUES (
    'admin@grow-folio.in',
    'Admin User',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5JBV/lC7BqVlm',
    'ADMIN',
    true,
    false
);
```

Password: `Growfolio@123` (change after first login!)

---

## ✅ Verification Checklist

- [ ] App deployed on Railway
- [ ] Database created and connected
- [ ] Environment variables set
- [ ] Custom domain configured in Railway
- [ ] CNAME added in Squarespace
- [ ] DNS propagated (check: whatsmydns.net)
- [ ] SSL certificate active (automatic)
- [ ] Admin user created
- [ ] Can login at https://cms.grow-folio.in
- [ ] Changed admin password

---

## 🔒 Authentication Flow

### All Pages Require Login
✅ **Implemented:** Pages automatically redirect to `/login` if not authenticated

### Root Path Behavior
✅ **Implemented:**
- `/` redirects to `/login` if not authenticated
- `/` redirects to `/dashboard` if authenticated

### User Invitation Flow
1. Admin goes to "Users" menu
2. Clicks "Invite User"
3. Fills form (name, email, role)
4. System generates secure temporary password
5. Admin copies credentials and shares with user
6. New user logs in with temporary password
7. **Forced to change password** on first login
8. User gains access based on role

---

## 📱 Domain Configuration Summary

### What You Need from Squarespace:

**DNS Settings for grow-folio.in:**

| Type  | Host | Value (from Railway)           | TTL  |
|-------|------|--------------------------------|------|
| CNAME | cms  | your-app.up.railway.app        | Auto |

**Example:**
- Go to Squarespace → Settings → Domains → grow-folio.in
- Click "Advanced Settings" → "DNS Settings"
- Add CNAME record pointing `cms` to your Railway URL

### What Railway Provides:

- Automatic HTTPS/SSL (via Let's Encrypt)
- Custom domain hosting
- Database (PostgreSQL)
- Auto-deploy on git push
- Environment variables
- Monitoring & logs

---

## 🎯 Key Features Implemented

### ✅ Authentication & Security
- Mandatory login on all pages
- JWT token-based authentication
- Secure password hashing (bcrypt)
- Forced password change for temp passwords
- 401 auto-redirect to login
- Admin-only routes protected

### ✅ User Management
- Role-based access (Admin/Employee)
- User invitation system
- Temporary password generation
- User activation/deactivation
- Admin-only invite feature

### ✅ Production-Ready
- Environment-based configuration
- CORS configured for production
- Debug mode disabled in production
- Custom domain support
- SSL/HTTPS automatic
- Database migrations ready

---

## 📂 Important Files

### Deployment Files
- `railway.json` - Railway configuration
- `Procfile` - Start command for Railway
- `runtime.txt` - Python version
- `.env.example` - Environment variables template
- `DEPLOYMENT.md` - Complete deployment guide

### Application Files
- `main.py` - FastAPI application
- `config.py` - Environment configuration
- `auth.py` - Authentication logic
- `models.py` - Database models
- `schemas.py` - API schemas

### Frontend Files
- `templates/auth/login.html` - Login page
- `templates/users/index.html` - User management
- `templates/components/base.html` - Base template (auth check)

---

## 🛠️ Commands You'll Need

### Generate Secure Keys
```bash
# SECRET_KEY for JWT
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Password hash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('YourPassword123'))"
```

### Check DNS Propagation
```bash
nslookup cms.grow-folio.in
# Or visit: https://www.whatsmydns.net
```

### Test SSL Certificate
```bash
curl -I https://cms.grow-folio.in
```

### View Logs (Railway CLI)
```bash
railway logs
```

---

## 🆘 Quick Troubleshooting

### Issue: Can't access cms.grow-folio.in
**Solution:**
1. Check DNS propagation (wait 30 mins)
2. Verify CNAME in Squarespace
3. Check Railway domain status
4. Clear browser cache

### Issue: Login not working
**Solution:**
1. Check SECRET_KEY is set in Railway
2. Verify admin user exists in database
3. Check browser console for errors
4. Verify DATABASE_URL is connected

### Issue: Email not sending
**Solution:**
1. Gmail: Enable 2FA and create App Password
2. Set SMTP_PASSWORD in Railway
3. Check logs for SMTP errors

---

## 📞 Support

**Documentation:**
- Full deployment guide: `DEPLOYMENT.md`
- Testing guide: `TESTING.md`
- API documentation: Visit `/docs` endpoint

**Resources:**
- Railway Docs: [docs.railway.app](https://docs.railway.app)
- Squarespace DNS: [support.squarespace.com](https://support.squarespace.com)

---

## 🎉 You're All Set!

Your GrowFolio CMS will be live at:
### https://cms.grow-folio.in

**Default Credentials:**
- Email: `admin@grow-folio.in`
- Password: `Growfolio@123`

**⚠️ Change password immediately after first login!**

---

**Need detailed instructions?** See `DEPLOYMENT.md`
