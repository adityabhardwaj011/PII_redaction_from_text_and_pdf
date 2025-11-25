import React from 'react';
import './RedactionControls.css';

function RedactionControls({ settings, onSettingsChange }) {
  const handleToggle = (key) => {
    onSettingsChange({
      ...settings,
      [key]: !settings[key]
    });
  };

  const handleStyleChange = (style) => {
    onSettingsChange({
      ...settings,
      redaction_style: style
    });
  };

  const handleCustomLabelChange = (e) => {
    onSettingsChange({
      ...settings,
      custom_label: e.target.value
    });
  };

  return (
    <div className="redaction-controls">
      <h3>⚙️ Redaction Controls</h3>
      
      <div className="controls-grid">
        <div className="control-group">
          <h4>PII Types to Redact</h4>
          <div className="toggle-group">
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_emails}
                onChange={() => handleToggle('redact_emails')}
              />
              <span>📧 Email Addresses</span>
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_phones}
                onChange={() => handleToggle('redact_phones')}
              />
              <span>📞 Phone Numbers</span>
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_names}
                onChange={() => handleToggle('redact_names')}
              />
              <span>👤 Names</span>
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_addresses}
                onChange={() => handleToggle('redact_addresses')}
              />
              <span>📍 Addresses</span>
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_ssn}
                onChange={() => handleToggle('redact_ssn')}
              />
              <span>🆔 SSN</span>
            </label>
            <label className="toggle-label">
              <input
                type="checkbox"
                checked={settings.redact_credit_cards}
                onChange={() => handleToggle('redact_credit_cards')}
              />
              <span>💳 Credit Cards</span>
            </label>
          </div>
        </div>

        <div className="control-group">
          <h4>Redaction Style</h4>
          <div className="style-options">
            <label className="radio-label">
              <input
                type="radio"
                name="redaction_style"
                value="labels"
                checked={settings.redaction_style === 'labels'}
                onChange={(e) => handleStyleChange(e.target.value)}
              />
              <span>Labels ([EMAIL_1], [PHONE_1])</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="redaction_style"
                value="black_boxes"
                checked={settings.redaction_style === 'black_boxes'}
                onChange={(e) => handleStyleChange(e.target.value)}
              />
              <span>Black Boxes (████)</span>
            </label>
            <label className="radio-label">
              <input
                type="radio"
                name="redaction_style"
                value="custom"
                checked={settings.redaction_style === 'custom'}
                onChange={(e) => handleStyleChange(e.target.value)}
              />
              <span>Custom Label</span>
            </label>
            {settings.redaction_style === 'custom' && (
              <input
                type="text"
                className="custom-label-input"
                placeholder="Enter custom label (e.g., [REDACTED])"
                value={settings.custom_label}
                onChange={handleCustomLabelChange}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default RedactionControls;

