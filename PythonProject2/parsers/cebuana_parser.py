import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class CebuanaParser(BaseParser):
    """Parser for Cebuana Lhuillier transaction files"""
    
    def __init__(self):
        super().__init__("CEBUANA")
        self.separator = ','
        self.min_fields = 7
        self.atm_ref_field_index = 4  # Field 5 (0-indexed)
        self.amount_field_index = 6   # Field 7 (0-indexed)
        self.date_field_index = 2     # Field 3 (0-indexed)
        self.date_field_index_alt = 1 # Field 2 (0-indexed) - alternative date field
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse Cebuana transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing CEBUANA file with {len(lines)} lines")
            
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
            
            logger.info(f"CEBUANA processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
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
            logger.error(f"Error parsing CEBUANA file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual Cebuana transaction line"""
        try:
            # Split by comma separator
            fields = [field.strip() for field in line.split(self.separator)]
            
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"CEBUANA line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference
            atm_ref = self._extract_atm_reference(fields)
            if not atm_ref:
                logger.warning(f"CEBUANA line {line_num}: Could not extract ATM reference")
                return None
            
            # Extract amount
            amount = self._extract_amount(fields)
            
            # Extract date
            date = self._extract_date(fields)
            
            # Extract additional fields
            field_1 = self._extract_field(fields, 1)  # Field 2 (alternative date)
            field_3 = self._extract_field(fields, 3)  # Field 4
            field_5 = self._extract_field(fields, 5)  # Field 6
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'date_alt': field_1,  # Alternative date field
                'field_4': field_3,
                'field_6': field_5,
                'fields': fields
            }
            
        except Exception as e:
            logger.error(f"Error parsing CEBUANA line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, fields: List[str]) -> str:
        """Extract ATM reference from Cebuana fields"""
        try:
            if len(fields) > self.atm_ref_field_index:
                atm_ref_field = fields[self.atm_ref_field_index]
                # Clean the reference (keep only digits)
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                # Take first 4 digits as ATM ref
                if len(clean_ref) >= 4:
                    atm_ref = clean_ref[:4]
                    logger.debug(f"Found CEBUANA ATM ref: {atm_ref} from {atm_ref_field}")
                    return atm_ref
        except Exception as e:
            logger.error(f"Error extracting CEBUANA ATM reference: {str(e)}")
        
        return '0000'  # Default fallback
    
    def _extract_amount(self, fields: List[str]) -> float:
        """Extract amount from Cebuana fields"""
        try:
            if len(fields) > self.amount_field_index:
                amount_str = fields[self.amount_field_index].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found CEBUANA amount: {amount}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract CEBUANA amount: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str]) -> str:
        """Extract date from Cebuana fields"""
        try:
            # Try primary date field (index 2)
            if len(fields) > self.date_field_index:
                date_str = fields[self.date_field_index].strip()
                if self._is_valid_cebuana_date(date_str):
                    logger.debug(f"Found CEBUANA date: {date_str}")
                    return date_str
            
            # Try alternative date field (index 1)
            if len(fields) > self.date_field_index_alt:
                date_str = fields[self.date_field_index_alt].strip()
                if self._is_valid_cebuana_date(date_str):
                    logger.debug(f"Found CEBUANA date (alt): {date_str}")
                    return date_str
                    
        except Exception as e:
            logger.warning(f"Could not extract CEBUANA date: {str(e)}")
        
        return 'N/A'
    
    def _extract_field(self, fields: List[str], index: int) -> str:
        """Extract field value safely"""
        try:
            if len(fields) > index:
                return fields[index].strip()
        except Exception as e:
            logger.warning(f"Could not extract field {index}: {str(e)}")
        
        return 'N/A'
    
    def _is_valid_cebuana_date(self, date_str: str) -> bool:
        """Check if date string is valid Cebuana date format"""
        try:
            # Cebuana dates should be in MM/DD/YYYY format without time
            if re.match(r'^\d{2}/\d{2}/\d{4}$', date_str):
                return True
        except:
            pass
        return False
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches Cebuana format"""
        try:
            fields = line.split(self.separator)
            if len(fields) < self.min_fields:
                return False
            
            # Check for Cebuana-specific patterns
            # Field 2 and 3 should contain dates without time
            if len(fields) >= 3:
                field_1 = fields[1].strip()
                field_2 = fields[2].strip()
                
                # Check if fields contain dates without time (MM/DD/YYYY)
                if (re.match(r'^\d{2}/\d{2}/\d{4}$', field_1) and 
                    re.match(r'^\d{2}/\d{2}/\d{4}$', field_2)):
                    return True
                
                # Check if this might be an ECPAY file (has time component)
                if re.search(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+[AP]M', field_1):
                    return False  # This is ECPAY format, not Cebuana
            
            return False
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches Cebuana format"""
        lines = file_content.split('\n')[:5]  # Check first 5 lines
        
        for line in lines:
            if not line.strip():
                continue
                
            # Skip if this looks like ECPAY format
            if self._is_ecpay_format(line):
                return False
                
            if self._is_valid_line(line):
                return True
                
        return False
    
    def _is_ecpay_format(self, line: str) -> bool:
        """Check if line looks like ECPAY format (has time component)"""
        try:
            fields = line.split(',')
            if len(fields) >= 2:
                field_1 = fields[1].strip()
                # ECPAY has time component in date field
                if re.search(r'\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2}\s+[AP]M', field_1):
                    return True
        except:
            pass
        return False
    
    def get_parser_info(self) -> Dict[str, Any]:
        """Get Cebuana parser information"""
        return {
            'payment_mode': 'CEBUANA',
            'full_name': 'Cebuana Lhuillier',
            'description': 'Cebuana Lhuillier transaction parser for comma-separated transaction files',
            'supported_formats': ['txt', 'csv', 'log'],
            'file_format': {
                'separator': ', (comma)',
                'minimum_fields': 7,
                'field_descriptions': [
                    'Field 1: Unknown',
                    'Field 2: Date (MM/DD/YYYY without time)',
                    'Field 3: Date (MM/DD/YYYY without time)',
                    'Field 4: Unknown',
                    'Field 5: ATM Reference',
                    'Field 6: Unknown',
                    'Field 7: Amount'
                ]
            },
            'extracted_fields': [
                'atm_ref (first 4 digits of ATM reference)',
                'date (MM/DD/YYYY format without time)',
                'amount (decimal number)',
                'date_alt (alternative date field)',
                'raw_text (original line)'
            ],
            'validation_rules': [
                'File must contain comma-separated values',
                'Each line must have at least 7 fields',
                'Fields 2 and 3 should contain dates in MM/DD/YYYY format without time',
                'Field 5 should contain ATM reference (numeric)',
                'Field 7 should contain amount (numeric)',
                'Must NOT contain time component in date fields (distinguishes from ECPAY)'
            ],
            'distinguishing_features': [
                'Dates without time component (unlike ECPAY)',
                'Comma-separated format',
                'MM/DD/YYYY date format in fields 2 and 3'
            ]
        }
