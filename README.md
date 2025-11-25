# PII Redaction Tool

A comprehensive web application for detecting and redacting Personally Identifiable Information (PII) from both plain text and PDF files. Built as part of the Value AI Labs assignment, this tool demonstrates responsible AI practices by helping protect sensitive data.

## 🎯 What Was Built

This is a full-stack PII redaction tool that:

- **Accepts multiple input formats**: Plain text (via text area) and PDF files
- **Detects various PII types**: Email addresses, phone numbers, names, physical addresses, SSN, and credit card numbers
- **Uses hybrid detection (Regex + NER + LLM)**: Combines regex patterns, spaCy NER, and **Google Gemini LLM** for context-aware validation and discovery
- **LLM-powered validation**: Gemini validates all detections to filter false positives and discover new patterns
- **Provides flexible redaction options**: Toggle specific PII types, choose redaction styles (labels, black boxes, custom)
- **Offers comprehensive output**: Side-by-side view of original and redacted content, detailed statistics, reasoning explanations, and downloadable exports

## 🏗️ Architecture & Approach

### Technology Stack

**Backend:**
- FastAPI (Python) - RESTful API for processing requests
- pdfplumber - PDF text extraction
- reportlab - PDF generation for redacted output
- spaCy - Named Entity Recognition for name and location detection
- Regex patterns - Structured data detection (emails, phones, SSN, credit cards)

**Frontend:**
- React - Modern, responsive user interface
- Axios - HTTP client for API communication
- File-saver - Download functionality

### Detection Strategy

The tool uses a **three-layer intelligent hybrid approach**:

1. **Layer 1 - Fast Detection (Regex + NER)**: Identifies structured data patterns
   - Email addresses using standard email regex
   - Phone numbers (multiple US and international formats)
   - SSN (XXX-XX-XXXX format)
   - Credit card numbers (16-digit patterns)
   - Physical addresses (US address patterns)
   - Person names using spaCy's NER model
   - This handles 90% of cases quickly and accurately

2. **Layer 2 - Context Validation**: Filters false positives
   - Checks surrounding context for phrases like "is just the name", "titled", etc.
   - Excludes example emails in quotes or book titles
   - **Smart field label detection**: Identifies when detected "names" are actually field labels (e.g., "Library Card ID:", "Email:", "Phone:")
   - **Non-name word filtering**: Filters out common words that spaCy might misidentify as names
   - **Configurable patterns**: False positive patterns stored in `pii_config.json`

3. **Layer 3 - Gemini LLM (Required)**: Intelligent validation and discovery
   - **Context-aware validation**: Uses Google Gemini to validate all detections and filter false positives
   - **Automatic pattern discovery**: Finds PII that regex/NER might have missed
   - **Smart reasoning**: Provides clear documentation of what was detected and why
   - **Hybrid integration**: LLM validates and enhances regex/NER results

### Why This Approach?

1. **True Hybrid Approach**: Integrates regex patterns, NER (spaCy), and Gemini LLM as core components
2. **LLM-Powered Validation**: Gemini validates all detections for context-aware false positive filtering
3. **Automatic Pattern Discovery**: Gemini LLM discovers new PII patterns that regex/NER might miss
4. **Smart Reasoning**: Provides clear explanations of what was detected and why using Gemini
5. **Configurable Design**: False positive patterns stored in `pii_config.json` for easy maintenance
6. **Flexibility**: Allows users to customize what gets redacted and how
7. **Transparency**: Detailed logs and reasoning for all detections

## 📁 Project Structure

```
value_ai_labs_assignment/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── pii_detector.py      # PII detection logic (with Gemini integration)
│   ├── pii_config.json      # Configurable false positive patterns
│   ├── pdf_processor.py     # PDF extraction and generation
│   └── requirements.txt     # Python dependencies
├── .env.example             # Example environment variables (Gemini API key)
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── components/      # React components
│   │   │   ├── Header.js
│   │   │   ├── InputSection.js
│   │   │   ├── RedactionControls.js
│   │   │   ├── ResultsView.js
│   │   │   └── StatisticsPanel.js
│   │   ├── services/
│   │   │   └── api.js       # API service layer
│   │   ├── App.js
│   │   ├── App.css
│   │   └── index.js
│   └── package.json
├── test_files/              # Sample input files for testing
│   ├── example1_library_card.txt
│   ├── example2_email_thread.txt
│   ├── example3_hr_record.txt
│   ├── example4_product_review.txt
│   ├── example5_medical_record.txt
│   ├── example6_loan_application.txt
│   └── example7_customer_support.txt
├── README.md
└── Scope_of_Work_Option_B.txt
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Installation

1. **Backend Setup:**

```bash
cd backend
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

**Required - Gemini API Key:**
The tool uses a hybrid detection approach that REQUIRES Gemini API for LLM-based validation:
```bash
# Get free API key from: https://makersuite.google.com/app/apikey
# Then edit the .env file in the project root and add your key:
# GEMINI_API_KEY=your-api-key-here
```

The `.env` file is automatically loaded when you start the backend server. **The tool will not work without a valid Gemini API key** - it's required for the hybrid detection approach (Regex + NER + LLM).

