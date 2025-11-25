import axios from 'axios';
import { saveAs } from 'file-saver';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const redactText = async (text, settings) => {
  try {
    const response = await api.post('/api/redact/text', {
      text,
      redaction_settings: settings,
    });
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to redact text');
  }
};

export const redactPDF = async (file, settings) => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('redact_emails', settings.redact_emails);
    formData.append('redact_phones', settings.redact_phones);
    formData.append('redact_names', settings.redact_names);
    formData.append('redact_addresses', settings.redact_addresses);
    formData.append('redact_ssn', settings.redact_ssn);
    formData.append('redact_credit_cards', settings.redact_credit_cards);
    formData.append('redaction_style', settings.redaction_style);
    if (settings.custom_label) {
      formData.append('custom_label', settings.custom_label);
    }

    const response = await axios.post(
      `${API_BASE_URL}/api/redact/pdf`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  } catch (error) {
    throw new Error(error.response?.data?.detail || 'Failed to redact PDF');
  }
};

export const exportText = async (redactedText) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/export/text`,
      { redacted_text: redactedText },
      { responseType: 'blob' }
    );
    const blob = new Blob([response.data], { type: 'text/plain' });
    saveAs(blob, 'redacted_output.txt');
  } catch (error) {
    throw new Error('Failed to export text file');
  }
};

export const exportPDF = async (redactedText) => {
  try {
    const response = await axios.post(
      `${API_BASE_URL}/api/export/pdf`,
      { redacted_text: redactedText },
      { responseType: 'blob' }
    );
    const blob = new Blob([response.data], { type: 'application/pdf' });
    saveAs(blob, 'redacted_output.pdf');
  } catch (error) {
    throw new Error('Failed to export PDF file');
  }
};

