# Splitter - Transaction Parser

A Flask-based API for parsing transaction files from various payment providers with a React frontend.

## Supported Payment Modes
- **BDO** (Banco de Oro)
- **Cebuana Lhuillier**
- **China Bank**
- **ECPay**

## Features

- **Multi-Payment Mode Support**: Parse transactions from BDO, Cebuana Lhuillier, and more
- **File Validation**: Validate file format before processing for each payment mode
- **Clean API Structure**: Modular design with separate parsers for each payment mode
- **React Frontend**: Modern UI for file upload and results display
- **Smart Format Detection**: Distinguish between similar formats (e.g., Cebuana vs ECPAY)

## Project Structure

```
PythonProject2/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── parsers/
│   ├── __init__.py       # Package initialization
│   ├── base_parser.py    # Base parser class
│   ├── bdo_parser.py     # BDO-specific parser
│   ├── cebuana_parser.py # Cebuana-specific parser
│   ├── chinabank_parser.py # Chinabank-specific parser
│   └── ecpay_parser.py   # ECPay-specific parser
├── routes/
│   ├── __init__.py       # Package initialization
│   ├── bdo_routes.py     # BDO API routes
│   ├── cebuana_routes.py # Cebuana API routes
│   ├── chinabank_routes.py # Chinabank API routes
│   └── ecpay_routes.py   # ECPay API routes
├── uploads/              # File upload directory
└── README.md            # This file
```

## File Formats

### BDO File Format

BDO transaction files use pipe (`|`) separated values with the following structure:

- **Separator**: `|` (pipe character)
- **Minimum Fields**: 10 fields per line
- **Key Fields**:
  - Field 3: Date (YYYYMMDD or MM/DD/YYYY)
  - Field 4: Time
  - Field 5: Terminal
  - Field 6: ATM Reference (first 4 digits used for grouping)
  - Field 10: Amount (decimal)

### Sample BDO Format:
```
Unknown1|Unknown2|20240115|14:30:00|ATM001|1234567890|Unknown7|Unknown8|Unknown9|1500.00
Unknown1|Unknown2|20240115|15:45:00|ATM002|0987654321|Unknown7|Unknown8|Unknown9|2500.50
```

### Cebuana Lhuillier File Format

Cebuana transaction files use comma (`,`) separated values with the following structure:

- **Separator**: `,` (comma character)
- **Minimum Fields**: 7 fields per line
- **Key Fields**:
  - Field 2: Date (MM/DD/YYYY without time)
  - Field 3: Date (MM/DD/YYYY without time)
  - Field 5: ATM Reference (first 4 digits used for grouping)
  - Field 7: Amount (decimal)

### Sample Cebuana Format:
```
Unknown1,01/15/2024,01/15/2024,Unknown4,1234567890,Unknown6,1500.00
Unknown1,01/15/2024,01/15/2024,Unknown4,0987654321,Unknown6,2500.50
```

### China Bank File Format

China Bank transaction files use space-separated values with the following structure:

- **Separator**: Space-separated (fixed-width format)
- **Minimum Fields**: 4 fields per line
- **Key Fields**:
  - Field 1: Date (MMDDYYYY format - 8 digits)
  - Field 3: Amount (decimal)
  - Field 4: ATM Reference (first 4 digits used for grouping)

### Sample China Bank Format:
```
01152024 Unknown2 1500.00 1234567890
01152024 Unknown2 2500.50 0987654321
01162024 Unknown2 750.25 1122334455
```

### ECPay File Format

ECPay transaction files use comma-separated values with the following structure:

- **Separator**: Comma-separated (`,`)
- **Minimum Fields**: 7 fields per line
- **Key Fields**:
  - Field 3: Date and time (MM/DD/YYYY HH:MM:SS AM/PM format)
  - Field 5: ATM Reference (first 4 digits used for grouping)
  - Field 7: Amount (decimal)

### Sample ECPay Format:
```
Unknown1,Unknown2,01/15/2024 14:30:00 PM,Unknown4,1234567890,Unknown6,1500.00
Unknown1,Unknown2,01/15/2024 15:45:30 AM,Unknown4,0987654321,Unknown6,2500.50
Unknown1,Unknown2,01/16/2024 09:20:15 PM,Unknown4,1122334455,Unknown6,750.25
```

### Format Distinctions:
- **BDO**: Pipe-separated (`|`) with 10+ fields
- **Cebuana**: Comma-separated (`,`) with 7+ fields, dates without time
- **China Bank**: Space-separated with 4+ fields, MMDDYYYY date format
- **ECPay**: Comma-separated with time in dates (MM/DD/YYYY HH:MM:SS AM/PM)

### ECPay vs Cebuana Distinction:
- **ECPay**: Dates include time (MM/DD/YYYY HH:MM:SS AM/PM)
- **Cebuana**: Dates without time (MM/DD/YYYY)

## API Endpoints

### BDO Routes

- `POST /api/bdo/process` - Process BDO transaction file
- `GET /api/bdo/info` - Get BDO parser information
- `POST /api/bdo/validate` - Validate BDO file format
- `GET /api/bdo/sample` - Get sample BDO format

