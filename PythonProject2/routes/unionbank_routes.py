#!/usr/bin/env python3

from flask import Blueprint, request, jsonify
import logging
import traceback
from parsers.unionbank_parser import UnionbankParser
from services.generic_file_processor import GenericFileProcessor

logger = logging.getLogger(__name__)

unionbank_bp = Blueprint('unionbank', __name__)

# Initialize Unionbank Parser
unionbank_parser = UnionbankParser()

def process_unionbank_file_generic():
    """Custom Unionbank file processing using generic processor utilities"""
    try:
        # Validate file request using generic processor
        is_valid, error_msg, file = GenericFileProcessor.validate_file_request()
        if not is_valid:
            return False, error_msg, {}
        
        # Get original filename
        from werkzeug.utils import secure_filename
        original_filename = secure_filename(file.filename)
        
        # Read file content with encoding fallback
        file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
        
        # Validate file format using Unionbank's custom validation
        lines = file_content.strip().split('\n')
        is_valid, message = unionbank_parser.validate_file(lines)
        
        if not is_valid:
            return False, message, {}
        
        # Parse the file
        result = unionbank_parser.parse_file(file_content)
        
        # Add filename to result
        result['original_filename'] = original_filename
        
        logger.info(f"Unionbank file {original_filename} processed successfully.")
        return True, '', result
        
    except Exception as e:
        logger.error(f"Error processing Unionbank file: {str(e)}")
        return False, f'Error processing file: {str(e)}', {}

@unionbank_bp.route('/process', methods=['POST'])
def process_unionbank_file():
    """Endpoint to upload and process Unionbank files."""
    success, error_message, result = process_unionbank_file_generic()
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() or 'does not match' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code


@unionbank_bp.route('/info', methods=['GET'])
def get_unionbank_info():
    """Endpoint to get information about the Unionbank parser."""
    return jsonify(unionbank_parser.get_parser_info())

@unionbank_bp.route('/validate', methods=['POST'])
def validate_unionbank_file():
    """Endpoint to validate Unionbank file format."""
    # Validate file request using generic processor
    is_valid, error_msg, file = GenericFileProcessor.validate_file_request()
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    try:
        # Read file content with encoding fallback
        file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
        lines = file_content.strip().split('\n')
        
        # Validate using Unionbank's custom validation
        is_valid, message = unionbank_parser.validate_file(lines)
        
        if is_valid:
            # Get additional info
            non_empty_lines = [line for line in lines if line.strip()]
            
            return jsonify({
                'valid': True,
                'message': message,
                'file_info': {
                    'total_lines': len(lines),
                    'non_empty_lines': len(non_empty_lines),
                    'first_line': non_empty_lines[0] if non_empty_lines else None,
                    'separator': ' (space-separated)',
                    'distinguishing_feature': 'Space-separated format with UB/UNIONBANK markers and long lines (200+ chars)'
                }
            })
        else:
            # Get parser requirements
            parser_info = unionbank_parser.get_parser_info()
            requirements = parser_info.get('requirements', [])
            
            return jsonify({
                'valid': False,
                'message': message,
                'requirements': requirements,
                'common_errors': [
                    'Missing UB or UNIONBANK markers',
                    'Lines too short (need 200+ characters)',
                    'Insufficient valid lines (need 50%+ valid)',
                    'Wrong separator (should be spaces)'
                ]
            }), 400
            
    except Exception as e:
        logger.error(f"Error validating Unionbank file: {str(e)}")
        return jsonify({'error': f'Validation failed: {str(e)}'}), 500

@unionbank_bp.route('/sample', methods=['GET'])
def get_unionbank_sample():
    """Endpoint to get a sample Unionbank file format."""
    return jsonify({
        'sample_format': unionbank_parser.get_sample_format()
    })

