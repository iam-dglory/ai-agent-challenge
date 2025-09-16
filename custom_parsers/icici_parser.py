import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            for line in lines:
                row = line.split()
                # pad or truncate to 6 columns
                if len(row) < 6:
                    row += [""] * (6 - len(row))
                elif len(row) > 6:
                    row = row[:6]
                rows.append(row)
    df = pd.DataFrame(rows, columns=["Date","Narration","Ref No","Debit","Credit","Balance"])
    return df

