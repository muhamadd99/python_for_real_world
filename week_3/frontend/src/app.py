import os
import httpx
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from pypdf import PdfReader
import io

load_dotenv()

app = FastAPI()

# Use os.path to safely locate the templates folder relative to this app.py file
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")
templates = Jinja2Templates(directory=templates_dir) #templates is jinja2 object

# BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
BACKEND_URL = os.getenv("BACKEND_URL")
if not BACKEND_URL:
    raise ValueError("BACKEND_URL environment variable is required")

@app.get("/", response_class=HTMLResponse) #make sure it return as HTTP header
def read_root(req: Request): #req is variable name, Request is data type
    # This will load your frontend/src/templates/index.html file
    return templates.TemplateResponse(
        request=req, 
        name="chat_page.html" 
    )

@app.post("/send-message")
async def handle_message(message: str = Form(""), file: UploadFile = File(None)):
    extracted_text = ""
    
    # 1. If a PDF is uploaded, convert it to text using Python
    if file and file.filename.endswith('.pdf'):
        try:
            pdf_bytes = await file.read() #pdf byte is raw byte object
            reader = PdfReader(io.BytesIO(pdf_bytes)) #io.bytesio turn raw file into a virtual file. reader is an object the contain anatomy of pdf file
            text_layers = [page.extract_text() for page in reader.pages if page.extract_text()]
            extracted_text = "\n".join(text_layers)
        except Exception as e:
            return JSONResponse(status_code=400, content={"error": f"Failed to parse PDF: {str(e)}"})

    # 2. Build the exact JSON payload required for tomorrow's backend
    payload = {
        "message": message,
        "pdf_text": extracted_text
    }

    # 3. Forward the payload to the Backend URL safely from the server side
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(f"{BACKEND_URL}/chat", json=payload)
            backend_data = response.json()
            return JSONResponse(content=backend_data)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Backend unreachable: {str(e)}"})