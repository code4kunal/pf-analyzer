# 📊 Prospects Management Feature - Quick Start Guide

## What's Been Built

A complete, production-ready prospects management system with:
- ✅ **Admin-only access** - Fully protected endpoints
- ✅ **Intelligent CSV/Excel import** - Auto-column mapping
- ✅ **Advanced filtering** - 10+ filter types
- ✅ **Conversion workflow** - Prospect → Customer
- ✅ **Analytics dashboard** - Conversion funnel, sources, metrics
- ✅ **Activity logging** - Full audit trail
- ✅ **Export to Excel** - Professional formatted reports
- ✅ **Bulk operations** - Update/delete/assign multiple prospects

## Quick Start

### 1. Database Setup (Already Done ✅)

The database tables have been created. To verify:

```bash
python migrations/create_prospect_tables.py
```

You should see:
```
✓ Tables created successfully!

Created tables:
  - prospects
  - prospect_communications
  - prospect_activities
  - import_batches
```

### 2. Start the Server

```bash
# Using uvicorn
uvicorn main:app --reload

# Or using Python
python main.py
```

Server will start on: http://localhost:8000

### 3. Test the API

```bash
# Basic health check
python test_prospects_api.py
```

### 4. Access API Documentation

Open your browser:
- **Interactive Docs:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

Look for the **"prospects"** tag to see all endpoints.

## Using the API

### Step 1: Login as Admin

```bash
# Login (replace with your admin credentials)
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "your-password"
  }'
```

Save the `access_token` from the response.

### Step 2: Create a Prospect

```bash
# Create a prospect
curl -X POST "http://localhost:8000/api/prospects" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "full_name": "John Doe",
    "email": "john.doe@example.com",
    "phone": "9876543210",
    "company": "Tech Solutions",
    "designation": "CEO",
    "priority": "HOT",
    "status": "NEW",
    "estimated_portfolio_value": 1500000,
    "tags": ["high-net-worth", "tech-industry"]
  }'
```

### Step 3: List Prospects with Filters

```bash
# Get HOT prospects
curl "http://localhost:8000/api/prospects?priority=HOT&page=1&page_size=20" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Search by name/email/phone
curl "http://localhost:8000/api/prospects?search=john" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Multiple filters
curl "http://localhost:8000/api/prospects?status=NEW&status=CONTACTED&priority=HOT&sort_by=created_at&sort_order=desc" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Step 4: Import Prospects from CSV

We've included a sample CSV file: `sample_import_prospects.csv`

**Using the API Docs (Easiest):**
1. Go to http://localhost:8000/docs
2. Find `POST /api/prospects/import/upload`
3. Click "Try it out"
4. Upload `sample_import_prospects.csv`
5. Review the preview and suggested mappings
6. Use the `file_key` from response
7. Call `POST /api/prospects/import/confirm` with the mappings

**Using curl:**

```bash
# Step 1: Upload file for preview
curl -X POST "http://localhost:8000/api/prospects/import/upload" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -F "file=@sample_import_prospects.csv"

# Response will include:
# - file_key
# - suggested_mappings
# - preview_rows

# Step 2: Confirm import
curl -X POST "http://localhost:8000/api/prospects/import/confirm" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "file_key": "THE_FILE_KEY_FROM_STEP_1",
    "column_mappings": {
      "Full Name": "full_name",
      "Email Address": "email",
      "Mobile Number": "phone",
      "Company Name": "company",
      "Job Title": "designation",
      "Portfolio Value": "estimated_portfolio_value",
      "Lead Source": "referral_source",
      "Notes": "notes"
    },
    "skip_duplicates": true
  }'
```

### Step 5: View Analytics

```bash
curl "http://localhost:8000/api/prospects/analytics" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

You'll get:
- Total prospects count
- Breakdown by status (with percentages)
- Breakdown by source (with conversion rates)
- Breakdown by priority
- Conversion statistics
- Average time to convert

### Step 6: Export Prospects

```bash
# Export all prospects
curl "http://localhost:8000/api/prospects/export" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o prospects_export.xlsx

# Export with filters (e.g., only HOT prospects)
curl "http://localhost:8000/api/prospects/export?priority=HOT" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o hot_prospects.xlsx
```

### Step 7: Convert Prospect to Customer

```bash
# Convert prospect ID 1 to customer
curl -X POST "http://localhost:8000/api/prospects/1/convert" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "relationship_manager_id": 2,
    "copy_notes": true
  }'
```

## API Endpoints Reference

### Prospect CRUD
- `GET /api/prospects` - List prospects (with filters & pagination)
- `POST /api/prospects` - Create prospect
- `GET /api/prospects/{id}` - Get prospect details
- `PUT /api/prospects/{id}` - Update prospect
- `DELETE /api/prospects/{id}` - Delete prospect

### Communications
- `POST /api/prospects/{id}/communications` - Log communication
- `GET /api/prospects/{id}/communications` - Get communication history

### Conversion
- `POST /api/prospects/{id}/convert` - Convert to customer

### Import/Export
- `POST /api/prospects/import/upload` - Upload CSV/Excel for preview
- `POST /api/prospects/import/confirm` - Confirm and process import
- `GET /api/prospects/import/history` - View import history
- `GET /api/prospects/export` - Export to Excel

### Analytics
- `GET /api/prospects/analytics` - Get analytics data

### Bulk Operations
- `POST /api/prospects/bulk-update` - Update multiple prospects
- `POST /api/prospects/bulk-delete` - Delete multiple prospects
- `POST /api/prospects/bulk-assign` - Assign prospects to user

## Filtering Options

