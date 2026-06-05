import os
import sys
import tempfile
import base64
from io import BytesIO
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Path fixing mechanics so your backend container can locate the week_2 folder
app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(app_dir))
sys.path.insert(0, parent_dir)

# Import your week 2 functions
from week_2.prompt_model import prompt_model
from week_2.find_skill_gaps import find_skill_gaps

# Import OCR dependencies
try:
    import pytesseract
    from PIL import Image
    import pdfplumber
    import pdf2image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

load_dotenv()

app = FastAPI()

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db_path = os.path.join(app_dir, "week_2", "data", "resources", "jobs_d1.db")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return JSONResponse(content={"status": "healthy", "ocr_available": OCR_AVAILABLE})

@app.post("/extract-receipt")
async def extract_receipt(file: UploadFile = File(...)):
    """Extracts text from receipt images or PDFs using OCR."""
    try:
        if not OCR_AVAILABLE:
            return JSONResponse(
                status_code=500,
                content={"error": "OCR dependencies not installed"}
            )
        
        # Read the uploaded file
        contents = await file.read()
        
        # Determine file type and extract text
        if file.filename.lower().endswith('.pdf'):
            extracted_text = extract_text_from_pdf(contents)
        elif file.filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp')):
            extracted_text = extract_text_from_image(contents)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Unsupported file format. Please upload an image or PDF."}
            )
        
        if not extracted_text:
            return JSONResponse(
                status_code=400,
                content={"error": "No text detected in the receipt. Try a clearer image."}
            )
        
        return JSONResponse(content={"receipt_text": extracted_text})
    
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Receipt extraction error: {str(e)}"}
        )

@app.post("/chat")
async def chat(request: Request):
    """Processes incoming prompt data and executes the LLM pipeline."""
    try:
        # Parse incoming JSON payload data
        data = await request.json()
        message = data.get("message", "")
        pdf_text = data.get("pdf_text", "")
        
        if pdf_text:
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False, suffix=".txt") as temp_file:
                    temp_file.write(pdf_text)
                    temp_path = temp_file.name

                skill_gap_result = find_skill_gaps(temp_path, db_path)
                gaps = skill_gap_result.gaps
                if gaps:
                    response_text = (
                        "We compared your resume to our job-skill database. "
                        "To improve your employability, consider studying or practicing: "
                        + ", ".join(gaps)
                    )
                else:
                    response_text = "Skill gaps: none detected in the resume."
            finally:
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)
        else:
            # Fallback to general chat if no resume text is provided
            response_text = prompt_model("flash", message)
        
        # Respond back with the structured answer the frontend expects
        return JSONResponse(content={"reply": response_text})
    
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Backend processing error: {str(e)}"}
        )

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image bytes using Tesseract OCR."""
    try:
        image = Image.open(BytesIO(image_bytes))
        text = pytesseract.image_to_string(image)
        return text.strip()
    except Exception as e:
        raise Exception(f"Image OCR failed: {str(e)}")

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """Extract text from PDF bytes using pdfplumber and OCR."""
    try:
        text_parts = []
        
        # First try pdfplumber for text extraction
        try:
            with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)
        except Exception:
            pass
        
        # If pdfplumber didn't extract text, use OCR on PDF images
        if not text_parts:
            try:
                images = pdf2image.convert_from_bytes(pdf_bytes)
                for image in images:
                    text = pytesseract.image_to_string(image)
                    if text.strip():
                        text_parts.append(text)
            except Exception as e:
                raise Exception(f"PDF OCR conversion failed: {str(e)}")
        
        return "\n".join(text_parts).strip()
    except Exception as e:
        raise Exception(f"PDF extraction failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
