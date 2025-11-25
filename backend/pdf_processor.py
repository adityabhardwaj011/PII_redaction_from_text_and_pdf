import pdfplumber
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import tempfile
import os
from typing import Optional


class PDFProcessor:
    def extract_text(self, pdf_path: str) -> str:
        try:
            text_content = []
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
            return "\n\n".join(text_content)
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def create_redacted_pdf(self, redacted_text: str, original_pdf_path: Optional[str] = None) -> str:
        try:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_path = temp_file.name
            temp_file.close()
            
            doc = SimpleDocTemplate(
                temp_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )
            
            # Build PDF from redacted text
            story = []
            styles = getSampleStyleSheet()
            
            paragraphs = redacted_text.split('\n\n')
            for para in paragraphs:
                if para.strip():
                    p = Paragraph(para.replace('\n', '<br/>'), styles['Normal'])
                    story.append(p)
                    story.append(Spacer(1, 0.2*inch))
            
            doc.build(story)
            
            return temp_path
        except Exception as e:
            raise Exception(f"Error creating PDF: {str(e)}")

