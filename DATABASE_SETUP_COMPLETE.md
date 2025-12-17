# ✅ Database Setup Complete!

## 🎯 What's Been Accomplished

### 1. ✅ Database Created
- **Type**: SQLite (for local development)
- **Location**: `scale_backend/scaledux.db`
- **Tables Created**: 5 tables
  - `startups` - Startup entities
  - `assessments` - Assessment responses and scores
  - `evidence_uploads` - Document uploads for verification
  - `published_snapshots` - Bi-monthly frozen scores
  - `calculation_audit_logs` - Calculation trace for debugging

### 2. ✅ Sample Data Seeded

**Startup Created:**
- **Name**: Sample SaaS Startup
- **Stage**: MVP_NO_TRACTION
- **ID**: `1ffaa196-c592-4b6e-9ea8-507809a4fdc3`

**Assessment Created:**
- **ID**: `fffd7375-1b6b-41f3-9342-fd083cee8f50`
- **Status**: DRAFT
- **Framework Version**: 1.0.0

### 3. ✅ 18 Questions Configured

All from **Team Category** (ready to use):

| # | KPI ID | Question |
|---|--------|----------|
| 1 | `fc_fulltime_founder` | Is at least one founder working full-time? |
| 2 | `fc_personal_financial_runway_months` | How many months of runway? |
| 3 | `fc_notice_period_remaining_weeks` | Notice period remaining? |
| 4 | `fc_cofounder_equity_locked` | Is equity vesting locked? |
| 5 | `fc_equity_split_documented` | Is equity split documented? |
| 6 | `fc_founder_financial_investment` | How much capital invested? |
| 7 | `fc_priorities_clear` | Are priorities defined? |
| 8 | `fc_technical_cofounder_present` | Technical co-founder present? |
| 9 | `fc_gtm_experience` | GTM experience? |
| 10 | `fc_saas_pricing_experience` | SaaS pricing experience? |
| 11 | `fc_saas_unit_economics_literacy` | Understands unit economics? |
| 12 | `fc_solo_advisory_board_strength` | [Solo] Advisory board? |
| 13 | `fc_solo_execution_bandwidth_plan` | [Solo] Bandwidth plan? |
| 14 | `vm_shared_vision` | Shared vision among founders? |
| 15 | `vm_problem_solution_thesis` | Clear problem-solution thesis? |
| 16 | `vm_story_pitch_ready` | Pitch deck ready? |
| 17 | `vm_saas_vision_scalability` | Vision addresses scalability? |
| 18 | `vm_exit_timeline_intent` | Exit timeline defined? |

---

## 🚀 How to Use the API

### 1. API Server is Running

```
http://localhost:8000
```

**Swagger UI (Interactive Docs):**
```
http://localhost:8000/docs
```

**Alternative Docs (ReDoc):**
```
http://localhost:8000/redoc
```

### 2. Test the API

You can now test with the sample data created above!

#### Example: Get Assessment

```bash
curl http://localhost:8000/api/v1/assessments/fffd7375-1b6b-41f3-9342-fd083cee8f50/score?mode=draft
```

#### Example: Update KPI Responses

```bash
curl -X PUT http://localhost:8000/api/v1/assessments/fffd7375-1b6b-41f3-9342-fd083cee8f50/responses \
  -H "Content-Type: application/json" \
  -d '[
    {
      "kpi_id": "fc_fulltime_founder",
      "value": true,
      "evidence_type": "self_reported"
    },
    {
      "kpi_id": "fc_personal_financial_runway_months",
      "value": 6,
      "evidence_type": "self_reported"
    }
  ]'
```

---

## 📂 File Structure

```
scale_backend/
├── scaledux.db                    ← ✅ YOUR DATABASE (SQLite)
├── app/
│   ├── models/
│   │   ├── startup.py            ← ✅ Startup model
│   │   └── assessment.py         ← ✅ Assessment, Evidence, Snapshot models
│   ├── config/
│   │   └── kpis_sample.yaml      ← ✅ 18 questions configured here
│   └── api/
│       └── assessments.py        ← ✅ REST API endpoints
├── scripts/
│   └── init_db.py                ← ✅ Database initialization script
└── venv/                          ← Python virtual environment
```

