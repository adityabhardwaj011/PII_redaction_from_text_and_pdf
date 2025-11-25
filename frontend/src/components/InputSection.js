import React from 'react';
import './InputSection.css';

function InputSection({ inputText, uploadedFile, onTextInput, onFileUpload, onProcess, onClear, loading }) {
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.type === 'application/pdf') {
        onFileUpload(file);
      } else {
        alert('Please upload a PDF file');
      }
    }
  };

  return (
    <div className="input-section">
      <div className="input-container">
        <div className="input-box">
          <h3>📄 Upload PDF File</h3>
          <div className="file-upload-area">
            <input
              type="file"
              id="pdf-upload"
              accept=".pdf"
              onChange={handleFileChange}
              style={{ display: 'none' }}
            />
            <label htmlFor="pdf-upload" className="upload-button">
              {uploadedFile ? uploadedFile.name : 'Browse PDF File'}
            </label>
            {uploadedFile && (
              <button className="clear-file-button" onClick={() => onFileUpload(null)}>
                ✕
              </button>
            )}
          </div>
        </div>

        <div className="divider">
          <span>OR</span>
        </div>

        <div className="input-box">
          <h3>✍️ Enter Text</h3>
          <textarea
            className="text-input"
            placeholder="Paste or type your text here..."
            value={inputText}
            onChange={(e) => onTextInput(e.target.value)}
            rows={8}
          />
        </div>
      </div>

      <div className="action-buttons">
        <button
          className="process-button"
          onClick={onProcess}
          disabled={loading || (!inputText.trim() && !uploadedFile)}
        >
          {loading ? 'Processing...' : '🔍 Detect & Redact PII'}
        </button>
        <button
          className="clear-button"
          onClick={onClear}
          disabled={loading}
        >
          Clear
        </button>
      </div>
    </div>
  );
}

export default InputSection;