### Cebuana Routes

- `POST /api/cebuana/process` - Process Cebuana transaction file
- `GET /api/cebuana/info` - Get Cebuana parser information
- `POST /api/cebuana/validate` - Validate Cebuana file format
- `GET /api/cebuana/sample` - Get sample Cebuana format
- `GET /api/cebuana/compare` - Compare Cebuana vs ECPAY formats

### China Bank Routes

- `POST /api/chinabank/process` - Process China Bank transaction file
- `GET /api/chinabank/info` - Get China Bank parser information
- `POST /api/chinabank/validate` - Validate China Bank file format
- `GET /api/chinabank/sample` - Get sample China Bank format
- `GET /api/chinabank/compare` - Compare China Bank vs other formats
- `GET /api/chinabank/format-guide` - Get detailed format guide

### ECPay Routes

- `POST /api/ecpay/process` - Process ECPay transaction file
- `GET /api/ecpay/info` - Get ECPay parser information
- `POST /api/ecpay/validate` - Validate ECPay file format
- `GET /api/ecpay/sample` - Get sample ECPay format
- `POST /api/ecpay/compare` - Compare ECPay vs Cebuana formats
- `GET /api/ecpay/compare` - Compare ECPay vs other formats
- `GET /api/ecpay/format-guide` - Get detailed format guide

### General Routes

- `GET /api/health` - Health check
- `GET /` - Serve React frontend

## Installation

1. **Install Python dependencies**:
   ```bash
   cd PythonProject2
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python app.py
   ```

3. **Access the application**:
   - Local: `http://localhost:5000`
   - Network: `http://[your-ip]:5000`

## Usage

### Processing Transaction Files

1. **Upload File**: Use the React frontend to upload a transaction file
2. **Select Payment Mode**: Choose the appropriate payment mode (BDO, Cebuana, etc.)
3. **Process**: The file will be parsed and results displayed
4. **Export**: Download results as CSV or JSON

### Supported Payment Modes:
- **BDO**: Pipe-separated format with 10+ fields
- **Cebuana**: Comma-separated format with 7+ fields, dates without time
- **China Bank**: Space-separated format with 4+ fields, MMDDYYYY date format
- **ECPay**: Comma-separated format with 7+ fields, dates with time

### API Usage

```bash
# Process BDO file
curl -X POST -F "file=@bdo_transactions.txt" http://localhost:5000/api/bdo/process

# Process Cebuana file
curl -X POST -F "file=@cebuana_transactions.txt" http://localhost:5000/api/cebuana/process

# Process China Bank file
curl -X POST -F "file=@chinabank_transactions.txt" http://localhost:5000/api/chinabank/process

# Process ECPay file
curl -X POST -F "file=@ecpay_transactions.txt" http://localhost:5000/api/ecpay/process

# Validate BDO file
curl -X POST -F "file=@bdo_transactions.txt" http://localhost:5000/api/bdo/validate

# Validate Cebuana file
curl -X POST -F "file=@cebuana_transactions.txt" http://localhost:5000/api/cebuana/validate

# Validate China Bank file
curl -X POST -F "file=@chinabank_transactions.txt" http://localhost:5000/api/chinabank/validate

# Validate ECPay file
curl -X POST -F "file=@ecpay_transactions.txt" http://localhost:5000/api/ecpay/validate

# Get parser info
curl http://localhost:5000/api/bdo/info
curl http://localhost:5000/api/cebuana/info
curl http://localhost:5000/api/chinabank/info
curl http://localhost:5000/api/ecpay/info

# Compare Cebuana vs ECPAY
curl http://localhost:5000/api/cebuana/compare

# Compare China Bank vs other formats
curl http://localhost:5000/api/chinabank/compare

# Compare ECPay vs Cebuana
curl -X POST -F "file=@ecpay_transactions.txt" http://localhost:5000/api/ecpay/compare

# Compare ECPay vs other formats
curl http://localhost:5000/api/ecpay/compare
```

## Response Format

### Successful Processing Response:
```json
{
  "grouped_data": {
    "1234": {
      "raw_contents": ["transaction_line_1", "transaction_line_2"],
      "transaction_count": 2,
      "total_amount": 3000.00,
      "payment_mode": "BDO",
      "dates": ["01/15/2024", "01/16/2024"],
      "transactions": [...]
    }
  },
  "raw_contents": ["all_transaction_lines"],
  "payment_mode": "BDO", // or "CEBUANA"
  "total_amount": 3000.00,
  "total_transactions": 2,
  "original_filename": "bdo_transactions.txt"
}
```

## Error Handling

The API includes comprehensive error handling for:
- Invalid file formats
- Missing required fields
- Encoding issues
- Processing errors

## Development

### Adding New Payment Modes

1. Create a new parser class inheriting from `BaseParser`
2. Create corresponding route file
3. Register the blueprint in `app.py`

### Testing

Test the BDO parser with various file formats and edge cases to ensure robust parsing.

## License

This project is for internal use only.
