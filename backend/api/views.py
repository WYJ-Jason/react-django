import os
import pandas as pd
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .utils import infer_data_types
import json
import re
from datetime import timedelta
import numpy as np

@api_view(['POST'])
def upload_file(request):
    # Check if the file is in the request
    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    file_path = os.path.join('temp', uploaded_file.name)

    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the uploaded file to a temporary location
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    try:
        # Read the file content based on its extension
        df = pd.read_csv(file_path) if uploaded_file.name.endswith('.csv') else pd.read_excel(file_path)

        # Convert all columns to string type
        df = df.astype(str)

        # Use the infer_and_convert_data_types function to infer data types
        df_inferred = infer_data_types.infer_and_convert_data_types(df)

        # Get inferred data types for each column
        inferred_types = {col: str(df_inferred[col].dtype) for col in df_inferred.columns}

        # Remove the temporary file
        os.remove(file_path)

        return Response({"inferred_types": inferred_types}, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

# Helper function to parse ISO 8601 duration strings
def parse_iso_8601_duration(duration_str):
    pattern = r'P(?:(?P<years>\d+)Y)?(?:(?P<months>\d+)M)?(?:(?P<weeks>\d+)W)?(?:(?P<days>\d+)D)?' \
                r'(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?'
    match = re.fullmatch(pattern, duration_str)
    if not match:
        return np.nan  # Return NaN if the format is not recognized
    
    # Convert parsed components to days and seconds for timedelta
    time_params = {k: int(v) if v else 0 for k, v in match.groupdict().items()}
    days = time_params['years'] * 365 + time_params['months'] * 30 + time_params['weeks'] * 7 + time_params['days']
    seconds = time_params['hours'] * 3600 + time_params['minutes'] * 60 + time_params['seconds']
    return timedelta(days=days, seconds=seconds)


@api_view(['POST'])
def convert_file(request):
    # Check if the file is in the request
    if 'file' not in request.FILES:
        return Response({"error": "No file uploaded."}, status=status.HTTP_400_BAD_REQUEST)

    uploaded_file = request.FILES['file']
    file_path = os.path.join('temp', uploaded_file.name)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Save the uploaded file to a temporary location
    with open(file_path, 'wb+') as destination:
        for chunk in uploaded_file.chunks():
            destination.write(chunk)

    try:
        # Read the file content based on its extension
        df = pd.read_csv(file_path) if uploaded_file.name.endswith('.csv') else pd.read_excel(file_path)

        conversion_errors = {}

        data_types_str = request.data.get('dataTypes')

        if data_types_str:
            data_types = json.loads(data_types_str)

            for column, expected_type in data_types.items():
                print(column, expected_type)

                try:
                    # Mapping expected types to pandas data types
                    if expected_type == "bool":
                        df[column] = df[column].map({'True': True, 'False': False, True: True, False: False}).astype('bool')
                    elif expected_type == "datetime64[ns]":
                        # Handle flexible date conversion with multiple formats and dayfirst=True
                        try:
                            df[column] = pd.to_datetime(df[column], errors='raise', dayfirst=True)
                        except ValueError:
                            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%m-%d-%Y", "%Y.%m.%d"]:
                                try:
                                    df[column] = pd.to_datetime(df[column], format=fmt, errors='raise', dayfirst=True)
                                    break
                                except ValueError:
                                    continue
                            else:
                                raise ValueError(f"Could not parse dates in column '{column}' with any common format.")
                    elif expected_type == "Int64":
                        df[column] = pd.to_numeric(df[column], errors='coerce', downcast='integer')
                        if df[column].isna().mean() > 0.3:
                            raise ValueError(f"More than 30% of the values in column '{column}' are NaN after conversion to Int64.")
                    elif expected_type == "float64":
                        df[column] = pd.to_numeric(df[column], errors='coerce')
                        if df[column].isna().mean() > 0.3:
                            raise ValueError(f"More than 30% of the values in column '{column}' are NaN after conversion to float64.")
                    elif expected_type == "complex128":
                        df[column] = df[column].apply(complex)
                    elif expected_type == "object":
                        df[column] = df[column].astype(str)
                    elif expected_type == "category":
                        df[column] = df[column].astype('category')
                    elif expected_type == "timedelta64[ns]":
                        # Check for ISO 8601 durations and parse if present
                        if df[column].str.startswith('P').any():
                            df[column] = df[column].apply(parse_iso_8601_duration)
                        else:
                            df[column] = pd.to_timedelta(df[column], errors='raise')

                except Exception:
                    conversion_errors[column] = expected_type

            # Remove the temporary file
            os.remove(file_path)

            if conversion_errors:
                return Response({
                    "error": "Conversion errors occurred.",
                    "details": conversion_errors
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Conversion successful."}, status=status.HTTP_200_OK)

    except Exception as e:
        print(e)
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
