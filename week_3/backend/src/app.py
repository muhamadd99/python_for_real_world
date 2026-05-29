import os
import sys
import tempfile
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Path fixing mechanics so your backend container can locate the week_2 folder
app_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(app_dir)) # Jumps up past src/ and backend/
sys.path.insert(0, parent_dir)

# Import your week 2 function
from week_2.prompt_model import prompt_model
from week_2.find_skill_gaps import find_skill_gaps

load_dotenv()

app = FastAPI()

db_path = os.path.join(app_dir, "week_2", "data", "resources", "jobs_d1.db")

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
                with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", delete=False) as temp_file:
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