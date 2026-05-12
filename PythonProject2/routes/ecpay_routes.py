from flask import Blueprint, request, jsonify
import logging
import os
from werkzeug.utils import secure_filename
from parsers.ecpay_parser import EcpayParser
from services.generic_file_processor import GenericFileProcessor

# Configure logging
logger = logging.getLogger(__name__)

ecpay_bp = Blueprint('ecpay', __name__)

@ecpay_bp.route('/process', methods=['POST'])
def process_file():
    """Process ECPay transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        parser_class=EcpayParser,
        route_name='ECPay',
        validation_error_message='File does not match ECPay format. ECPay files should contain comma-separated values with time in dates (MM/DD/YYYY HH:MM:SS AM/PM format in field 2, date without time in field 3, ATM reference in field 6, and amount in field 7).'
    )
    
    if success:
        return jsonify(result)
    else:
        # Check if it's a split line error (more specific error)
        if 'malformed line' in error_message.lower() or 'split line' in error_message.lower():
            status_code = 400
        elif 'format' in error_message.lower():
            status_code = 400
        else:
            status_code = 500
        return jsonify({'error': error_message}), status_code

@ecpay_bp.route('/info', methods=['GET'])
def get_info():
    """Get ECPay parser information"""
    parser = EcpayParser()
    return jsonify(parser.get_parser_info())

@ecpay_bp.route('/validate', methods=['POST'])
def validate_file():
    """Validate ECPay file format without processing"""
    requirements = [
        'File must contain comma-separated values',
        'Each line must have at least 7 fields',
        'Each transaction must be on a single line (no split/wrapped lines)',
        'Lines must not start with comma (indicates split line)',
        'Field 2 should contain date with time in MM/DD/YYYY HH:MM:SS AM/PM format',
        'Field 3 should contain date without time in MM/DD/YYYY format',
        'Field 6 should contain ATM reference (numeric)',
        'Field 7 should contain amount (numeric)',
        'Dates must include time component (distinguishes from Cebuana)'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        parser_class=EcpayParser,
        route_name='ECPay',
        requirements=requirements
    )
    
    if success:
        # Add ECPay-specific info to validation data
        if validation_data.get('valid'):
            validation_data['file_info']['separator'] = ', (comma-separated)'
            validation_data['file_info']['distinguishing_feature'] = 'Comma-separated format with datetime fields including time component'
            
            if validation_data['file_info'].get('first_line'):
                fields = [f.strip() for f in validation_data['file_info']['first_line'].split(',')]
                validation_data['file_info']['estimated_fields'] = len(fields)
            
            # Check date format in field 3
            date_format_detected = 'Unknown'
            time_component_detected = False
            if fields and len(fields) > 2:
                date_field = fields[2]
                if 'AM' in date_field.upper() or 'PM' in date_field.upper():
                    time_component_detected = True
                    date_format_detected = 'MM/DD/YYYY HH:MM:SS AM/PM (with time)'
                elif len(date_field) >= 10:
                    date_format_detected = 'MM/DD/YYYY (without time - possibly Cebuana)'
                else:
                    date_format_detected = 'Non-standard format'
            
                validation_data['file_info']['date_format_detected'] = date_format_detected
                validation_data['file_info']['time_component_detected'] = time_component_detected
                
                # Compare with Cebuana if parser has this method
                try:
                    parser = EcpayParser()
                    if hasattr(parser, 'compare_with_cebuana'):
                        comparison_result = parser.compare_with_cebuana(validation_data['file_info']['first_line'])
                        validation_data['file_info']['cebuana_comparison'] = comparison_result
                except:
                    pass  # Skip comparison if method doesn't exist
        
        return jsonify(validation_data)
    else:
        # Add ECPay-specific error details
        if not validation_data.get('valid'):
            validation_data['common_errors'] = [
                    'Insufficient fields per line (need at least 7)',
                    'Split lines - transaction data broken across multiple lines',
                    'Lines starting with comma (indicates continuation of previous line)',
                    'Date format incorrect (should include time: MM/DD/YYYY HH:MM:SS AM/PM)',
                    'Missing amount or ATM reference fields',
                    'Using wrong separators (should be commas, not pipes or spaces)',
                    'Dates without time component (might be Cebuana format)'
                ]
            return jsonify(validation_data), 400
        else:
            return jsonify({'error': error_message}), 500

@ecpay_bp.route('/sample', methods=['GET'])
def get_sample_format():
    """Get sample ECPay file format"""
    sample_content = """PAY&GO,01/15/2024 14:30:00 PM,01/15/2024,Unknown4,1234567890,Unknown6,1500.00
