import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI()

# Use os.path to safely locate the templates folder relative to this app.py file
current_dir = os.path.dirname(os.path.abspath(__file__))
templates_dir = os.path.join(current_dir, "templates")

templates = Jinja2Templates(directory=templates_dir) #templates is jinja2 object

@app.get("/", response_class=HTMLResponse) #make sure it return as HTTP header
def read_root(req: Request): #req is variable name, Request is data type
    # This will load your frontend/src/templates/index.html file
    return templates.TemplateResponse(
        request=req, 
        name="chat_page.html" 
    )