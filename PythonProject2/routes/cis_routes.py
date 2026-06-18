from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.cis_parser import CISParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

cis_bp = Blueprint('cis', __name__)

@cis_bp.route('/process', methods=['POST'])
def process_file():
    """Process CIS transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        CISParser, 
        'CIS', 
        'File does not match CIS format. CIS files should contain caret-separated values with specific field patterns (date in field 1, reference number in field 2, and amount in field 3).'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@cis_bp.route('/info', methods=['GET'])
def get_info():
    """Get CIS parser information"""
    return jsonify({
        'payment_mode': 'CIS',
        'full_name': 'CIS Bayad',
        'description': 'CIS transaction parser for caret-separated transaction files',
        'supported_formats': ['txt', 'log'],
        'file_format': {
            'type': 'Caret-separated format',
            'separator': '^',
            'minimum_fields': 3,
            'field_descriptions': [
                'Field 1: Date (MM/DD/YYYY or DD/MM/YYYY format)',
                'Field 2: ATM Reference',
                'Field 3: Amount'
            ]
        },
        'extracted_fields': [
            'atm_ref (first 4 digits of ATM reference)',
            'full_atm_ref (complete ATM reference)',
            'date (from field 1, time removed if present)',
            'amount (from field 3)',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain caret-separated values',
            'Each line must have at least 3 fields',
            'Field 1 must contain a valid date format',
            'Field 2 must contain a valid ATM reference (4+ digits)',
            'Field 3 must contain a valid amount'
        ],
        'rtp_support': {
            'description': 'Files containing RTP or NONRTP are labeled in split reports',
            'split_filename_format': 'ATM_{4digit_atm_ref}_CIS_RTP.txt or ATM_{4digit_atm_ref}_CIS_NONRTP.txt',
            'detection': 'RTP or NONRTP in uploaded filename or file content'
        },
        'sample_format': 'Date^ATMReference^Amount'
    })

@cis_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate CIS file format without processing"""
    requirements = [
        'File must contain caret-separated values',
        'Each line must have at least 3 fields',
        'Field 1 must contain a valid date format',
        'Field 2 must contain a valid ATM reference (4+ digits)',
        'Field 3 must contain a valid amount'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        CISParser, 
        'CIS', 
        requirements
    )
    
    if success:
        # Enhance validation data with CIS-specific info
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
                    if len(fields) >= 3:
                        transaction_lines.append(line.strip())
        else:
            transaction_lines = []
        
        # Add CIS-specific file info
        validation_data['file_info'].update({
            'transaction_lines': len(transaction_lines),
            'first_transaction': transaction_lines[0] if transaction_lines else None,
            'format_type': 'Caret-separated with 3+ fields',
            'separator': '^ (caret)',
            'distinguishing_feature': 'Caret-separated format with 3+ fields per line (simpler than PNB)',
            'field_count': 'Minimum 3 fields required per transaction line',
            'key_fields': 'Field 1 (Date), Field 2 (ATM Reference), Field 3 (Amount)',
            'date_flexibility': 'Supports both MM/DD/YYYY and DD/MM/YYYY date formats'
        })
        
        validation_data['common_errors'] = [
            'Missing caret separators (^)',
            'Insufficient fields (need 3+ fields per line)',
            'Invalid date format in field 1 (need MM/DD/YYYY or DD/MM/YYYY)',
            'Invalid ATM reference in field 2 (need 4+ digits)',
            'Invalid amount in field 3 (need valid decimal)',
            'Empty or malformed transaction lines'
        ]
        
        return jsonify(validation_data)
    else:
        return jsonify(validation_data), 400

@cis_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample CIS file format"""
    sample_content = """01/15/2024^1234567890^150.00
01/16/2024^9876543210^250.50
01/17/2024^1122334455^75.25"""
    
    return jsonify({
        'sample_format': 'CIS Transaction File',
        'format_type': 'Caret-separated format',
        'description': 'Each file contains transaction lines with caret-separated fields',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Date (MM/DD/YYYY or DD/MM/YYYY format)',
            'Field 2': 'ATM Reference (4+ digits)',
            'Field 3': 'Amount (decimal number)'
        },
        'position_details': {
            'field_1': 'Date in MM/DD/YYYY or DD/MM/YYYY format',
            'field_2': 'ATM Reference (used for grouping)',
            'field_3': 'Transaction amount'
        },
        'notes': [
            'ATM Reference is used for grouping transactions (first 4 digits)',
            'Amount is stored as decimal number',
            'Date is extracted from field 1 (time removed if present)',
            'All fields are separated by caret (^) character',
            'Only lines with valid field patterns are processed'
        ],
        'validation_checks': [
            'Each line must contain caret separators',
            'Minimum 3 fields per line required',
            'Field 1 must contain valid date format',
            'Field 2 must contain 4+ digits for ATM reference',
            'Field 3 must contain valid decimal amount'
        ]
    })
