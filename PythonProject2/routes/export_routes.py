from flask import Blueprint, request, jsonify, make_response
import csv
import io
import json
import logging
import os
from datetime import datetime
from services.report_generator import ReportGenerator

# Configure logging
logger = logging.getLogger(__name__)

export_bp = Blueprint('export', __name__)

@export_bp.route('/csv', methods=['POST'])
def export_csv():
    """Export transaction data as CSV"""
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({'error': 'No transaction data provided'}), 400
        
        transactions = data['transactions']
        payment_mode = data.get('payment_mode', 'Unknown')
        original_filename = data.get('original_filename', '')
        
        # Create CSV in memory
        output = io.StringIO()
        
        # Write CSV header
        fieldnames = ['ATM_REF', 'DATE', 'AMOUNT', 'TYPE', 'ACCOUNT', 'RAW_TEXT']
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        # Write transaction data
        for transaction in transactions:
            writer.writerow({
                'ATM_REF': transaction.get('atmRef', ''),
                'DATE': transaction.get('date', ''),
                'AMOUNT': transaction.get('amount', ''),
                'TYPE': transaction.get('type', ''),
                'ACCOUNT': transaction.get('account', ''),
                'RAW_TEXT': transaction.get('rawText', '')
            })
        
        # Get CSV content
        csv_content = output.getvalue()
        output.close()
        
        # Use original filename if provided, otherwise use default pattern
        if original_filename:
            # Remove extension from original filename and add .csv
            base_filename = os.path.splitext(original_filename)[0]
            filename = f'{base_filename}.csv'
        else:
            filename = f'splitter_export_{payment_mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        
        # Create response
        response = make_response(csv_content)
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting CSV: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/json', methods=['POST'])
def export_json():
    """Export transaction data as JSON"""
    try:
        data = request.get_json()
        
        if not data or 'transactions' not in data:
            return jsonify({'error': 'No transaction data provided'}), 400
        
        transactions = data['transactions']
        payment_mode = data.get('payment_mode', 'Unknown')
        original_filename = data.get('original_filename', '')
        
        # Create JSON response
        export_data = {
            'export_info': {
                'payment_mode': payment_mode,
                'export_date': datetime.now().isoformat(),
                'total_transactions': len(transactions)
            },
            'transactions': transactions
        }
        
        # Use original filename if provided, otherwise use default pattern
        if original_filename:
            # Remove extension from original filename and add .json
            base_filename = os.path.splitext(original_filename)[0]
            filename = f'{base_filename}.json'
        else:
            filename = f'splitter_export_{payment_mode}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
        # Create response
        response = make_response(json.dumps(export_data, indent=2))
        response.headers['Content-Type'] = 'application/json'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
        
    except Exception as e:
        logger.error(f"Error exporting JSON: {str(e)}")
        return jsonify({'error': f'Export failed: {str(e)}'}), 500

@export_bp.route('/report', methods=['POST'])
def generate_comprehensive_report():
    """Generate comprehensive report (like the old splitter)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extract data from request
        processed_data = data.get('processed_data', {})
        raw_contents = data.get('raw_contents', [])
        original_filename = data.get('original_filename', 'transactions')
        payment_mode = data.get('payment_mode', 'Unknown')
        detected_header = data.get('detected_header', None)
        rtp_type = data.get('rtp_type', None)
        product_suffix = data.get('product_suffix', None)
        
        if not processed_data:
            return jsonify({'error': 'No processed data provided'}), 400
        
        # Generate comprehensive report
        report_generator = ReportGenerator()
        zip_path = report_generator.generate_report(
            processed_data=processed_data,
            raw_contents=raw_contents,
            original_filename=original_filename,
            payment_mode=payment_mode,
            detected_header=detected_header,
            rtp_type=rtp_type,
            product_suffix=product_suffix
        )
        
        # Read zip file
        with open(zip_path, 'rb') as f:
            zip_data = f.read()
        
        # Create response
        response = make_response(zip_data)
        response.headers['Content-Type'] = 'application/zip'
        
        # Remove extension from original filename and add .zip
        base_filename = os.path.splitext(original_filename)[0]
        filename = f'{base_filename}.zip'
        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        # Clean up
        report_generator.cleanup()
        
        logger.info(f"Generated comprehensive report: {filename}")
        return response
        
    except Exception as e:
        logger.error(f"Error generating comprehensive report: {str(e)}")
        return jsonify({'error': f'Report generation failed: {str(e)}'}), 500
