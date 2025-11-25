import React from 'react';
import './ResultsView.css';

function ResultsView({ original, redacted }) {
  return (
    <div className="results-view">
      <h3>📊 Results</h3>
      <div className="results-container">
        <div className="result-panel">
          <div className="panel-header original-header">
            <h4>ORIGINAL</h4>
          </div>
          <div className="panel-content original-content">
            <pre>{original}</pre>
          </div>
        </div>

        <div className="result-panel">
          <div className="panel-header redacted-header">
            <h4>REDACTED</h4>
          </div>
          <div className="panel-content redacted-content">
            <pre>{redacted}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}

export default ResultsView;

