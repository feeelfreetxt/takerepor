import pytest
from novotestrelatorio import AnalisadorExcel
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def sample_df():
    """Generate test data with various date formats and edge cases"""
    data = {
        'DATA_CRIACAO': [
            '2023-01-01', '01/02/2023', 'invalid', '2023-03-01 12:00',
            datetime(2023, 1, 5), pd.NaT
        ],
        'DATA_RESOLUCAO': [
            '2023-01-02',  # +1 day
            '01/03/2023',  # +1 day (March 1st)
            '2023-01-01',
            'invalid',
            datetime(2023, 1, 6),  # +1 day
            pd.NaT
        ]
    }
    return pd.DataFrame(data)

def test_date_parsing(sample_df):
    analyzer = AnalisadorExcel()
    parsed_df = analyzer._parse_dates(sample_df)
    
    # Check valid conversions
    assert pd.api.types.is_datetime64_any_dtype(parsed_df['data_criacao'])
    assert pd.api.types.is_datetime64_any_dtype(parsed_df['resolucao'])
    
    # Verify invalid date handling
    assert parsed_df['data_criacao'].isna().sum() == 2  # 'invalid' and NaT
    assert parsed_df['resolucao'].isna().sum() == 2     # 'invalid' and NaT

def test_time_metrics_calculation(sample_df):
    analyzer = AnalisadorExcel()
    parsed_df = analyzer._parse_dates(sample_df)
    metrics = analyzer._calculate_time_metrics(parsed_df)
    
    # Check calculated metrics
    assert metrics['tempo_medio'] == 1.0  # (1+1+1)/3 valid pairs
    assert metrics['tempo_maximo'] == 1
    assert metrics['tempo_minimo'] == 1

# Test requirements for CI/CD
# <write_to_file>
# {
#   "TargetFile": "f:\okok\requirements-test.txt",
#   "CodeContent": "pandas>=2.0.0\npytest>=7.0.0"
# }
