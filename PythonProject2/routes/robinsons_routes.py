from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.robinsons_parser import ROBINSONSParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

robinsons_bp = Blueprint('robinsons', __name__)

@robinsons_bp.route('/process', methods=['POST'])
def process_file():
    """Process ROBINSONS transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        ROBINSONSParser, 
        'ROBINSONS', 
        'File does not match ROBINSONS format. ROBINSONS files should contain both pipe and caret separators with specific field patterns.'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@robinsons_bp.route('/info', methods=['GET'])
def get_info():
    """Get ROBINSONS parser information"""
    return jsonify({
        'payment_mode': 'ROB',
        'full_name': 'Robinsons Bank',
        'description': 'ROBINSONS transaction parser for pipe and caret-separated transaction files',
        'supported_formats': ['txt', 'log'],
        'file_format': {
            'type': 'Pipe and caret-separated format',
            'separators': ['|', '^'],
            'minimum_fields': 7,
            'field_descriptions': [
                'Field 1: Date',
                'Field 2: Unknown/System data',
                'Field 3: Unknown/System data',
                'Field 4: Unknown/System data',
                'Field 5: ATM Reference',
                'Field 6: Unknown/System data',
                'Field 7: Amount'
            ]
        },
        'extracted_fields': [
            'atm_ref (first 4 digits of ATM reference)',
            'full_atm_ref (complete ATM reference)',
            'date (from field 1, time removed if present)',
            'amount (from field 7)',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain both pipe and caret separators',
            'Each line must have at least 7 fields',
            'Field 1 must contain a valid date format',
            'Field 5 must contain a valid ATM reference (4+ characters)',
            'Field 7 must contain a valid amount'
        ],
        'sample_format': 'Date|Field2|Field3|Field4|ATMReference|Field6|Amount'
    })

@robinsons_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate ROBINSONS file format without processing"""
    requirements = [
        'File must contain both pipe and caret separators',
        'Each line must have at least 7 fields',
        'Field 1 must contain a valid date format',
        'Field 5 must contain a valid ATM reference (4+ characters)',
        'Field 7 must contain a valid amount'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        ROBINSONSParser, 
        'ROBINSONS', 
        requirements
    )
    
    if success:
        # Enhance validation data with ROBINSONS-specific info
        # We need to re-read the file to get the content for analysis
        is_valid_request, _, file = GenericFileProcessor.validate_file_request()
        if is_valid_request:
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            lines = file_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Find transaction lines
            transaction_lines = []
            
            for line in non_empty_lines:
                if '|' in line and '^' in line:
                    # Split and check minimum fields
                    fields = []
                    parts = line.split('|')
                    for part in parts:
                        fields.extend(part.split('^'))
                    fields = [f.strip() for f in fields if f.strip()]
                    if len(fields) >= 7:
                        transaction_lines.append(line.strip())
        else:
            transaction_lines = []
        
        # Add ROBINSONS-specific file info
        validation_data['file_info'].update({
            'transaction_lines': len(transaction_lines),
            'first_transaction': transaction_lines[0] if transaction_lines else None,
            'format_type': 'Pipe and caret-separated with 7+ fields',
            'separator': '| (pipe) and ^ (caret)',
            'distinguishing_feature': 'Dual separator format with both pipe and caret separators',
            'field_count': 'Minimum 7 fields required per transaction line',
            'key_fields': 'Field 1 (Date), Field 5 (ATM Reference), Field 7 (Amount)',
            'separator_complexity': 'Most complex separator format (dual separators)',
            'date_flexibility': 'Supports both MM/DD/YYYY and DD/MM/YYYY date formats'
        })
        
        validation_data['common_errors'] = [
            'Missing pipe separators (|)',
            'Missing caret separators (^)',
            'Insufficient fields (need 7+ fields per line)',
            'Invalid date format in field 1 (need MM/DD/YYYY or DD/MM/YYYY)',
            'Invalid ATM reference in field 5 (need 4+ characters)',
            'Invalid amount in field 7 (need valid decimal)',
            'Empty or malformed transaction lines'
        ]
        
        return jsonify(validation_data)
    else:
        return jsonify(validation_data), 400

@robinsons_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample ROBINSONS file format"""
    sample_content = """01/15/2024|Field2|Field3|Field4|1234567890|Field6|150.00
01/16/2024|Field2|Field3|Field4|9876543210|Field6|250.50
01/17/2024|Field2|Field3|Field4|1122334455|Field6|75.25"""
    
    return jsonify({
        'sample_format': 'ROBINSONS Transaction File',
        'format_type': 'Pipe and caret-separated format',
        'description': 'Each file contains transaction lines with both pipe and caret separators',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Date (MM/DD/YYYY or DD/MM/YYYY format)',
            'Field 2': 'Unknown/System data',
            'Field 3': 'Unknown/System data',
            'Field 4': 'Unknown/System data',
            'Field 5': 'ATM Reference (4+ characters)',
            'Field 6': 'Unknown/System data',
            'Field 7': 'Amount (decimal number)'
        },
        'position_details': {
            'field_1': 'Date in MM/DD/YYYY or DD/MM/YYYY format',
            'field_2': 'System/Unknown data',
            'field_3': 'System/Unknown data',
            'field_4': 'System/Unknown data',
            'field_5': 'ATM Reference (used for grouping)',
            'field_6': 'System/Unknown data',
            'field_7': 'Transaction amount'
        },
        'notes': [
            'ATM Reference is used for grouping transactions (first 4 characters)',
            'Amount is stored as decimal number',
            'Date is extracted from field 1 (time removed if present)',
            'All fields are separated by both pipe (|) and caret (^) characters',
            'Only lines with valid field patterns are processed'
        ],
        'validation_checks': [
            'Each line must contain both pipe and caret separators',
            'Minimum 7 fields per line required',
            'Field 1 must contain valid date format',
            'Field 5 must contain 4+ characters for ATM reference',
            'Field 7 must contain valid decimal amount'
        ]
    })
