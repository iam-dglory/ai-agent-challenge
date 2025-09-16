import pandas as pd
import custom_parsers.icici_parser as icici_parser

def test_parser():
    """Test the generated parser against the ground truth CSV."""
    pdf_path = "data/icici/icici_sample.pdf"
    csv_path = "data/icici/icici_sample.csv"

    # Load the ground truth CSV
    expected_df = pd.read_csv(csv_path)

    # Parse the PDF using the agent-generated parser
    parsed_df = icici_parser.parse(pdf_path)

    if parsed_df is not None and parsed_df.equals(expected_df):
        print("Test Passed: The generated parser works correctly!")
        return True
    else:
        print("Test Failed: The parsed DataFrame does not match the expected CSV.")
        return False

if __name__ == "__main__":
    test_parser()
