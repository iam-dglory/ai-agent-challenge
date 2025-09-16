import importlib.util
from pathlib import Path
import pandas as pd
import pytest  # ✅ important for pytest discovery

def test_icici_parser():
    repo_root = Path(__file__).parent.parent
    pdf_path = repo_root / "data" / "icici" / "icici_sample.pdf"
    csv_path = repo_root / "data" / "icici" / "icici_sample.csv"

    parser_path = repo_root / "custom_parsers" / "icici_parser.py"
    spec = importlib.util.spec_from_file_location("icici_parser", parser_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    df_pdf = mod.parse(str(pdf_path))
    df_csv = pd.read_csv(csv_path)

    # normalize whitespace
    df_pdf = df_pdf.applymap(lambda x: str(x).strip() if pd.notnull(x) else x)
    df_csv = df_csv.applymap(lambda x: str(x).strip() if pd.notnull(x) else x)

    assert df_pdf.equals(df_csv), "Parser output does not match CSV"
