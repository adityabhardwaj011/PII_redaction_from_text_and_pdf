import React, { useState } from 'react';
import './App.css';
import Header from './components/Header';
import InputSection from './components/InputSection';
import RedactionControls from './components/RedactionControls';
import ResultsView from './components/ResultsView';
import StatisticsPanel from './components/StatisticsPanel';
import { redactText, redactPDF } from './services/api';

function App() {
  const [inputText, setInputText] = useState('');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [originalContent, setOriginalContent] = useState('');
  const [redactedContent, setRedactedContent] = useState('');
  const [statistics, setStatistics] = useState(null);
  const [detections, setDetections] = useState(null);
  const [explanation, setExplanation] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [redactionSettings, setRedactionSettings] = useState({
    redact_emails: true,
    redact_phones: true,
    redact_names: true,
    redact_addresses: true,
    redact_ssn: true,
    redact_credit_cards: true,
    redaction_style: 'labels',
    custom_label: ''
  });

  const handleTextInput = (text) => {
    setInputText(text);
    setUploadedFile(null);
  };

  const handleFileUpload = (file) => {
    setUploadedFile(file);
    setInputText('');
  };

  const handleRedactionSettingsChange = (newSettings) => {
    setRedactionSettings(newSettings);
  };

  const handleProcess = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let result;
      
      if (uploadedFile) {
        // Process PDF
        result = await redactPDF(uploadedFile, redactionSettings);
      } else if (inputText.trim()) {
        // Process text
        result = await redactText(inputText, redactionSettings);
      } else {
        setError('Please provide text input or upload a PDF file');
        setLoading(false);
        return;
      }
      
      setOriginalContent(result.original);
      setRedactedContent(result.redacted);
      setStatistics(result.statistics);
      setDetections(result.detections);
      setExplanation(result.explanation || null);
    } catch (err) {
      setError(err.message || 'An error occurred while processing');
      console.error('Processing error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleClear = () => {
    setInputText('');
    setUploadedFile(null);
    setOriginalContent('');
    setRedactedContent('');
    setStatistics(null);
    setDetections(null);
    setExplanation(null);
    setError(null);
  };

  return (
    <div className="App">
      <Header />
      <div className="container">
        <InputSection
          inputText={inputText}
          uploadedFile={uploadedFile}
          onTextInput={handleTextInput}
          onFileUpload={handleFileUpload}
          onProcess={handleProcess}
          onClear={handleClear}
          loading={loading}
        />
        
        {error && (
          <div className="error-message">
            {error}
          </div>
        )}

        <RedactionControls
          settings={redactionSettings}
          onSettingsChange={handleRedactionSettingsChange}
        />

        {(originalContent || redactedContent) && (
          <>
            <ResultsView
              original={originalContent}
              redacted={redactedContent}
            />
            <StatisticsPanel
              statistics={statistics}
              detections={detections}
              redactedContent={redactedContent}
              explanation={explanation}
            />
          </>
        )}
      </div>
    </div>
  );
}

export default App;

