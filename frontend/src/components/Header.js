import React from 'react';
import './Header.css';

function Header() {
  return (
    <header className="header">
      <div className="header-content">
        <h1>🔒 PII Redaction Tool</h1>
        <p>Protect sensitive information by detecting and redacting PII from text and PDF files</p>
      </div>
    </header>
  );
}

export default Header;

