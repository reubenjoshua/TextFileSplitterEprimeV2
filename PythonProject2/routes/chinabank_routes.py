from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.chinabank_parser import ChinabankParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

chinabank_bp = Blueprint('chinabank', __name__)

@chinabank_bp.route('/process', methods=['POST'])
def process_file():
    """Process China Bank transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        parser_class=ChinabankParser,
        route_name='China Bank',
        validation_error_message='File does not match China Bank format. China Bank files should contain space-separated values with specific field patterns (date in MMDDYYYY format in field 1, amount in field 3, and ATM reference in field 4).'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@chinabank_bp.route('/info', methods=['GET'])
def get_info():
    """Get China Bank parser information"""
    parser = ChinabankParser()
    return jsonify(parser.get_parser_info())

@chinabank_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate China Bank file format without processing"""
    requirements = [
        'File must contain space-separated values (no special separators)',
        'Each line must have at least 4 fields',
        'Field 1 should contain date in MMDDYYYY format (8 digits)',
        'Field 3 should contain amount (numeric)',
        'Field 4 should contain ATM reference (numeric)',
        'Fixed-width format with space separation'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        parser_class=ChinabankParser,
        route_name='China Bank',
        requirements=requirements
    )
    
    if success:
        # Add China Bank-specific info to validation data
        if validation_data.get('valid'):
            validation_data['file_info']['separator'] = ' (space-separated, fixed-width)'
            validation_data['file_info']['distinguishing_feature'] = 'Space-separated fixed-width format with MMDDYYYY dates'
            
            if validation_data['file_info'].get('first_line'):
                fields = [f.strip() for f in validation_data['file_info']['first_line'].split() if f.strip()]
                validation_data['file_info']['estimated_fields'] = len(fields)
                
                # Check date format in first field
                date_format_detected = 'Unknown'
                if fields and len(fields) > 0:
                    date_field = fields[0]
                    if len(date_field) == 8 and date_field.isdigit():
                        date_format_detected = 'MMDDYYYY (8 digits)'
                    else:
                        date_format_detected = 'Non-standard format'
                validation_data['file_info']['date_format_detected'] = date_format_detected
        
        return jsonify(validation_data)
    else:
        # Add China Bank-specific error details
        if not validation_data.get('valid'):
            validation_data['common_errors'] = [
                'Insufficient fields per line (need at least 4)',
                'Date format incorrect (should be MMDDYYYY - 8 digits)',
                'Missing amount or ATM reference fields',
                'Using wrong separators (should be spaces, not pipes or commas)'
            ]
            return jsonify(validation_data), 400
        else:
            return jsonify({'error': error_message}), 500

@chinabank_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample China Bank file format"""
    sample_content = """01152024 Unknown2 1500.00 1234567890
