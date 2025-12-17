# SCORE™ Questions Inventory

## 📍 Question Files Location

```
scale_backend/app/config/
├── kpis_sample.yaml       ← CURRENT QUESTIONS (18 KPIs)
├── kpi_template.yaml      ← TEMPLATE for adding new questions
├── fatal_flags.yaml       ← Penalty rules
└── dependencies.yaml      ← Cross-category rules
```

---

## ✅ Currently Implemented (18 Questions)

### **Category 1: TEAM** (40% weight at MVP stage)

#### Sub-Category: Founder Commitment (10 questions)

1. **fc_fulltime_founder**
   - Question: "Is at least one founder working full-time on the startup?"
   - Type: Boolean (Yes/No)
   - Weight: 18% of sub-category
   - Evidence: Resignation letter (1.0) vs Self-report (0.6)
   - **FATAL FLAG**: If false, caps execution score

2. **fc_personal_financial_runway_months**
   - Question: "How many months of personal financial runway does the full-time founder have?"
   - Type: Number
   - Weight: 15% of sub-category
   - Evidence: Bank statement (0.95) vs Self-report (0.5)
   - Scoring: Green ≥6 months, Yellow 3-6, Red <3

3. **fc_notice_period_remaining_weeks**
   - Question: "If any founder is currently employed, how many weeks of notice period remain?"
   - Type: Number
   - Weight: 6% of sub-category
   - Evidence: Employment contract (1.0) vs Self-report (0.7)
   - **SKIP LOGIC**: Skip if founder already full-time

4. **fc_cofounder_equity_locked**
   - Question: "Has co-founder equity been locked with a standard vesting schedule?"
   - Type: Boolean
   - Weight: 10% of sub-category
   - Evidence: SHA/vesting agreement (1.0) vs Self-report (0.5)

5. **fc_equity_split_documented**
   - Question: "What is the equity split (%) among founders? Is it formally documented?"
   - Type: Composite (Number + Boolean)
   - Weight: 11% of sub-category
   - Evidence: Founders' Agreement (1.0) vs Self-report (0.5)
   - **WARNING FLAG**: Undocumented = co-founder breakup risk

6. **fc_founder_financial_investment**
   - Question: "How much personal capital (₹) have the founders collectively invested?"
   - Type: Number
   - Weight: 9% of sub-category
   - Evidence: Bank receipts (0.95) vs Self-report (0.5)

7. **fc_priorities_clear**
   - Question: "Are the founder's weekly time allocation and priorities clearly defined?"
   - Type: Boolean
   - Weight: 6% of sub-category
   - Evidence: Tracker screenshot (0.9) vs Self-report (0.6)

8. **fc_technical_cofounder_present**
   - Question: "Is there a technical co-founder with prior SaaS development experience?"
   - Type: Boolean
   - Weight: 14% of sub-category
   - Evidence: LinkedIn + GitHub (0.95) vs Self-report (0.5)
   - **FATAL FLAG**: If false at traction stage, caps Solution category at 60%

9. **fc_gtm_experience**
   - Question: "Does any founder have prior go-to-market experience in SaaS?"
   - Type: Boolean
   - Weight: 7% of sub-category
   - Evidence: LinkedIn verified (0.85) vs Self-report (0.5)

10. **fc_saas_pricing_experience**
    - Question: "Does the founding team have experience designing SaaS pricing models?"
    - Type: Boolean
    - Weight: 9% of sub-category
    - Evidence: Portfolio/case study (0.9) vs Self-report (0.5)
    - **CONDITIONAL**: Only for SaaS business models

#### Sub-Category: Vision & Mission (5 questions)

11. **vm_shared_vision**
    - Question: "Do all founders share the same long-term vision (5-10 year outcome)?"
    - Type: Boolean
    - Weight: 28% of sub-category
    - Evidence: Separate founder interviews (0.95) vs Self-report (0.5)
    - **FATAL FLAG**: Misalignment blocks long-term planning

