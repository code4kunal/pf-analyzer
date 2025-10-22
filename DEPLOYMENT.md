# GrowFolio CMS - Deployment Guide

Complete guide for deploying GrowFolio CMS to Railway with custom domain (cms.grow-folio.in)

## Configuration Note

Your app is already configured to work with Railway:
- **Local:** Uses `.env` file
- **Railway:** Uses environment variables (dashboard)
- **No conflicts:** Environment variables take priority

---

## Prerequisites

- Railway account ([railway.app](https://railway.app))
- GitHub account
- Domain purchased from Squarespace (grow-folio.in)
- Access to Squarespace DNS settings

---

## Part 1: Railway Deployment

### Step 1: Create New Project on Railway

1. Go to [railway.app](https://railway.app) and login
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Connect your GitHub account if not already connected
5. Select the `pf-analyzer` repository

### Step 2: Add PostgreSQL Database

1. In your Railway project, click "New" → "Database" → "PostgreSQL"
2. Railway will automatically create a PostgreSQL database
3. The `DATABASE_URL` environment variable will be automatically set

### Step 3: Configure Environment Variables

In Railway project settings, go to "Variables" tab and add:

```bash
# Environment - Tells app it's in production
ENVIRONMENT=production

# Required - Generate a secure random string (see command below)
SECRET_KEY=your-super-secret-key-minimum-32-characters-long

# Frontend URL (your custom domain)
FRONTEND_URL=https://cms.grow-folio.in

# Debug mode - MUST be False in production
DEBUG=False

# Email Configuration (Optional - for invitation emails)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=help@grow-folio.in
SMTP_PASSWORD=your-gmail-app-password
SMTP_FROM_EMAIL=help@grow-folio.in
SMTP_FROM_NAME=GrowFolio

# Google API (Optional - for calendar integration)
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=https://cms.grow-folio.in/auth/google/callback

# Storage (Optional)
STORAGE_TYPE=local
UPLOAD_DIR=/app/uploads
```

**Important:** Generate a secure SECRET_KEY using:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Deploy

1. Railway will automatically deploy after pushing to GitHub
2. Wait for deployment to complete (usually 2-3 minutes)
3. You'll get a temporary Railway URL like: `https://your-app.railway.app`

### Step 5: Initialize Database

1. Once deployed, go to Railway project → "Settings" → "Database"
2. Click "Connect" to get database connection details
3. Run database migrations (if using Alembic):
   ```bash
   # In Railway shell or locally with production DATABASE_URL
   alembic upgrade head
   ```

4. **Create Admin User** (Important!)

   Connect to your Railway PostgreSQL database and run:
   ```sql
   INSERT INTO users (
       email,
       full_name,
       hashed_password,
       role,
       is_active,
       is_temp_password
   ) VALUES (
       'admin@grow-folio.in',
       'Admin User',
       -- Password: Growfolio@123 (change after first login!)
       '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5JBV/lC7BqVlm',
       'ADMIN',
       true,
       false
   );
   ```

   **Or use Python script:**
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
   print(pwd_context.hash("Growfolio@123"))
   ```

---

## Part 2: Custom Domain Setup (Squarespace DNS)

### Step 1: Get Railway Domain Info

1. In Railway project → "Settings" → "Domains"
2. Click "Generate Domain" if not already generated
3. Click "Add Custom Domain"
4. Enter: `cms.grow-folio.in`
5. Railway will show you DNS records to add

Railway will provide:
- **CNAME Record:** `cms.grow-folio.in` → `your-app.railway.app`

### Step 2: Configure Squarespace DNS

1. Login to Squarespace
2. Go to "Settings" → "Domains" → "grow-folio.in"
3. Click "Advanced Settings" → "DNS Settings"

4. Add the following DNS record:

| Type  | Host | Value                     | TTL  |
|-------|------|---------------------------|------|
| CNAME | cms  | your-app.railway.app      | Auto |

**Example:**
```
Type: CNAME
Host: cms
Points to: pf-analyzer-production.up.railway.app
TTL: Automatic
```

### Step 3: Wait for DNS Propagation

- DNS changes can take 5 minutes to 48 hours to propagate
- Usually takes 15-30 minutes
- Check propagation: [whatsmydns.net](https://www.whatsmydns.net)
  - Enter: `cms.grow-folio.in`
  - Select: CNAME
  - Should show your Railway URL

### Step 4: Verify Custom Domain in Railway

1. Go back to Railway → "Domains"
2. Your custom domain should show "Active" status
3. Railway automatically provisions SSL certificate (Let's Encrypt)
4. Your app is now accessible at: `https://cms.grow-folio.in`

---

## Part 3: Post-Deployment Configuration

### Step 1: Update Frontend URL

In Railway environment variables, update:
```bash
FRONTEND_URL=https://cms.grow-folio.in
```

Redeploy the application.

### Step 2: Test the Application

1. Visit: `https://cms.grow-folio.in`
2. Should redirect to login page
3. Login with admin credentials:
   - Email: `admin@grow-folio.in`
   - Password: `Growfolio@123` (or whatever you set)

### Step 3: Change Admin Password

1. After first login, immediately change the admin password
2. Go to user menu → "Change Password"
3. Set a strong, unique password

### Step 4: Create Additional Users

1. As admin, go to "Users" in sidebar
2. Click "Invite User"
3. Fill in details and select role (Admin/Employee)
4. System generates temporary password
5. Share credentials securely with the user
6. User must change password on first login

---

## Part 4: Email Configuration (Optional but Recommended)

### Gmail SMTP Setup

1. **Enable 2-Factor Authentication** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account → Security
   - Under "2-Step Verification", find "App passwords"
   - Select "Mail" and "Other (Custom name)"
   - Enter "GrowFolio CMS"
   - Copy the generated 16-character password

3. **Add to Railway Environment Variables:**
   ```bash
   SMTP_USERNAME=help@grow-folio.in
   SMTP_PASSWORD=your-16-char-app-password
   ```

4. Test by inviting a new user - they should receive an email

---

## Part 5: Monitoring & Maintenance

### View Logs

1. Railway Dashboard → Your Project → "Deployments"
2. Click on latest deployment
3. View real-time logs

### Monitor Database

1. Railway Dashboard → PostgreSQL service
2. View metrics (CPU, Memory, Storage)
3. Create backups regularly

### Database Backups

Railway doesn't auto-backup. Set up manual backups:

```bash
# Export database
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Restore database
psql $DATABASE_URL < backup_20240101.sql
```

**Recommended:** Use Railway's scheduled backups or external backup service.

---

## Part 6: Security Checklist

### Before Going Live

- [ ] Changed SECRET_KEY from default
- [ ] Changed admin password from default
- [ ] Set DEBUG=False in production
- [ ] Enabled HTTPS (automatic with Railway)
- [ ] Configured proper CORS origins
- [ ] Set up regular database backups
- [ ] Configured email notifications
- [ ] Tested all user flows
- [ ] Tested mobile responsiveness
- [ ] Set up monitoring/alerts

### Ongoing Security

- [ ] Regular security updates
- [ ] Monitor error logs
- [ ] Review user access periodically
- [ ] Rotate SECRET_KEY periodically
- [ ] Keep dependencies updated

---

## Part 7: Troubleshooting

### Issue: Site Not Loading

**Check:**
1. Railway deployment status (should be "Active")
2. DNS propagation (use whatsmydns.net)
3. SSL certificate status in Railway
4. Environment variables are set correctly

### Issue: Database Connection Error

**Check:**
1. DATABASE_URL is set in Railway
2. PostgreSQL service is running
3. Database has been initialized
4. Check logs for specific error

### Issue: Authentication Not Working

**Check:**
1. SECRET_KEY is set
2. Admin user exists in database
3. Password hash is correct
4. Check browser console for errors

### Issue: Custom Domain Not Working

**Check:**
1. CNAME record is correct in Squarespace
2. DNS has propagated (wait 30 mins)
3. Domain is verified in Railway
4. SSL certificate is issued (automatic)

---

## Part 8: Updating the Application

### Deploying New Changes

1. Push code to GitHub:
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

2. Railway automatically deploys:
   - Watches your GitHub repository
   - Auto-deploys on push to main branch
   - Usually takes 2-3 minutes

3. Monitor deployment in Railway dashboard

### Rolling Back

1. Railway Dashboard → "Deployments"
2. Click on previous successful deployment
3. Click "Redeploy"

---

## Part 9: Cost Estimation

### Railway Pricing (as of 2024)

**Free Tier:**
- $5 credit/month
- Suitable for development/testing
- May need to upgrade for production

**Pro Plan ($20/month):**
- $20 credit + $0.02/GB-hour for usage
- Includes:
  - PostgreSQL database
  - Web service
  - Custom domain
  - SSL certificate
  - Recommended for production

**Estimated Monthly Cost:**
- Small app (low traffic): $10-20
- Medium traffic: $20-40
- High traffic: $40-80

---

## Part 10: Support & Resources

### Railway Documentation
- [Railway Docs](https://docs.railway.app)
- [Railway Discord](https://discord.gg/railway)

### Application Help
- Check logs in Railway dashboard
- Review `TESTING.md` for running tests
- Check `README.md` for local development

### Emergency Contacts
- Admin: admin@grow-folio.in
- Support: help@grow-folio.in

---

## Quick Reference Commands

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate password hash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('password'))"

# Check DNS propagation
nslookup cms.grow-folio.in

# Test SSL certificate
curl -I https://cms.grow-folio.in

# View application logs (if using Railway CLI)
railway logs

# Connect to database (if using Railway CLI)
railway connect postgres
```

---

## Checklist: First Deployment

- [ ] Create Railway account
- [ ] Create new Railway project from GitHub
- [ ] Add PostgreSQL database
- [ ] Set all environment variables
- [ ] Deploy application
- [ ] Initialize database
- [ ] Create admin user
- [ ] Configure custom domain in Railway
- [ ] Add CNAME record in Squarespace
- [ ] Wait for DNS propagation
- [ ] Verify SSL certificate
- [ ] Test login at https://cms.grow-folio.in
- [ ] Change admin password
- [ ] Configure email (optional)
- [ ] Invite team members
- [ ] Set up monitoring

---

**Deployment Complete! 🚀**

Your GrowFolio CMS is now live at https://cms.grow-folio.in