ATM,01/15/2024 15:45:30 AM,01/15/2024,Unknown4,0987654321,Unknown6,2500.50
PAY&GO,01/16/2024 09:20:15 PM,01/16/2024,Unknown4,1122334455,Unknown6,750.25"""
    
    return jsonify({
        'sample_format': 'ECPay Transaction File',
        'separator': ', (comma-separated)',
        'description': 'Each line represents one transaction with comma-separated fields including datetime',
        'sample_content': sample_content,
        'field_explanations': {
            'Field 1': 'Transaction type (PAY&GO or ATM) - determines folder structure',
            'Field 2': 'Unknown field - varies by ECPay system',
            'Field 3': 'Date and time (MM/DD/YYYY HH:MM:SS AM/PM)',
            'Field 4': 'Unknown field - varies by ECPay system',
            'Field 5': 'ATM Reference number (numeric)',
            'Field 6': 'Unknown field - varies by ECPay system',
            'Field 7': 'Transaction amount (decimal)'
        },
        'notes': [
            'ATM Reference (Field 5) is used for grouping transactions',
            'Only first 4 digits of ATM reference are used for display',
            'Amount should be a valid decimal number',
            'Date includes time component (MM/DD/YYYY HH:MM:SS AM/PM)',
            'Time component distinguishes ECPay from Cebuana format',
            'Comma-separated format (not pipes or spaces)',
            'PAY&GO transactions create separate folders with PAY&GO_ATMREF_paymentmode format'
        ],
        'paygo_feature': {
            'description': 'PAY&GO transactions are automatically detected and grouped separately',
            'detection': 'Field 1 contains "PAY&GO" (case insensitive)',
            'folder_format': 'PAY&GO_ATMREF_paymentmode instead of ATM_ATMREF_paymentmode',
            'example': 'PAY&GO transactions create files like PAY&GO_1234_ECPAY.txt'
        },
        'date_format': {
            'input_format': 'MM/DD/YYYY HH:MM:SS AM/PM',
            'output_format': 'MM/DD/YYYY (time component extracted)',
            'example': '01/15/2024 14:30:00 PM -> 01/15/2024'
        },
        'cebuana_distinction': {
            'ecpay': 'Dates with time (MM/DD/YYYY HH:MM:SS AM/PM)',
            'cebuana': 'Dates without time (MM/DD/YYYY)',
            'how_to_tell': 'Look for AM/PM or time components in date field'
        }
    })

@ecpay_bp.route('/compare', methods=['POST'])
def compare_with_cebuana():
    """Compare file with Cebuana format to determine if it's ECPay"""
    # Validate file request using generic processor
    is_valid, error_msg, file = GenericFileProcessor.validate_file_request()
    if not is_valid:
        return jsonify({'error': error_msg}), 400
    
    try:
        # Read file content with encoding fallback
        file_content = GenericFileProcessor.read_file_with_encoding_fallback(file)
        
        # Compare with Cebuana
        parser = EcpayParser()
        comparison_result = parser.compare_with_cebuana(file_content)
        
        # Analyze the file for detailed comparison
        lines = file_content.strip().split('\n')
        ecpay_patterns = 0
        cebuana_patterns = 0
        analyzed_lines = 0
        
        for line in lines[:10]:
            if not line.strip():
                continue
            
            fields = [f.strip() for f in line.split(',')]
            if len(fields) >= 7:
                date_field = fields[2] if len(fields) > 2 else ""
                
                if 'AM' in date_field.upper() or 'PM' in date_field.upper():
                    ecpay_patterns += 1
                elif len(date_field) == 10 and '/' in date_field:  # MM/DD/YYYY format
                    cebuana_patterns += 1
                
                analyzed_lines += 1
        
        return jsonify({
            'detected_format': comparison_result,
            'analysis': {
                'total_lines_analyzed': analyzed_lines,
                'ecpay_patterns_found': ecpay_patterns,
                'cebuana_patterns_found': cebuana_patterns,
                'confidence': 'high' if abs(ecpay_patterns - cebuana_patterns) > 2 else 'medium'
            },
            'format_characteristics': {
                'ecpay': {
                    'date_format': 'MM/DD/YYYY HH:MM:SS AM/PM',
                    'time_component': 'Included',
                    'example': '01/15/2024 14:30:00 PM',
                    'separator': 'comma'
                },
                'cebuana': {
                    'date_format': 'MM/DD/YYYY',
                    'time_component': 'Not included',
                    'example': '01/15/2024',
                    'separator': 'comma'
                }
            },
            'recommendation': {
                'use_ecpay_parser': comparison_result == 'ECPAY',
                'use_cebuana_parser': comparison_result == 'CEBUANA',
                'reason': f'File shows {comparison_result} patterns based on date format analysis'
            }
        })
        
    except Exception as e:
        logger.error(f"Error comparing ECPay with Cebuana: {str(e)}")
        return jsonify({'error': f'Comparison failed: {str(e)}'}), 500

