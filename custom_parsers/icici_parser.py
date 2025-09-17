import pandas as pd
import camelot
import os

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parses an ICICI bank statement PDF using Camelot and returns a pandas DataFrame.
    """
    try:
        if not os.path.exists(pdf_path):
            print(f"File not found: {pdf_path}")
            return pd.DataFrame()

        # Use Camelot with 'lattice' flavor to handle table borders and empty cells
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='lattice')

        # If no tables are found, return an empty DataFrame
        if len(tables) == 0:
            print("No tables found in the PDF.")
            return pd.DataFrame()

        # Concatenate all tables into a single DataFrame
        df = pd.concat([table.df for table in tables])

        # The first row is the header; remove it
        df = df.iloc[1:].reset_index(drop=True)

        # Set columns to match the expected schema
        df.columns = ["Date", "Description", "Debit Amt", "Credit Amt", "Balance"]

        # Convert to numeric, handling commas and empty as NaN
        df['Debit Amt'] = pd.to_numeric(df['Debit Amt'].str.replace(',', ''), errors='coerce')
        df['Credit Amt'] = pd.to_numeric(df['Credit Amt'].str.replace(',', ''), errors='coerce')
        df['Balance'] = pd.to_numeric(df['Balance'].str.replace(',', ''), errors='coerce')

        # Convert date
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y', errors='coerce')

        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return pd.DataFrame()

if __name__ == '__main__':
    # For local testing
    pdf_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "icici", "icici_sample.pdf")
    parsed_df = parse(pdf_path)
    if not parsed_df.empty:
        print(parsed_df)
