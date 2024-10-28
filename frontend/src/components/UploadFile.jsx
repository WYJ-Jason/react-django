import React, { useState, useEffect } from 'react';
import Papa from 'papaparse'; // Import papaparse for CSV parsing
import ExcelJS from 'exceljs'; // Import ExcelJS for Excel parsing

const UploadFile = () => {
  const [file, setFile] = useState(null);
  const [filePreview, setFilePreview] = useState([]);
  const [responseData, setResponseData] = useState(null);
  const [dataTypes, setDataTypes] = useState({});
  const [originalDataTypes, setOriginalDataTypes] = useState({});
  const [isConvertEnabled, setIsConvertEnabled] = useState(false);
  const [message, setMessage] = useState(''); // Feedback message state
  const [messageType, setMessageType] = useState(''); // Track message type (success/error)
  const [conversionErrors, setConversionErrors] = useState({}); // Store conversion errors

  // Unified type mapping between inferred and Python-compatible data types
  const typeMapping = {
    complex128: 'Complex',
    'datetime64[ns]': 'Date',
    'timedelta64[ns]': 'Duration',
    Int64: 'Integer',
    float64: 'Float',
    object: 'Text', // Assume string type for general objects
    category: 'Category',
    bool: 'True/False',
  };

  useEffect(() => {
    // Enable or disable convert button based on changes in dataTypes
    setIsConvertEnabled(
      JSON.stringify(dataTypes) !== JSON.stringify(originalDataTypes)
    );
  }, [dataTypes, originalDataTypes]);

  const handleFileChange = async (event) => {
    const selectedFile = event.target.files[0];
    setFile(selectedFile);
    setMessage(''); // Clear any previous messages

    if (selectedFile.type === 'text/csv') {
      Papa.parse(selectedFile, {
        complete: (result) => {
          const previewData = result.data.slice(0, 6);
          setFilePreview(previewData);
        },
        header: false,
      });
    } else if (
      selectedFile.type ===
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' ||
      selectedFile.type === 'application/vnd.ms-excel'
    ) {
      const workbook = new ExcelJS.Workbook();
      const reader = new FileReader();

      reader.onload = async (e) => {
        const buffer = e.target.result;
        await workbook.xlsx.load(buffer);
        const worksheet = workbook.worksheets[0];

        const rows = [];
        worksheet.eachRow((row) => {
          rows.push(row.values.slice(1));
        });

        const csvData = rows.map((row) => row.join(',')).join('\n');
        const result = Papa.parse(csvData, { header: false });
        const previewData = result.data.slice(0, 6);
        setFilePreview(previewData);
      };

      reader.readAsArrayBuffer(selectedFile);
    } else {
      setMessage('Please upload a CSV or Excel file.'); // Update message for invalid file type
      setMessageType('error'); // Set message type to error
    }
  };

  const handleSubmit = async (event) => {
    setDataTypes({});
    setOriginalDataTypes({});
    event.preventDefault();
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/upload/', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data);
        setResponseData(data);

        // Use typeMapping to adjust inferred types
        const adjustedTypes = Object.fromEntries(
          Object.entries(data.inferred_types).map(([key, value]) => {
            return [key, typeMapping[value] || 'str']; // Fallback to 'str' if type not found
          })
        );

        setDataTypes(adjustedTypes);
        setOriginalDataTypes(adjustedTypes); // Save initial types for comparison
        setMessage('File uploaded successfully.'); // Success message
        setMessageType('success'); // Set message type to success
      } else {
        const errorData = await response.json();
        setMessage(`Upload failed: ${errorData.error || response.statusText}`);
        setMessageType('error'); // Set message type to error
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error uploading file. Please try again.'); // General error message
      setMessageType('error'); // Set message type to error
    }
  };

  const handleConvert = async () => {
    if (!file) {
      console.error('No file available for conversion.');
      return;
    }

    // Map displayed types (modified by user) to Python-compatible types
    const pythonDataTypes = Object.fromEntries(
      Object.entries(dataTypes).map(([key, value]) => [
        key,
        Object.keys(typeMapping).find((k) => typeMapping[k] === value) || 'str' // Fallback to 'str' if type not found
      ])
    );

    const formData = new FormData();
    formData.append('file', file); // Add file data
    formData.append('dataTypes', JSON.stringify(pythonDataTypes)); // Add converted data types as JSON

    console.log(formData);

    try {
      const response = await fetch('http://127.0.0.1:8000/api/convert/', {
        method: 'POST',
        body: formData, // Send FormData with file and data types
      });

      if (response.ok) {
        const data = await response.json();
        console.log('Conversion successful:', data);
        setMessage('Conversion successful.'); // Success message
        setMessageType('success'); // Set message type to success
        setConversionErrors({}); // Clear any previous errors
        setOriginalDataTypes(dataTypes);
      } else {
        const errorData = await response.json();
        setMessage(`Conversion failed: ${errorData.error || response.statusText}`);
        setMessageType('error'); // Set message type to error

        // Map the error details to user-friendly types
        const mappedErrors = Object.fromEntries(
          Object.entries(errorData.details || {}).map(([column, type]) => [
            column,
            typeMapping[type] || type // Map type to user-friendly name
          ])
        );

        setConversionErrors(mappedErrors);
      }
    } catch (error) {
      console.error('Error:', error);
      setMessage('Error during conversion. Please try again.'); // General error message
      setMessageType('error'); // Set message type to error
    }
  };

  const handleDataTypeChange = (column, event) => {
    setDataTypes({
      ...dataTypes,
      [column]: event.target.value,
    });
  };

  return (
    <div>
      <h1>Upload CSV/Excel File</h1>
      <form onSubmit={handleSubmit}>
        <input
          type="file"
          onChange={handleFileChange}
          accept=".csv, .xls, .xlsx"
          required
        />

        {filePreview.length > 0 && (
          <div>
            <h2>File Preview (First 5 Rows)</h2>
            <div className="table">
              <div className="table-wrapper">
                <table>
                  <thead>
                    <tr>
                      {filePreview[0].map((header, index) => (
                        <th key={index}>{header}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {filePreview.slice(1).map((row, rowIndex) => (
                      <tr key={rowIndex}>
                        {row.map((cell, cellIndex) => (
                          <td key={cellIndex}>{cell}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        <button type="submit" style={{ width: '100%' }}>
          Upload
        </button>
      </form>

      {responseData && (
        <div className="inferred-data-types">
          <h2>Inferred Data Types</h2>
          <div className="convert-data-types">
            <ul>
              {Object.entries(dataTypes).map(([column, type]) => (
                <li key={column}>
                  <span>{column}: </span>
                  <select
                    value={type}
                    onChange={(e) => handleDataTypeChange(column, e)}
                  >
                    <option value="Text">Text</option>
                    <option value="Date">Date</option>
                    <option value="Integer">Integer</option>
                    <option value="Float">Float</option>
                    <option value="Category">Category</option>
                    <option value="True/False">True/False</option>
                    <option value="Complex">Complex</option>
                    <option value="Duration">Duration</option>
                  </select>
                </li>
              ))}
            </ul>
          </div>
          <button
            onClick={handleConvert}
            disabled={!isConvertEnabled}
            style={{ width: '100%' }}
          >
            Convert
          </button>
        </div>
      )}

      {/* Display feedback messages */}
      {message && (
        <div className={`message ${messageType}`}>
          <h2>{messageType === 'success' ? 'Success' : 'Error'}</h2>
          <p>{message}</p>
          {Object.entries(conversionErrors).length > 0 && (
            <div className="conversion-errors">
              <h3>Conversion Errors</h3>
              <ul>
                {Object.entries(conversionErrors).map(([column, type]) => (
                  <li key={column}>
                    <strong>{column}:</strong> Failed to convert to {type}.
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default UploadFile;