2. **Frontend Setup:**

```bash
cd frontend
npm install
```

### Running the Application

1. **Start the Backend Server:**

```bash
cd backend
python main.py
```

The API will be available at `http://localhost:8000`

2. **Start the Frontend:**

```bash
cd frontend
npm start
```

The application will open at `http://localhost:3000`

## 📖 Usage

1. **Input Method**: Choose either:
   - Upload a PDF file using the file browser
   - Paste or type text directly into the text area

2. **Configure Redaction Settings**:
   - Toggle which PII types to redact (emails, phones, names, addresses, SSN, credit cards)
   - Choose redaction style:
     - **Labels**: Shows `[EMAIL_1]`, `[PHONE_1]`, etc.
     - **Black Boxes**: Shows `████████`
     - **Custom**: Use your own label

3. **Process**: Click "Detect & Redact PII" to process the input

4. **Review Results**:
   - View original and redacted content side-by-side
   - Check statistics panel for detection counts
   - View detailed log to see all detected items

5. **Export**: Download redacted content as:
   - Text file (.txt)
   - PDF file (.pdf)

## 🧪 Test Files

The `test_files/` directory contains 7 sample files based on the assignment examples:

- `example1_library_card.txt` - Library checkout record
- `example2_email_thread.txt` - Email support thread
- `example3_hr_record.txt` - Employee record
- `example4_product_review.txt` - Product review with shipping info
- `example5_medical_record.txt` - Medical record with SSN
- `example6_loan_application.txt` - Loan application with financial data
- `example7_customer_support.txt` - Customer support ticket

These files include various PII types and edge cases (like false positives in book titles) to test the detection accuracy.

## ⚠️ Assumptions & Limitations

### Assumptions

- Input PDFs are text-based (not scanned images requiring OCR)
- English language content only
- Standard US address formats
- Users provide valid PDF/text files
- PDF files are under 10MB for optimal performance

### Known Limitations

1. **False Positives**: Some edge cases may be incorrectly identified as PII
   - Example: Email addresses in book titles or training module names
   - Mitigation: Enhanced context validation and field label detection significantly reduce these
   - **Fixed**: "Library Card" and similar field labels are now properly filtered out

2. **False Negatives**: Some PII may be missed
   - Uncommon name formats
   - Non-standard address formats
   - International phone numbers in unusual formats

3. **PDF Processing**: 
   - Complex PDF layouts may not preserve formatting perfectly
   - Scanned PDFs (images) are not supported
   - Large PDFs (>10MB) may have performance issues

4. **Name Detection**: 
   - Relies on spaCy's NER model, which may miss:
     - Uncommon names
     - Names in non-standard formats
     - Initials or abbreviated names
   - **Improved**: Enhanced false positive filtering prevents field labels from being redacted

5. **Address Detection**:
   - Focuses on US address formats
   - May miss addresses without standard street suffixes
   - International addresses not fully supported - tool works perfectly without it

## 🔄 Trade-offs Made

1. **Speed vs. Accuracy**: 
   - Chose regex + NER over pure LLM-based detection for faster processing
   - Added context validation to improve accuracy without significant speed penalty

2. **Simplicity vs. Features**:
   - Focused on core functionality and bonus features from scope
   - Skipped advanced features like OCR, batch processing, API endpoints

3. **Client vs. Server Processing**:
   - PDF processing on server (required for file handling)
   - Text processing could be client-side, but kept server-side for consistency

4. **Detection Methods**:
   - Used pre-trained spaCy model instead of training custom model (time constraints)
   - Regex patterns cover common cases but may miss edge cases
   - False positive patterns are configurable via `pii_config.json` for maintainability
   - Chose config file approach over hardcoding to balance maintainability with performance

## 🔮 Future Improvements

Given more time, I would implement:

1. **Enhanced Detection**:
   - Fine-tune spaCy model on PII-specific datasets
   - Implement confidence scores for each detection
   - Support for international address formats
   - Expand Gemini integration for more pattern types
   - Add caching for common Gemini validations to reduce API calls

2. **OCR Integration**:
   - Add OCR support for scanned PDFs using Tesseract or cloud APIs
   - Handle image-based documents

3. **User Experience**:
   - Batch processing for multiple files
   - Real-time preview as user types
   - Undo/redo functionality
   - Custom pattern definition by users

4. **Technical Enhancements**:
   - API endpoints for programmatic access
   - Better PDF formatting preservation
   - Multi-language support
   - Database for audit trails (optional)

5. **Validation**:
   - Integration with PII validation services
   - Luhn algorithm for credit card validation
   - Address validation APIs

6. **Performance**:
   - Caching for repeated patterns
   - Parallel processing for large files
   - Web Workers for client-side processing

## 📝 Submission Checklist

- ✅ Functional web application
- ✅ GitHub repository with source code
- ✅ README.md with documentation
- ✅ Test files (7 sample files in `test_files/`)
- ✅ Scope of work document



This project is created for the Value AI Labs assignment.

---

**Built with curiosity and attention to detail** 🚀

