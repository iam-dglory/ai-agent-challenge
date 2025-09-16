import pandas as pd
import re
import fitz  # PyMuPDF

def parse(pdf_path: str) -> pd.DataFrame:
    """Parses an ICICI bank statement PDF and returns a DataFrame."""
    try:
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        
        # Example regex pattern to find transaction data
        # This will need to be refined by your agent based on the specific PDF layout
        pattern = r"(\d{2}-\d{2}-\d{4})\s+([\w\s]+?)\s+([\d,.]+)"
        
        transactions = []
        for line in text.split('\n'):
            match = re.search(pattern, line)
            if match:
                transactions.append(match.groups())

        # Create DataFrame with appropriate columns based on the CSV schema
        df = pd.DataFrame(transactions, columns=['date', 'description', 'amount'])
        # Further data cleaning and type conversion...
        return df

    except Exception as e:
        # The agent should log and handle this error for self-correction
        print(f"Error during parsing: {e}")
        return None
