import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Path fixing mechanics so your backend container can locate the week_2 folder
app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(app_dir)) # Jumps up past src/ and backend/
sys.path.insert(0, parent_dir)

# Import your week 2 function
from week_2.prompt_model import prompt_model

load_dotenv()

app = FastAPI()

@app.post("/chat")
async def chat(request: Request):
    """Processes incoming prompt data and executes the LLM pipeline."""
    try:
        # Parse incoming JSON payload data
        data = await request.json()
        message = data.get("message", "")
        pdf_text = data.get("pdf_text", "")
        
        # If PDF text exists, merge it cleanly into the prompt context structure
        if pdf_text:
            full_prompt = f"Resume Content:\n{pdf_text}\n\nUser Question:\n{message}"
        else:
            full_prompt = message
        
        # Trigger your actual AI model pipeline execution from last week
        response_text = prompt_model("flash", full_prompt)
        
        # Respond back with the structured answer the frontend expects
        return JSONResponse(content={"reply": response_text})
    
    except Exception as e:
        return JSONResponse(
            status_code=500, 
            content={"error": f"Backend processing error: {str(e)}"}
        )