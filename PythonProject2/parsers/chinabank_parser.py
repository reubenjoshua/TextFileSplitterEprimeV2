import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class ChinabankParser(BaseParser):
    """Parser for China Bank transaction files"""
    
    def __init__(self):
        super().__init__("CHINABANK")
        self.separator = ' '  # Space-separated (fixed-width format)
        self.min_fields = 4
        self.atm_ref_field_index = 3  # Field 4 (0-indexed)
        self.amount_field_index = 2   # Field 3 (0-indexed)
        self.date_field_index = 0     # Field 1 (0-indexed)
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse China Bank transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing CHINABANK file with {len(lines)} lines")
            
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
            
            logger.info(f"CHINABANK processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
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
            logger.error(f"Error parsing CHINABANK file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual China Bank transaction line"""
        try:
            # Split by multiple spaces for fixed-width format
            fields = [f.strip() for f in re.split(r'\s+', line.strip()) if f.strip()]
            
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"CHINABANK line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference
            atm_ref = self._extract_atm_reference(fields)
            if not atm_ref:
                logger.warning(f"CHINABANK line {line_num}: Could not extract ATM reference")
                return None
            
            # Extract amount
            amount = self._extract_amount(fields)
            
            # Extract date
            date = self._extract_date(fields)
            
            # Extract additional fields
            field_1 = self._extract_field(fields, 1)  # Field 2
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'field_2': field_1,
                'fields': fields
            }
            
        except Exception as e:
            logger.error(f"Error parsing CHINABANK line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, fields: List[str]) -> str:
        """Extract ATM reference from China Bank fields"""
        try:
            if len(fields) > self.atm_ref_field_index:
                atm_ref_field = fields[self.atm_ref_field_index]
                # Clean the reference (keep only digits)
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                # Take first 4 digits as ATM ref
                if len(clean_ref) >= 4:
                    atm_ref = clean_ref[:4]
                    logger.debug(f"Found CHINABANK ATM ref: {atm_ref} from {atm_ref_field}")
                    return atm_ref
        except Exception as e:
            logger.error(f"Error extracting CHINABANK ATM reference: {str(e)}")
        
        return '0000'  # Default fallback
    
    def _extract_amount(self, fields: List[str]) -> float:
        """Extract amount from China Bank fields"""
        try:
            if len(fields) > self.amount_field_index:
                amount_str = fields[self.amount_field_index].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found CHINABANK amount: {amount}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract CHINABANK amount: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str]) -> str:
        """Extract date from China Bank fields"""
        try:
            if len(fields) > self.date_field_index:
                date_str = fields[self.date_field_index].strip()
                # Format the date from MMDDYYYY to MM/DD/YYYY
                formatted_date = self._format_chinabank_date(date_str)
                logger.debug(f"Found CHINABANK date: {formatted_date}")
                return formatted_date
        except Exception as e:
            logger.warning(f"Could not extract CHINABANK date: {str(e)}")
        
        return 'N/A'
    
    def _extract_field(self, fields: List[str], index: int) -> str:
        """Extract field value safely"""
        try:
            if len(fields) > index:
                return fields[index].strip()
        except Exception as e:
            logger.warning(f"Could not extract field {index}: {str(e)}")
        
        return 'N/A'
    
    def _format_chinabank_date(self, date_str: str) -> str:
        """Format China Bank date from MMDDYYYY to MM/DD/YYYY"""
        try:
            # Check if it's in MMDDYYYY format (8 digits)
            if re.match(r'^\d{8}$', date_str):
                # Format: MMDDYYYY -> MM/DD/YYYY
                month = date_str[:2]
                day = date_str[2:4]
                year = date_str[4:]
                formatted_date = f"{month}/{day}/{year}"
                logger.debug(f"Formatted CHINABANK date: {date_str} -> {formatted_date}")
                return formatted_date
            else:
                # Return as-is if not in expected format
                return date_str
        except Exception as e:
            logger.warning(f"Could not format CHINABANK date '{date_str}': {str(e)}")
            return date_str
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches China Bank format"""
        try:
            # Split by multiple spaces
            fields = [f.strip() for f in re.split(r'\s+', line.strip()) if f.strip()]
            
            if len(fields) < self.min_fields:
                return False
            
            # Check for China Bank-specific patterns
            # Field 1 should contain date in MMDDYYYY format
            if len(fields) > 0:
                date_field = fields[0].strip()
                # Check if it's 8 digits (MMDDYYYY format)
                if re.match(r'^\d{8}$', date_field):
                    # Check if fields 2 and 3 contain numeric values (amount and ATM ref)
                    if len(fields) > 2:
                        amount_field = fields[2].strip()
                        atm_ref_field = fields[3].strip()
                        # Both should contain digits
                        if re.search(r'\d+', amount_field) and re.search(r'\d+', atm_ref_field):
                            return True
            
            return False
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches China Bank format"""
        lines = file_content.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            if not line.strip():
                continue
                
            if self._is_valid_line(line):
                return True
                
        return False
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get China Bank parser information"""
        return {
            'payment_mode': 'CHINABANK',
            'full_name': 'China Bank',
            'description': 'China Bank transaction parser for space-separated (fixed-width) transaction files',
            'supported_formats': ['txt', 'csv', 'log'],
            'file_format': {
                'separator': ' (space-separated, fixed-width format)',
                'minimum_fields': 4,
                'field_descriptions': [
                    'Field 1: Date in MMDDYYYY format',
                    'Field 2: Unknown field',
                    'Field 3: Amount (decimal)',
                    'Field 4: ATM Reference'
                ]
            },
            'extracted_fields': [
                'atm_ref (first 4 digits of ATM reference)',
                'date (formatted as MM/DD/YYYY)',
                'amount (decimal number)',
                'field_2 (second field)',
                'raw_text (original line)'
            ],
            'validation_rules': [
                'File must contain space-separated values',
                'Each line must have at least 4 fields',
                'Field 1 should contain date in MMDDYYYY format (8 digits)',
                'Field 3 should contain amount (numeric)',
                'Field 4 should contain ATM reference (numeric)',
                'Fixed-width format with space separation'
            ],
            'distinguishing_features': [
                'Space-separated fixed-width format',
                'MMDDYYYY date format in field 1',
                'Amount in field 3, ATM reference in field 4',
                'No special separators (unlike BDO with pipes or Cebuana with commas)'
            ],
            'date_format': {
                'input': 'MMDDYYYY (8 digits)',
                'output': 'MM/DD/YYYY',
                'example': '01152024 -> 01/15/2024'
            }
        }
