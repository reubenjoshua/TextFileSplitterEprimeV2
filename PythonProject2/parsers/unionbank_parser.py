#!/usr/bin/env python3

import re
import logging
from typing import List, Dict, Any, Tuple, Optional
from .base_parser import BaseParser

logger = logging.getLogger(__name__)


class UnionbankParser(BaseParser):
    """Parser for Unionbank transaction files"""
    
    def __init__(self):
        super().__init__("UNIONBANK")
        self.separator = ' '  # Space-separated values
        self.min_fields = 4
    
    def validate_file(self, lines: List[str]) -> Tuple[bool, str]:
        """Validate if file matches Unionbank format"""
        try:
            total_lines = sum(1 for line in lines if line.strip())
            valid_lines = sum(1 for line in lines if line.strip() and self._is_valid_line(line))
            
            if total_lines > 0:
                is_valid = (valid_lines / total_lines) >= 0.5
                message = "File format is valid for Unionbank" if is_valid else "File does not match Unionbank format"
                return is_valid, message
            
            return False, "File is empty"
                
        except Exception as e:
            return False, f"Error validating Unionbank file: {str(e)}"
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches Unionbank format"""
        try:
            # UB/UNIONBANK with long lines
            if (('UB' in line and re.search(r'UB\d{6,}', line)) or 
                ('UNIONBANK' in line.upper())) and len(line) > 200:
                return True
            
            # Unionbank footer format
            if re.match(r'^T\s+', line) and len(line) > 100:
                return True
            
            # Long sequences of spaces followed by digits
            if len(line) > 200 and re.search(r'\s{20,}\d{6,}\s+\d+', line):
                return True
            
            return False
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches Unionbank format"""
        lines = file_content.split('\n')[:10]
        return any(self._is_valid_line(line) for line in lines if line.strip())
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse Unionbank transaction file"""
        try:
            lines = file_content.strip().split('\n')
            logger.info(f"Processing UNIONBANK file with {len(lines)} lines")
            
            # Filter transaction lines
            transaction_lines = self._filter_transaction_lines(lines)
            
            # Parse transactions
            grouped_data = {}
            individual_transactions = []
            total_amount = 0.0
            
            for line_num, line in enumerate(transaction_lines, 1):
                transaction = self._parse_transaction_line(line, line_num)
                if transaction:
                    atm_ref = transaction['atm_ref']
                    
                    # Add to grouped data
                    if atm_ref not in grouped_data:
                        grouped_data[atm_ref] = {
                            'raw_contents': [],
                            'transaction_count': 0,
                            'total_amount': 0.0,
                            'payment_mode': self.payment_mode,
                            'dates': set(),
                            'transactions': []
                        }
                    
                    grouped_data[atm_ref]['raw_contents'].append(line)
                    grouped_data[atm_ref]['transaction_count'] += 1
                    grouped_data[atm_ref]['total_amount'] += transaction['amount']
                    grouped_data[atm_ref]['dates'].add(transaction['date'])
                    grouped_data[atm_ref]['transactions'].append(transaction)
                    
                    individual_transactions.append(transaction)
                    total_amount += transaction['amount']
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
            
            logger.info(f"UNIONBANK processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
            return {
                'grouped_data': grouped_data,
                'individual_transactions': individual_transactions,
                'raw_contents': transaction_lines,
                'payment_mode': self.payment_mode,
                'total_amount': total_amount,
                'total_transactions': len(transaction_lines)
            }
            
        except Exception as e:
            logger.error(f"Error parsing Unionbank file: {str(e)}")
            raise
    
    def _filter_transaction_lines(self, lines: List[str]) -> List[str]:
        """Filter out header and footer lines"""
        return [
            line for line in lines 
            if line.strip() and not line.startswith('H UNIONBANK') and not line.startswith('T')
        ]
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Optional[Dict[str, Any]]:
        """Parse a single Unionbank transaction line"""
        try:
            # Normalize UB reference format
            line = self._normalize_ub_reference(line, line_num)
            
            # Extract transaction data
            atm_ref = self._extract_atm_reference(line)
            amount = self._extract_amount(line, line_num)
            date = self._extract_date(line, line_num)
            
            if amount is None or date is None:
                return None
            
            logger.debug(f"Line {line_num}: Found ATM ref {atm_ref}, amount {amount}, date {date}")
            
            return {
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'line_number': line_num
            }
            
        except Exception as e:
            logger.error(f"Error parsing Unionbank line {line_num}: {str(e)}")
            return None
    
    def _normalize_ub_reference(self, line: str, line_num: int) -> str:
        """Normalize UB reference by fixing spacing issues"""
        ub_pattern = re.search(r'UB(\d{7,})', line)
        if ub_pattern:
            ub_ref_num = ub_pattern.group(1)
            logger.debug(f"Line {line_num}: Found UB reference: {ub_ref_num} (length: {len(ub_ref_num)})")
            
            # Fix spacing if UB reference is too long
            if len(ub_ref_num) > 7:
                ub_ref_cut = ub_ref_num[:7]  # Take first 7 characters
                ub_remaining = ub_ref_num[7:]  # Get remaining characters
                
                logger.debug(f"Line {line_num}: UB reference too long, inserting space after 7th character")
                
                # Replace the long UB reference with properly spaced version
                original_part = f"UB{ub_ref_num}"
                corrected_part = f"UB{ub_ref_cut} {ub_remaining}"
                line = line.replace(original_part, corrected_part, 1)
                
                logger.debug(f"Line {line_num}: Modified line after UB reference correction: {line[:100]}...")
        
        return line
    
    def _extract_atm_reference(self, line: str) -> str:
        """Extract ATM reference from line"""
        # Try 14-digit reference first
        matches = list(re.finditer(r'\s{10,}(\d{14})\s+', line))
        if matches:
            return matches[-1].group(1)[:4]  # Take last match, first 4 digits
        
        # Try shorter reference
        ref_match = re.search(r'\s{10,}(\d{4,})\s+', line)
        if ref_match:
            return ref_match.group(1)[:4]
        
        # Fallback to field-based extraction
        fields = line.strip().split()
        if len(fields) > 4:
            clean_ref = ''.join(c for c in fields[4] if c.isdigit())[:4]
            return clean_ref if len(clean_ref) >= 4 else '0000'
        
        return '0000'
    
    def _extract_amount(self, line: str, line_num: int) -> Optional[float]:
        """Extract amount from line"""
        amount_match = re.search(r'(\d{12})(?:DB|LC)\d*\s*$', line)
        if not amount_match:
            logger.debug(f"Line {line_num}: No amount pattern found")
            return None
        
        amount_str = amount_match.group(1)
        return float(amount_str) / 100  # Amount is usually in cents
    
    def _extract_date(self, line: str, line_num: int) -> Optional[str]:
        """Extract date from line"""
        fields = line.strip().split()
        if len(fields) <= 3:
            logger.debug(f"Line {line_num}: Not enough fields for date extraction")
            return None
        
        date_field = fields[3]
        date_match = re.search(r'(\d{6})', date_field)
        if not date_match:
            logger.debug(f"Line {line_num}: No date pattern found in field: {date_field}")
            return None
        
        date_str = date_match.group(1)
        return self._validate_and_format_date(date_str, line_num)
    
    def _validate_and_format_date(self, date_str: str, line_num: int) -> Optional[str]:
        """Validate and format date string"""
        try:
            month = int(date_str[:2])
            day = int(date_str[2:4])
            year = int(date_str[4:])
            
            # Validate month and day
            if not (1 <= month <= 12 and 1 <= day <= 31):
                logger.debug(f"Line {line_num}: Invalid date: {date_str}")
                return None
            
            # Validate day for specific month
            if not self._is_valid_day_for_month(month, day):
                logger.debug(f"Line {line_num}: Invalid day {day} for month {month}")
                return None
            
            formatted_date = f"{month:02d}/{day:02d}/20{year:02d}"
            logger.debug(f"Line {line_num}: Found valid date {formatted_date} from: {date_str}")
            return formatted_date
            
        except (ValueError, IndexError) as e:
            logger.debug(f"Line {line_num}: Error parsing date {date_str}: {e}")
            return None
    
    def _is_valid_day_for_month(self, month: int, day: int) -> bool:
        """Check if day is valid for given month"""
        if month in [1, 3, 5, 7, 8, 10, 12]:
            return day <= 31  # 31-day months
        elif month in [4, 6, 9, 11]:
            return day <= 30  # 30-day months
        elif month == 2:
            return day <= 29  # February (leap year handling)
        return False
    
    def get_sample_format(self) -> str:
        """Get sample Unionbank file format"""
        return """H UNIONBANK OF THE PHILIPPINES
UB12345678901234567890 250317 123456789012DB
UB12345678901234567890 250317 123456789012LC
T 12345678901234567890"""
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get parser information"""
        return {
            'name': 'Unionbank Parser',
            'payment_mode': self.payment_mode,
            'description': 'Parses Unionbank transaction files with UB prefix and varying reference lengths',
            'file_format': 'Fixed-width with UB prefix, long lines (200+ characters)',
            'requirements': [
                'File must contain lines with UB prefix followed by digits',
                'Each transaction line must be 200+ characters long',
                'Must contain ATM reference sequences',
                'Must contain 12-digit amount followed by DB or LC',
                'Must contain 6-digit date in MMDDYY format'
            ],
            'field_descriptions': [
                'UB prefix followed by digits (7-8 characters)',
                '6-digit date in MMDDYY format',
                '12-digit amount followed by DB or LC',
                'ATM reference sequence'
            ],
            'example_format': 'UB1174154091625223306RAZEL',
            'validation_rules': [
                'File must contain UB prefix in transaction lines',
                'Lines must be 200+ characters long',
                'Must contain amount pattern (12 digits + DB/LC)',
                'Must contain valid date pattern',
                'UB reference automatically normalized for spacing'
            ]
        }