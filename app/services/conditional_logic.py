"""
Conditional Logic Service for Dynamic Question Filtering

This service evaluates which questions should be shown based on:
- Previous answers
- Startup stage
- Conditional rules from questions
"""

from typing import List, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.question import Question, QuestionCategory, AnswerType
from app.models.answer import StartupAnswer
from app.models.startup import Startup, StartupStage


class ConditionalLogicService:
    """
    Service to filter questions based on conditional logic

    Rules evaluated:
    1. Stage-specific questions (some questions only for certain stages)
    2. Answer-dependent questions (show/hide based on previous answers)
    3. Category dependencies (e.g., team questions before execution questions)
    """

    def __init__(self, db: Session):
        self.db = db

    def get_applicable_questions(
        self,
        startup_id: UUID,
        category: Optional[QuestionCategory] = None,
        limit: int = 1000
    ) -> List[Question]:
        """
        Get questions applicable to this startup based on:
        - Their current stage
        - Their previous answers
        - Conditional logic rules

        Args:
            startup_id: UUID of the startup
            category: Optional category filter
            limit: Maximum questions to return

        Returns:
            List of applicable questions in recommended order
        """
        # Get startup details
        startup = self.db.query(Startup).filter(Startup.id == startup_id).first()
        if not startup:
            return []

        # Get all active questions
        query = self.db.query(Question).filter(Question.is_active == True)

        if category:
            query = query.filter(Question.category == category)

        all_questions = query.all()

        # Get existing answers for this startup
        existing_answers = self.db.query(StartupAnswer).filter(
            StartupAnswer.startup_id == startup_id
        ).all()

        answer_map = self._build_answer_map(existing_answers)

        # Filter questions based on conditions
        applicable_questions = []

        for question in all_questions:
            if self._should_show_question(question, startup, answer_map):
                applicable_questions.append(question)

        # Order by category and weight
        applicable_questions.sort(
            key=lambda q: (q.category.value, -q.base_weight)
        )

        return applicable_questions[:limit]

    def _build_answer_map(self, answers: List[StartupAnswer]) -> Dict[UUID, any]:
        """Build a map of question_id -> answer value"""
        answer_map = {}
        for ans in answers:
            if ans.answer_number is not None:
                answer_map[ans.question_id] = ans.answer_number
            elif ans.answer_text is not None:
                answer_map[ans.question_id] = ans.answer_text
            elif ans.selected_option_id is not None:
                answer_map[ans.question_id] = ans.selected_option_id
        return answer_map

    def _should_show_question(
        self,
        question: Question,
        startup: Startup,
        answer_map: Dict[UUID, any]
    ) -> bool:
        """
        Determine if a question should be shown based on:
        1. Startup stage
        2. Previous answers (conditional logic)
        3. Question text patterns (simple rule matching)
        """
        # Rule 1: Team size questions
        # If startup has "founder" questions answered, filter accordingly
        if self._is_founder_team_question(question):
            has_team = self._has_team_members(answer_map)
            if not has_team and "co-founder" in question.text.lower():
                return False  # Skip co-founder questions if solo

        # Rule 2: Stage-specific questions
        # Some questions are only for later stages
        if startup.stage in [StartupStage.IDEA, StartupStage.MVP_NO_TRACTION]:
            # Skip advanced traction questions for early stage
            if self._is_advanced_traction_question(question):
                return False

        # Rule 3: MVP/Product questions
        # If no MVP yet, skip product-specific questions
        if startup.stage == StartupStage.IDEA:
            if self._is_mvp_required_question(question):
                return False

        # Rule 4: Revenue questions
        # Only show revenue questions if company has revenue
        if self._is_revenue_question(question):
            has_revenue = self._has_revenue(answer_map)
            if not has_revenue:
                return False

        return True

    def _is_founder_team_question(self, question: Question) -> bool:
        """Check if question is about founder/team"""
        keywords = ["founder", "co-founder", "team", "equity split"]
        return any(kw in question.text.lower() for kw in keywords)

    def _has_team_members(self, answer_map: Dict[UUID, any]) -> bool:
        """Check if startup has indicated team members"""
        # This is a simplified check
        # In production, you'd check specific question IDs
        for value in answer_map.values():
            if isinstance(value, (int, float)) and value > 1:
                # Assuming number questions about team size
                return True
        return False

    def _is_advanced_traction_question(self, question: Question) -> bool:
        """Check if question requires advanced traction"""
        if question.category != QuestionCategory.TRACTION:
            return False

        advanced_keywords = [
            "retention rate",
            "churn",
            "ltv",
            "cac",
            "payback period",
            "arr",
            "mrr growth"
        ]
        return any(kw in question.text.lower() for kw in advanced_keywords)

    def _is_mvp_required_question(self, question: Question) -> bool:
        """Check if question requires MVP to exist"""
        mvp_keywords = [
            "product features",
            "user feedback",
            "mvp",
            "prototype",
            "beta users",
            "active users"
        ]
        return any(kw in question.text.lower() for kw in mvp_keywords)

    def _is_revenue_question(self, question: Question) -> bool:
        """Check if question is about revenue"""
        revenue_keywords = [
            "revenue",
            "mrr",
            "arr",
            "sales",
            "paying customers",
            "pricing"
        ]
        return any(kw in question.text.lower() for kw in revenue_keywords)

    def _has_revenue(self, answer_map: Dict[UUID, any]) -> bool:
        """Check if startup has indicated revenue"""
        # Simplified check - in production, check specific revenue question IDs
        for value in answer_map.values():
            if isinstance(value, (int, float)) and value > 0:
                # Could be revenue amount
                return True
        return False

    def get_next_unanswered_questions(
        self,
        startup_id: UUID,
        count: int = 10
    ) -> List[Question]:
        """
        Get the next set of unanswered questions for this startup

        Args:
            startup_id: UUID of the startup
            count: Number of questions to return

        Returns:
            List of next questions to answer
        """
        # Get applicable questions
        applicable = self.get_applicable_questions(startup_id)

        # Get answered question IDs
        answered = self.db.query(StartupAnswer.question_id).filter(
            StartupAnswer.startup_id == startup_id
        ).all()
        answered_ids = {q[0] for q in answered}

        # Filter to unanswered
        unanswered = [q for q in applicable if q.id not in answered_ids]

        return unanswered[:count]

    def get_progress(self, startup_id: UUID) -> Dict:
        """
        Get assessment progress for a startup

        Returns:
            Dictionary with progress statistics
        """
        applicable = self.get_applicable_questions(startup_id)

        answered = self.db.query(StartupAnswer).filter(
            StartupAnswer.startup_id == startup_id
        ).all()

        answered_ids = {ans.question_id for ans in answered}
        applicable_ids = {q.id for q in applicable}

        # Calculate progress
        total_applicable = len(applicable_ids)
        total_answered = len(answered_ids & applicable_ids)

        progress_pct = (total_answered / total_applicable * 100) if total_applicable > 0 else 0

        # By category
        by_category = {}
        for category in QuestionCategory:
            cat_questions = [q for q in applicable if q.category == category]
            cat_answered = len([q for q in cat_questions if q.id in answered_ids])
            by_category[category.value] = {
                'total': len(cat_questions),
                'answered': cat_answered,
                'progress': (cat_answered / len(cat_questions) * 100) if cat_questions else 0
            }

        return {
            'total_applicable': total_applicable,
            'total_answered': total_answered,
            'progress_percentage': round(progress_pct, 1),
            'by_category': by_category
        }
