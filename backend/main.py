from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import uvicorn
import tempfile
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from pii_detector import PIIDetector
from pdf_processor import PDFProcessor

app = FastAPI(title="PII Redaction API", version="1.0.0")

# Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Need Gemini API key to work - can't run without it
gemini_api_key = os.getenv("GEMINI_API_KEY")
if not gemini_api_key:
    raise ValueError(
        "GEMINI_API_KEY environment variable is required. "
        "Please set it in your .env file. Get your free key from: https://makersuite.google.com/app/apikey"
    )

try:
    pii_detector = PIIDetector(gemini_api_key=gemini_api_key)
except ValueError as e:
    raise ValueError(f"Failed to initialize PII detector: {e}")

pdf_processor = PDFProcessor()


class TextInput(BaseModel):
    text: str
    redaction_settings: Dict


@app.get("/")
async def root():
    return {"message": "PII Redaction API is running"}


@app.post("/api/redact/text")
async def redact_text(input_data: TextInput):
    try:
        text = input_data.text
        settings = input_data.redaction_settings
        
        # Find all PII and then replace it with redaction labels
        detection_results, explanation = pii_detector.detect_all(text, settings)
        redacted_text = pii_detector.redact_text(text, detection_results, settings)
        
        # Count what we found for the stats
        stats = {
            "emails": len(detection_results.get("emails", [])),
            "phones": len(detection_results.get("phones", [])),
            "names": len(detection_results.get("names", [])),
            "addresses": len(detection_results.get("addresses", [])),
            "ssn": len(detection_results.get("ssn", [])),
            "credit_cards": len(detection_results.get("credit_cards", []))
        }
        
        return {
            "original": text,
            "redacted": redacted_text,
            "statistics": stats,
            "detections": detection_results,
            "explanation": explanation
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Gemini API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/redact/pdf")
async def redact_pdf(
    file: UploadFile = File(...),
    redact_emails: bool = True,
    redact_phones: bool = True,
    redact_names: bool = True,
    redact_addresses: bool = True,
    redact_ssn: bool = True,
    redact_credit_cards: bool = True,
    redaction_style: str = "labels",
    custom_label: Optional[str] = None
):
    try:
        # Save uploaded PDF to temp file so we can process it
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        try:
            # Extract text from PDF, then detect and redact PII
            extracted_text = pdf_processor.extract_text(tmp_path)
            
            settings = {
                "redact_emails": redact_emails,
                "redact_phones": redact_phones,
                "redact_names": redact_names,
                "redact_addresses": redact_addresses,
                "redact_ssn": redact_ssn,
                "redact_credit_cards": redact_credit_cards,
                "redaction_style": redaction_style,
                "custom_label": custom_label
            }
            
            detection_results, explanation = pii_detector.detect_all(extracted_text, settings)
            redacted_text = pii_detector.redact_text(extracted_text, detection_results, settings)
            
            stats = {
                "emails": len(detection_results.get("emails", [])),
                "phones": len(detection_results.get("phones", [])),
                "names": len(detection_results.get("names", [])),
                "addresses": len(detection_results.get("addresses", [])),
                "ssn": len(detection_results.get("ssn", [])),
                "credit_cards": len(detection_results.get("credit_cards", []))
            }
            
            return {
                "original": extracted_text,
                "redacted": redacted_text,
                "statistics": stats,
                "detections": detection_results,
                "explanation": explanation
            }
        finally:
            # Clean up temp file when done
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=f"Gemini API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export/text")
async def export_text(data: Dict):
    try:
        redacted_text = data.get("redacted_text", "")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as tmp_file:
            tmp_file.write(redacted_text)
            tmp_path = tmp_file.name
        
        return FileResponse(
            tmp_path,
            media_type='text/plain',
            filename='redacted_output.txt'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/export/pdf")
async def export_pdf(data: Dict):
    try:
        redacted_text = data.get("redacted_text", "")
        original_pdf_path = data.get("original_pdf_path", None)
        
        output_path = pdf_processor.create_redacted_pdf(redacted_text, original_pdf_path)
        
        return FileResponse(
            output_path,
            media_type='application/pdf',
            filename='redacted_output.pdf'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