@ecpay_bp.route('/compare', methods=['GET'])
def compare_formats():
    """Compare ECPay format with other payment modes"""
    return jsonify({
        'comparison': {
            'ecpay': {
                'name': 'ECPay',
                'separator': ', (comma-separated)',
                'date_format': 'MM/DD/YYYY HH:MM:SS AM/PM',
                'example_date': '01/15/2024 14:30:00 PM',
                'minimum_fields': 7,
                'distinguishing_feature': 'Comma-separated with time component in dates'
            },
            'cebuana': {
                'name': 'Cebuana Lhuillier',
                'separator': ', (comma-separated)',
                'date_format': 'MM/DD/YYYY (without time)',
                'example_date': '01/15/2024',
                'minimum_fields': 7,
                'distinguishing_feature': 'Comma-separated without time component'
            },
            'bdo': {
                'name': 'BDO',
                'separator': '| (pipe)',
                'date_format': 'YYYYMMDD or MM/DD/YYYY',
                'example_date': '20240115 or 01/15/2024',
                'minimum_fields': 10,
                'distinguishing_feature': 'Pipe-separated format'
            },
            'chinabank': {
                'name': 'China Bank',
                'separator': ' (space-separated)',
                'date_format': 'MMDDYYYY (8 digits)',
                'example_date': '01152024',
                'minimum_fields': 4,
                'distinguishing_feature': 'Space-separated fixed-width format'
            }
        },
        'how_to_distinguish': [
            'Check the separator used:',
            'ECPay: Comma-separated (,)',
            'Cebuana: Comma-separated (,) - same as ECPay!',
            'BDO: Pipe-separated (|)',
            'China Bank: Space-separated (no special characters)',
            'For ECPay vs Cebuana (both comma-separated):',
            'ECPay: Dates include time (MM/DD/YYYY HH:MM:SS AM/PM)',
            'Cebuana: Dates without time (MM/DD/YYYY)',
            'Look for AM/PM or time components in the date field'
        ],
        'sample_lines': {
            'ecpay': 'Unknown1,Unknown2,01/15/2024 14:30:00 PM,Unknown4,1234567890,Unknown6,1500.00',
            'cebuana': 'Unknown1,01/15/2024,01/15/2024,Unknown4,1234567890,Unknown6,1500.00',
            'bdo': 'Unknown1|Unknown2|20240115|14:30:00|ATM001|1234567890|Unknown7|Unknown8|Unknown9|1500.00',
            'chinabank': '01152024 Unknown2 1500.00 1234567890'
        }
    })