---

## 🔄 Next Steps for Integration with Auth Backend

Since your team already has authentication built, you need to:

### Option 1: Pass `user_id` in Requests (Recommended)

Modify API endpoints to accept `user_id` from your auth system:

```python
# In app/api/assessments.py

from fastapi import Header

@router.post("")
async def create_assessment(
    request: AssessmentRequest,
    user_id: str = Header(..., alias="X-User-ID")  # From auth backend
):
    # Validate user_id with your auth system
    # Then create assessment for that user's startup
    pass
```

### Option 2: JWT Token Validation

If your auth uses JWT tokens:

```python
from fastapi import Depends
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(token: str = Depends(security)):
    # Decode JWT token from your auth backend
    # Extract user_id
    return user_id

@router.post("")
async def create_assessment(
    request: AssessmentRequest,
    user_id: str = Depends(get_current_user)
):
    pass
```

---

## 🗄️ Switching to PostgreSQL for Production

Currently using SQLite for local development. To switch to PostgreSQL:

### 1. Install PostgreSQL

```bash
brew install postgresql@15
brew services start postgresql@15
```

### 2. Create Database

```bash
createdb scaledux_prod
```

### 3. Update Connection String

In `.env` file:

```bash
# Change from:
DATABASE_URL=sqlite:///./scaledux.db

# To:
DATABASE_URL=postgresql://user:password@localhost:5432/scaledux_prod
```

### 4. Re-run Init Script

```bash
python scripts/init_db.py
```

---

## 📊 Database Schema

### Startups Table
```sql
CREATE TABLE startups (
  id UUID PRIMARY KEY,
  name VARCHAR(255),
  stage VARCHAR(18),  -- MVP_NO_TRACTION, MVP_EARLY_TRACTION, etc.
  created_at DATETIME,
  updated_at DATETIME
);
```

### Assessments Table
```sql
CREATE TABLE assessments (
  id UUID PRIMARY KEY,
  startup_id UUID REFERENCES startups(id),
  stage VARCHAR(18),
  framework_version VARCHAR(20),
  status VARCHAR(11),  -- DRAFT, COMPLETED, PUBLISHED
  computed_score INTEGER,
  score_band VARCHAR(9),  -- critical, poor, fair, good, excellent
  responses JSON,  -- {kpi_id: {value, evidence_type, ...}}
  score_metadata JSON,  -- Full breakdown for explainability
  created_at DATETIME,
  updated_at DATETIME
);
```

### Evidence Uploads Table
```sql
CREATE TABLE evidence_uploads (
  id UUID PRIMARY KEY,
  assessment_id UUID REFERENCES assessments(id),
  kpi_id VARCHAR(100),
  file_url VARCHAR(500),
  file_name VARCHAR(255),
  verified BOOLEAN,
  decay_lambda FLOAT,  -- For time-decay calculation
  uploaded_at DATETIME,
  created_at DATETIME,
  updated_at DATETIME
);
```

---

## 🧪 Testing Checklist

- [ ] API server is running (`http://localhost:8000`)
- [ ] Swagger UI accessible (`http://localhost:8000/docs`)
- [ ] Database file exists (`scaledux.db`)
- [ ] Sample startup created
- [ ] Sample assessment created
- [ ] Can update KPI responses via API
- [ ] Can retrieve score breakdown

---

## 🆘 Troubleshooting

### API Not Starting?
```bash
# Kill existing process
pkill -f uvicorn

# Restart
cd scale_backend
source venv/bin/activate
uvicorn app.main:app --reload
```

### Database Locked?
```bash
# Close all connections and recreate
rm scaledux.db
python scripts/init_db.py
```

### Missing Dependencies?
```bash
source venv/bin/activate
pip install -r requirements_api_only.txt
```

---

## 📞 Support

For questions or issues:
1. Check `README.md` for full documentation
2. Review `ARCHITECTURE.md` for system design
3. See `IMPLEMENTATION_GUIDE.md` for development guide

---

**Status**: ✅ Ready for Development
**Last Updated**: December 16, 2025
**Database**: SQLite (local), ready for PostgreSQL migration
