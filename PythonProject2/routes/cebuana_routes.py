from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.cebuana_parser import CebuanaParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

cebuana_bp = Blueprint('cebuana', __name__)

@cebuana_bp.route('/process', methods=['POST'])
def process_file():
    """Process Cebuana transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        parser_class=CebuanaParser,
        route_name='Cebuana',
        validation_error_message='File does not match Cebuana format. Cebuana files should contain comma-separated values with dates in MM/DD/YYYY format (without time), ATM reference, and amount.'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@cebuana_bp.route('/info', methods=['GET'])
def get_info():
    """Get Cebuana parser information"""
    parser = CebuanaParser()
    return jsonify(parser.get_parser_info())

@cebuana_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate Cebuana file format without processing"""
    requirements = [
        'File must contain comma-separated values (,)',
        'Each line must have at least 7 fields',
        'Fields 2 and 3 should contain dates in MM/DD/YYYY format without time',
        'Field 5 should contain ATM reference (numeric)',
        'Field 7 should contain amount (numeric)',
        'Must NOT contain time component in date fields (distinguishes from ECPAY)'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        parser_class=CebuanaParser,
        route_name='Cebuana',
        requirements=requirements
    )
    
    if success:
        # Add Cebuana-specific info to validation data
        if validation_data.get('valid'):
            validation_data['file_info']['separator'] = ', (comma)'
            validation_data['file_info']['date_format_detected'] = 'MM/DD/YYYY (without time)'
            validation_data['file_info']['distinguishing_feature'] = 'No time component in dates (unlike ECPAY)'
            
            if validation_data['file_info'].get('first_line'):
                fields = validation_data['file_info']['first_line'].split(',')
                validation_data['file_info']['estimated_fields'] = len(fields)
        
        return jsonify(validation_data)
    else:
        # Add Cebuana-specific error details
        if not validation_data.get('valid'):
            validation_data['common_errors'] = [
                'File might be ECPAY format (has time component in dates)',
                'Insufficient fields per line (need at least 7)',
                'Date format incorrect (should be MM/DD/YYYY without time)',
                'Missing ATM reference or amount fields'
            ]
            return jsonify(validation_data), 400
        else:
            return jsonify({'error': error_message}), 500

@cebuana_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample Cebuana file format"""
    sample_content = """Unknown1,01/15/2024,01/15/2024,Unknown4,1234567890,Unknown6,1500.00
Unknown1,01/15/2024,01/15/2024,Unknown4,0987654321,Unknown6,2500.50
Unknown1,01/16/2024,01/16/2024,Unknown4,1122334455,Unknown6,750.25"""
    
    return jsonify({
        'sample_format': 'Cebuana Lhuillier Transaction File',
        'separator': ', (comma character)',
        'description': 'Each line represents one transaction with comma-separated fields',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Unknown - varies by Cebuana system',
            'Field 2': 'Date in MM/DD/YYYY format (without time)',
            'Field 3': 'Date in MM/DD/YYYY format (without time)',
            'Field 4': 'Unknown - varies by Cebuana system',
            'Field 5': 'ATM Reference number (numeric)',
            'Field 6': 'Unknown - varies by Cebuana system',
            'Field 7': 'Transaction amount (decimal)'
        },
        'notes': [
            'ATM Reference (Field 5) is used for grouping transactions',
            'Only first 4 digits of ATM reference are used for display',
            'Amount should be a valid decimal number',
            'Dates are in MM/DD/YYYY format without time component',
            'This distinguishes Cebuana from ECPAY (which has time in dates)'
        ],
        'vs_ecpay': {
            'cebuana': 'Dates: MM/DD/YYYY (no time)',
            'ecpay': 'Dates: MM/DD/YYYY HH:MM:SS AM/PM (with time)'
        }
    })

@cebuana_bp.route('/compare', methods=['GET'])
def compare_with_ecpay():
    """Compare Cebuana format with ECPAY format"""
    return jsonify({
        'comparison': {
            'cebuana': {
                'name': 'Cebuana Lhuillier',
                'separator': ', (comma)',
                'date_format': 'MM/DD/YYYY (without time)',
                'example_date': '01/15/2024',
                'minimum_fields': 7,
                'distinguishing_feature': 'No time component in date fields'
            },
            'ecpay': {
                'name': 'ECPAY',
                'separator': ', (comma)',
                'date_format': 'MM/DD/YYYY HH:MM:SS AM/PM (with time)',
                'example_date': '01/15/2024 14:30:00 PM',
                'minimum_fields': 7,
                'distinguishing_feature': 'Time component in date fields'
            }
        },
        'how_to_distinguish': [
            'Check Field 2 (date field) for time component',
            'Cebuana: 01/15/2024 (no time)',
            'ECPAY: 01/15/2024 14:30:00 PM (with time)',
            'Both use comma separators and have similar field counts',
            'The presence of time in date fields is the key differentiator'
        ],
        'sample_lines': {
            'cebuana': 'Unknown1,01/15/2024,01/15/2024,Unknown4,1234567890,Unknown6,1500.00',
            'ecpay': 'Unknown1,01/15/2024 14:30:00 PM,01/15/2024,Unknown4,Unknown5,1234567890,1500.00'
        }
    })
