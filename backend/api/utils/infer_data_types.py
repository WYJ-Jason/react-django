import re
import warnings
import numpy as np
import pandas as pd

# Function to check if a value is in complex format
def is_complex(val):
    try:
        pattern = r"\s*\(?[+-]?\d+\s*[+-]\s*\d+\s*j\s*\)?"
        return bool(re.search(pattern, str(val)))
    except:
        return False

# Function to infer and convert data types of a DataFrame
def infer_and_convert_data_types(df, error_threshold=0.3, category_threshold=0.8):
    for col in df.columns:
        # Try converting to numeric type (float)
        df_converted = pd.to_numeric(df[col], errors='coerce')
        num_errors = df_converted.isna().sum() / len(df_converted)

        # If there are no errors, and the column can be float, convert it to float
        if num_errors <= error_threshold:
            if not df_converted.dropna().apply(lambda x: x.is_integer()).all():
                df[col] = df_converted.astype(float)
                continue

            # If all values are integer-like, convert to nullable integer type
            df[col] = df_converted.astype(pd.Int64Dtype())
            continue

        # Try converting to boolean type (True, False or 0, 1)
        unique_values = df[col].dropna().unique()
        if set(unique_values).issubset({0, 1, '0', '1', True, False, 'True', 'False'}):
            df[col] = df[col].map({'0': False, '1': True, 'True': True, 'False': False, 0: False, 1: True})
            df[col] = df[col].astype(bool)
            continue

        # Check for complex numbers
        if df[col].apply(is_complex).sum() / len(df[col]) > (1 - error_threshold):
            df[col] = df[col].apply(lambda x: complex(x) if is_complex(x) else np.nan)
            continue
        
        # Try converting to datetime type with multiple format options
        date_patterns = [
            r"^\d{4}-\d{2}-\d{2}$",           # YYYY-MM-DD
            r"^\d{2}/\d{2}/\d{4}$",           # MM/DD/YYYY
            r"^\d{2}-\d{2}-\d{4}$",           # DD-MM-YYYY
            r"^\d{4}\.\d{2}\.\d{2}$",         # YYYY.MM.DD
            r"^\d{4}/\d{2}/\d{2}$",           # YYYY/MM/DD
            r"^\d{2}\s\w+\s\d{4}$",           # DD Mon YYYY
        ]
        
        if any(df[col].str.match(pattern).any() for pattern in date_patterns):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)  # Ignore warnings
                df_converted = pd.to_datetime(df[col], errors='coerce', exact=False, infer_datetime_format=True)
            
            num_errors = df_converted.isna().sum() / len(df_converted)
            if num_errors <= error_threshold:
                df[col] = df_converted
                continue

        # Attempting to convert to timedelta for durations like "days", "weeks", "hours", etc.
        duration_patterns = {
            'years': r'(\d+)\s*years?',
            'months': r'(\d+)\s*months?',
            'weeks': r'(\d+)\s*weeks?',
            'days': r'(\d+)\s*days?',
            'hours': r'(\d+)\s*hours?',
            'minutes': r'(\d+)\s*minutes?',
            'seconds': r'(\d+)\s*seconds?',
        }
        
        if any(df[col].astype(str).str.match(pattern).any() for pattern in duration_patterns.values()):
            df[col] = pd.to_timedelta(df[col], errors='coerce')
            continue


        # Attempting to convert to timedelta for ISO 8601 duration strings
        if df[col].str.contains(r'^P\d+Y$', na=False).sum() > 0:
            df[col] = df[col].str.replace(r'^P(\d+)Y$', r'\1Y', regex=True).replace({'Y': ' years'}, regex=True)
            df[col] = pd.to_timedelta(df[col].str.replace(r' years', ' days').replace({'days': '365 days'}, regex=True), errors='coerce')
            continue

        # Try converting to categorical type based on unique value ratio
        unique_count = df[col].nunique(dropna=True)  # Count distinct non-null values
        total_count = len(df[col])
        unique_ratio = unique_count / total_count
        
        # Convert to category if the unique value ratio is below the category_threshold
        if unique_ratio < category_threshold:
            df[col] = pd.Categorical(df[col].fillna("Unknown"))  # Convert to category and handle NaNs
            continue

        # Convert remaining values to string
        df[col] = df[col].astype(str)

    return df