The `GET /api/prospects` endpoint supports these query parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `search` | string | Search in name, email, phone, company | `?search=john` |
| `status` | enum[] | Filter by status (multi-select) | `?status=NEW&status=CONTACTED` |
| `priority` | enum[] | Filter by priority (multi-select) | `?priority=HOT&priority=WARM` |
| `source` | enum[] | Filter by source (multi-select) | `?source=IMPORT&source=REFERRAL` |
| `assigned_to_id` | int | Filter by assigned user | `?assigned_to_id=2` |
| `created_from` | date | Created after this date | `?created_from=2024-01-01` |
| `created_to` | date | Created before this date | `?created_to=2024-12-31` |
| `next_followup_from` | date | Follow-up after this date | `?next_followup_from=2024-01-15` |
| `next_followup_to` | date | Follow-up before this date | `?next_followup_to=2024-01-31` |
| `estimated_value_min` | float | Min portfolio value | `?estimated_value_min=1000000` |
| `estimated_value_max` | float | Max portfolio value | `?estimated_value_max=5000000` |
| `tags` | string[] | Filter by tags | `?tags=high-net-worth` |
| `is_converted` | bool | Converted or not | `?is_converted=false` |
| `page` | int | Page number (default 1) | `?page=2` |
| `page_size` | int | Results per page (default 20, max 100) | `?page_size=50` |
| `sort_by` | string | Sort field (default created_at) | `?sort_by=full_name` |
| `sort_order` | string | asc or desc (default desc) | `?sort_order=asc` |

## Prospect Lifecycle

```
NEW → CONTACTED → QUALIFIED → NEGOTIATION → CONVERTED/LOST
```

- **NEW:** Just added, not contacted yet
- **CONTACTED:** Initial contact made
- **QUALIFIED:** Meets criteria, interested
- **NEGOTIATION:** In discussions
- **CONVERTED:** Became a customer
- **LOST:** No longer interested

## Priority Levels

- **HOT:** High priority, immediate follow-up
- **WARM:** Medium priority, regular follow-up
- **COLD:** Low priority, occasional follow-up

## Source Types

- **IMPORT:** Imported from CSV/Excel
- **MANUAL:** Manually entered
- **REFERRAL:** Referred by existing customer
- **WEBSITE:** From website form
- **EVENT:** Met at event/seminar
- **OTHER:** Other sources

## Import File Format

Your CSV/Excel file can have any column names. The system will auto-suggest mappings. Common columns:

| Your Column | Maps To | Required |
|-------------|---------|----------|
| Name, Full Name, Client Name | full_name | One of: name, email, or phone |
| Email, E-mail, Email Address | email | Optional |
| Phone, Mobile, Contact Number | phone | Optional |
| Company, Organization | company | Optional |
| Designation, Title, Position | designation | Optional |
| Portfolio Value, Investment, AUM | estimated_portfolio_value | Optional |
| Source, Referral, Lead Source | referral_source | Optional |
| Notes, Comments, Remarks | notes | Optional |
| Tags, Categories | tags | Optional |

**Any unmapped columns** are automatically stored in `custom_fields` for later review.

## Testing Import

Use the provided sample file:

```bash
# File: sample_import_prospects.csv
# Contains 10 sample prospects with various formats

# Upload via API docs (easiest):
1. Go to http://localhost:8000/docs
2. Find POST /api/prospects/import/upload
3. Upload sample_import_prospects.csv
4. Review auto-suggested mappings
5. Confirm import

# Check results:
curl "http://localhost:8000/api/prospects" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Common Tasks

### Find prospects needing follow-up today

```bash
curl "http://localhost:8000/api/prospects?next_followup_to=2024-01-15" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Get all HOT prospects not assigned

```bash
curl "http://localhost:8000/api/prospects?priority=HOT&assigned_to_id=" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Export converted prospects

```bash
curl "http://localhost:8000/api/prospects/export?is_converted=true" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -o converted_prospects.xlsx
```

### Bulk assign HOT prospects to user

```bash
curl -X POST "http://localhost:8000/api/prospects/bulk-assign" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "prospect_ids": [1, 2, 3, 4, 5],
    "assigned_to_id": 2
  }'
```

## Troubleshooting

### "Detail: Not authenticated"
- Make sure you're including the `Authorization: Bearer TOKEN` header
- Get a new token if yours expired (login again)

### "Access denied. Admin role required"
- Prospects feature is admin-only
- Make sure the logged-in user has role "ADMIN"

### Import fails
- Check file format (CSV, XLSX, XLS only)
- Max file size: 10MB
- Max rows per import: 10,000
- At least one of name/email/phone required per row

### No prospects showing up
- Check pagination (page 1, page_size 20 default)
- Check filters - clear all filters to see all prospects
- Verify prospects were created (check database or import history)

## Next Steps (Frontend)

The backend is complete. Next, build the frontend:

1. **Prospects List Page**
   - Table with sorting, filtering, pagination
   - Bulk actions toolbar
   - Export button

2. **Import Wizard**
   - Drag-drop file upload
   - Column mapping interface
   - Preview table with validation
   - Progress bar

3. **Prospect Detail Modal**
   - View/edit form
   - Communication timeline
   - Activity log
   - Convert button

4. **Analytics Dashboard**
   - Charts (Chart.js)
   - Key metrics cards
   - Conversion funnel

5. **Sidebar Navigation**
   - Add "Prospects" menu (admin only)
   - Sub-menu: All, Import, Analytics

## Need Help?

- **API Docs:** http://localhost:8000/docs
- **Summary:** See `PROSPECTS_FEATURE_SUMMARY.md`
- **Sample CSV:** See `sample_import_prospects.csv`
- **Test Script:** Run `python test_prospects_api.py`

---

**Backend Status:** ✅ 100% Complete and Production-Ready

Ready to build the frontend! 🚀
