import os
import sys
import pandas as pd
import pytest

# Add project's root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_parsers.icici_parser import parse

def test_parser():
    """
    Tests if the parser for ICICI bank statements works correctly.
    """
    # Relative paths
    pdf_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'icici', 'icici_sample.pdf')
    expected_csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'icici', 'icici_sample.csv')

    # Parse the PDF
    parsed_df = parse(pdf_path)

    # Read the expected data from the CSV
    expected_df = pd.read_csv(expected_csv_path)
    expected_df['Date'] = pd.to_datetime(expected_df['Date'], format='%d-%m-%Y')

    # Compare
    pd.testing.assert_frame_equal(parsed_df, expected_df, check_dtype=False)
