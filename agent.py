# agent.py
import argparse
import subprocess
import sys
import pandas as pd
import pdfplumber
from pathlib import Path
import importlib.util

ATTEMPTS = 3

# --- parser writer ---
def write_icici_parser():
    code = '''import pandas as pd
import pdfplumber

def parse(pdf_path: str) -> pd.DataFrame:
    rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            table = page.extract_table()
            if table:
                for row in table[1:]:  # skip header
                    rows.append(row)
    # adjust schema according to icici_sample.csv
    df = pd.DataFrame(rows, columns=["Date","Narration","Ref No","Debit","Credit","Balance"])
    return df
'''
    path = Path("custom_parsers/icici_parser.py")
    path.write_text(code)
    print(f"✅ Wrote parser at {path}")

# --- tester ---
def run_test(target: str) -> bool:
    # Get the absolute path to the repo root
    repo_root = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(repo_root, "data", target)
    
    pdf_path = os.path.join(data_dir, f"{target}_sample.pdf")
    csv_path = os.path.join(data_dir, f"{target}_sample.csv")
    
    # dynamically import parser
    parser_path = os.path.join(repo_root, "custom_parsers", f"{target}_parser.py")
    
    spec = importlib.util.spec_from_file_location(f"{target}_parser", parser_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

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
        return False

# --- agent loop ---
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True, help="bank name e.g. icici")
    args = parser.parse_args()
    target = args.target

    for attempt in range(ATTEMPTS):
        print(f"\nAttempt {attempt+1}/{ATTEMPTS} for {target}")
        if target == "icici":
            write_icici_parser()
        else:
            print(f"No generator for {target} yet. Extend agent.py.")
            sys.exit(1)

        if run_test(target):
            print("✅ Success!")
            return
        else:
            print("Retrying...")

    print("⚠️ Failed after retries.")

if __name__ == "__main__":
    main()

