"""
FastAPI Application Entry Point
SCORE™ Backend API
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import (
    assessments,
    assessments_crud,
    health,
    questions,
    question_options,
    startups,
    answers,
    investors,
    investor_preferences,
    matches,
    industries,
    data_import,
)
from .config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    print(f"🚀 Starting SCORE™ Engine v{settings.FRAMEWORK_VERSION}")
    print(f"   Environment: {settings.ENVIRONMENT}")
    print(f"   Debug Mode: {settings.DEBUG}")

    yield

    # Shutdown
    print("👋 Shutting down SCORE™ Engine")


app = FastAPI(
    title="ScaleDux SCORE™ API",
    description="""
    ## Startup Investment Readiness Assessment System

    The SCORE™ (Startup Capability & Operational Readiness Evaluation) engine
    quantifies investment readiness through evidence-based assessment.

    ### Key Features
    - **Evidence-Weighted Scoring**: Self-reported vs. documented responses
    - **Stage-Adaptive Weights**: Dynamic weighting based on startup maturity
    - **Fatal Flags System**: Automatic penalties for critical gaps
    - **Dependency Resolution**: Cross-category logic enforcement (DAG)
    - **Time Decay**: Evidence freshness factored into confidence
    - **Glass Box Explainability**: Full calculation transparency

    ### Score Range
    - **300-400**: Critical (Legally uninvestable)
    - **401-550**: Poor (Major gaps)
    - **551-680**: Fair (Needs improvement)
    - **681-800**: Good (Investment-ready)
    - **801-900**: Excellent (Highly competitive)

    ### Mathematical Formula
    ```
    SCORE = clamp(⌊(S_raw × 600) + 300 - P_total⌋, 300, S_cap)
    ```

    where S_raw is the weighted sum of category scores, P_total is penalties,
    and S_cap is the dependency-driven ceiling.
    """,
    version=settings.FRAMEWORK_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])

# Assessment routers
app.include_router(
    assessments.router,
    prefix=f"{settings.API_V1_PREFIX}/assessments",
    tags=["Assessments"]
)
app.include_router(
    assessments_crud.router,
    prefix=f"{settings.API_V1_PREFIX}/assessments-crud",
    tags=["Assessments CRUD"]
)

# Question routers
app.include_router(
    questions.router,
    prefix=f"{settings.API_V1_PREFIX}/questions",
    tags=["Questions"]
)
app.include_router(
    question_options.router,
    prefix=f"{settings.API_V1_PREFIX}/question-options",
    tags=["Question Options"]
)

# Startup routers
app.include_router(
    startups.router,
    prefix=f"{settings.API_V1_PREFIX}/startups",
    tags=["Startups"]
)

# Answer routers
app.include_router(
    answers.router,
    prefix=f"{settings.API_V1_PREFIX}/answers",
    tags=["Answers"]
)

# Investor routers
app.include_router(
    investors.router,
    prefix=f"{settings.API_V1_PREFIX}/investors",
    tags=["Investors"]
)
app.include_router(
    investor_preferences.router,
    prefix=f"{settings.API_V1_PREFIX}/investor-preferences",
    tags=["Investor Preferences"]
)

# Matching routers
app.include_router(
    matches.router,
    prefix=f"{settings.API_V1_PREFIX}/matches",
    tags=["Matches"]
)

# Lookup routers
app.include_router(
    industries.router,
    prefix=f"{settings.API_V1_PREFIX}/industries",
    tags=["Industries"]
)

# Data Import routers
app.include_router(
    data_import.router,
    prefix=f"{settings.API_V1_PREFIX}/data",
    tags=["Data Import"]
)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if settings.DEBUG else "An unexpected error occurred",
        },
    )


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "ScaleDux SCORE™ API",
        "version": settings.FRAMEWORK_VERSION,
        "status": "operational",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )
