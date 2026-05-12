import re
import logging
from typing import List, Dict, Any
from .base_parser import BaseParser

logger = logging.getLogger(__name__)

class BDOParser(BaseParser):
    """Parser for BDO (Banco de Oro) transaction files"""
    
    def __init__(self):
        super().__init__("BDO")
        self.separator = '|'
        self.min_fields = 10
        self.atm_ref_field_index = 5  # Field 6 (0-indexed)
        self.amount_field_index = 9   # Field 10 (0-indexed)
        self.date_field_index = 2     # Field 3 (0-indexed)
        self.time_field_index = 3     # Field 4 (0-indexed)
        self.terminal_field_index = 4 # Field 5 (0-indexed)
    
    def parse_file(self, file_content: str) -> Dict[str, Any]:
        """Parse BDO transaction file"""
        try:
            lines = file_content.strip().split('\n')
            grouped_data = {}
            raw_contents = []
            total_amount = 0.0
            
            logger.info(f"Processing BDO file with {len(lines)} lines")
            
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
            
            logger.info(f"BDO processing completed. Found {len(grouped_data)} ATM references, total amount: {total_amount}")
            
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
            logger.error(f"Error parsing BDO file: {str(e)}")
            raise
    
    def _parse_transaction_line(self, line: str, line_num: int) -> Dict[str, Any]:
        """Parse individual BDO transaction line"""
        try:
            # Split by pipe separator
            fields = [field.strip() for field in line.split(self.separator)]
            
            # Validate minimum fields
            if len(fields) < self.min_fields:
                logger.warning(f"BDO line {line_num} has insufficient fields: {len(fields)} < {self.min_fields}")
                return None
            
            # Extract ATM reference
            atm_ref = self._extract_atm_reference(fields)
            if not atm_ref:
                logger.warning(f"BDO line {line_num}: Could not extract ATM reference")
                return None
            
            # Extract amount
            amount = self._extract_amount(fields)
            
            # Extract date
            date = self._extract_date(fields)
            
            # Extract time
            time = self._extract_time(fields)
            
            # Extract terminal
            terminal = self._extract_terminal(fields)
            
            return {
                'line_number': line_num,
                'raw_text': line,
                'payment_mode': self.payment_mode,
                'atm_ref': atm_ref,
                'amount': amount,
                'date': date,
                'time': time,
                'terminal': terminal,
                'fields': fields
            }
            
        except Exception as e:
            logger.error(f"Error parsing BDO line {line_num}: {str(e)}")
            return None
    
    def _extract_atm_reference(self, fields: List[str]) -> str:
        """Extract ATM reference from BDO fields"""
        try:
            if len(fields) > self.atm_ref_field_index:
                atm_ref_field = fields[self.atm_ref_field_index]
                # Clean the reference (keep only digits)
                clean_ref = ''.join(c for c in atm_ref_field if c.isdigit())
                # Take first 4 digits as ATM ref
                if len(clean_ref) >= 4:
                    atm_ref = clean_ref[:4]
                    logger.debug(f"Found BDO ATM ref: {atm_ref} from {atm_ref_field}")
                    return atm_ref
        except Exception as e:
            logger.error(f"Error extracting BDO ATM reference: {str(e)}")
        
        return '0000'  # Default fallback
    
    def _extract_amount(self, fields: List[str]) -> float:
        """Extract amount from BDO fields"""
        try:
            if len(fields) > self.amount_field_index:
                amount_str = fields[self.amount_field_index].replace(',', '')
                amount = float(amount_str)
                logger.debug(f"Found BDO amount: {amount}")
                return amount
        except (ValueError, IndexError) as e:
            logger.warning(f"Could not extract BDO amount: {str(e)}")
        
        return 0.0
    
    def _extract_date(self, fields: List[str]) -> str:
        """Extract date from BDO fields"""
        try:
            if len(fields) > self.date_field_index:
                date_str = fields[self.date_field_index].strip()
                # Format date if needed
                formatted_date = self._format_bdo_date(date_str)
                logger.debug(f"Found BDO date: {formatted_date}")
                return formatted_date
        except Exception as e:
            logger.warning(f"Could not extract BDO date: {str(e)}")
        
        return 'N/A'
    
    def _extract_time(self, fields: List[str]) -> str:
        """Extract time from BDO fields"""
        try:
            if len(fields) > self.time_field_index:
                time_str = fields[self.time_field_index].strip()
                return time_str
        except Exception as e:
            logger.warning(f"Could not extract BDO time: {str(e)}")
        
        return 'N/A'
    
    def _extract_terminal(self, fields: List[str]) -> str:
        """Extract terminal from BDO fields"""
        try:
            if len(fields) > self.terminal_field_index:
                terminal_str = fields[self.terminal_field_index].strip()
                return terminal_str
        except Exception as e:
            logger.warning(f"Could not extract BDO terminal: {str(e)}")
        
        return 'N/A'
    
    def _format_bdo_date(self, date_str: str) -> str:
        """Format BDO date to MM/DD/YYYY format"""
        try:
            # Handle different date formats
            if len(date_str) == 8 and date_str.isdigit():
                # YYYYMMDD format
                year = date_str[:4]
                month = f"{int(date_str[4:6]):02d}"
                day = f"{int(date_str[6:]):02d}"
                return f"{month}/{day}/{year}"
            elif '/' in date_str and len(date_str.split('/')) == 3:
                # MM/DD/YYYY format - ensure leading zeros
                m, d, y = date_str.split('/')
                month = f"{int(m):02d}"
                day = f"{int(d):02d}"
                return f"{month}/{day}/{y}"
            elif '-' in date_str and len(date_str.split('-')) == 3:
                # YYYY-MM-DD format
                y, m, d = date_str.split('-')
                month = f"{int(m):02d}"
                day = f"{int(d):02d}"
                return f"{month}/{day}/{y}"
            else:
                return date_str  # Return as-is if format is not recognized
        except Exception as e:
            logger.warning(f"Could not format BDO date '{date_str}': {str(e)}")
            return date_str
    
    def _is_valid_line(self, line: str) -> bool:
        """Check if line matches BDO format"""
        try:
            fields = line.split(self.separator)
            return len(fields) >= self.min_fields
        except:
            return False
    
    def generate_formatted_report_line(self, transaction: Dict[str, Any]) -> str:
        """Generate formatted line for BDO report"""
        try:
            fields = transaction['fields']
            ref_num = fields[5].strip()
            date_raw = fields[2].strip()
            amount = fields[9].strip()
            time = fields[3].strip()
            terminal = fields[4].strip()
            
            # Format date
            date_fmt = self._format_bdo_date(date_raw)
            
            # Build formatted line with proper spacing
            ref_part = f"{ref_num}{' ' * 32}"
            date_part = f"{date_fmt}"
            
            # Use exactly 6 spaces after the date (to get 10 total spaces)
            after_date_spaces = ' ' * 6
            
            amount_part = f"{amount:>10}"
            after_amount_spaces = ' ' * 5
            time_part = f"{time} "
            terminal_part = f"{terminal}"
            
            formatted_line = f"{ref_part}{date_part}{after_date_spaces}{amount_part}{after_amount_spaces}{time_part}{terminal_part}\n"
            
            return formatted_line
            
        except Exception as e:
            logger.error(f"Error formatting BDO report line: {str(e)}")
            return f"{transaction['raw_text']}\n"
