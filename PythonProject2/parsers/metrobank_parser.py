#!/usr/bin/env python3

import re
import logging
from typing import List, Dict, Any, Tuple
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class MetrobankParser(BaseParser):
    """Parser for Metrobank transaction files"""
    
    def __init__(self):
        super().__init__("METROBANK")
        self.separator = ' '  # Space-separated values
        self.min_fields = 2
        self.atm_ref_field_index = 1  # Field 2 (0-indexed) - ATM reference
        self.amount_field_index = 3   # Field 4 (0-indexed) - amount (with letters)
        self.date_field_index = -1    # Date is at the end of the line
    
    def validate_file(self, lines: List[str]) -> Tuple[bool, str]:
        """Validate if file matches Metrobank format"""
        try:
            valid_lines = 0
            total_lines = 0
            
            for line in lines:
                if not line.strip():
                    continue
                    
                total_lines += 1
                if self._is_valid_line(line):
                    valid_lines += 1
            
            # Consider it valid if at least 50% of lines are valid
            if total_lines > 0 and (valid_lines / total_lines) >= 0.5:
                return True, "File format is valid for Metrobank"
            else:
                return False, "File does not match Metrobank format"
                
        except Exception as e:
            return False, f"Error validating Metrobank file: {str(e)}"
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches Metrobank format"""
        try:
            # Split by spaces
            fields = [f.strip() for f in line.split() if f.strip()]
            
            if len(fields) < self.min_fields:
                return False
            
            # More specific Metrobank validation to avoid false positives
            # Must have specific amount pattern (11-13 digits + 2 letters) AND ATM reference (4+ digits)
            # AND should NOT match other bank patterns
            
            # Check for Metrobank-specific amount pattern (11-13 digits followed by exactly 2 letters)
            amount_pattern = re.search(r'\d{11,13}[A-Z]{2}', line)
            
            # Check for ATM reference (4+ digits)
            atm_ref_pattern = re.search(r'\d{4,}', line)
            
            # Exclude lines that look like other bank formats
            # Exclude lines with 'UB' (Unionbank)
            # Exclude lines with 'UNIONBANK' 
            # Exclude lines that are too long (likely Unionbank)
            # Exclude lines starting with 'T' followed by spaces (likely Unionbank footer)
            if (amount_pattern and atm_ref_pattern and len(fields) >= 2 and
                'UB' not in line and 'UNIONBANK' not in line.upper() and
                len(line) < 200 and not re.match(r'^T\s+', line)):
                return True
            
            return False
        except:
            return False
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse Metrobank transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing METROBANK file with {len(lines)} lines")
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                raw_contents.append(line)
                
                # Parse the line
                transaction = self._parse_transaction_line(line, line_num)
                if transaction:
                    atm_ref = transaction['atm_ref']
                    
                    # Initialize group if not exists
                    if atm_ref not in grouped_data:
                        grouped_data[atm_ref] = {
                            'raw_contents': [],
                            'transaction_count': 0,
                            'total_amount': 0.0,
                            'payment_mode': self.payment_mode,
                            'dates': set(),
                            'transactions': []
                        }
                    
                    # Add to group
                    grouped_data[atm_ref]['raw_contents'].append(line)
                    grouped_data[atm_ref]['transaction_count'] += 1
                    grouped_data[atm_ref]['total_amount'] += transaction['amount']
                    grouped_data[atm_ref]['dates'].add(transaction['date'])
                    grouped_data[atm_ref]['transactions'].append(transaction)
                    
                    total_amount += transaction['amount']
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
            
            logger.info(f"METROBANK processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
            # Also create individual transactions list for frontend compatibility
            individual_transactions = []
            for atm_ref, group in grouped_data.items():
                if group.get('transactions'):
                    individual_transactions.extend(group['transactions'])
                else:
                    # Create individual transactions from raw contents if detailed transactions not available
                    for i, raw_line in enumerate(group['raw_contents']):
                        dates = group['dates'] if isinstance(group['dates'], list) else []
                        date = dates[i] if i < len(dates) else (dates[0] if dates else 'N/A')
                        amount = group['total_amount'] / group['transaction_count'] if group['transaction_count'] > 0 else 0
                        
                        individual_transactions.append({
                            'atm_ref': atm_ref,
                            'date': date,
                            'amount': amount,
                            'raw_text': raw_line,
                            'payment_mode': self.payment_mode
                        })
            
            return {
                'grouped_data': grouped_data,
                'individual_transactions': individual_transactions,
                'raw_contents': raw_contents,
                'payment_mode': self.payment_mode,
                'total_amount': total_amount,
                'total_transactions': len(raw_contents)
            }
            
        except Exception as e:
            logger.error(f"Error parsing Metrobank file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual Metrobank transaction line"""
        try:
            # Split by spaces for Metrobank (following old logic)
            fields = [f.strip() for f in line.split() if f.strip()]
            
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"Metrobank line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference (from field 1, index 1)
            atm_ref = self._extract_atm_reference(fields)
            if not atm_ref:
                logger.warning(f"Metrobank line {line_num}: Could not extract ATM reference")
                return None
            
            # Extract amount
            amount = self._extract_amount(fields, line)
            
            # Extract date
            date = self._extract_date(fields, line)
            
            # Extract additional fields for debugging
            field_1 = self._extract_field(fields, 0)  # Field 1 (amount with letters)
            field_2 = self._extract_field(fields, 1)  # Field 2 (ATM ref)
            field_3 = self._extract_field(fields, 2)  # Field 3
            field_4 = self._extract_field(fields, 3)  # Field 4 (amount with letters)
            
            logger.debug(f"Metrobank line {line_num} parsed: ATM={atm_ref}, Amount={amount}, Date={date}")
            
            return {
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'field_1': field_1,
                'field_2': field_2,
                'field_3': field_3,
                'field_4': field_4,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'line_number': line_num
            }
            
        except Exception as e:
            logger.error(f"Error parsing Metrobank line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, fields: List[str]) -> str:
        """Extract ATM reference from Metrobank fields"""
        try:
            if len(fields) > self.atm_ref_field_index:
                atm_ref_field = fields[self.atm_ref_field_index]
                # For METROBANK, the ATM reference is a simple number (like "1")
                # Clean the reference (keep only digits)
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                if clean_ref:
                    # Take first 4 digits and pad with underscores if less than 4
                    if len(clean_ref) >= 4:
                        atm_ref = clean_ref[:4]  # Take first 4 digits
                    else:
                        # Pad with underscores to make it 4 characters
                        atm_ref = clean_ref.ljust(4, '_')
                    
                    logger.debug(f"Found Metrobank ATM ref: {atm_ref} from {atm_ref_field}")
                    return atm_ref
        except Exception as e:
            logger.error(f"Error extracting Metrobank ATM reference: {str(e)}")
        
        return '0000'  # Default fallback
    
    def _extract_amount(self, fields: List[str], line: str) -> float:
        """Extract amount from Metrobank fields"""
        try:
            # Look for amount pattern in the line (11-13 digits + 2 letters)
            amount_match = re.search(r'(\d{11,13})[A-Z]{2}', line)
            if amount_match:
                amount_str = amount_match.group(1)
                amount = float(amount_str) / 100  # Convert to decimal
                logger.debug(f"Found Metrobank amount: {amount} from {amount_str}")
                return amount
            
            # Fallback: try to find amount in fields
            for field in fields:
                if re.match(r'^\d{11,13}[A-Z]{2}$', field):
                    amount_str = field[:-2]  # Remove the 2 letters
                    amount = float(amount_str) / 100
                    logger.debug(f"Found Metrobank amount in field: {amount} from {field}")
                    return amount
            
            logger.warning(f"Could not extract Metrobank amount from line: {line}")
            return 0.0
            
        except Exception as e:
            logger.error(f"Error extracting Metrobank amount: {str(e)}")
            return 0.0
    
    def _extract_date(self, fields: List[str], line: str) -> str:
        """Extract date from Metrobank fields"""
        try:
            # Extract date from the last field of the line (following old logic)
            if fields:  # Check if we have any fields
                last_field = fields[-1]  # Get the last field
                
                # First try to find a 6-digit date at the start of the field
                if len(last_field) >= 6 and last_field[:6].isdigit():
                    date_str = last_field[:6]
                # If not found at start, try to find it at the end
                elif len(last_field) >= 6 and last_field[-6:].isdigit():
                    date_str = last_field[-6:]
                else:
                    # Fallback: try regex search on the line
                    date_match = re.search(r'(\d{6})\s*$', line)
                    if date_match:
                        date_str = date_match.group(1)
                    else:
                        logger.warning(f"Could not extract Metrobank date from line: {line}")
                        return 'N/A'
                
                # Format from MMDDYY to MM/DD/YYYY
                month = f"{int(date_str[:2]):02d}"
                day = f"{int(date_str[2:4]):02d}"
                year = f"20{date_str[4:]}"  # Assume 20YY format
                formatted_date = f"{month}/{day}/{year}"
                logger.debug(f"Found Metrobank date: {formatted_date} from {date_str}")
                return formatted_date
            
            logger.warning(f"Could not extract Metrobank date from line: {line}")
            return 'N/A'
            
        except Exception as e:
            logger.error(f"Error extracting Metrobank date: {str(e)}")
            return 'N/A'
    
    def _extract_field(self, fields: List[str], index: int) -> str:
        """Extract field by index"""
        try:
            if index < len(fields):
                return fields[index].strip()
            return ''
        except:
            return ''
    
    def get_sample_format(self) -> str:
        """Get sample Metrobank file format"""
        return """00000184193DR 0611 00000184193DR 00000184193DR 031725
00000184193DR 0611 00000184193DR 00000184193DR 031725"""
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get parser information"""
        return {
            'name': 'Metrobank Parser',
            'description': 'Parser for Metrobank transaction files',
            'file_format': 'Space-separated values',
            'separator': ' ',
            'min_fields': 2,
            'field_descriptions': [
                'Field 1: Transaction reference (long reference number)',
                'Field 2: ATM Reference (simple number like "1")',
                'Field 3: Customer name (first part)',
                'Field 4: Customer name (additional parts)',
                'Field 5: Amount with letters (11-13 digits + 2 letters)',
                'Field 6: Date (6 digits in MMDDYY format)'
            ],
            'example_format': 'D491180002306032961210331 1 HERMILA B ROA 00000035200CS 031325',
            'validation_rules': [
                'File must contain space-separated values',
                'Each line must have at least 2 fields',
                'Must contain amount pattern (11-13 digits followed by 2 letters)',
                'Must contain ATM reference (4+ digits)',
                'Date should be 6 digits at the end of each line (MMDDYY format)'
            ]
        }
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches Metrobank format"""
        lines = file_content.split('\n')[:10]  # Check first 10 lines
        
        valid_lines = 0
        total_lines = 0
        
        for line in lines:
            if not line.strip():
                continue
                
            total_lines += 1
            if self._is_valid_line(line):
                valid_lines += 1
        
        # Consider it valid if at least 50% of lines are valid (more lenient)
        if total_lines > 0:
            return (valid_lines / total_lines) >= 0.5
            
        return False
