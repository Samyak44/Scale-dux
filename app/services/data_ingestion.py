"""Data ingestion service for importing questions from Excel files"""

import pandas as pd
from typing import Dict, List, Tuple, Optional
from uuid import UUID
import re

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.models.question import Question, QuestionOption, AnswerType, QuestionCategory
from app.models.base import uuid4


class ExcelDataIngestionService:
    """
    Service to ingest question data from Excel files

    Expected Excel structure:
    - Multiple sheets named 'Category1', 'Category2', etc.
    - Each sheet contains questions with columns:
        - Sub-Category
        - KPI ID
        - KPI / Input (Human Question Format)
        - Type (Boolean, Number, Enum, Text, etc.)
        - KPI Base Weight
        - And other metadata
    """

    # Mapping from Excel types to our AnswerType enum
    TYPE_MAPPING = {
        'boolean': AnswerType.BOOLEAN,
        'number': AnswerType.NUMBER,
        'text': AnswerType.TEXT,
        'enum': AnswerType.ENUM,
    }

    # Mapping from sheet names to categories
    CATEGORY_MAPPING = {
        'category1': QuestionCategory.TEAM,
        'category2': QuestionCategory.MARKET,
        'category3': QuestionCategory.MARKET,
        'category4': QuestionCategory.MARKET,
        'category5': QuestionCategory.FINANCE,
        'category6': QuestionCategory.TRACTION,
        'category7': QuestionCategory.TRACTION,
    }

    def __init__(self, db: Session):
        self.db = db
        self.stats = {
            'questions_created': 0,
            'questions_updated': 0,
            'options_created': 0,
            'errors': []
        }

    def ingest_from_file(self, file_path: str, clear_existing: bool = False) -> Dict:
        """
        Ingest questions from an Excel file

        Args:
            file_path: Path to the Excel file
            clear_existing: If True, delete all existing questions before importing

        Returns:
            Dictionary with ingestion statistics
        """
        try:
            # Clear existing data if requested
            if clear_existing:
                self._clear_existing_data()

            # Read Excel file
            xls = pd.ExcelFile(file_path)

            # Process each category sheet
            for sheet_name in xls.sheet_names:
                if sheet_name.lower().startswith('category'):
                    self._process_category_sheet(xls, sheet_name)

            # Commit all changes
            self.db.commit()

            return self.stats

        except Exception as e:
            self.db.rollback()
            self.stats['errors'].append(f"Fatal error: {str(e)}")
            raise

    def _clear_existing_data(self):
        """Delete all existing questions and options"""
        self.db.query(QuestionOption).delete()
        self.db.query(Question).delete()
        self.db.commit()

    def _process_category_sheet(self, xls: pd.ExcelFile, sheet_name: str):
        """Process a single category sheet"""
        try:
            # Read the sheet
            df = pd.read_excel(xls, sheet_name=sheet_name)

            # Get category from sheet name
            category = self._get_category_from_sheet(sheet_name)

            # Process each row as a question
            for idx, row in df.iterrows():
                try:
                    self._process_question_row(row, category, sheet_name)
                except Exception as e:
                    error_msg = f"Sheet '{sheet_name}', Row {idx + 2}: {str(e)}"
                    self.stats['errors'].append(error_msg)
                    print(f"Error: {error_msg}")
                    continue

        except Exception as e:
            self.stats['errors'].append(f"Error processing sheet '{sheet_name}': {str(e)}")

    def _get_category_from_sheet(self, sheet_name: str) -> QuestionCategory:
        """Map sheet name to question category"""
        sheet_key = sheet_name.lower().replace(' ', '')
        return self.CATEGORY_MAPPING.get(sheet_key, QuestionCategory.MARKET)

    def _process_question_row(self, row: pd.Series, category: QuestionCategory, sheet_name: str):
        """Process a single row as a question"""
        # Extract key fields
        kpi_id = self._safe_str(row.get('KPI ID'))
        question_text = self._safe_str(row.get('KPI / Input (Human Question Format)'))
        type_str = self._safe_str(row.get('Type'))
        base_weight = self._safe_float(row.get('KPI Base Weight'), 1.0)
        sub_category = self._safe_str(row.get('Sub-Category'))

        # Skip if essential fields are missing
        if not kpi_id or not question_text or not type_str:
            return

        # Skip header rows or invalid data
        if kpi_id == 'KPI ID' or question_text == 'KPI / Input (Human Question Format)':
            return

        # Determine answer type
        answer_type = self._parse_answer_type(type_str)

        # Create help text from sub-category
        help_text = f"Sub-Category: {sub_category}" if sub_category else None

        # Check if question already exists (by KPI ID or similar text)
        existing_question = self.db.query(Question).filter(
            Question.text == question_text
        ).first()

        if existing_question:
            # Update existing question
            existing_question.category = category
            existing_question.answer_type = answer_type
            existing_question.base_weight = base_weight
            existing_question.help_text = help_text
            existing_question.is_active = True
            question = existing_question
            self.stats['questions_updated'] += 1
        else:
            # Create new question
            question = Question(
                id=uuid4(),
                text=question_text,
                category=category,
                answer_type=answer_type,
                base_weight=base_weight,
                help_text=help_text,
                is_active=True
            )
            self.db.add(question)
            self.stats['questions_created'] += 1

        # Flush to get the question ID
        self.db.flush()

        # If it's an enum type, create options
        if answer_type == AnswerType.ENUM:
            self._create_question_options(question, type_str)

    def _create_question_options(self, question: Question, type_str: str):
        """Create options for enum-type questions"""
        # Parse enum options from type string
        # Format: "Enum (option1 | option2 | option3)"
        options = self._parse_enum_options(type_str)

        if not options:
            return

        # Delete existing options for this question
        self.db.query(QuestionOption).filter(
            QuestionOption.question_id == question.id
        ).delete()

        # Create new options
        for idx, option_value in enumerate(options):
            option = QuestionOption(
                id=uuid4(),
                question_id=question.id,
                value=option_value,
                score_weight=1.0,  # Default weight
                display_order=idx
            )
            self.db.add(option)
            self.stats['options_created'] += 1

    def _parse_answer_type(self, type_str: str) -> AnswerType:
        """Parse answer type from Excel type string"""
        type_str = type_str.lower().strip()

        if 'boolean' in type_str:
            return AnswerType.BOOLEAN
        elif 'number' in type_str or 'min:' in type_str:
            return AnswerType.NUMBER
        elif 'enum' in type_str:
            return AnswerType.ENUM
        elif 'text' in type_str:
            return AnswerType.TEXT
        else:
            # Default to text for unknown types
            return AnswerType.TEXT

    def _parse_enum_options(self, type_str: str) -> List[str]:
        """
        Parse enum options from type string

        Examples:
            "Enum (option1 | option2 | option3)" -> ["option1", "option2", "option3"]
            "Enum (1_to_2_weeks | 3_to_4_weeks)" -> ["1_to_2_weeks", "3_to_4_weeks"]
        """
        # Find content within parentheses
        match = re.search(r'\((.*?)\)', type_str)
        if not match:
            return []

        options_str = match.group(1)

        # Split by | and clean up
        options = [opt.strip() for opt in options_str.split('|')]

        # Filter out empty options
        options = [opt for opt in options if opt]

        return options

    def _safe_str(self, value) -> Optional[str]:
        """Safely convert value to string"""
        if pd.isna(value):
            return None
        return str(value).strip()

    def _safe_float(self, value, default: float = 0.0) -> float:
        """Safely convert value to float"""
        if pd.isna(value):
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default


def ingest_excel_file(db: Session, file_path: str, clear_existing: bool = False) -> Dict:
    """
    Convenience function to ingest data from Excel file

    Args:
        db: Database session
        file_path: Path to Excel file
        clear_existing: Whether to clear existing data before import

    Returns:
        Dictionary with ingestion statistics
    """
    service = ExcelDataIngestionService(db)
    return service.ingest_from_file(file_path, clear_existing)
