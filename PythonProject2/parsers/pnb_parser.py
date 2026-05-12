import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class PNBParser(BaseParser):
    """Parser for PNB (Philippine National Bank) transaction files"""
    
    def __init__(self):
        super().__init__("PNB")
        self.separator = '^'
        self.min_fields = 7
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse PNB transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing PNB file with {len(lines)} lines")
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                raw_contents.append(line)
                
                # For PNB, split by caret
                fields = [f.strip() for f in line.split('^')]
                
                # Validate minimum fields
                if len(fields) < self.min_fields:
                    logger.warning(f"PNB line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                    continue
                
                # Parse the transaction line
                transaction = self._parse_transaction_line(line, fields, line_num)
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
                            'transactions': [],
                            'atm_refs': set()
                        }
                    
                    # Add to group
                    grouped_data[atm_ref]['raw_contents'].append(line)
                    grouped_data[atm_ref]['transaction_count'] += 1
                    grouped_data[atm_ref]['total_amount'] += transaction['amount']
                    grouped_data[atm_ref]['dates'].add(transaction['date'])
                    grouped_data[atm_ref]['transactions'].append(transaction)
                    grouped_data[atm_ref]['atm_refs'].add(transaction['full_atm_ref'])
                    
                    total_amount += transaction['amount']
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                if 'dates' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['dates'], set):
                    grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
                if 'atm_refs' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['atm_refs'], set):
                    grouped_data[atm_ref]['atm_refs'] = list(grouped_data[atm_ref]['atm_refs'])
            
            logger.info(f"PNB processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
            # Create individual transactions list for frontend compatibility
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
                'total_transactions': len([line for line in raw_contents if line.strip()]),
            }
            
        except Exception as e:
            logger.error(f"Error parsing PNB file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, fields: List[str], line_num: int) -> Dict[str, Any]:
        """Parse individual PNB transaction line"""
        try:
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"PNB line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference from field 5 (index 4)
            atm_ref_field = fields[4].strip()
            clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
            
            if len(clean_ref) < 4:
                logger.warning(f"PNB line {line_num}: Invalid ATM reference format: {atm_ref_field}")
                return None
            
            atm_ref = clean_ref[:4]  # First 4 digits for grouping
            full_atm_ref = clean_ref  # Full reference
            
            # Extract amount from field 7 (index 6)
            amount = self._extract_amount(fields, line_num)
            
            # Extract date from field 2 (index 1)
            date = self._extract_date(fields, line_num)
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'full_atm_ref': full_atm_ref,
                'amount': amount,
                'date': date
            }
            
        except Exception as e:
            logger.error(f"Error parsing PNB line {line_num}: {str(e)}")
            return None
    
    def _extract_amount(self, fields: List[str], line_num: int) -> float:
        """Extract amount from PNB fields (field 7, index 6)"""
        try:
            if len(fields) > 6:
                amount_str = fields[6].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found PNB amount: {amount} from {fields[6]}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract PNB amount from line {line_num}: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str], line_num: int) -> str:
        """Extract date from PNB fields (field 2, index 1)"""
        try:
            if len(fields) > 1:
                date_str = fields[1].strip()
                if date_str:
                    logger.debug(f"Found PNB date: {date_str}")
                    return date_str
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract PNB date from line {line_num}: {str(e)}")
        
        return 'N/A'
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches PNB format"""
        try:
            # Check for caret separator
            if self.separator not in line:
                return False
            
            # Split by caret and check minimum fields
            fields = [f.strip() for f in line.split(self.separator)]
            if len(fields) < self.min_fields:
                return False
            
            # Check for valid ATM reference in field 5 (index 4)
            if len(fields) > 4:
                atm_ref_field = fields[4].strip()
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                if len(clean_ref) < 4:
                    return False
            
            # Check for valid amount in field 7 (index 6)
            if len(fields) > 6:
                amount_str = fields[6].replace(',', '')
                try:
                    float(amount_str)
                except ValueError:
                    return False
            
            return True
            
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches PNB format"""
        lines = file_content.split('\n')[:10]  # Check first 10 lines
        
        valid_transaction_found = False
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check for valid transaction line
            if self._is_valid_line(line):
                valid_transaction_found = True
                break
        
        return valid_transaction_found
    
    def generate_formatted_report_line(self, transaction: Dict[str, Any]) -> str:
        """Generate formatted line for PNB report"""
        try:
            # For PNB, we return the original line as it's already in the correct format
            return f"{transaction['raw_text']}\n"
            
        except Exception as e:
            logger.error(f"Error formatting PNB report line: {str(e)}")
            return f"{transaction['raw_text']}\n"
