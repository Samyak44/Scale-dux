"""Assessment management API endpoints"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Body, Header
from pydantic import BaseModel

from ..schemas.scoring import (
    AssessmentRequest,
    KPIResponseUpdate,
    ScoreResponse,
    StartupStage,
    ScoreBreakdown
)

router = APIRouter()


# Mock database for demonstration
# In production, replace with actual database queries
MOCK_ASSESSMENTS = {}


class CreateAssessmentResponse(BaseModel):
    """Response for assessment creation"""
    assessment_id: UUID
    startup_id: UUID
    stage: StartupStage
    status: str
    created_at: datetime
    message: str


@router.post("", response_model=CreateAssessmentResponse, status_code=201)
async def create_assessment(
    request: AssessmentRequest,
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend")
):
    """
    Create a new assessment for a startup

    Initializes a draft assessment that can be progressively filled out.

    **Authentication:**
    - Requires X-User-ID header from your authentication system
    - User must own the startup to create assessments

    **Process:**
    1. Validates user owns the startup (or creates startup if startup_id not provided)
    2. Creates assessment record with 'draft' status
    3. Loads stage-appropriate KPI framework
    4. Returns assessment ID for subsequent updates

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/assessments \
      -H "Content-Type: application/json" \
      -H "X-User-ID: user-123-from-auth" \
      -d '{
        "startup_id": "123e4567-e89b-12d3-a456-426614174000",
        "stage": "mvp_no_traction",
        "framework_version": "1.0.0"
      }'
    ```
    """
    from uuid import uuid4

    # Validate user_id is not empty
    if not user_id or user_id.strip() == "":
        raise HTTPException(
            status_code=401,
            detail="X-User-ID header is required. Please authenticate first."
        )

    assessment_id = uuid4()

    # TODO: In production, validate that user owns this startup by querying database:
    # startup = db.query(Startup).filter_by(id=request.startup_id, user_id=user_id).first()
    # if not startup:
    #     raise HTTPException(status_code=403, detail="You don't have permission to access this startup")

    # Mock creation (includes user_id for filtering)
    MOCK_ASSESSMENTS[str(assessment_id)] = {
        "id": assessment_id,
        "startup_id": request.startup_id,
        "user_id": user_id,  # Store for authorization
        "stage": request.stage,
        "status": "draft",
        "responses": {},
        "created_at": datetime.utcnow(),
    }

    return CreateAssessmentResponse(
        assessment_id=assessment_id,
        startup_id=request.startup_id,
        stage=request.stage,
        status="draft",
        created_at=datetime.utcnow(),
        message="Assessment created successfully. Start answering KPIs to generate score."
    )


@router.put("/{assessment_id}/responses", status_code=200)
async def update_kpi_responses(
    assessment_id: UUID,
    responses: List[KPIResponseUpdate] = Body(...),
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend")
):
    """
    Update one or more KPI responses

    **Authentication:**
    - Requires X-User-ID header
    - User must own the assessment's startup

    **Behavior:**
    - Updates are incremental (doesn't clear existing responses)
    - Draft score is recalculated immediately
    - Evidence uploads trigger higher confidence scoring
    - Returns updated draft score for user feedback

    **Example:**
    ```bash
    curl -X PUT http://localhost:8000/api/v1/assessments/{assessment_id}/responses \
      -H "Content-Type: application/json" \
      -H "X-User-ID: user-123-from-auth" \
      -d '[
        {
          "kpi_id": "fc_fulltime_founder",
          "value": true,
          "evidence_type": "document_uploaded",
          "evidence_id": "uuid-of-uploaded-resignation-letter"
        }
      ]'
    ```

    **Returns:**
    - Updated responses count
    - Draft score (if enabled)
    - Recommendations for improvement
    """
    assessment = MOCK_ASSESSMENTS.get(str(assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify user owns this assessment
    if assessment.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to modify this assessment"
        )

    # Update responses
    for response in responses:
        assessment["responses"][response.kpi_id] = response.model_dump()

    # TODO: Trigger scoring engine to calculate draft score

    return {
        "assessment_id": assessment_id,
        "updated_kpis": len(responses),
        "total_kpis_answered": len(assessment["responses"]),
        "status": "draft",
        "message": "Responses updated successfully",
        "draft_score_available": True,  # If ENABLE_DRAFT_SCORES is True
        "next_action": f"GET /api/v1/assessments/{assessment_id}/score?mode=draft"
    }


@router.get("/{assessment_id}/score", response_model=ScoreResponse)
async def get_assessment_score(
    assessment_id: UUID,
    mode: str = Query("draft", regex="^(draft|published)$"),
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend")
):
    """
    Retrieve assessment score with full breakdown

    **Authentication:**
    - Requires X-User-ID header
    - User must own the assessment's startup

    **Modes:**
    - **draft**: Real-time preview score (updates as user answers)
    - **published**: Official bi-monthly snapshot (1st or 15th of month)

    **Returns:**
    - Final SCORE (300-900)
    - Score band (critical/poor/fair/good/excellent)
    - Category-level breakdown
    - Fatal flags triggered
    - Dependency violations
    - Actionable recommendations

    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/assessments/{assessment_id}/score?mode=draft \
      -H "X-User-ID: user-123-from-auth"
    ```

    **Example Response:**
    ```json
    {
      "assessment_id": "uuid",
      "score": 685,
      "score_band": "good",
      "breakdown": {
        "category_scores": [...],
        "fatal_flags_triggered": [...],
        "recommendations": [
          "Upload incorporation certificate to remove -150 penalty",
          "Add technical co-founder to unlock Solution category"
        ]
      },
      "is_draft": true
    }
    ```
    """
    assessment = MOCK_ASSESSMENTS.get(str(assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify user owns this assessment
    if assessment.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this assessment"
        )

    # TODO: Call scoring engine
    # from ..core.scoring_engine import ScoringEngine
    # engine = ScoringEngine(config, fatal_flags_config, dependencies_config)
    # breakdown = engine.calculate_score(responses, stage, evidence_uploads)

    # Mock response for demonstration
    return ScoreResponse(
        assessment_id=assessment_id,
        startup_id=assessment["startup_id"],
        status=assessment["status"],
        score=685,
        score_band="good",
        breakdown=None,  # Would include full ScoreBreakdown from engine
        is_draft=(mode == "draft"),
        published_at=None if mode == "draft" else datetime.utcnow()
    )


@router.post("/{assessment_id}/evidence")
async def upload_evidence(
    assessment_id: UUID,
    kpi_id: str = Body(...),
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend")
    # file: UploadFile = File(...),  # TODO: Add when implementing S3 upload
):
    """
    Upload evidence document for a KPI

    **Authentication:**
    - Requires X-User-ID header
    - User must own the assessment's startup

    **Process:**
    1. Validates file type and size
    2. Stores file (S3/local storage)
    3. Creates evidence record with metadata
    4. Automatically updates KPI response evidence_type to 'document_uploaded'
    5. Recalculates score with higher confidence (E=1.0 vs E=0.6)

    **Evidence Decay:**
    - Different document types have different decay rates (λ)
    - Bank statements: High volatility (λ=0.1, ~7 day half-life)
    - Legal docs: Low volatility (λ=0.001, ~693 day half-life)

    **Example:**
    ```bash
    curl -X POST http://localhost:8000/api/v1/assessments/{assessment_id}/evidence \
      -H "Content-Type: application/json" \
      -H "X-User-ID: user-123-from-auth" \
      -d '{"kpi_id": "fc_fulltime_founder"}'
    ```

    **Returns:**
    - evidence_id (UUID for linking to KPI response)
    - verified status (initially False, pending manual/AI review)
    - decay_lambda (for time-decay calculation)
    """
    assessment = MOCK_ASSESSMENTS.get(str(assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify user owns this assessment
    if assessment.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to upload evidence for this assessment"
        )

    # TODO: Implement actual file upload logic
    from uuid import uuid4
    evidence_id = uuid4()

    return {
        "evidence_id": evidence_id,
        "kpi_id": kpi_id,
        "assessment_id": assessment_id,
        "file_name": "document.pdf",  # From file upload
        "uploaded_at": datetime.utcnow(),
        "verified": False,
        "decay_lambda": 0.005,
        "message": "Evidence uploaded successfully. Score will update automatically."
    }


@router.get("")
async def list_assessments(
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend"),
    startup_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List assessments for the authenticated user

    **Authentication:**
    - Requires X-User-ID header
    - Returns only assessments owned by the user

    **Filters:**
    - startup_id: Get assessments for specific startup (must be owned by user)
    - status: Filter by status (draft/completed/published)

    **Pagination:**
    - limit: Results per page (default 10, max 100)
    - offset: Skip N results (for pagination)

    **Example:**
    ```bash
    curl http://localhost:8000/api/v1/assessments?status=draft&limit=20 \
      -H "X-User-ID: user-123-from-auth"
    ```
    """
    # Mock implementation - filter by user_id first
    all_assessments = [
        a for a in MOCK_ASSESSMENTS.values()
        if a.get("user_id") == user_id
    ]

    # Apply additional filters
    if startup_id:
        all_assessments = [a for a in all_assessments if a["startup_id"] == startup_id]
    if status:
        all_assessments = [a for a in all_assessments if a["status"] == status]

    # Pagination
    total = len(all_assessments)
    results = all_assessments[offset:offset+limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results
    }


@router.delete("/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: UUID,
    user_id: str = Header(..., alias="X-User-ID", description="User ID from auth backend")
):
    """
    Delete an assessment

    **Authentication:**
    - Requires X-User-ID header
    - User must own the assessment's startup

    **Warning:**
    - This is a soft delete (sets status to 'archived')
    - Published snapshots are preserved for audit trail
    - Cannot delete assessments with investor activity

    **Example:**
    ```bash
    curl -X DELETE http://localhost:8000/api/v1/assessments/{assessment_id} \
      -H "X-User-ID: user-123-from-auth"
    ```
    """
    assessment = MOCK_ASSESSMENTS.get(str(assessment_id))
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")

    # Verify user owns this assessment
    if assessment.get("user_id") != user_id:
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this assessment"
        )

    # Soft delete
    MOCK_ASSESSMENTS[str(assessment_id)]["status"] = "archived"

    return None
