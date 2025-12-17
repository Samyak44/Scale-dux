#!/usr/bin/env python3
"""
Helper script to convert Excel KPI data to YAML configuration

Usage:
    python scripts/convert_excel_to_yaml.py input.xlsx output.yaml
"""

import pandas as pd
import yaml
import sys
from pathlib import Path


def parse_scoring_logic(scoring_mvp_no_traction, scoring_mvp_early_traction):
    """Parse scoring logic strings into structured format"""

    def parse_single_logic(logic_str):
        if not logic_str or pd.isna(logic_str):
            return {}

        result = {}
        # Example: "G: value = true | R: value = false"
        parts = str(logic_str).split('|')

        for part in parts:
            part = part.strip()
            if part.startswith('G:'):
                result['green'] = part.replace('G:', '').strip()
            elif part.startswith('Y:'):
                result['yellow'] = part.replace('Y:', '').strip()
            elif part.startswith('R:'):
                result['red'] = part.replace('R:', '').strip()

        return result

    return {
        'mvp_no_traction': parse_single_logic(scoring_mvp_no_traction),
        'mvp_early_traction': parse_single_logic(scoring_mvp_early_traction)
    }


def parse_confidence_method(confidence_str):
    """Parse confidence scoring method string"""
    if not confidence_str or pd.isna(confidence_str):
        return {
            'self_reported': 0.6,
            'document_uploaded': 1.0
        }

    result = {}
    # Example: "Self-reported: 0.6 | LinkedIn verified: 0.9 | Document upload: 1.0"
    parts = str(confidence_str).split('|')

    for part in parts:
        part = part.strip().lower()
        if 'self' in part or 'self-reported' in part:
            try:
                result['self_reported'] = float(part.split(':')[1].strip())
            except:
                result['self_reported'] = 0.6
        elif 'linkedin' in part:
            try:
                result['linkedin_verified'] = float(part.split(':')[1].strip())
            except:
                pass
        elif 'document' in part or 'upload' in part:
            try:
                result['document_uploaded'] = float(part.split(':')[1].strip())
            except:
                result['document_uploaded'] = 1.0
        elif 'reference' in part:
            try:
                result['reference_check'] = float(part.split(':')[1].strip())
            except:
                pass
        elif 'ca' in part or 'verified' in part:
            try:
                result['ca_verified'] = float(part.split(':')[1].strip())
            except:
                pass

    return result


def parse_fatal_flag(fatal_flag_str, trigger_condition, cascade_impact):
    """Parse fatal flag configuration"""
    if not fatal_flag_str or pd.isna(fatal_flag_str) or str(fatal_flag_str).upper() == 'NO':
        return None

    flag = {
        'is_fatal': True,
        'condition': str(trigger_condition) if not pd.isna(trigger_condition) else "value == false"
    }

    if cascade_impact and not pd.isna(cascade_impact):
        # Parse cascade impact string
        # Example: "C5: Auto-RED in 'Role Clarity' | C7: Block all milestone"
        impacts = []
        parts = str(cascade_impact).split('|')
        for part in parts:
            part = part.strip()
            # Simple parsing - you may need to enhance this
            if 'auto-red' in part.lower() or 'auto-yellow' in part.lower():
                impacts.append({
                    'category': 'execution',  # You'll need to map this
                    'effect': 'auto_red' if 'red' in part.lower() else 'auto_yellow'
                })

        if impacts:
            flag['cascade_impact'] = impacts

    return flag


def convert_excel_to_yaml(excel_path, output_path):
    """
    Convert Excel KPI sheet to YAML configuration

    Expected Excel columns:
    - Sub-Category
    - Sub-Category Weight
    - KPI ID
    - KPI / Input (Human Question Format)
    - Type
    - Priority
    - KPI Base Weight
    - Stage Weight Multiplier (MVP_no_traction)
    - Stage Weight Multiplier (MVP_early_traction)
    - Scoring Logic (MVP_no_traction)
    - Scoring Logic (MVP_early_traction)
    - Confidence Scoring Method
    - Fatal Flag
    - Fatal Flag Trigger Condition
    - Cascade Impact
    """

    print(f"📖 Reading Excel file: {excel_path}")
    df = pd.read_excel(excel_path)

    print(f"   Found {len(df)} KPIs")
    print(f"   Columns: {df.columns.tolist()}")

    # Group by Sub-Category
    config = {
        'version': '1.0.0',
        'categories': {}
    }

    # You'll need to manually specify category groupings
    # For now, let's assume everything is in 'team' category
    category_name = 'team'

    config['categories'][category_name] = {
        'weight_mvp_no_traction': 0.40,  # You'll need to set these
        'weight_mvp_early_traction': 0.30,
        'sub_categories': {}
    }

    # Group by sub-category
    for sub_cat_name, group in df.groupby('Sub-Category'):
        if pd.isna(sub_cat_name):
            continue

        # Convert to snake_case for ID
        sub_cat_id = sub_cat_name.lower().replace(' ', '_').replace('&', 'and')

        # Get sub-category weight (should be same for all rows in group)
        sub_cat_weight = group['Sub-Category Weight'].iloc[0]

        config['categories'][category_name]['sub_categories'][sub_cat_id] = {
            'weight': float(sub_cat_weight),
            'kpis': {}
        }

        # Process each KPI in this sub-category
        for _, row in group.iterrows():
            kpi_id = str(row['KPI ID']).strip()

            kpi_config = {
                'question': str(row['KPI / Input (Human Question Format)']),
                'type': str(row['Type']).lower(),
                'priority': str(row['Priority']).lower(),
                'base_weight': float(row['KPI Base Weight']),
                'stage_multiplier': {
                    'mvp_no_traction': float(row['Stage Weight Multiplier (MVP_no_traction)']),
                    'mvp_early_traction': float(row['Stage Weight Multiplier (MVP_early_traction)'])
                },
                'universal': row['Universal/Conditional'] == 'Universal Core',
                'scoring_logic': parse_scoring_logic(
                    row['Scoring Logic (MVP_no_traction)'],
                    row['Scoring Logic (MVP_early_traction)']
                ),
                'confidence_method': parse_confidence_method(
                    row['Confidence Scoring Method']
                )
            }

            # Add fatal flag if present
            fatal_flag = parse_fatal_flag(
                row.get('Fatal Flag'),
                row.get('Fatal Flag Trigger Condition'),
                row.get('Cascade Impact')
            )
            if fatal_flag:
                kpi_config['fatal_flag'] = fatal_flag

            # Add skip condition if present
            if 'Skip Condition' in row and not pd.isna(row['Skip Condition']):
                kpi_config['skip_condition'] = {
                    'kpi_id': 'unknown',  # You'll need to parse this
                    'value': True
                }

            config['categories'][category_name]['sub_categories'][sub_cat_id]['kpis'][kpi_id] = kpi_config

    # Write to YAML
    print(f"\n💾 Writing YAML to: {output_path}")
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    print(f"✅ Done! Generated {len(df)} KPIs in YAML format")
    print(f"\n⚠️  IMPORTANT: Please review the output file and:")
    print(f"   1. Verify scoring logic parsing")
    print(f"   2. Set correct category weights")
    print(f"   3. Add conditional trigger logic")
    print(f"   4. Test with scoring engine")


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_excel_to_yaml.py input.xlsx output.yaml")
        sys.exit(1)

    excel_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    if not excel_path.exists():
        print(f"❌ Error: File not found: {excel_path}")
        sys.exit(1)

    convert_excel_to_yaml(excel_path, output_path)


if __name__ == '__main__':
    main()
