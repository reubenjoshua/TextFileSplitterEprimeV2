from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.bdo_parser import BDOParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

bdo_bp = Blueprint('bdo', __name__)

@bdo_bp.route('/process', methods=['POST'])
def process_file():
    """Process BDO transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        parser_class=BDOParser,
        route_name='BDO',
        validation_error_message='File does not match BDO format. BDO files should contain pipe-separated values with at least 10 fields.'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@bdo_bp.route('/info', methods=['GET'])
def get_info():
    """Get BDO parser information"""
    return jsonify({
        'payment_mode': 'BDO',
        'full_name': 'Banco de Oro',
        'description': 'BDO transaction parser for pipe-separated transaction files',
        'supported_formats': ['txt', 'csv', 'log'],
        'file_format': {
            'separator': '| (pipe)',
            'minimum_fields': 10,
            'field_descriptions': [
                'Field 1: Unknown',
                'Field 2: Unknown', 
                'Field 3: Date (YYYYMMDD or MM/DD/YYYY)',
                'Field 4: Time',
                'Field 5: Terminal',
                'Field 6: ATM Reference',
                'Field 7: Unknown',
                'Field 8: Unknown',
                'Field 9: Unknown',
                'Field 10: Amount'
            ]
        },
        'extracted_fields': [
            'atm_ref (first 4 digits of ATM reference)',
            'date (formatted as MM/DD/YYYY)',
            'amount (decimal number)',
            'time',
            'terminal',
            'raw_text (original line)'
        ],
        'validation_rules': [
            'File must contain pipe-separated values',
            'Each line must have at least 10 fields',
            'ATM reference must be numeric in field 6',
            'Amount must be numeric in field 10',
            'Date must be in YYYYMMDD, MM/DD/YYYY, or YYYY-MM-DD format in field 3'
        ],
        'sample_format': 'Field1|Field2|20240115|14:30|ATM001|1234567890|Field7|Field8|Field9|1500.00'
    })

@bdo_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate BDO file format without processing"""
    requirements = [
        'File must contain pipe-separated values (|)',
        'Each line must have at least 10 fields',
        'Field 6 should contain ATM reference (numeric)',
        'Field 10 should contain amount (numeric)',
        'Field 3 should contain date'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        parser_class=BDOParser,
        route_name='BDO',
        requirements=requirements
    )
    
    if success:
        # Add BDO-specific info to validation data
        if validation_data.get('valid'):
            validation_data['file_info']['separator'] = '| (pipe)'
            if validation_data['file_info'].get('first_line'):
                validation_data['file_info']['estimated_fields'] = len(
                    validation_data['file_info']['first_line'].split('|')
                )
        return jsonify(validation_data)
    else:
        status_code = 400 if error_message == '' else 500
        return jsonify({'error': error_message}), status_code

@bdo_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample BDO file format"""
    sample_content = """Unknown1|Unknown2|20240115|14:30:00|ATM001|1234567890|Unknown7|Unknown8|Unknown9|1500.00
Unknown1|Unknown2|20240115|15:45:00|ATM002|0987654321|Unknown7|Unknown8|Unknown9|2500.50
Unknown1|Unknown2|20240116|09:15:00|ATM001|1122334455|Unknown7|Unknown8|Unknown9|750.25"""
    
    return jsonify({
        'sample_format': 'BDO Transaction File',
        'separator': '| (pipe character)',
        'description': 'Each line represents one transaction with pipe-separated fields',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Unknown - varies by BDO system',
            'Field 2': 'Unknown - varies by BDO system', 
            'Field 3': 'Date in YYYYMMDD format',
            'Field 4': 'Time in HH:MM:SS format',
            'Field 5': 'Terminal/ATM identifier',
            'Field 6': 'ATM Reference number (numeric)',
            'Field 7': 'Unknown - varies by BDO system',
            'Field 8': 'Unknown - varies by BDO system',
            'Field 9': 'Unknown - varies by BDO system',
            'Field 10': 'Transaction amount (decimal)'
        },
        'notes': [
            'ATM Reference (Field 6) is used for grouping transactions',
            'Only first 4 digits of ATM reference are used for display',
            'Amount should be a valid decimal number',
            'Date can be in YYYYMMDD, MM/DD/YYYY, or YYYY-MM-DD format'
        ]
    })