12. **vm_problem_solution_thesis**
    - Question: "Is there a clearly articulated problem-solution thesis?"
    - Type: Boolean
    - Weight: 25% of sub-category
    - Evidence: Written thesis document (0.95) vs Self-report (0.5)

13. **vm_story_pitch_ready**
    - Question: "Is a compelling pitch deck ready for investors?"
    - Type: Boolean
    - Weight: 17% of sub-category
    - Evidence: Pitch deck uploaded (0.85) vs Self-report (0.5)

14. **vm_saas_vision_scalability**
    - Question: "Does the vision address SaaS scalability elements (global market, multi-tenant architecture)?"
    - Type: Boolean
    - Weight: 15% of sub-category
    - Evidence: Vision document (0.95) vs Self-report (0.6)
    - **CONDITIONAL**: Only for SaaS business models

15. **vm_exit_timeline_intent**
    - Question: "What is the founder's intended exit timeline and strategy?"
    - Type: Enum (3yr_exit | 5to7yr_exit | 10plus_yr_build | lifestyle_business)
    - Weight: 15% of sub-category
    - Evidence: Investor discussion notes (0.9) vs Self-report (0.7)

#### Sub-Category: Other Team Sub-Categories (3 questions)

16. **fc_saas_unit_economics_literacy**
    - Question: "Does at least one founder understand core SaaS unit economics (LTV, CAC, Payback)?"
    - Type: Boolean
    - Weight: 10% of sub-category
    - Evidence: Quiz >75% (0.85) vs Self-report (0.4)

17. **fc_solo_advisory_board_strength**
    - Question: "[SOLO ONLY] Do you have a committed advisory board (≥2 advisors)?"
    - Type: Boolean
    - Weight: 14% of sub-category
    - Evidence: Advisor agreements (0.95) vs Self-report (0.5)
    - **CONDITIONAL**: Only for solo founders

18. **fc_solo_execution_bandwidth_plan**
    - Question: "[SOLO ONLY] Do you have a documented plan for managing execution bandwidth?"
    - Type: Boolean
    - Weight: 11% of sub-category
    - Evidence: Execution plan document (0.95) vs Self-report (0.6)
    - **CONDITIONAL**: Only for solo founders

---

## ❌ Still Missing (52+ Questions)

Based on your Excel file, you still need to add:

### **Category 2: MARKET** (~12 questions)
- Target market definition
- Market size (TAM/SAM/SOM)
- Competitive landscape
- Customer personas
- Market timing
- etc.

### **Category 3: SOLUTION** (~15 questions)
- MVP/prototype status
- Technical architecture
- Scalability plans
- IP/patents
- Product roadmap
- etc.

### **Category 4: VALIDATION** (~10 questions)
- Customer discovery
- User interviews conducted
- Beta users/pilot customers
- Feedback iteration cycles
- PMF indicators
- etc.

### **Category 5: EXECUTION** (~12 questions)
- Operational infrastructure
- Team roles clarity
- Budget allocation
- Burn rate
- Hiring plan
- etc.

### **Category 6: LEGAL** (~8 questions)
- Incorporation status
- IP ownership
- Contracts/agreements
- Regulatory compliance
- etc.

### **Category 7: MILESTONES** (~6 questions)
- 30-day goals
- 60-day goals
- 90-day goals
- 12-month vision
- Success metrics
- etc.

---

## 🚀 How to Add Remaining Questions

### Method 1: Use Excel Converter (Recommended)

```bash
cd scale_backend

# Install dependencies
pip install pandas openpyxl pyyaml

# Convert your Excel file
python scripts/convert_excel_to_yaml.py \
  ~/Documents/Projects/scale/scaleDUX.xlsx \
  app/config/all_kpis_generated.yaml

# Review the output
less app/config/all_kpis_generated.yaml

# Merge with existing kpis_sample.yaml
# (Manual step - copy relevant sections)
```

