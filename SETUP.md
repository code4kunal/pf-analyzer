# GrowFolio CMS - Setup Guide

## 📋 Overview

GrowFolio CMS is a comprehensive customer management system for investment consultancy firms. This guide will help you set up and deploy the application.

## 🏗️ Architecture

- **Backend**: FastAPI (Python)
- **Database**: PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Deployment**: Railway (configured)
- **Authentication**: JWT with RBAC (Admin/Employee)
- **Integrations**: Google Meet, Gmail SMTP

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Google Workspace account (for email and meetings)

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd pf-analyzer

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

```bash
# Create PostgreSQL database
createdb growfolio

# Or using psql:
psql -U postgres
CREATE DATABASE growfolio;
\q
```

### 3. Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your actual values
# See "Environment Variables" section below
```

### 4. Initialize Database

```bash
# Reset database and create all tables
python reset_database.py

# This will:
# - Drop all old tables (if any)
# - Create new GrowFolio CMS tables
# - Create default admin user:
#   Email: admin@grow-folio.in
#   Password: Admin@123
```

### 5. Run the Application

```bash
# Development mode
uvicorn main:app --reload

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000
```

Visit: http://localhost:8000

## 🔐 Environment Variables

### Required Variables

#### Database
```bash
DATABASE_URL=postgresql://username:password@localhost/growfolio
```

#### Security
```bash
# Generate with: openssl rand -hex 32
SECRET_KEY=your-secret-key-here
```

#### Google SMTP (for sending emails)
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=help@grow-folio.in
SMTP_PASSWORD=your-app-specific-password
SMTP_FROM_EMAIL=help@grow-folio.in
SMTP_FROM_NAME=GrowFolio
```

**Setup Google App Password:**
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2-factor authentication if not already enabled
3. Generate an App Password for "Mail"
4. Use this password as `SMTP_PASSWORD`

#### Google Calendar API (for Google Meet)
```bash
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback
```

**Setup Google Calendar API:**
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable "Google Calendar API"
4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
5. Application type: "Web application"
6. Add authorized redirect URI: `http://localhost:8000/api/auth/google/callback`
7. Copy Client ID and Client Secret

### Optional Variables

#### AWS S3 (for scalable storage)
```bash
STORAGE_TYPE=s3
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_BUCKET=growfolio-documents
AWS_REGION=ap-south-1
```

## 🎯 Key Features

### 1. Customer Management
- Complete customer profiles with KYC details
- Financial profile and risk assessment
- Family members and nominees
- Document storage
- Search and filter capabilities

### 2. Investment Tracking
- Manual entry for all investment types
- Portfolio tracking and performance
- Returns calculation

### 3. Calendar & Events
- Global calendar view
- Event types: Seminars, 1-on-1, Group Calls, Reviews
- Google Meet integration
- Event reminders

### 4. Communication Hub
- Communication logs (calls, emails, meetings)
- Internal notes (public/private)
- Activity timeline

### 5. Commission & Billing
- Commission tracking
- Invoice generation
- Payment management

### 6. User Management
- Role-based access (Admin/Employee)
- Invite-based user creation
- Temporary password flow

### 7. Notifications
- In-app notifications
- Email reminders
- Birthday/anniversary alerts

### 8. Reports & Analytics
- Customer acquisition reports
- Revenue reports
- Investment performance
- Excel/PDF export

## 📦 Database Schema

### Core Tables
- `users` - Admin and employee accounts
- `customers` - Customer profiles
- `investments` - Investment tracking
- `events` - Calendar events
- `communications` - Communication logs
- `notes` - Internal notes
- `commissions` - Commission tracking
- `invoices` - Billing and invoices
- `documents` - Document management
- `notifications` - User notifications
- `activity_logs` - Activity timeline

### Support Tables
- `family_members` - Customer family info
- `nominees` - Investment nominees
- `event_participants` - Event-customer mapping

## 🚢 Deployment (Railway)

Railway is already configured for this project.

### 1. Connect Repository
1. Go to https://railway.app/
2. Connect your GitHub repository
3. Railway will auto-detect the configuration

### 2. Configure Environment Variables
In Railway dashboard, add these variables:
- `SECRET_KEY`
- `SMTP_USERNAME`
- `SMTP_PASSWORD`
- `GOOGLE_CLIENT_ID`
- `GOOGLE_CLIENT_SECRET`
- `GOOGLE_REDIRECT_URI` (update with your Railway URL)
- `FRONTEND_URL` (your Railway app URL)
- `DEBUG=False`

Note: Railway automatically provides `DATABASE_URL`

### 3. Initialize Database
```bash
# Connect to Railway project
railway link

# Run database reset
railway run python reset_database.py
```

### 4. Deploy
```bash
git push origin main
```

Railway will automatically deploy your app.

## 👥 Default Users

After running `reset_database.py`, you'll have:

**Admin User:**
- Email: `admin@grow-folio.in`
- Password: `Admin@123`
- Role: Admin

⚠️ **Important:** Change the default password immediately after first login!

## 🔒 Security Checklist

- [ ] Change default admin password
- [ ] Set strong `SECRET_KEY` in production
- [ ] Enable HTTPS in production
- [ ] Set `DEBUG=False` in production
- [ ] Use environment variables for all secrets
- [ ] Enable database backups
- [ ] Configure CORS properly
- [ ] Set up rate limiting
- [ ] Use strong password policies

## 📁 Project Structure

```
pf-analyzer/
├── models.py           # Database models
├── database.py         # Database connection
├── config.py          # Configuration settings
├── auth.py            # Authentication logic
├── schemas.py         # Pydantic schemas
├── main.py            # Main FastAPI application
├── reset_database.py  # Database initialization script
├── requirements.txt   # Python dependencies
├── .env.example       # Environment template
├── railway.toml       # Railway configuration
└── static/            # Frontend files
    ├── css/
    ├── js/
    └── index.html
```

## 🛠️ Development Workflow

### Phase 1: Foundation (Current)
✅ Database schema designed
✅ Models created
✅ Configuration setup
⏳ Authentication & user management
⏳ Basic API structure

### Phase 2: Customer Management
- Customer CRUD operations
- Search and filters
- Document upload

### Phase 3: Calendar & Events
- Calendar view
- Event management
- Google Meet integration

### Phase 4: Advanced Features
- Communication logs
- Commission tracking
- Notifications

### Phase 5: Reports & Polish
- Analytics dashboard
- Report generation
- UI refinements

## 🐛 Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL is running
pg_isready

# Check connection
psql -U postgres -d growfolio
```

### Google API Issues
- Ensure APIs are enabled in Google Cloud Console
- Check OAuth redirect URIs match exactly
- Verify credentials are correct

### Email Issues
- Verify App Password is generated correctly
- Check 2FA is enabled on Google account
- Test SMTP connection

## 📚 Next Steps

1. **Setup Google Workspace**
   - Configure Google Calendar API
   - Generate App Password for SMTP

2. **Initialize Database**
   - Run `python reset_database.py`

3. **Start Development**
   - Implement authentication endpoints
   - Build customer management APIs
   - Design frontend pages

4. **Testing**
   - Create test users
   - Test all workflows
   - Verify integrations

## 💡 Tips

- Use `uvicorn main:app --reload` for development
- Check logs regularly during development
- Test email functionality in development
- Use PostgreSQL locally (matches production)
- Keep `.env` file secure and never commit it

## 🤝 Support

For issues or questions:
1. Check this documentation
2. Review error logs
3. Verify environment variables
4. Check database connections

## 📄 License

MIT License