@ecpay_bp.route('/format-guide', methods=['GET'])
def get_format_guide():
    """Get detailed format guide for ECPay files"""
    return jsonify({
        'format_guide': {
            'file_structure': {
                'type': 'Comma-separated values (CSV-like)',
                'encoding': 'UTF-8 (with fallback to latin-1, cp1252)',
                'line_endings': 'Unix (LF) or Windows (CRLF)',
                'field_separation': 'Comma (,) between fields'
            },
            'field_specifications': {
                'field_1': {
                    'position': 1,
                    'name': 'Unknown',
                    'format': 'Variable',
                    'example': 'Unknown1',
                    'description': 'Unknown field - varies by ECPay system'
                },
                'field_2': {
                    'position': 2,
                    'name': 'Unknown',
                    'format': 'Variable',
                    'example': 'Unknown2',
                    'description': 'Unknown field - varies by ECPay system'
                },
                'field_3': {
                    'position': 3,
                    'name': 'Date and Time',
                    'format': 'MM/DD/YYYY HH:MM:SS AM/PM',
                    'example': '01/15/2024 14:30:00 PM',
                    'description': 'Transaction date and time with AM/PM indicator'
                },
                'field_4': {
                    'position': 4,
                    'name': 'Unknown',
                    'format': 'Variable',
                    'example': 'Unknown4',
                    'description': 'Unknown field - varies by ECPay system'
                },
                'field_5': {
                    'position': 5,
                    'name': 'ATM Reference',
                    'format': 'Numeric string',
                    'example': '1234567890',
                    'description': 'ATM reference number (first 4 digits used for grouping)'
                },
                'field_6': {
                    'position': 6,
                    'name': 'Unknown',
                    'format': 'Variable',
                    'example': 'Unknown6',
                    'description': 'Unknown field - varies by ECPay system'
                },
                'field_7': {
                    'position': 7,
                    'name': 'Amount',
                    'format': 'Decimal number',
                    'example': '1500.00',
                    'description': 'Transaction amount as decimal number'
                }
            },
            'validation_criteria': [
                'Each line must have at least 7 comma-separated fields',
                'Each transaction must be on a single line (no split/wrapped lines)',
                'Lines must not start with comma (indicates continuation)',
                'Field 3 must contain date with time in MM/DD/YYYY HH:MM:SS AM/PM format',
                'Field 5 must contain numeric ATM reference',
                'Field 7 must be a valid decimal number',
                'Time component (AM/PM) must be present in date field'
            ],
            'cebuana_distinction': {
                'key_difference': 'Time component in date field',
                'ecpay_date': '01/15/2024 14:30:00 PM (with time)',
                'cebuana_date': '01/15/2024 (without time)',
                'identification_method': 'Look for AM/PM or HH:MM:SS in date field'
            },
            'common_issues': {
                'split_lines': 'Transaction data broken across multiple lines - each transaction must be on a single line with all 7 fields',
                'continuation_lines': 'Lines starting with comma indicate they are continuations of previous line - fix by combining into single line',
                'insufficient_fields': 'Lines with fewer than 7 fields will be rejected',
                'invalid_date_format': 'Date field must include time component with AM/PM',
                'missing_time_component': 'Dates without time might be Cebuana format',
                'non_numeric_amount': 'Amount field must be a valid decimal number',
                'missing_atm_reference': 'ATM reference field must contain numeric characters'
            }
        }
    })
