from flask import Blueprint, request, jsonify, make_response, send_file
import logging
import os
import uuid
import threading
import traceback
from io import BytesIO
import csv
import tempfile
import shutil

from parsers.metrobank_parser import MetrobankParser
from services.generic_file_processor import GenericFileProcessor

metrobank_bp = Blueprint('metrobank', __name__)
logger = logging.getLogger(__name__)

# In-memory storage for processing status and results
processing_status = {}
processing_results = {}

# Initialize Metrobank Parser
metrobank_parser = MetrobankParser()

@metrobank_bp.route('/process', methods=['POST'])
def process_metrobank_file():
    """Process Metrobank transaction file"""
    success, error_message, result = GenericFileProcessor.process_file_generic(
        parser_class=MetrobankParser,
        route_name='Metrobank',
        validation_error_message='File does not match Metrobank format. Metrobank files should contain space-separated values with amount pattern (11-13 digits + 2 letters) and ATM reference (4+ digits).'
    )
    
    if success:
        return jsonify(result)
    else:
        status_code = 400 if 'format' in error_message.lower() else 500
        return jsonify({'error': error_message}), status_code

@metrobank_bp.route('/info', methods=['GET'])
def get_metrobank_info():
    """Get Metrobank parser information"""
    try:
        return jsonify(metrobank_parser.get_parser_info())
    except Exception as e:
        logger.error(f"Error getting Metrobank info: {str(e)}")
        return jsonify({'error': f'Error getting parser info: {str(e)}'}), 500

@metrobank_bp.route('/validate', methods=['POST'])
def validate_metrobank_file():
    """Validate Metrobank file format"""
    requirements = [
        'File must contain space-separated values',
        'Each line must have at least 2 fields',
        'Must contain amount pattern (11-13 digits followed by 2 letters)',
        'Must contain ATM reference (4+ digits)',
        'Date should be 6 digits at the end of each line'
    ]
    
    success, error_message, validation_data = GenericFileProcessor.validate_file_generic(
        parser_class=MetrobankParser,
        route_name='Metrobank',
        requirements=requirements
    )
    
    if success:
        # Add Metrobank-specific info to validation data
        if validation_data.get('valid'):
            validation_data['file_info']['separator'] = ' (space-separated)'
            validation_data['file_info']['distinguishing_feature'] = 'Space-separated format with amount pattern (11-13 digits + 2 letters)'
            
            if validation_data['file_info'].get('first_line'):
                fields = [f.strip() for f in validation_data['file_info']['first_line'].split() if f.strip()]
                validation_data['file_info']['estimated_fields'] = len(fields)
        
        return jsonify(validation_data)
    else:
        # Add Metrobank-specific error details
        if not validation_data.get('valid'):
            validation_data['common_errors'] = [
                'Missing amount pattern (should be 11-13 digits + 2 letters)',
                'Missing ATM reference (should be 4+ digits)',
                'Incorrect date format (should be 6 digits at end of line)',
                'Wrong separator (should be spaces, not commas or pipes)'
            ]
            return jsonify(validation_data), 400
        else:
            return jsonify({'error': error_message}), 500

@metrobank_bp.route('/sample', methods=['GET'])
def get_metrobank_sample():
    """Get sample Metrobank file format"""
    try:
        return jsonify({'sample_format': metrobank_parser.get_sample_format()})
    except Exception as e:
        logger.error(f"Error getting Metrobank sample: {str(e)}")
        return jsonify({'error': f'Error getting sample format: {str(e)}'}), 500

# Helper function for background processing
def _process_metrobank_file_in_thread(processing_id, file_path):
    """Process Metrobank file in background thread"""
    try:
        # Update status to processing
        processing_status[processing_id] = {
            'status': 'processing',
            'progress': 0,
            'error': None
        }
        
        logger.info(f"Starting to process Metrobank file: {file_path}")
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            file_content = f.read()
        
        # Parse the file
        result = metrobank_parser.parse_file(file_content)
        
        # Store results
        processing_results[processing_id] = result
        
        # Update status to completed
        processing_status[processing_id] = {
            'status': 'completed',
            'progress': 100,
            'error': None
        }
        
        logger.info(f"Successfully processed Metrobank file: {file_path}")
        logger.info(f"Processed {result.get('total_transactions', 0)} transactions")
        
    except Exception as e:
        logger.error(f"Error processing Metrobank file: {str(e)}")
        logger.error(f"Traceback:\n{traceback.format_exc()}")
        
        # Update status with error
        processing_status[processing_id] = {
            'status': 'error',
            'progress': 0,
            'error': str(e)
        }

# Helper function for report generation
def _generate_metrobank_report(processed_data, original_filename):
    """Generate Metrobank report"""
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        
        # Create CSV summary
        csv_file_path = os.path.join(temp_dir, 'metrobank_summary.csv')
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['METROBANK TRANSACTION SUMMARY'])
            writer.writerow([])
            
            # Write totals
            total_transactions = sum(data.get('transaction_count', 0) for data in processed_data.values())
            total_amount = sum(data.get('total_amount', 0) for data in processed_data.values())
            
            writer.writerow(['Total Transactions', total_transactions])
            writer.writerow(['Total Amount', f'₱{total_amount:,.2f}'])
            writer.writerow([])
            
            # Write ATM breakdown
            writer.writerow(['ATM REFERENCE BREAKDOWN'])
            writer.writerow(['ATM Reference', 'Count', 'Amount', 'Payment Mode', 'Dates'])
            
            for atm_ref, data in processed_data.items():
                transaction_count = data.get('transaction_count', 0)
                group_total = data.get('total_amount', 0.0)
                payment_mode = data.get('payment_mode', 'METROBANK')
                dates = data.get('dates', [])
                
                formatted_dates = ', '.join(dates) if dates else ''
                
                writer.writerow([
                    atm_ref,
                    transaction_count,
                    f'{group_total:,.2f}',
                    payment_mode,
                    formatted_dates
                ])
        
        # Create individual ATM reports
        for atm_ref, data in processed_data.items():
            report_path = os.path.join(temp_dir, f'ATM_{atm_ref}_METROBANK.txt')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # Write transaction lines
                raw_lines = data.get('raw_contents', [])
                for line in raw_lines:
                    f.write(f'{line}\n')
        
        # Create zip file
        import zipfile
        zip_path = os.path.join(temp_dir, f'{original_filename}_report.zip')
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add CSV summary
            zipf.write(csv_file_path, os.path.basename(csv_file_path))
            
            # Add all individual ATM files
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    if file.startswith('ATM_') and file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        arc_name = os.path.basename(file_path)
                        zipf.write(file_path, arc_name)
        
        return zip_path
        
    except Exception as e:
        logger.error(f"Error generating Metrobank report: {str(e)}")
        raise
