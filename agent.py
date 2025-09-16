import importlib.util
import pandas as pd
from pathlib import Path

def write_icici_parser():
    parser_code = '''import pdfplumber
import pandas as pd

def parse(pdf_path: str) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\\n")
            for line in lines:
                # split by spaces (simplest approach, customize if needed)
                row = line.split()
                if len(row) < 6:
                    row += [""] * (6 - len(row))
                elif len(row) > 6:
                    row = row[:6]
                rows.append(row)
    df = pd.DataFrame(rows, columns=["Date","Narration","Ref No","Debit","Credit","Balance"])
    return df
'''
    parser_file = Path("custom_parsers/icici_parser.py")
    parser_file.write_text(parser_code)
    print(f"✅ Wrote parser at {parser_file}")

def run_test(target: str) -> bool:
    # define paths
    repo_root = Path(__file__).parent
    pdf_path = repo_root / "data" / target / f"{target}_sample.pdf"
    csv_path = repo_root / "data" / target / f"{target}_sample.csv"
    
    # dynamic import
    parser_path = repo_root / "custom_parsers" / f"{target}_parser.py"
    spec = importlib.util.spec_from_file_location(f"{target}_parser", parser_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    
    print("Looking for PDF at:", pdf_path)
    
    df_pdf = mod.parse(str(pdf_path))
    df_csv = pd.read_csv(csv_path)

    # normalize whitespace
    df_pdf = df_pdf.applymap(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_csv = df_csv.applymap(lambda x: str(x).strip() if pd.notnull(x) else x)

    if df_pdf.equals(df_csv):
        print("🎉 Test passed! Parser matches CSV.")
        return True
    else:
        print("❌ Test failed! Parser output != CSV.")
        # optional: print differences
        print(df_pdf.compare(df_csv))
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="Bank name target")
    args = parser.parse_args()
    target = args.target.lower()

    print(f"Attempt 1/3 for {target}")
    write_icici_parser()
    success = run_test(target)
    if success:
        print("✅ Success!")
    else:
        print("❌ Failed!")

if __name__ == "__main__":
    main()
