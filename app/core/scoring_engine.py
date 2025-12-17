"""
SCORE™ Scoring Engine - Core Mathematical Implementation

Implements the bounded weighted linear combination (BWLC) model with
non-linear penalty functions as specified in the technical specification.

Mathematical Formula:
    SCORE_final = clamp(⌊(S_raw × 600) + 300 - P_total⌋, 300, S_cap)

where:
    S_raw   = Σ(W_stage,c × S_c) for all categories c
    S_c     = min(Σ(w_sub,s × S_s), C_dep,c) for all sub-categories s
    S_s     = Σ V_earned,k / Σ V_max,k for all KPIs k
    V_earned,k = B_k × Q_correctness × E_evidence × D_decay(t)
"""

import math
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any
from uuid import UUID

from ..schemas.scoring import (
    ScoreBreakdown, CategoryScore, SubCategoryScore, KPIScore,
    FatalFlag, DependencyViolation, StartupStage,
    EvidenceType, AnswerCorrectness, KPIResponse
)


class ScoringEngine:
    """
    Deterministic expert system for startup readiness assessment

    This is a "Glass Box" model - every calculation is traceable and explainable.
    """

    # Constants from mathematical specification
    SCALING_FACTOR = 600
    BASE_OFFSET = 300
    MIN_SCORE = 300
    MAX_SCORE = 900

    # Evidence confidence multipliers
    EVIDENCE_MULTIPLIERS = {
        EvidenceType.SELF_REPORTED: 0.6,
        EvidenceType.DOCUMENT_UPLOADED: 1.0,
        EvidenceType.LINKEDIN_VERIFIED: 0.9,
        EvidenceType.REFERENCE_CHECK: 1.0,
        EvidenceType.CA_VERIFIED: 1.0,
    }

    # Correctness multipliers
    CORRECTNESS_MULTIPLIERS = {
        AnswerCorrectness.CORRECT: 1.0,
        AnswerCorrectness.PARTIAL: 0.5,
        AnswerCorrectness.INCORRECT: 0.0,
    }

    # Time decay lambdas (per day)
    DECAY_LAMBDA_DEFAULT = 0.005
    DECAY_LAMBDA_HIGH_VOLATILITY = 0.1    # Financial docs (10 days half-life)
    DECAY_LAMBDA_LOW_VOLATILITY = 0.001   # Legal docs (693 days half-life)

    def __init__(
        self,
        config: Dict[str, Any],
        fatal_flags_config: Dict[str, Any],
        dependencies_config: Dict[str, Any]
    ):
        """
        Initialize scoring engine with configuration

        Args:
            config: KPI definitions, weights, and scoring logic
            fatal_flags_config: Fatal flag rules and penalties
            dependencies_config: Cross-category dependency rules
        """
        self.config = config
        self.fatal_flags_config = fatal_flags_config
        self.dependencies_config = dependencies_config

    def calculate_score(
        self,
        responses: Dict[str, KPIResponse],
        stage: StartupStage,
        evidence_uploads: Dict[str, datetime]
    ) -> ScoreBreakdown:
        """
        Execute the complete scoring pipeline

        Pipeline:
        1. Calculate KPI scores (with evidence weighting and time decay)
        2. Aggregate sub-categories
        3. Aggregate categories
        4. Check fatal flags
        5. Apply dependencies and caps
        6. Calculate final score
        7. Generate explainability payload

        Args:
            responses: Map of kpi_id -> user response
            stage: Current startup stage
            evidence_uploads: Map of kpi_id -> upload timestamp

        Returns:
            Complete score breakdown with explanations
        """
        calculation_start = datetime.now(timezone.utc)

        # Step 1: Calculate KPI-level scores
        kpi_scores = self._calculate_kpi_scores(responses, evidence_uploads)

        # Step 2: Aggregate into sub-categories
        subcategory_scores = self._aggregate_subcategories(kpi_scores, stage)

        # Step 3: Aggregate into categories
        category_scores = self._aggregate_categories(subcategory_scores, stage)

        # Step 4: Check fatal flags
        fatal_flags = self._check_fatal_flags(responses)
        total_penalty = sum(flag.penalty_points for flag in fatal_flags)
        global_cap = min(
            (flag.global_cap for flag in fatal_flags if flag.global_cap),
            default=self.MAX_SCORE
        )

        # Step 5: Apply dependency rules
        dependency_violations = self._apply_dependencies(responses, category_scores)
        category_scores = self._apply_category_caps(
            category_scores, dependency_violations
        )

        # Step 6: Calculate raw score (weighted sum of categories)
        raw_score = sum(cat.raw_score * cat.stage_weight for cat in category_scores)

        # Step 7: Apply final transformation
        final_score = self._calculate_final_score(raw_score, total_penalty, global_cap)
        score_band = self._get_score_band(final_score)

        # Step 8: Generate actionable insights
        gaps = self._identify_gaps(kpi_scores, subcategory_scores)
        recommendations = self._generate_recommendations(
            fatal_flags, dependency_violations, gaps
        )

        # Calculate execution time
        calculation_end = datetime.now(timezone.utc)
        duration_ms = int((calculation_end - calculation_start).total_seconds() * 1000)

        return ScoreBreakdown(
            final_score=final_score,
            score_band=score_band,
            raw_score=raw_score,
            framework_version=self.config.get("version", "1.0.0"),
            category_scores=category_scores,
            fatal_flags_triggered=fatal_flags,
            total_penalty_points=total_penalty,
            global_cap_applied=global_cap if global_cap < self.MAX_SCORE else None,
            dependency_violations=dependency_violations,
            gaps=gaps,
            recommendations=recommendations,
            calculation_timestamp=calculation_end,
            calculation_duration_ms=duration_ms
        )

    def _calculate_kpi_scores(
        self,
        responses: Dict[str, KPIResponse],
        evidence_uploads: Dict[str, datetime]
    ) -> Dict[str, KPIScore]:
        """
        Calculate V_earned for each KPI

        Formula: V_earned,k = B_k × Q_correctness × E_evidence × D_decay(t)

        Args:
            responses: User responses for each KPI
            evidence_uploads: Upload timestamps for decay calculation

        Returns:
            Map of kpi_id -> calculated KPI score
        """
        kpi_scores = {}

        for kpi_id, kpi_config in self._get_all_kpis().items():
            response = responses.get(kpi_id)

            # Skip if not answered
            if not response:
                kpi_scores[kpi_id] = KPIScore(
                    kpi_id=kpi_id,
                    base_weight=kpi_config.get("base_weight", 0.0),
                    correctness_multiplier=0.0,
                    evidence_multiplier=0.0,
                    decay_multiplier=0.0,
                    earned_value=0.0,
                    max_possible=kpi_config.get("base_weight", 0.0)
                )
                continue

            # Base weight (B_k)
            base_weight = kpi_config.get("base_weight", 0.0)

            # Correctness multiplier (Q_correctness)
            correctness = self._evaluate_correctness(
                kpi_id, response.value, kpi_config
            )
            correctness_mult = self.CORRECTNESS_MULTIPLIERS[correctness]

            # Evidence multiplier (E_evidence)
            evidence_mult = self.EVIDENCE_MULTIPLIERS.get(
                response.evidence_type, 0.6
            )

            # Time decay multiplier (D_decay)
            decay_mult = self._calculate_time_decay(
                kpi_id, response.answered_at, evidence_uploads.get(kpi_id)
            )

            # Final earned value
            earned_value = base_weight * correctness_mult * evidence_mult * decay_mult

            kpi_scores[kpi_id] = KPIScore(
                kpi_id=kpi_id,
                base_weight=base_weight,
                correctness_multiplier=correctness_mult,
                evidence_multiplier=evidence_mult,
                decay_multiplier=decay_mult,
                earned_value=earned_value,
                max_possible=base_weight
            )

        return kpi_scores

    def _evaluate_correctness(
        self,
        kpi_id: str,
        value: Any,
        kpi_config: Dict[str, Any]
    ) -> AnswerCorrectness:
        """
        Evaluate answer correctness based on scoring logic

        This implements the business rules for what constitutes a "green",
        "yellow", or "red" answer.

        Args:
            kpi_id: KPI identifier
            value: User's answer
            kpi_config: KPI configuration with scoring logic

        Returns:
            Correctness level
        """
        scoring_logic = kpi_config.get("scoring_logic", {})

        # For boolean KPIs
        if isinstance(value, bool):
            green_condition = scoring_logic.get("green", "")
            red_condition = scoring_logic.get("red", "")

            if "true" in green_condition.lower() and value is True:
                return AnswerCorrectness.CORRECT
            if "false" in red_condition.lower() and value is False:
                return AnswerCorrectness.INCORRECT

        # For numeric KPIs (ranges)
        if isinstance(value, (int, float)):
            green_range = self._parse_range(scoring_logic.get("green", ""))
            yellow_range = self._parse_range(scoring_logic.get("yellow", ""))

            if green_range and self._in_range(value, green_range):
                return AnswerCorrectness.CORRECT
            if yellow_range and self._in_range(value, yellow_range):
                return AnswerCorrectness.PARTIAL

        # For enum KPIs
        if isinstance(value, str):
            green_values = self._parse_enum_list(scoring_logic.get("green", ""))
            yellow_values = self._parse_enum_list(scoring_logic.get("yellow", ""))

            if value in green_values:
                return AnswerCorrectness.CORRECT
            if value in yellow_values:
                return AnswerCorrectness.PARTIAL

        return AnswerCorrectness.INCORRECT

    def _calculate_time_decay(
        self,
        kpi_id: str,
        answered_at: datetime,
        uploaded_at: Optional[datetime]
    ) -> float:
        """
        Calculate exponential time decay: D_decay(t) = e^(-λt)

        Args:
            kpi_id: KPI identifier (determines decay rate)
            answered_at: When response was given
            uploaded_at: When document was uploaded (if applicable)

        Returns:
            Decay multiplier between 0.0 and 1.0
        """
        if not uploaded_at:
            return 1.0  # No decay for recent answers without documents

        # Determine decay rate based on KPI type
        decay_lambda = self._get_decay_lambda(kpi_id)

        # Calculate days since upload
        now = datetime.now(timezone.utc)
        days_old = (now - uploaded_at).total_seconds() / 86400

        # Exponential decay formula
        decay = math.exp(-decay_lambda * days_old)

        return max(decay, 0.0)  # Ensure non-negative

    def _get_decay_lambda(self, kpi_id: str) -> float:
        """
        Get decay rate for specific KPI type

        Financial documents decay fast (high volatility)
        Legal documents decay slowly (low volatility)
        """
        # High volatility KPIs (bank statements, revenue, runway)
        if any(keyword in kpi_id for keyword in ["financial", "runway", "revenue", "burn"]):
            return self.DECAY_LAMBDA_HIGH_VOLATILITY

        # Low volatility KPIs (incorporation, contracts, IP)
        if any(keyword in kpi_id for keyword in ["legal", "incorporation", "patent", "contract"]):
            return self.DECAY_LAMBDA_LOW_VOLATILITY

        return self.DECAY_LAMBDA_DEFAULT

    def _aggregate_subcategories(
        self,
        kpi_scores: Dict[str, KPIScore],
        stage: StartupStage
    ) -> Dict[str, SubCategoryScore]:
        """
        Aggregate KPI scores into sub-category scores

        Formula: S_s = Σ V_earned,k / Σ V_max,k

        Args:
            kpi_scores: Calculated KPI scores
            stage: Current startup stage

        Returns:
            Map of sub_category_id -> aggregated score
        """
        subcategory_scores = {}

        for category_id, category_config in self.config.get("categories", {}).items():
            for subcat_id, subcat_config in category_config.get("sub_categories", {}).items():
                kpi_ids = subcat_config.get("kpis", {}).keys()

                relevant_scores = [
                    kpi_scores[kpi_id] for kpi_id in kpi_ids if kpi_id in kpi_scores
                ]

                total_earned = sum(score.earned_value for score in relevant_scores)
                total_possible = sum(score.max_possible for score in relevant_scores)

                normalized_score = (
                    total_earned / total_possible if total_possible > 0 else 0.0
                )

                kpis_completed = sum(
                    1 for score in relevant_scores if score.earned_value > 0
                )

                subcategory_scores[subcat_id] = SubCategoryScore(
                    sub_category_id=subcat_id,
                    weight=subcat_config.get("weight", 0.0),
                    kpi_scores=relevant_scores,
                    total_earned=total_earned,
                    total_possible=total_possible,
                    normalized_score=normalized_score,
                    kpis_completed=kpis_completed,
                    kpis_total=len(kpi_ids)
                )

        return subcategory_scores

    def _aggregate_categories(
        self,
        subcategory_scores: Dict[str, SubCategoryScore],
        stage: StartupStage
    ) -> List[CategoryScore]:
        """
        Aggregate sub-category scores into category scores

        Formula: S_c = Σ(w_sub,s × S_s) for all sub-categories s

        Args:
            subcategory_scores: Calculated sub-category scores
            stage: Current startup stage (determines weights)

        Returns:
            List of category scores
        """
        category_scores = []

        for category_id, category_config in self.config.get("categories", {}).items():
            # Get stage-specific weight
            stage_weight = self._get_stage_weight(category_config, stage)

            # Get sub-categories for this category
            subcat_ids = category_config.get("sub_categories", {}).keys()
            relevant_subcats = [
                subcategory_scores[subcat_id]
                for subcat_id in subcat_ids
                if subcat_id in subcategory_scores
            ]

            # Weighted sum of sub-categories
            raw_score = sum(
                subcat.weight * subcat.normalized_score
                for subcat in relevant_subcats
            )

            # Initially, no cap (will be applied in dependency step)
            capped_score = raw_score

            # Calculate contribution to final score
            weighted_contribution = capped_score * stage_weight
            max_possible_contribution = stage_weight

            category_scores.append(CategoryScore(
                category_id=category_id,
                stage_weight=stage_weight,
                sub_category_scores=relevant_subcats,
                raw_score=raw_score,
                capped_score=capped_score,
                weighted_contribution=weighted_contribution,
                max_possible_contribution=max_possible_contribution
            ))

        return category_scores

    def _check_fatal_flags(
        self,
        responses: Dict[str, KPIResponse]
    ) -> List[FatalFlag]:
        """
        Evaluate fatal flag conditions

        Fatal flags impose penalties and caps on the final score.

        Args:
            responses: User responses

        Returns:
            List of triggered fatal flags
        """
        triggered_flags = []

        for flag in self.fatal_flags_config.get("fatal_flags", []):
            flag_id = flag.get("flag_id")
            trigger_kpi = flag.get("trigger_kpi")
            condition = flag.get("trigger_condition")

            response = responses.get(trigger_kpi)

            if self._evaluate_condition(response, condition):
                triggered_flags.append(FatalFlag(
                    flag_id=flag_id,
                    trigger_kpi=trigger_kpi,
                    penalty_points=flag.get("penalty_points", 0),
                    global_cap=flag.get("global_cap"),
                    severity=flag.get("severity", "warning"),
                    reason=flag.get("reason", ""),
                    user_message=flag.get("user_message", "")
                ))

        return triggered_flags

    def _apply_dependencies(
        self,
        responses: Dict[str, KPIResponse],
        category_scores: List[CategoryScore]
    ) -> List[DependencyViolation]:
        """
        Check cross-category dependency rules

        Example: "No technical co-founder" caps "Solution" category at 60%

        Args:
            responses: User responses
            category_scores: Calculated category scores

        Returns:
            List of dependency violations
        """
        violations = []

        for rule in self.dependencies_config.get("dependency_rules", []):
            source_kpi = rule.get("source_kpi")
            condition = rule.get("condition")
            response = responses.get(source_kpi)

            if self._evaluate_condition(response, condition):
                violations.append(DependencyViolation(
                    dependency_rule_id=rule.get("rule_id"),
                    source_kpi=source_kpi,
                    target_category=rule.get("target_category"),
                    action=rule.get("action"),
                    cap_value=rule.get("cap_value"),
                    reason=rule.get("reason", "")
                ))

        return violations

    def _apply_category_caps(
        self,
        category_scores: List[CategoryScore],
        violations: List[DependencyViolation]
    ) -> List[CategoryScore]:
        """
        Apply dependency-driven caps to category scores

        Formula: S_c = min(S_c_raw, C_dep,c)

        Args:
            category_scores: Original category scores
            violations: Dependency violations with cap values

        Returns:
            Updated category scores with caps applied
        """
        for category in category_scores:
            applicable_violations = [
                v for v in violations
                if v.target_category == category.category_id and v.action == "apply_cap"
            ]

            if applicable_violations:
                # Apply the most restrictive cap
                min_cap = min(v.cap_value for v in applicable_violations if v.cap_value)
                if min_cap and category.capped_score > min_cap:
                    category.capped_score = min_cap
                    category.applied_cap = min_cap
                    category.cap_reason = applicable_violations[0].reason

        return category_scores

    def _calculate_final_score(
        self,
        raw_score: float,
        penalty_points: int,
        global_cap: int
    ) -> int:
        """
        Apply final transformation to get SCORE in 300-900 range

        Formula: SCORE_final = clamp(⌊(S_raw × 600) + 300 - P_total⌋, 300, S_cap)

        Args:
            raw_score: Weighted sum of category scores (0.0-1.0)
            penalty_points: Sum of penalty points from fatal flags
            global_cap: Maximum allowed score from blocking flags

        Returns:
            Final SCORE as integer
        """
        # Linear transformation
        scaled = (raw_score * self.SCALING_FACTOR) + self.BASE_OFFSET

        # Apply penalty
        penalized = scaled - penalty_points

        # Floor to integer
        floored = math.floor(penalized)

        # Clamp to bounds
        clamped = max(self.MIN_SCORE, min(floored, global_cap))

        return int(clamped)

    def _get_score_band(self, score: int) -> str:
        """Map numeric score to categorical band"""
        if score <= 400:
            return "critical"
        elif score <= 550:
            return "poor"
        elif score <= 680:
            return "fair"
        elif score <= 800:
            return "good"
        else:
            return "excellent"

    def _identify_gaps(
        self,
        kpi_scores: Dict[str, KPIScore],
        subcategory_scores: Dict[str, SubCategoryScore]
    ) -> List[Dict[str, Any]]:
        """Identify missing or low-scoring KPIs for recommendations"""
        gaps = []

        for kpi_id, score in kpi_scores.items():
            if score.earned_value == 0:
                gaps.append({
                    "kpi_id": kpi_id,
                    "issue": "not_answered",
                    "potential_gain": score.max_possible
                })
            elif score.evidence_multiplier < 1.0:
                gaps.append({
                    "kpi_id": kpi_id,
                    "issue": "no_evidence",
                    "potential_gain": score.max_possible * (1.0 - score.evidence_multiplier)
                })

        return sorted(gaps, key=lambda x: x["potential_gain"], reverse=True)[:10]

    def _generate_recommendations(
        self,
        fatal_flags: List[FatalFlag],
        dependency_violations: List[DependencyViolation],
        gaps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations for improvement"""
        recommendations = []

        # Fatal flags are top priority
        for flag in fatal_flags:
            recommendations.append(flag.user_message)

        # Dependency violations
        for violation in dependency_violations:
            recommendations.append(
                f"Resolve '{violation.source_kpi}' to unlock '{violation.target_category}' category"
            )

        # Top 3 gaps
        for gap in gaps[:3]:
            if gap["issue"] == "not_answered":
                recommendations.append(f"Answer question: {gap['kpi_id']}")
            elif gap["issue"] == "no_evidence":
                recommendations.append(f"Upload evidence for: {gap['kpi_id']}")

        return recommendations

    # Helper methods

    def _get_all_kpis(self) -> Dict[str, Any]:
        """Flatten all KPIs from nested config structure"""
        kpis = {}
        for category in self.config.get("categories", {}).values():
            for subcat in category.get("sub_categories", {}).values():
                kpis.update(subcat.get("kpis", {}))
        return kpis

    def _get_stage_weight(self, category_config: Dict[str, Any], stage: StartupStage) -> float:
        """Get stage-specific weight for a category"""
        weight_key = f"weight_{stage.value}"
        return category_config.get(weight_key, 0.0)

    def _evaluate_condition(self, response: Optional[KPIResponse], condition: str) -> bool:
        """Evaluate a condition string against a response"""
        if not response:
            return "null" in condition or "false" in condition

        value = response.value

        # Simple condition evaluation (extend as needed)
        if "==" in condition:
            expected = condition.split("==")[1].strip()
            if expected.lower() == "true":
                return value is True
            elif expected.lower() == "false":
                return value is False
            else:
                return str(value) == expected

        return False

    def _parse_range(self, range_str: str) -> Optional[Tuple[float, float]]:
        """Parse range string like '≥6 months' or '<3 months'"""
        # Simplified parser - extend as needed
        if "≥" in range_str or ">=" in range_str:
            parts = range_str.replace("≥", ">=").split(">=")
            if len(parts) == 2:
                try:
                    val = float(parts[1].strip().split()[0])
                    return (val, float('inf'))
                except ValueError:
                    pass

        if "<" in range_str and "<=" not in range_str:
            parts = range_str.split("<")
            if len(parts) == 2:
                try:
                    val = float(parts[1].strip().split()[0])
                    return (0, val)
                except ValueError:
                    pass

        return None

    def _in_range(self, value: float, range_tuple: Tuple[float, float]) -> bool:
        """Check if value is within range"""
        return range_tuple[0] <= value < range_tuple[1]

    def _parse_enum_list(self, enum_str: str) -> List[str]:
        """Parse comma-separated enum values"""
        return [v.strip().strip("'\"") for v in enum_str.split(",") if v.strip()]
