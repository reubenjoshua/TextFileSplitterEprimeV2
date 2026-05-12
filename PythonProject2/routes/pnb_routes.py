from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.pnb_parser import PNBParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

pnb_bp = Blueprint('pnb', __name__)

@pnb_bp.route('/process', methods=['POST'])
def process_file():
    """Process PNB transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        PNBParser, 
        'PNB', 
        'File does not match PNB format. PNB files should contain caret-separated values with specific field patterns (reference number in field 5 and amount in field 7).'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@pnb_bp.route('/info', methods=['GET'])
def get_info():
    """Get PNB parser information"""
    return jsonify({
        'payment_mode': 'PNB',
        'full_name': 'Philippine National Bank',
        'description': 'PNB transaction parser for caret-separated transaction files',
        'supported_formats': ['txt', 'log'],
        'file_format': {
            'type': 'Caret-separated format',
            'separator': '^',
            'minimum_fields': 7,
            'field_descriptions': [
                'Field 1: Date',
                'Field 2: Date (duplicate)',
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
            'date (from field 2)',
            'amount (from field 7)',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain caret-separated values',
            'Each line must have at least 7 fields',
            'Field 5 must contain a valid ATM reference (4+ digits)',
            'Field 7 must contain a valid amount',
            'Field 2 must contain a valid date'
        ],
        'sample_format': 'Date^Date^Field3^Field4^ATMReference^Field6^Amount'
    })

@pnb_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate PNB file format without processing"""
    requirements = [
        'File must contain caret-separated values',
        'Each line must have at least 7 fields',
        'Field 5 must contain a valid ATM reference (4+ digits)',
        'Field 7 must contain a valid amount',
        'Field 2 must contain a valid date'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        PNBParser, 
        'PNB', 
        requirements
    )
    
    if success:
        # Enhance validation data with PNB-specific info
        # We need to re-read the file to get the content for analysis
        is_valid_request, _, file = GenericFileProcessor.validate_file_request()
        if is_valid_request:
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            lines = file_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Find transaction lines
            transaction_lines = []
            
            for line in non_empty_lines:
                if '^' in line:
                    fields = line.split('^')
                    if len(fields) >= 7:
                        transaction_lines.append(line.strip())
        else:
            transaction_lines = []
        
        # Add PNB-specific file info
        validation_data['file_info'].update({
            'transaction_lines': len(transaction_lines),
            'first_transaction': transaction_lines[0] if transaction_lines else None,
            'format_type': 'Caret-separated with 7+ fields',
            'separator': '^ (caret)',
            'distinguishing_feature': 'Caret-separated format with 7+ fields per line',
            'field_count': 'Minimum 7 fields required per transaction line',
            'key_fields': 'Field 5 (ATM Reference), Field 7 (Amount), Field 2 (Date)'
        })
        
        validation_data['common_errors'] = [
            'Missing caret separators (^)',
            'Insufficient fields (need 7+ fields per line)',
            'Invalid ATM reference in field 5 (need 4+ digits)',
            'Invalid amount in field 7 (need valid decimal)',
            'Invalid date format in field 2',
            'Empty or malformed transaction lines'
        ]
        
        return jsonify(validation_data)
    else:
        return jsonify(validation_data), 400

@pnb_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample PNB file format"""
    sample_content = """01/15/2024^01/15/2024^Field3^Field4^1234567890^Field6^150.00
01/16/2024^01/16/2024^Field3^Field4^9876543210^Field6^250.50
01/17/2024^01/17/2024^Field3^Field4^1122334455^Field6^75.25"""
    
    return jsonify({
        'sample_format': 'PNB Transaction File',
        'format_type': 'Caret-separated format',
        'description': 'Each file contains transaction lines with caret-separated fields',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Date (MM/DD/YYYY format)',
            'Field 2': 'Date (duplicate of Field 1)',
            'Field 3': 'Unknown/System data',
            'Field 4': 'Unknown/System data',
            'Field 5': 'ATM Reference (4+ digits)',
            'Field 6': 'Unknown/System data',
            'Field 7': 'Amount (decimal number)'
        },
        'position_details': {
            'field_1': 'Date in MM/DD/YYYY format',
            'field_2': 'Date (duplicate)',
            'field_3': 'System/Unknown data',
            'field_4': 'System/Unknown data',
            'field_5': 'ATM Reference (used for grouping)',
            'field_6': 'System/Unknown data',
            'field_7': 'Transaction amount'
        },
        'notes': [
            'ATM Reference is used for grouping transactions (first 4 digits)',
            'Amount is stored as decimal number',
            'Date is extracted from field 2',
            'All fields are separated by caret (^) character',
            'Only lines with valid field patterns are processed'
        ],
        'validation_checks': [
            'Each line must contain caret separators',
            'Minimum 7 fields per line required',
            'Field 5 must contain 4+ digits for ATM reference',
            'Field 7 must contain valid decimal amount',
            'Field 2 must contain valid date format'
        ]
    })