01152024 Unknown2 2500.50 0987654321
01162024 Unknown2 750.25 1122334455"""
    
    return jsonify({
        'sample_format': 'China Bank Transaction File',
        'separator': ' (space-separated, fixed-width format)',
        'description': 'Each line represents one transaction with space-separated fields',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Date in MMDDYYYY format (8 digits)',
            'Field 2': 'Unknown field - varies by China Bank system',
            'Field 3': 'Transaction amount (decimal)',
            'Field 4': 'ATM Reference number (numeric)'
        },
        'notes': [
            'ATM Reference (Field 4) is used for grouping transactions',
            'Only first 4 digits of ATM reference are used for display',
            'Amount should be a valid decimal number',
            'Date is in MMDDYYYY format (8 digits) and gets converted to MM/DD/YYYY',
            'Space-separated format (no pipes or commas)',
            'Fixed-width format with space separation'
        ],
        'date_conversion': {
            'input_format': 'MMDDYYYY (8 digits)',
            'output_format': 'MM/DD/YYYY',
            'example': '01152024 -> 01/15/2024'
        }
    })

@chinabank_bp.route('/compare', methods=['GET'])
def compare_with_other_formats():
    """Compare China Bank format with other payment modes"""
    return jsonify({
        'comparison': {
            'chinabank': {
                'name': 'China Bank',
                'separator': ' (space-separated)',
                'date_format': 'MMDDYYYY (8 digits)',
                'example_date': '01152024',
                'minimum_fields': 4,
                'distinguishing_feature': 'Space-separated fixed-width format'
            },
            'bdo': {
                'name': 'BDO',
                'separator': '| (pipe)',
                'date_format': 'YYYYMMDD or MM/DD/YYYY',
                'example_date': '20240115 or 01/15/2024',
                'minimum_fields': 10,
                'distinguishing_feature': 'Pipe-separated format'
            },
            'cebuana': {
                'name': 'Cebuana Lhuillier',
                'separator': ', (comma)',
                'date_format': 'MM/DD/YYYY (without time)',
                'example_date': '01/15/2024',
                'minimum_fields': 7,
                'distinguishing_feature': 'Comma-separated format'
            }
        },
        'how_to_distinguish': [
            'Check the separator used:',
            'China Bank: Space-separated (no special characters)',
            'BDO: Pipe-separated (| character)',
            'Cebuana: Comma-separated (, character)',
            'Check the date format:',
            'China Bank: MMDDYYYY (8 digits)',
            'BDO: YYYYMMDD or MM/DD/YYYY',
            'Cebuana: MM/DD/YYYY (without time)'
        ],
        'sample_lines': {
            'chinabank': '01152024 Unknown2 1500.00 1234567890',
            'bdo': 'Unknown1|Unknown2|20240115|14:30:00|ATM001|1234567890|Unknown7|Unknown8|Unknown9|1500.00',
            'cebuana': 'Unknown1,01/15/2024,01/15/2024,Unknown4,1234567890,Unknown6,1500.00'
        }
    })

@chinabank_bp.route('/format-guide', methods=['GET'])
def get_format_guide():
    """Get detailed format guide for China Bank files"""
    return jsonify({
        'format_guide': {
            'file_structure': {
                'type': 'Fixed-width space-separated',
                'encoding': 'UTF-8 (with fallback to latin-1, cp1252)',
                'line_endings': 'Unix (LF) or Windows (CRLF)',
                'field_separation': 'One or more spaces between fields'
            },
            'field_specifications': {
                'field_1': {
                    'position': 1,
                    'name': 'Date',
                    'format': 'MMDDYYYY (8 digits)',
                    'example': '01152024',
                    'description': 'Transaction date in MMDDYYYY format'
                },
                'field_2': {
                    'position': 2,
                    'name': 'Unknown',
                    'format': 'Variable',
                    'example': 'Unknown2',
                    'description': 'Unknown field - varies by China Bank system'
                },
                'field_3': {
                    'position': 3,
                    'name': 'Amount',
                    'format': 'Decimal number',
                    'example': '1500.00',
                    'description': 'Transaction amount as decimal number'
                },
                'field_4': {
                    'position': 4,
                    'name': 'ATM Reference',
                    'format': 'Numeric string',
                    'example': '1234567890',
                    'description': 'ATM reference number (first 4 digits used for grouping)'
                }
            },
            'validation_criteria': [
                'Each line must have at least 4 space-separated fields',
                'Field 1 must be exactly 8 digits (MMDDYYYY format)',
                'Field 3 must be a valid decimal number',
                'Field 4 must contain numeric characters',
                'No special separators (pipes or commas) should be present'
            ],
            'common_issues': {
                'insufficient_fields': 'Lines with fewer than 4 fields will be rejected',
                'invalid_date_format': 'Date field must be exactly 8 digits in MMDDYYYY format',
                'non_numeric_amount': 'Amount field must be a valid decimal number',
                'missing_atm_reference': 'ATM reference field must contain numeric characters',
                'wrong_separators': 'Files with pipe (|) or comma (,) separators are not China Bank format'
            }
        }
    })
