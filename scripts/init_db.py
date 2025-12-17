#!/usr/bin/env python3
"""
Initialize database and create tables

This script:
1. Creates all tables from SQLAlchemy models
2. Seeds the 18 Team category questions from YAML config
3. Creates a sample startup for testing
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import yaml

from app.models.base import Base
from app.models.startup import Startup, StartupStage
from app.models.assessment import Assessment, AssessmentStatus


# Database URL (SQLite for local development)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scaledux.db")

print(f"📊 Connecting to database: {DATABASE_URL}")


def init_database():
    """Create all tables"""
    engine = create_engine(DATABASE_URL, echo=True)

    print("\n🏗️  Creating tables...")
    Base.metadata.create_all(bind=engine)

    print("\n✅ Database tables created successfully!")

    return engine


def seed_sample_data(engine):
    """Seed database with sample startup"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Check if sample data already exists
        existing = session.query(Startup).filter_by(name="Sample SaaS Startup").first()
        if existing:
            print("\n⏭️  Sample data already exists, skipping...")
            return

        print("\n🌱 Seeding sample data...")

        # Create sample startup
        startup = Startup(
            name="Sample SaaS Startup",
            user_id="sample-user-123",  # Sample user_id from auth backend
            stage=StartupStage.MVP_NO_TRACTION
        )
        session.add(startup)
        session.commit()

        # Create draft assessment
        assessment = Assessment(
            startup_id=startup.id,
            stage=StartupStage.MVP_NO_TRACTION,
            framework_version="1.0.0",
            status=AssessmentStatus.DRAFT,
            responses={}
        )
        session.add(assessment)
        session.commit()

        print(f"   ✅ Created startup: {startup.name} (ID: {startup.id})")
        print(f"   ✅ Created assessment (ID: {assessment.id})")
        print(f"\n📝 You can now test the API with:")
        print(f"   Startup ID: {startup.id}")
        print(f"   Assessment ID: {assessment.id}")

    except Exception as e:
        print(f"\n❌ Error seeding data: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def load_questions_from_yaml():
    """Load the 18 questions from YAML config"""
    config_path = Path(__file__).parent.parent / "app" / "config" / "kpis_sample.yaml"

    if not config_path.exists():
        print(f"\n⚠️  Config file not found: {config_path}")
        return None

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Extract all questions
    questions = []
    for category_id, category_data in config.get("categories", {}).items():
        for subcat_id, subcat_data in category_data.get("sub_categories", {}).items():
            for kpi_id, kpi_data in subcat_data.get("kpis", {}).items():
                questions.append({
                    "kpi_id": kpi_id,
                    "category": category_id,
                    "sub_category": subcat_id,
                    "question": kpi_data.get("question"),
                    "type": kpi_data.get("type"),
                    "priority": kpi_data.get("priority"),
                    "base_weight": kpi_data.get("base_weight"),
                })

    print(f"\n📖 Loaded {len(questions)} questions from config:")
    for i, q in enumerate(questions[:5], 1):
        print(f"   {i}. {q['kpi_id']}: {q['question'][:60]}...")
    print(f"   ... and {len(questions) - 5} more")

    return questions


def main():
    """Main initialization function"""
    print("=" * 60)
    print("ScaleDux SCORE™ Database Initialization")
    print("=" * 60)

    # Create tables
    engine = init_database()

    # Seed sample data
    seed_sample_data(engine)

    # Load and display questions
    questions = load_questions_from_yaml()

    if questions:
        print(f"\n✅ System ready with {len(questions)} questions configured!")

    print("\n" + "=" * 60)
    print("🚀 Next steps:")
    print("   1. Start the API: uvicorn app.main:app --reload")
    print("   2. Open Swagger UI: http://localhost:8000/docs")
    print("   3. Test with the sample startup ID printed above")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
