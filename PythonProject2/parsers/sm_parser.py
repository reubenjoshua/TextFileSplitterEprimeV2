import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class SMParser(BaseParser):
    """Parser for SM (SM Store/SM Supermarket) transaction files"""
    
    def __init__(self):
        super().__init__("SM")
        self.min_line_length = 45
        self.cs_marker = 'CS'
        self.date_start_pos = 3
        self.date_end_pos = 11
        self.atm_ref_start_pos = 17
        self.atm_ref_end_pos = 30
        self.header_lengths = [10, 30]  # Valid header lengths
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse SM transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            sm_header = None
            
            logger.info(f"Processing SM file with {len(lines)} lines")
            
            for line_num, line in enumerate(lines, 1):
                if not line.strip():
                    continue
                
                # Detect and handle header
                if sm_header is None:
                    line_length = len(line.strip())
                    if line_length in self.header_lengths:
                        if line_length == 30:
                            date_part = line.strip()[:8]
                            sm_header = f"{date_part}SM"
                        else:
                            sm_header = line.strip()
                        raw_contents.append(sm_header)
                        logger.debug(f"Detected SM Header: {sm_header}")
                        continue
                
                # Skip lines that are too short
                if len(line.strip()) < self.min_line_length:
                    continue
                
                # Parse the transaction line
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
                
                # Add to raw contents
                if line not in raw_contents:
                    raw_contents.append(line)
            
            # Convert dates set to list for JSON serialization
            for atm_ref in grouped_data:
                if 'dates' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['dates'], set):
                    grouped_data[atm_ref]['dates'] = list(grouped_data[atm_ref]['dates'])
                if 'atm_refs' in grouped_data[atm_ref] and isinstance(grouped_data[atm_ref]['atm_refs'], set):
                    grouped_data[atm_ref]['atm_refs'] = list(grouped_data[atm_ref]['atm_refs'])
            
            logger.info(f"SM processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
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
                'total_transactions': len([line for line in raw_contents if len(line.strip()) >= self.min_line_length]),
                'detected_header': sm_header
            }
            
        except Exception as e:
            logger.error(f"Error parsing SM file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual SM transaction line"""
        try:
            # Validate line length
            if len(line) < self.min_line_length:
                logger.warning(f"SM line {line_num} is too short: {len(line)} < {self.min_line_length}")
                return None
            
            # Check for CS marker
            if self.cs_marker not in line:
                logger.warning(f"SM line {line_num} does not contain CS marker")
                return None
            
            # Extract ATM reference using the pattern from old code
            atm_ref_match = re.search(r'0{6}(\d{14})', line)
            if not atm_ref_match:
                logger.warning(f"SM line {line_num}: Could not extract ATM reference using pattern")
                return None
            
            full_atm_ref = atm_ref_match.group(1)
            if not full_atm_ref.isdigit() or len(full_atm_ref) != 14:
                logger.warning(f"SM line {line_num}: Invalid ATM reference format: {full_atm_ref}")
                return None
            
            atm_ref = full_atm_ref[:4]  # First 4 digits for grouping
            
            # Extract amount
            amount = self._extract_amount(line)
            
            # Extract date
            date = self._extract_date(line)
            
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
            logger.error(f"Error parsing SM line {line_num}: {str(e)}")
            return None
    
    def _extract_amount(self, line: str) -> float:
        """Extract amount from SM line (digits before 'CS')"""
        try:
            cs_pos = line.find(self.cs_marker)
            if cs_pos <= 0:
                return 0.0
            
            # Look backwards from CS to find the amount
            amount_str = ''
            for i in range(cs_pos - 1, max(0, cs_pos - 10), -1):
                if line[i].isdigit():
                    amount_str = line[i] + amount_str
                else:
                    break
            
            if amount_str:
                amount = float(amount_str) / 100  # Convert to decimal
                logger.debug(f"Found SM amount: {amount} from {amount_str}")
                return amount
            
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract SM amount: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, line: str) -> str:
        """Extract date from SM line (positions 3-11 for MMDDYYYY format)"""
        try:
            if len(line) >= self.date_end_pos:
                date_str = line[self.date_start_pos:self.date_end_pos]
                if date_str and date_str.isdigit() and len(date_str) == 8:
                    # Format from MMDDYYYY to MM/DD/YYYY
                    formatted_date = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]}"
                    logger.debug(f"Found SM date: {formatted_date} from {date_str}")
                    return formatted_date
        except Exception as e:
            logger.warning(f"Could not extract SM date: {str(e)}")
        
        return 'N/A'
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches SM format"""
        try:
            # Check minimum length
            if len(line.strip()) < self.min_line_length:
                return False
            
            # Check for CS marker
            if self.cs_marker not in line:
                return False
            
            # Check for valid date format in positions 3-11
            if len(line) >= self.date_end_pos:
                date_str = line[self.date_start_pos:self.date_end_pos]
                if not (date_str.isdigit() and len(date_str) == 8):
                    return False
            
            # Check for valid ATM reference pattern
            atm_ref_match = re.search(r'0{6}(\d{14})', line)
            if not atm_ref_match:
                return False
            
            return True
            
        except:
            return False
    
    def validate_file_format(self, file_content: str) -> bool:
        """Validate if file matches SM format"""
        lines = file_content.split('\n')[:10]  # Check first 10 lines
        
        header_found = False
        valid_transaction_found = False
        
        for line in lines:
            if not line.strip():
                continue
            
            # Check for header
            if not header_found and len(line.strip()) in self.header_lengths:
                header_found = True
                continue
            
            # Check for valid transaction line
            if self._is_valid_line(line):
                valid_transaction_found = True
                break
        
        return header_found and valid_transaction_found
    
    def generate_formatted_report_line(self, transaction: Dict[str, Any]) -> str:
        """Generate formatted line for SM report"""
        try:
            # For SM, we return the original line as it's already in the correct format
            return f"{transaction['raw_text']}\n"
            
        except Exception as e:
            logger.error(f"Error formatting SM report line: {str(e)}")
            return f"{transaction['raw_text']}\n"
