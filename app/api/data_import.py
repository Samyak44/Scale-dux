"""Data import API endpoints for bulk importing questions"""

import os
import tempfile
from typing import Dict

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.data_ingestion import ingest_excel_file

router = APIRouter()


@router.post("/import/excel", response_model=Dict)
async def import_questions_from_excel(
    file: UploadFile = File(..., description="Excel file (.xlsx) containing questions"),
    clear_existing: bool = Query(
        False,
        description="If true, delete all existing questions before importing"
    ),
    db: Session = Depends(get_db)
):
    """
    Import questions from Excel file

    This endpoint accepts an Excel file in the ScaleDUX format and imports:
    - Questions from all category sheets
    - Question options for enum-type questions
    - Categories and weights

    **Expected Excel Structure:**
    - Multiple sheets named 'Category1', 'Category2', etc.
    - Each sheet should have columns:
      - Sub-Category
      - KPI ID
      - KPI / Input (Human Question Format)
      - Type (Boolean, Number, Enum, Text)
      - KPI Base Weight
      - And other metadata

    **Parameters:**
    - `file`: Excel file (.xlsx format)
    - `clear_existing`: If true, removes all existing questions before import (use with caution!)

    **Returns:**
    - Statistics about the import:
      - questions_created: Number of new questions created
      - questions_updated: Number of existing questions updated
      - options_created: Number of question options created
      - errors: List of any errors encountered

    **Security Notes:**
    - Only .xlsx files are accepted
    - Files are processed in memory and discarded after import
    - Maximum file size is limited by FastAPI settings
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx) are supported"
        )

    # Create temporary file to store upload
    temp_file = None
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as temp:
            # Read and write uploaded file
            content = await file.read()
            temp.write(content)
            temp_file = temp.name

        # Perform ingestion
        stats = ingest_excel_file(db, temp_file, clear_existing=clear_existing)

        return {
            "success": True,
            "filename": file.filename,
            "statistics": stats,
            "message": f"Successfully imported {stats['questions_created']} questions"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error importing file: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass


@router.get("/import/template-info")
async def get_template_info():
    """
    Get information about the expected Excel template format

    Returns details about the required structure for importing questions.
    """
    return {
        "template_format": "ScaleDUX Excel Format",
        "required_sheets": [
            "Category1", "Category2", "Category3", "Category4",
            "Category5", "Category6", "Category7"
        ],
        "required_columns": [
            "Sub-Category",
            "KPI ID",
            "KPI / Input (Human Question Format)",
            "Type",
            "KPI Base Weight"
        ],
        "supported_types": {
            "Boolean": "True/False questions",
            "Number": "Numeric answers",
            "Enum": "Multiple choice (options separated by |)",
            "Text": "Free text answers"
        },
        "category_mapping": {
            "Category1": "team",
            "Category2": "market",
            "Category3": "market",
            "Category4": "market",
            "Category5": "finance",
            "Category6": "traction",
            "Category7": "traction"
        },
        "notes": [
            "Enum types should use format: Enum (option1 | option2 | option3)",
            "Questions are matched by text - duplicate texts will be updated",
            "Use clear_existing=true parameter to remove all questions before import (caution!)",
            "Sub-Category is used as help_text for questions"
        ]
    }


@router.post("/import/validate-excel")
async def validate_excel_file(
    file: UploadFile = File(..., description="Excel file (.xlsx) to validate"),
):
    """
    Validate an Excel file without importing

    Checks if the file structure is correct and returns any potential issues.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith('.xlsx'):
        raise HTTPException(
            status_code=400,
            detail="Only Excel files (.xlsx) are supported"
        )

    temp_file = None
    try:
        import pandas as pd

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xlsx', delete=False) as temp:
            content = await file.read()
            temp.write(content)
            temp_file = temp.name

        # Read file
        xls = pd.ExcelFile(temp_file)

        # Validation results
        validation = {
            "valid": True,
            "filename": file.filename,
            "sheets_found": xls.sheet_names,
            "issues": [],
            "warnings": []
        }

        # Check for category sheets
        category_sheets = [s for s in xls.sheet_names if s.lower().startswith('category')]
        if not category_sheets:
            validation['valid'] = False
            validation['issues'].append("No category sheets found (expected sheets like 'Category1', 'Category2', etc.)")

        # Check each category sheet
        required_columns = ['KPI ID', 'KPI / Input (Human Question Format)', 'Type']
        for sheet in category_sheets:
            df = pd.read_excel(xls, sheet_name=sheet, nrows=1)
            sheet_columns = list(df.columns)

            missing_columns = [col for col in required_columns if col not in sheet_columns]
            if missing_columns:
                validation['valid'] = False
                validation['issues'].append(
                    f"Sheet '{sheet}' missing required columns: {', '.join(missing_columns)}"
                )

        # Count potential questions
        total_questions = 0
        for sheet in category_sheets:
            df = pd.read_excel(xls, sheet_name=sheet)
            # Filter out header/empty rows
            valid_rows = df[df['KPI ID'].notna() & (df['KPI ID'] != 'KPI ID')]
            total_questions += len(valid_rows)
            validation['warnings'].append(
                f"Sheet '{sheet}': {len(valid_rows)} potential questions found"
            )

        validation['estimated_questions'] = total_questions

        if validation['valid']:
            validation['message'] = f"File is valid! Ready to import approximately {total_questions} questions."
        else:
            validation['message'] = "File has validation errors. Please fix issues before importing."

        return validation

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error validating file: {str(e)}"
        )

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.unlink(temp_file)
            except:
                pass
