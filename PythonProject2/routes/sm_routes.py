from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.sm_parser import SMParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

sm_bp = Blueprint('sm', __name__)

@sm_bp.route('/process', methods=['POST'])
def process_file():
    """Process SM transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        SMParser, 
        'SM', 
        'File does not match SM format. SM files should contain lines with CS marker, valid date format (MMDDYYYY), and valid ATM reference.'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@sm_bp.route('/info', methods=['GET'])
def get_info():
    """Get SM parser information"""
    return jsonify({
        'payment_mode': 'SM',
        'full_name': 'SM Store / SM Supermarket',
        'description': 'SM transaction parser for fixed-width transaction files with CS markers',
        'supported_formats': ['txt', 'log'],
        'file_format': {
            'type': 'Fixed-width format',
            'minimum_line_length': 45,
            'required_markers': ['CS'],
            'field_positions': {
                'date': 'Positions 3-11 (MMDDYYYY format)',
                'atm_reference': 'Pattern: 6 zeros followed by 14 digits',
                'amount': 'Digits before CS marker (divided by 100)'
            },
            'header_formats': [
                '10 characters (exact)',
                '30 characters (exact)'
            ]
        },
        'extracted_fields': [
            'atm_ref (first 4 digits of 14-digit ATM reference)',
            'full_atm_ref (complete 14-digit ATM reference)',
            'date (formatted as MM/DD/YYYY)',
            'amount (decimal number, original value divided by 100)',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain header lines (10 or 30 characters)',
            'Transaction lines must be at least 45 characters long',
            'Each transaction line must contain CS marker',
            'Date must be in MMDDYYYY format at positions 3-11',
            'ATM reference must follow pattern: 000000XXXXXXXXXX (6 zeros + 14 digits)',
            'Amount must be numeric digits before CS marker'
        ],
        'sample_format': 'Header line (10 or 30 chars)\nTransaction line with CS marker and fixed positions'
    })

@sm_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate SM file format without processing"""
    requirements = [
        'File must contain header lines (exactly 10 or 30 characters)',
        'Transaction lines must be at least 45 characters long',
        'Each transaction line must contain CS marker',
        'Date must be in MMDDYYYY format at positions 3-11',
        'ATM reference must follow pattern: 000000XXXXXXXXXX'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        SMParser, 
        'SM', 
        requirements
    )
    
    if success:
        # Enhance validation data with SM-specific info
        # We need to re-read the file to get the content for analysis
        is_valid_request, _, file = GenericFileProcessor.validate_file_request()
        if is_valid_request:
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            lines = file_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Find header and transaction lines
            header_lines = []
            transaction_lines = []
            
            for line in non_empty_lines:
                if len(line.strip()) in [10, 30]:
                    header_lines.append(line.strip())
                elif len(line.strip()) >= 45 and 'CS' in line:
                    transaction_lines.append(line.strip())
        else:
            header_lines = []
            transaction_lines = []
        
        # Add SM-specific file info
        validation_data['file_info'].update({
            'header_lines': len(header_lines),
            'transaction_lines': len(transaction_lines),
            'first_header': header_lines[0] if header_lines else None,
            'first_transaction': transaction_lines[0] if transaction_lines else None,
            'format_type': 'Fixed-width with CS markers',
            'separator': ' (fixed-width positions)',
            'distinguishing_feature': 'Fixed-width format with CS markers and header lines (10/30 chars)',
            'header_detection': 'SM files include header lines that are preserved in output'
        })
        
        validation_data['common_errors'] = [
            'Missing header lines (need 10 or 30 character lines)',
            'Transaction lines too short (need 45+ characters)',
            'Missing CS markers in transaction lines',
            'Invalid date format (need MMDDYYYY at positions 3-11)',
            'Invalid ATM reference pattern (need 000000XXXXXXXXXX)',
            'No valid transaction lines found'
        ]
        
        return jsonify(validation_data)
    else:
        return jsonify(validation_data), 400

@sm_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample SM file format"""
    sample_content = """1234567890
000000123456789012345678901234567890CS1234567890
000000987654321098765432109876543210CS9876543210
000000112233445511223344551122334455CS1122334455"""
    
    return jsonify({
        'sample_format': 'SM Transaction File',
        'format_type': 'Fixed-width with CS markers',
        'description': 'Each file contains header lines and transaction lines with fixed positions',
        'sample_content': sample_content,
        'field_explanations': {
            'Header Line': 'Exactly 10 or 30 characters (varies by SM system)',
            'Date': 'Positions 3-11 in MMDDYYYY format (e.g., 01152024 for January 15, 2024)',
            'ATM Reference': 'Pattern: 000000XXXXXXXXXX (6 zeros + 14 digits)',
            'CS Marker': 'Required marker indicating transaction type',
            'Amount': 'Numeric digits before CS marker (stored as cents, displayed as decimal)'
        },
        'position_details': {
            'positions_0_2': 'Unknown/System data',
            'positions_3_10': 'Date in MMDDYYYY format',
            'positions_11_16': 'Unknown/System data',
            'positions_17_30': 'ATM Reference (14 digits)',
            'positions_31_CS': 'Amount digits',
            'CS_marker': 'Transaction type indicator',
            'after_CS': 'Additional transaction data'
        },
        'notes': [
            'ATM Reference is used for grouping transactions (first 4 digits)',
            'Amount is stored as cents and converted to decimal for display',
            'Date is automatically formatted from MMDDYYYY to MM/DD/YYYY',
            'Header lines are preserved in output for system compatibility',
            'Only lines with valid CS markers and proper length are processed'
        ],
        'validation_checks': [
            'Header lines must be exactly 10 or 30 characters',
            'Transaction lines must be at least 45 characters',
            'CS marker must be present in transaction lines',
            'Date positions 3-11 must contain 8 digits',
            'ATM reference must match pattern: 000000XXXXXXXXXX'
        ]
    })
