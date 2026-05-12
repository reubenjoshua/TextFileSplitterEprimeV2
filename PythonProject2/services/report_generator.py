import csv
import os
import tempfile
import shutil
import zipfile
import logging
from datetime import datetime
from typing import Dict, Any, List
from parsers.bdo_parser import BDOParser

logger = logging.getLogger(__name__)

class ReportGenerator:
    """Generate comprehensive reports for transaction data"""
    
    def __init__(self):
        self.temp_dir = None
    
    def generate_report(self, processed_data: Dict[str, Any], raw_contents: List[str], 
                       original_filename: str, payment_mode: str, detected_header: str = None) -> str:
        """
        Generate a comprehensive report with CSV summary and individual ATM files
        
        Args:
            processed_data: Processed transaction data
            raw_contents: Raw file contents
            original_filename: Original filename
            payment_mode: Payment mode used for processing
            
        Returns:
            Path to the generated zip file
        """
        try:
            logger.info("Starting report generation")
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp()
            
            # Create CSV summary file
            csv_file_path = self._create_csv_summary(processed_data, payment_mode)
            
            # Create individual ATM reports
            self._create_atm_reports(processed_data, raw_contents, payment_mode, detected_header)
            
            # Create zip file
            zip_path = self._create_zip_file(original_filename)
            
            logger.info(f"Report generation completed: {zip_path}")
            return zip_path
            
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            raise
    
    def _create_csv_summary(self, processed_data: Dict[str, Any], payment_mode: str) -> str:
        """Create CSV summary file"""
        csv_file_path = os.path.join(self.temp_dir, 'transactions_summary.csv')
        
        with open(csv_file_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['OVERALL SUMMARY REPORT'])
            writer.writerow([])
            
            # Calculate totals
            total_transactions = 0
            total_amount = 0.0
            
            # Process transactions to calculate totals
            for atm_ref, group_data in processed_data.items():
                if isinstance(group_data, dict):
                    transaction_count = group_data.get('transaction_count', 0)
                    group_total = group_data.get('total_amount', 0.0)
                    
                    total_transactions += transaction_count
                    total_amount += group_total
            
            # Write totals
            writer.writerow(['Total Transactions', total_transactions])
            writer.writerow(['Total Amount', f'₱{total_amount:,.2f}'])
            writer.writerow([])
            
            # Write ATM breakdown header
            writer.writerow(['ATM REFERENCE BREAKDOWN'])
            writer.writerow(['ATM Reference', 'Count', 'Amount', 'PaymentMode', 'Dates'])
            
            # Process each ATM reference group
            for group_key, group_data in processed_data.items():
                if not isinstance(group_data, dict):
                    continue
                
                transaction_count = group_data.get('transaction_count', 0)
                group_total = group_data.get('total_amount', 0.0)
                dates = group_data.get('dates', [])
                atm_ref = group_data.get('atm_ref', group_key)
                is_paygo = group_data.get('is_paygo', False)
                
                # Format dates
                if isinstance(dates, list):
                    formatted_dates = ', '.join(sorted(dates))
                elif isinstance(dates, set):
                    formatted_dates = ', '.join(sorted(list(dates)))
                else:
                    formatted_dates = str(dates) if dates else ''
                
                # Create display reference with PAY&GO indicator
                display_ref = f"PAY&GO_{atm_ref}" if is_paygo else atm_ref
                
                # Write row
                writer.writerow([
                    display_ref,
                    transaction_count,
                    f'{group_total:,.2f}',
                    payment_mode if payment_mode else 'Unknown',
                    formatted_dates
                ])
        
        return csv_file_path
    
    def _create_atm_reports(self, processed_data: Dict[str, Any], 
                           raw_contents: List[str], payment_mode: str, detected_header: str = None):
        """Create individual ATM report files"""
        
        for group_key, group_data in processed_data.items():
            if not isinstance(group_data, dict):
                continue
            
            # Determine the prefix for the filename based on transaction type
            is_paygo = group_data.get('is_paygo', False)
            atm_ref = group_data.get('atm_ref', group_key)
            
            if is_paygo and payment_mode.upper() == 'ECPAY':
                # Use PAY&GO prefix for PAY&GO transactions in ECPAY
                filename_prefix = 'PAY&GO'
            else:
                # Use ATM prefix for regular transactions
                filename_prefix = 'ATM'
            
            # Create report file path
            report_path = os.path.join(self.temp_dir, f'{filename_prefix}_{atm_ref}_{payment_mode}.txt')
            
            with open(report_path, 'w', encoding='utf-8') as f:
                # Handle SM headers
                if payment_mode and payment_mode.upper() == 'SM' and detected_header:
                    f.write(f"{detected_header}\n")
                
                # Write transaction lines
                raw_lines = group_data.get('raw_contents', [])
                
                for line in raw_lines:
                    if payment_mode and payment_mode.upper() == 'BDO':
                        # Format BDO lines using the BDO parser method
                        formatted_line = self._format_bdo_line_with_parser(line)
                        f.write(formatted_line)
                    else:
                        f.write(f'{line}\n')
    
    
    def _format_bdo_line_with_parser(self, line: str) -> str:
        """Format BDO line using the BDO parser's formatting method"""
        try:
            # Parse the line into fields
            fields = line.strip().split('|')
            
            if len(fields) >= 10:
                # Create a transaction dict that the BDO parser expects
                transaction = {
                    'fields': fields,
                    'raw_text': line
                }
                
                # Use the BDO parser's formatting method
                bdo_parser = BDOParser()
                formatted_line = bdo_parser.generate_formatted_report_line(transaction)
                return formatted_line
            else:
                return f'{line}\n'
        except Exception as e:
            logger.error(f"Error formatting BDO line: {str(e)}")
            return f'{line}\n'
    
    def _format_bdo_date(self, date_raw: str) -> str:
        """Format BDO date to MM/DD/YYYY with leading zeros"""
        try:
            date_fmt = date_raw
            
            if len(date_raw) == 8 and date_raw.isdigit():
                # YYYYMMDD format
                year = date_raw[:4]
                month = f"{int(date_raw[4:6]):02d}"
                day = f"{int(date_raw[6:]):02d}"
                date_fmt = f"{month}/{day}/{year}"
            elif '/' in date_raw and len(date_raw.split('/')) == 3:
                # MM/DD/YYYY format - ensure leading zeros
                m, d, y = date_raw.split('/')
                month = f"{int(m):02d}"
                day = f"{int(d):02d}"
                date_fmt = f"{month}/{day}/{y}"
            elif '-' in date_raw and len(date_raw.split('-')) == 3:
                # YYYY-MM-DD format
                y, m, d = date_raw.split('-')
                month = f"{int(m):02d}"
                day = f"{int(d):02d}"
                date_fmt = f"{month}/{day}/{y}"
            
            return date_fmt
        except Exception as e:
            logger.warning(f"Error formatting BDO date: {str(e)}")
            return date_raw
    
    def _create_zip_file(self, original_filename: str) -> str:
        """Create zip file containing all report files"""
        zip_path = os.path.join(self.temp_dir, f'{original_filename}.zip')
        
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            # Add all files except the zip itself
            for root, _, files in os.walk(self.temp_dir):
                for file in files:
                    if file != f'{original_filename}.zip':
                        file_path = os.path.join(root, file)
                        arc_name = os.path.basename(file_path)
                        zipf.write(file_path, arc_name)
        
        return zip_path
    
    def cleanup(self):
        """Clean up temporary files"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary files")
            except Exception as e:
                logger.error(f"Error cleaning up temp directory: {e}")
