#!/usr/bin/env python3
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

try:
    import pypdf
    pdf_reader = pypdf.PdfReader("Take-home assignment (1).pdf")
    for page in pdf_reader.pages:
        print(page.extract_text())
except ImportError:
    try:
        import pdfplumber
        with pdfplumber.open("Take-home assignment (1).pdf") as pdf:
            for page in pdf.pages:
                print(page.extract_text())
    except ImportError:
        print("No PDF library available. Please install pypdf or pdfplumber")
        sys.exit(1)

