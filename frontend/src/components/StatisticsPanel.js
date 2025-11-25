import React, { useState } from 'react';
import './StatisticsPanel.css';
import { exportText, exportPDF } from '../services/api';

function StatisticsPanel({ statistics, detections, redactedContent, explanation }) {
  const [showDetails, setShowDetails] = useState(false);

  const handleExportText = async () => {
    try {
      await exportText(redactedContent);
    } catch (error) {
      alert('Error exporting text file');
      console.error(error);
    }
  };

  const handleExportPDF = async () => {
    try {
      await exportPDF(redactedContent);
    } catch (error) {
      alert('Error exporting PDF file');
      console.error(error);
    }
  };

  if (!statistics) return null;

  const totalDetected = Object.values(statistics).reduce((sum, count) => sum + count, 0);

  return (
    <div className="statistics-panel">
      <h3>📈 Statistics & Documentation</h3>
      
      <div className="stats-summary">
        <div className="stat-item">
          <span className="stat-label">Total PII Detected:</span>
          <span className="stat-value">{totalDetected}</span>
        </div>
      </div>

      {explanation && (
        <div className="explanation-section">
          <h4>📝 Detection Explanation</h4>
          <p className="explanation-text">{explanation}</p>
        </div>
      )}

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📧</div>
          <div className="stat-info">
            <div className="stat-name">Emails</div>
            <div className="stat-count">{statistics.emails || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📞</div>
          <div className="stat-info">
            <div className="stat-name">Phone Numbers</div>
            <div className="stat-count">{statistics.phones || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">👤</div>
          <div className="stat-info">
            <div className="stat-name">Names</div>
            <div className="stat-count">{statistics.names || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">📍</div>
          <div className="stat-info">
            <div className="stat-name">Addresses</div>
            <div className="stat-count">{statistics.addresses || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🆔</div>
          <div className="stat-info">
            <div className="stat-name">SSN</div>
            <div className="stat-count">{statistics.ssn || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💳</div>
          <div className="stat-info">
            <div className="stat-name">Credit Cards</div>
            <div className="stat-count">{statistics.credit_cards || 0}</div>
          </div>
        </div>
      </div>

      <div className="panel-actions">
        <button
          className="details-button"
          onClick={() => setShowDetails(!showDetails)}
        >
          {showDetails ? 'Hide' : 'Show'} Detailed Log
        </button>
        <button className="export-button" onClick={handleExportText}>
          📥 Download Redacted Text
        </button>
        <button className="export-button" onClick={handleExportPDF}>
          📥 Download Redacted PDF
        </button>
      </div>

      {showDetails && detections && (
        <div className="details-section">
          <h4>Detection Details</h4>
          {Object.entries(detections).map(([type, items]) => {
            if (!items || items.length === 0) return null;
            return (
              <div key={type} className="detection-group">
                <h5>{type.toUpperCase()} ({items.length})</h5>
                <ul>
                  {items.map((item, idx) => (
                    <li key={idx}>
                      <strong>{item.value}</strong>
                      {item.start !== undefined && (
                        <span className="position"> (position: {item.start}-{item.end})</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default StatisticsPanel;

