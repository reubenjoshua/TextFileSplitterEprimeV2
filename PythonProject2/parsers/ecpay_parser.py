import re
import logging
from typing import List, Dict, Any, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class EcpayParser(BaseParser):
    """Parser for ECPay transaction files"""
    
    def __init__(self):
        super().__init__("ECPAY")
        self.separator = ','  # Comma-separated values
        self.min_fields = 7
        self.atm_ref_field_index = 5  # Field 6 (0-indexed)
        self.amount_field_index = 6   # Field 7 (0-indexed)
        self.date_field_index = 1     # Field 2 (0-indexed) - date with time
        self.date_field_index_2 = 2   # Field 3 (0-indexed) - date without time
    
    @staticmethod
    def detect_product_suffix(file_content: str, filename: str = '') -> Optional[str]:
        """Detect ePRIME (EPR) or PRIMEWATER (PIC) from filename or file content."""
        text = f"{filename}\n{file_content}".upper()
        if 'PRIMEWATER' in text:
            return 'PIC'
        if 'EPRIME' in text:
            return 'EPR'
        return None
    
    @staticmethod
    def apply_product_suffix_to_result(result: Dict[str, Any], product_suffix: str) -> None:
        """Attach product suffix to parse result and all ATM groups."""
        result['product_suffix'] = product_suffix
        for group in result.get('grouped_data', {}).values():
            if isinstance(group, dict):
                group['product_suffix'] = product_suffix
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse ECPay transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing ECPAY file with {len(lines)} lines")
            
            # First, validate for malformed lines (split lines)
            self._validate_no_split_lines(lines)
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                raw_contents.append(line)
                
                # Parse the line
                transaction = self._parse_transaction_line(line, line_num)
                if transaction:
                    atm_ref = transaction['atm_ref']
                    is_paygo = transaction.get('is_paygo', False)
                    
                    # Create unique group key for PAY&GO transactions
                    if is_paygo:
                        group_key = f"PAY&GO_{atm_ref}"
                    else:
                        group_key = f"ATM_{atm_ref}"
                    
                    # Initialize group if not exists
                    if group_key not in grouped_data:
                        grouped_data[group_key] = {
                            'raw_contents': [],
                            'transaction_count': 0,
                            'total_amount': 0.0,
                            'payment_mode': self.payment_mode,
                            'dates': set(),
                            'transactions': [],
                            'is_paygo': is_paygo,
                            'atm_ref': atm_ref
                        }
                    
                    # Add to group
                    grouped_data[group_key]['raw_contents'].append(line)
                    grouped_data[group_key]['transaction_count'] += 1
                    grouped_data[group_key]['total_amount'] += transaction['amount']
                    grouped_data[group_key]['dates'].add(transaction['date'])
                    grouped_data[group_key]['transactions'].append(transaction)
                    
                    total_amount += transaction['amount']
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
            
            logger.info(f"ECPAY processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
            product_suffix = self.detect_product_suffix(file_content)
            if product_suffix:
                logger.info(f"ECPAY file detected as {product_suffix}")
            
            # Also create individual transactions list for frontend compatibility
            individual_transactions = []
            for group_key, group in grouped_data.items():
                if group.get('transactions'):
                    individual_transactions.extend(group['transactions'])
                else:
                    # Create individual transactions from raw contents if detailed transactions not available
                    for i, raw_line in enumerate(group['raw_contents']):
                        dates = group['dates'] if isinstance(group['dates'], list) else []
                        date = dates[i] if i < len(dates) else (dates[0] if dates else 'N/A')
                        amount = group['total_amount'] / group['transaction_count'] if group['transaction_count'] > 0 else 0
                        
                        individual_transactions.append({
                            'atm_ref': group.get('atm_ref', group_key),
                            'date': date,
                            'amount': amount,
                            'raw_text': raw_line,
                            'payment_mode': self.payment_mode,
                            'is_paygo': group.get('is_paygo', False)
                        })
            
            result = {
                'grouped_data': grouped_data,
                'individual_transactions': individual_transactions,
                'raw_contents': raw_contents,
                'payment_mode': self.payment_mode,
                'total_amount': total_amount,
                'total_transactions': len(raw_contents)
            }
            
            if product_suffix:
                self.apply_product_suffix_to_result(result, product_suffix)
            
            return result
            
        except Exception as e:
            logger.error(f"Error parsing ECPAY file: {str(e)}")
            raise
    
    def _validate_no_split_lines(self, lines: List[str]) -> None:
        """Validate that there are no split lines in the file"""
        total_errors = 0
        error_details = []
        
        # First pass: count all potential errors
        for line_num, line in enumerate(lines, 1):
            stripped_line = line.strip()
            
            # Skip empty lines
            if not stripped_line:
                continue
            
            # Check if line starts with a comma (indicates it's a continuation of previous line)
            if stripped_line.startswith(','):
                total_errors += 1
                error_details.append({
                    'type': 'continuation_line',
                    'line_num': line_num,
                    'line_content': line
                })
                continue
            
            # Check if the previous line had insufficient fields and might be incomplete
            if line_num > 1:
                prev_line = lines[line_num - 2].strip()
                if prev_line:  # Previous line is not empty
                    prev_fields = [f.strip() for f in prev_line.split(',')]
                    
                    # If previous line has fewer than required fields and current line starts with comma
                    # or if previous line ends with comma pattern and current continues
                    if len(prev_fields) < self.min_fields:
                        # Check if combining them would make sense
                        if stripped_line.startswith(',') or (prev_line.endswith(',') and not prev_line.endswith(',,')): 
                            total_errors += 1
                            error_details.append({
                                'type': 'split_transaction',
                                'line_num': line_num,
                                'prev_line_num': line_num - 1,
                                'line_content': line,
                                'prev_line_content': prev_line,
                                'prev_field_count': len(prev_fields)
                            })
        
        # If we found errors, raise error with the first one and indicate if there are more
        if total_errors > 0:
            first_error = error_details[0]
            
            if first_error['type'] == 'continuation_line':
                error_msg = (
                    f"ERROR: Malformed line detected at line {first_error['line_num']}. "
                    f"Line starts with comma, indicating it's a continuation of the previous line.\n"
                    f"Line content: '{first_error['line_content']}'\n\n"
                    f"This appears to be a split line issue where data that should be on one line "
                    f"is incorrectly broken into multiple lines. Please fix the source file and ensure "
                    f"each transaction is on a single line with all {self.min_fields} required fields."
                )
            else:  # split_transaction
                error_msg = (
                    f"ERROR: Split line detected between lines {first_error['prev_line_num']} and {first_error['line_num']}.\n"
                    f"Line {first_error['prev_line_num']}: '{first_error['prev_line_content']}' (has only {first_error['prev_field_count']} fields, expected {self.min_fields})\n"
                    f"Line {first_error['line_num']}: '{first_error['line_content']}'\n\n"
                    f"These lines appear to be one transaction incorrectly split across multiple lines. "
                    f"Please fix the source file by combining these into a single line with all required fields."
                )
            
            # Add information about additional errors if there are more
            if total_errors > 1:
                error_msg += (
                    f"\n\n⚠️  NOTE: This file contains {total_errors} malformed line(s) total. "
                    f"After fixing this error, please re-upload the file to check for additional issues."
                )
            
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual ECPay transaction line"""
        try:
            # Split by comma for ECPAY
            fields = [f.strip() for f in line.split(',')]
            
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"ECPAY line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference
            atm_ref = self._extract_atm_reference(fields)
            if not atm_ref:
                logger.warning(f"ECPAY line {line_num}: Could not extract ATM reference")
                return None
            
            # Extract amount
            amount = self._extract_amount(fields)
            
            # Extract date
            date = self._extract_date(fields)
            
            # Extract additional fields
            field_1 = self._extract_field(fields, 0)  # Field 1
            field_2 = self._extract_field(fields, 1)  # Field 2
            field_4 = self._extract_field(fields, 3)  # Field 4
            field_5 = self._extract_field(fields, 4)  # Field 5 (ATM ref field)
            field_6 = self._extract_field(fields, 5)  # Field 6
            
            # Check if this is a PAY&GO transaction
            is_paygo = self._is_paygo_transaction(fields)
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'field_1': field_1,
                'field_2': field_2,
                'field_4': field_4,
                'field_5': field_5,
                'field_6': field_6,
                'fields': fields,
                'is_paygo': is_paygo
            }
            
        except Exception as e:
            logger.error(f"Error parsing ECPAY line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, fields: List[str]) -> str:
        """Extract ATM reference from ECPay fields"""
        try:
            if len(fields) > self.atm_ref_field_index:
                atm_ref_field = fields[self.atm_ref_field_index]
                # Clean the reference (keep only digits)
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                # Take first 4 digits as ATM ref
                if len(clean_ref) >= 4:
                    atm_ref = clean_ref[:4]
                    logger.debug(f"Found ECPAY ATM ref: {atm_ref} from {atm_ref_field}")
                    return atm_ref
        except Exception as e:
            logger.error(f"Error extracting ECPAY ATM reference: {str(e)}")
        
        return '0000'  # Default fallback
    
    def _extract_amount(self, fields: List[str]) -> float:
        """Extract amount from ECPay fields"""
        try:
            if len(fields) > self.amount_field_index:
                amount_str = fields[self.amount_field_index].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found ECPAY amount: {amount}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract ECPAY amount: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str]) -> str:
        """Extract date from ECPay fields"""
        try:
            if len(fields) > self.date_field_index:
                date_str = fields[self.date_field_index].strip()
                # Extract date part from datetime string (MM/DD/YYYY HH:MM:SS AM/PM)
                formatted_date = self._extract_date_from_datetime(date_str)
                logger.debug(f"Found ECPAY date: {formatted_date}")
                return formatted_date
        except Exception as e:
            logger.warning(f"Could not extract ECPAY date: {str(e)}")
        
        return 'N/A'
    
    def _extract_field(self, fields: List[str], index: int) -> str:
        """Extract field value safely"""
        try:
            if len(fields) > index:
                return fields[index].strip()
        except Exception as e:
            logger.warning(f"Could not extract field {index}: {str(e)}")
        
        return 'N/A'
    
    def _extract_date_from_datetime(self, datetime_str: str) -> str:
        """Extract date part from ECPay datetime string"""
        try:
            # ECPay dates are typically in format: MM/DD/YYYY HH:MM:SS AM/PM
            # Extract just the date part (MM/DD/YYYY)
            date_match = re.search(r'(\d{1,2}/\d{1,2}/\d{4})', datetime_str)
            if date_match:
                formatted_date = date_match.group(1)
                logger.debug(f"Extracted ECPAY date: {datetime_str} -> {formatted_date}")
                return formatted_date
            else:
                # Return as-is if no date pattern found
                return datetime_str
        except Exception as e:
            logger.warning(f"Could not extract date from ECPAY datetime '{datetime_str}': {str(e)}")
            return datetime_str
    
    def _is_paygo_transaction(self, fields: List[str]) -> bool:
        """Check if transaction is a PAY&GO transaction"""
        try:
            # Check if field 1 contains "PAY&GO"
            if len(fields) > 0:
                field_1 = fields[0].strip().upper()
                if 'PAY&GO' in field_1 or 'PAYGO' in field_1:
                    logger.debug(f"PAY&GO transaction detected: {field_1}")
                    return True
        except Exception as e:
            logger.warning(f"Error checking PAY&GO transaction: {str(e)}")
        
        return False
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches ECPay format"""
        try:
            # Split by comma
            fields = [f.strip() for f in line.split(',')]
            
            if len(fields) < self.min_fields:
                return False
            
            # Check for ECPay-specific patterns based on old code
            # Field 2 (index 1) should contain date with time: MM/DD/YYYY HH:MM:SS AM/PM
            # Field 3 (index 2) should contain date without time
            # Field 6 (index 5) should contain ATM reference
            # Field 7 (index 6) should contain amount
            
            if len(fields) > self.date_field_index:
                date_with_time_field = fields[self.date_field_index].strip()
                # Check if it contains date with time pattern
                if re.search(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(AM|PM)', date_with_time_field, re.IGNORECASE):
                    # Check if field 3 (index 2) contains date without time
                    if len(fields) > self.date_field_index_2:
                        date_without_time_field = fields[self.date_field_index_2].strip()
                        if re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_without_time_field):
                            # Check if field 6 (index 5) contains ATM reference (digits)
                            if len(fields) > self.atm_ref_field_index:
                                atm_ref_field = fields[self.atm_ref_field_index].strip()
                                # Check if field 7 (index 6) contains amount (digits)
                                if len(fields) > self.amount_field_index:
                                    amount_field = fields[self.amount_field_index].strip()
                                    # Both should contain digits
                                    if re.search(r'\d+', atm_ref_field) and re.search(r'\d+', amount_field):
                                        return True
            
            return False
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches ECPay format"""
        lines = file_content.split('\n')
        
        # First check for split lines - if found, raise detailed error
        # Use all lines for split line validation to get accurate count
        try:
            self._validate_no_split_lines(lines)
        except ValueError as e:
            # Re-raise the detailed split line error
            raise e
        
        # For format validation, check first 10 lines to determine if it's ECPay format
        format_lines = lines[:10]
        valid_lines = 0
        total_lines = 0
        
        for line in format_lines:
            stripped_line = line.strip()
            if not stripped_line:
                continue
                
            total_lines += 1
            if self._is_valid_line(stripped_line):
                valid_lines += 1
        
        # Consider it valid if at least 50% of lines are valid (more lenient)
        if total_lines > 0:
            return (valid_lines / total_lines) >= 0.5
            
        return False
    
    def compare_with_cebuana(self, file_content: str) -> str:
        """Compare file format with Cebuana to distinguish from ECPay"""
        try:
            lines = file_content.strip().split('\n')
            ecpay_patterns = 0
            cebuana_patterns = 0
            
            for line in lines[:10]:  # Check first 10 lines
                if not line.strip():
                    continue
                
                # Split by comma
                fields = [f.strip() for f in line.split(',')]
                
                if len(fields) >= 7:
                    # Check date field (usually field 3)
                    date_field = fields[2].strip() if len(fields) > 2 else ""
                    
                    # ECPay dates typically include time: MM/DD/YYYY HH:MM:SS AM/PM
                    if re.search(r'\d{1,2}/\d{1,2}/\d{4}\s+\d{1,2}:\d{2}:\d{2}\s+(AM|PM)', date_field, re.IGNORECASE):
                        ecpay_patterns += 1
                    # Cebuana dates are typically without time: MM/DD/YYYY
                    elif re.match(r'^\d{1,2}/\d{1,2}/\d{4}$', date_field):
                        cebuana_patterns += 1
            
            logger.info(f"ECPAY patterns: {ecpay_patterns}, Cebuana patterns: {cebuana_patterns}")
            
            if ecpay_patterns > cebuana_patterns:
                return 'ECPAY'
            else:
                return 'CEBUANA'
                
        except Exception as e:
            logger.error(f"Error comparing ECPAY with Cebuana: {str(e)}")
            return 'ECPAY'  # Default to ECPAY if comparison fails
    
    def get_sample_format(self) -> str:
        """Get sample ECPay file format"""
        return """Field1,Field2,03/16/2025 02:30:45 PM,03/16/2025,Field5,123456789012,100.50
Field1,Field2,03/16/2025 03:15:22 AM,03/16/2025,Field5,987654321098,250.75"""

    def get_parser_info(self) -> Dict[str, Any]:
        """Get ECPay parser information"""
        return {
            'payment_mode': 'ECPAY',
            'full_name': 'ECPay',
            'description': 'ECPay transaction parser for comma-separated transaction files with datetime fields',
            'supported_formats': ['txt', 'csv', 'log'],
            'file_format': {
                'separator': ', (comma-separated)',
                'minimum_fields': 7,
                'field_descriptions': [
                    'Field 1: Transaction type (PAY&GO or ATM)',
                    'Field 2: Date with time (MM/DD/YYYY HH:MM:SS AM/PM)',
                    'Field 3: Date without time (MM/DD/YYYY)',
                    'Field 4: Unknown field',
                    'Field 5: Unknown field',
                    'Field 6: ATM Reference',
                    'Field 7: Amount (decimal)'
                ]
            },
            'extracted_fields': [
                'atm_ref (first 4 digits of ATM reference)',
                'date (extracted from datetime, formatted as MM/DD/YYYY)',
                'amount (decimal number)',
                'field_1 (first field - transaction type)',
                'field_2 (second field)',
                'field_4 (fourth field)',
                'field_5 (ATM reference field)',
                'field_6 (sixth field)',
                'raw_text (original line)',
                'is_paygo (boolean indicating if transaction is PAY&GO)'
            ],
            'validation_rules': [
                'File must contain comma-separated values',
                'Each line must have at least 7 fields',
                'Each transaction must be on a single line (no split/wrapped lines)',
                'Lines must not start with comma (indicates split line)',
                'Field 3 should contain date with time in MM/DD/YYYY HH:MM:SS AM/PM format',
                'Field 5 should contain ATM reference (numeric)',
                'Field 7 should contain amount (numeric)',
                'Dates must include time component (distinguishes from Cebuana)'
            ],
            'distinguishing_features': [
                'Comma-separated format',
                'Dates include time component (MM/DD/YYYY HH:MM:SS AM/PM)',
                '7+ fields per line',
                'ATM reference in field 5, amount in field 7',
                'Time component in dates distinguishes from Cebuana',
                'PAY&GO transaction detection in field 1'
            ],
            'paygo_feature': {
                'description': 'Automatic detection of PAY&GO transactions',
                'detection_field': 'Field 1 (first field)',
                'detection_pattern': 'PAY&GO or PAYGO (case insensitive)',
                'folder_structure': 'PAY&GO_ATMREF_paymentmode (instead of ATM_ATMREF_paymentmode)',
                'example': 'PAY&GO,10/21/2025 10:52:56 PM,10/21/2025,4B085675774B,651405200287,06026681571562,762.0000'
            },
            'product_suffix_support': {
                'description': 'ePRIME and PRIMEWATER files are labeled in split reports',
                'split_filename_format': 'ATM_{atm_ref}_ECPAY_EPR.txt or ATM_{atm_ref}_ECPAY_PIC.txt',
                'detection': {
                    'ePRIME': 'EPR suffix',
                    'PRIMEWATER': 'PIC suffix'
                }
            },
            'date_format': {
                'input': 'MM/DD/YYYY HH:MM:SS AM/PM',
                'output': 'MM/DD/YYYY (time component extracted)',
                'example': '01/15/2024 14:30:00 PM -> 01/15/2024'
            },
            'cebuana_distinction': {
                'ecpay': 'Dates with time (MM/DD/YYYY HH:MM:SS AM/PM)',
                'cebuana': 'Dates without time (MM/DD/YYYY)',
                'comparison_method': 'Analyzes first 10 lines for date patterns'
            }
        }
