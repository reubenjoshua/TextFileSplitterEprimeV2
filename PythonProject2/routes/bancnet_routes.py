from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.bancnet_parser import BANCNETParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

bancnet_bp = Blueprint('bancnet', __name__)

@bancnet_bp.route('/process', methods=['POST'])
def process_file():
    """Process BANCNET transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        BANCNETParser, 
        'BANCNET', 
        'File does not match BANCNET format. BANCNET files should contain asterisk markers and be at least 50 characters long.'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@bancnet_bp.route('/info', methods=['GET'])
def get_info():
    """Get BANCNET parser information"""
    return jsonify({
        'payment_mode': 'BANCNET',
        'full_name': 'BANCNET',
        'description': 'BANCNET transaction parser for fixed-width transaction files with asterisk markers',
        'supported_formats': ['txt', 'log'],
        'file_format': {
            'type': 'Fixed-width format',
            'minimum_line_length': 50,
            'required_markers': ['*'],
            'field_positions': {
                'date': 'Last 6 digits of first 20 characters (YYMMDD format)',
                'atm_reference': '4 characters before first asterisk',
                'amount': '8 characters starting from position 21 after last asterisk'
            }
        },
        'extracted_fields': [
            'atm_ref (first 4 digits of ATM reference)',
            'full_atm_ref (complete ATM reference)',
            'date (formatted as DD/MM/2025)',
            'amount (decimal number, original value divided by 100)',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain lines with asterisk markers',
            'Each line must be at least 50 characters long',
            'ATM reference must be 4 characters before first asterisk',
            'Amount must be 8 digits after last asterisk',
            'Date must be 6 digits in YYMMDD format'
        ],
        'sample_format': 'Fixed-width line with asterisk markers and specific field positions'
    })

@bancnet_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate BANCNET file format without processing"""
    requirements = [
        'File must contain lines with asterisk markers',
        'Each line must be at least 50 characters long',
        'ATM reference must be 4 characters before first asterisk',
        'Amount must be 8 digits after last asterisk',
        'Date must be 6 digits in YYMMDD format'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        BANCNETParser, 
        'BANCNET', 
        requirements
    )
    
    if success:
        # Enhance validation data with BANCNET-specific info
        # We need to re-read the file to get the content for analysis
        is_valid_request, _, file = GenericFileProcessor.validate_file_request()
        if is_valid_request:
            file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
            lines = file_content.split('\n')
            non_empty_lines = [line for line in lines if line.strip()]
            
            # Find transaction lines
            transaction_lines = []
            
            for line in non_empty_lines:
                if '*' in line and len(line) >= 50:
                    transaction_lines.append(line.strip())
        else:
            transaction_lines = []
        
        # Add BANCNET-specific file info
        validation_data['file_info'].update({
            'transaction_lines': len(transaction_lines),
            'first_transaction': transaction_lines[0] if transaction_lines else None,
            'format_type': 'Fixed-width with asterisk markers',
            'separator': ' (fixed-width positions)',
            'distinguishing_feature': 'Fixed-width format with asterisk markers and specific field positions',
            'min_line_length': '50 characters minimum per line',
            'marker_type': 'Asterisk (*) markers required',
            'date_format': 'YYMMDD format in last 6 digits of first 20 characters',
            'date_output': 'Automatically formatted to DD/MM/2025 (fixed year)'
        })
        
        validation_data['common_errors'] = [
            'Missing asterisk markers (*)',
            'Lines too short (need 50+ characters)',
            'Invalid ATM reference position (need 4 chars before first asterisk)',
            'Invalid amount position (need 8 digits after last asterisk)',
            'Invalid date format (need 6 digits in YYMMDD format)',
            'Malformed transaction lines'
        ]
        
        return jsonify(validation_data)
    else:
        return jsonify(validation_data), 400

@bancnet_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample BANCNET file format"""
    sample_content = """12345678901234567890*123456789012345678901234567890
98765432109876543210*987654321098765432109876543210
11223344551122334455*112233445511223344551122334455"""
    
    return jsonify({
        'sample_format': 'BANCNET Transaction File',
        'format_type': 'Fixed-width with asterisk markers',
        'description': 'Each file contains transaction lines with fixed positions and asterisk markers',
        'sample_content': sample_content,
        'field_explanations': {
            'First 20 chars': 'Contains date in last 6 digits (YYMMDD format)',
            'Asterisk': 'Required marker indicating transaction data',
            'ATM Reference': '4 characters before first asterisk',
            'Amount': '8 digits starting from position 21 after last asterisk'
        },
        'position_details': {
            'positions_0_13': 'System/Unknown data',
            'positions_14_17': 'ATM Reference (4 characters)',
            'position_18': 'Asterisk marker',
            'positions_19_39': 'Transaction data',
            'positions_40_47': 'Amount (8 digits)',
            'positions_48_49': 'Additional data'
        },
        'notes': [
            'ATM Reference is used for grouping transactions (first 4 digits)',
            'Amount is stored as cents and converted to decimal for display',
            'Date is automatically formatted from YYMMDD to DD/MM/2025',
            'Only lines with valid asterisk markers and proper length are processed'
        ],
        'validation_checks': [
            'Each line must contain asterisk markers',
            'Minimum line length of 50 characters required',
            'ATM reference must be 4 characters before first asterisk',
            'Amount must be 8 digits after last asterisk',
            'Date must be 6 digits in YYMMDD format'
        ]
    })