### Method 2: Manual Entry

1. Open `app/config/kpi_template.yaml`
2. Copy a relevant example (boolean, number, enum)
3. Fill in your question details
4. Paste into appropriate section of `kpis_sample.yaml`

**Example: Adding a Market question**

```yaml
# In kpis_sample.yaml, add a new category:

categories:
  team: [existing...]

  market:  # NEW CATEGORY
    weight_mvp_no_traction: 0.25
    weight_mvp_early_traction: 0.15

    sub_categories:
      market_sizing:
        weight: 0.35
        kpis:
          ms_tam_calculation:
            question: "What is your Total Addressable Market (TAM) in ₹?"
            type: number
            priority: core
            base_weight: 0.30
            stage_multiplier:
              mvp_no_traction: 1.2
              mvp_early_traction: 1.0
            universal: true
            scoring_logic:
              mvp_no_traction:
                green: "value >= 10000000000"  # ₹100 Cr+
                yellow: "value >= 1000000000"  # ₹10 Cr+
                red: "value < 1000000000"      # <₹10 Cr
              mvp_early_traction:
                green: "value >= 10000000000"
                yellow: "value >= 1000000000"
                red: "value < 1000000000"
            confidence_method:
              self_reported: 0.4  # Market sizing is often inflated!
              document_uploaded: 0.9  # Market research report
```

---

## 🎯 Priority Order for Adding Questions

Based on investor importance:

### **Phase 1: Critical (Week 1)**
1. Legal category (8 questions) - Incorporation, IP, contracts
2. Execution category - Role clarity, burn rate, runway

### **Phase 2: High Priority (Week 2)**
3. Market category (12 questions) - TAM/SAM, competition
4. Solution category - MVP status, tech stack

### **Phase 3: Important (Week 3)**
5. Validation category - Customer discovery, traction
6. Milestones category - Goal setting, success metrics

---

## 📊 Category Weight Distribution

Once all categories are added:

```yaml
# Idea Stage (MVP_no_traction)
Team: 40%       ✅ DONE
Market: 25%     ❌ TODO
Solution: 15%   ❌ TODO
Validation: 10% ❌ TODO
Execution: 5%   ❌ TODO
Legal: 3%       ❌ TODO
Milestones: 2%  ❌ TODO

# Growth Stage (MVP_early_traction)
Team: 20%       ✅ DONE
Market: 15%     ❌ TODO
Solution: 15%   ❌ TODO
Validation: 25% ❌ TODO
Execution: 15%  ❌ TODO
Legal: 5%       ❌ TODO
Milestones: 5%  ❌ TODO
```

---

## 🔧 Testing Your Questions

After adding questions, test them:

```python
# Test script
from app.core.scoring_engine import ScoringEngine
import yaml

# Load your new config
with open('app/config/kpis_sample.yaml') as f:
    config = yaml.safe_load(f)

# Create mock responses
responses = {
    'ms_tam_calculation': {
        'value': 5000000000,  # ₹50 Cr
        'evidence_type': 'self_reported'
    }
}

# Calculate score
engine = ScoringEngine(config, {}, {})
# ... (engine will process your new questions)
```

---

## 📝 Checklist Before Going Live

- [ ] All 70+ KPIs defined in YAML
- [ ] Each KPI has scoring logic for both stages
- [ ] Confidence methods defined for each evidence type
- [ ] Fatal flags configured for critical blockers
- [ ] Dependencies mapped between categories
- [ ] Sub-category weights sum to 1.0
- [ ] Category weights sum to 1.0 per stage
- [ ] Skip logic tested for conditional questions
- [ ] Sample responses test with scoring engine
- [ ] Frontend team has list of all questions

---

**Last Updated**: December 16, 2025
**Total Questions**: 18/70 (25% complete)
**Next Action**: Add Market category (12 questions)
