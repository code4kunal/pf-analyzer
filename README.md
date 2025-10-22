# GrowFolio CMS

A comprehensive customer management system for investment consultancy firms, built with FastAPI and vanilla JavaScript.

## Features

- **Customer Management**: Complete customer profiles with KYC, financial details, and documents
- **Investment Tracking**: Manual entry for mutual funds, stocks, bonds, insurance, and more
- **Calendar & Events**: Global calendar with Google Meet integration for seminars, 1-on-1s, and group calls
- **Communication Hub**: Track calls, emails, meetings, and internal notes with activity timeline
- **Commission & Billing**: Commission tracking, invoice generation, and payment management
- **User Management**: Role-based access control (Admin/Employee) with invite system
- **Notifications**: In-app and email notifications for events, birthdays, and follow-ups
- **Reports & Analytics**: Customer acquisition, revenue reports, and Excel/PDF export
- **Professional UI**: Clean, responsive interface optimized for consultancy workflows
- **Railway Ready**: Configured for easy deployment on Railway

## Tech Stack

- **Backend**: FastAPI, SQLAlchemy, PostgreSQL
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Charts**: Chart.js
- **Authentication**: JWT with RBAC (Admin/Employee)
- **Integrations**: Google Meet, Gmail SMTP
- **Storage**: Local (S3-ready architecture)
- **Deployment**: Railway ready

## Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL 13+
- Google Workspace account

### Installation

1. **Clone and setup**:
```bash
git clone <your-repo-url>
cd pf-analyzer
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. **Create database**:
```bash
createdb growfolio
```

3. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your credentials (see SETUP.md for details)
```

4. **Initialize database**:
```bash
python reset_database.py --yes
```

5. **Run the application**:
```bash
uvicorn main:app --reload
```

Visit `http://localhost:8000`

**Default Admin Login**:
- Email: `admin@grow-folio.in`
- Password: `Admin@123` (change after first login)

## Configuration

### Google API Setup

**For Google Meet & Calendar**:
1. Create project in Google Cloud Console
2. Enable Google Calendar API
3. Create OAuth 2.0 credentials
4. Add to `.env`: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`

**For Email (SMTP)**:
1. Enable 2FA on help@grow-folio.in
2. Generate App Password at https://myaccount.google.com/apppasswords
3. Add to `.env`: `SMTP_PASSWORD`

See [SETUP.md](SETUP.md) for detailed configuration guide.

## Deployment (Railway)

1. **Connect Repository**:
   - Go to https://railway.app/
   - Connect your GitHub repository
   - Railway auto-detects configuration

2. **Configure Environment Variables**:
   - Add all variables from `.env.example`
   - Set `DEBUG=False` for production
   - Railway provides `DATABASE_URL` automatically

3. **Initialize Database**:
```bash
railway link
railway run python reset_database.py --yes
```

4. **Deploy**:
```bash
git push origin main
```

See [RAILWAY_SETUP.md](RAILWAY_SETUP.md) for details.

## Core Modules

### 1. Customer Management
- Complete customer profiles with KYC
- Search and advanced filters
- Document management
- Family members and nominees

### 2. Calendar & Events
- Global calendar view (FullCalendar.js)
- Event types: Seminar, 1-on-1, Group Call, Follow-up, Review
- Google Meet integration
- Email notifications

### 3. Investment Tracking
- Manual entry for all investment types
- Portfolio summary per customer
- Returns calculation

### 4. Communication Hub
- Communication logs (calls, emails, meetings)
- Internal notes (public/private)
- Activity timeline

### 5. Commission & Billing
- Commission tracking per investment
- Invoice generation
- Payment management

### 6. User Management
- RBAC (Admin/Employee)
- Invite-based registration
- Temporary password flow

## Database Schema

- **users**: Admin and employee accounts with RBAC
- **customers**: Complete customer profiles
- **investments**: Investment tracking
- **events**: Calendar events with Google Meet links
- **communications**: Communication logs
- **notes**: Internal notes
- **commissions**: Commission tracking
- **invoices**: Billing and payments
- **documents**: Document storage
- **notifications**: User notifications
- **activity_logs**: Activity timeline
- **family_members**: Customer family info
- **nominees**: Investment nominees
- **event_participants**: Event-customer mapping

## Security

- Passwords hashed with bcrypt
- JWT authentication with RBAC
- Role-based access control (Admin/Employee)
- Environment variables for all secrets
- Invite-based user creation
- Temporary password with forced change
- HTTPS required for production

## Documentation

- [SETUP.md](SETUP.md) - Complete setup guide
- [RAILWAY_SETUP.md](RAILWAY_SETUP.md) - Railway deployment guide
- [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) - General deployment guide

## Development Status

**Phase 1**: Foundation (Current)
- ✅ Database schema
- ✅ Configuration
- ⏳ Authentication APIs
- ⏳ Frontend layout

**Next Phases**: Customer Management → Calendar & Events → Advanced Features → Reports

## License

MIT License

## Support

For questions or issues, please create an issue on GitHub.