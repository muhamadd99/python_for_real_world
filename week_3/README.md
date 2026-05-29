## Project Overview
This project builds and containerizes a full-stack chat application with a FastAPI frontend, a FastAPI backend, and an AI model integration from Week 2. The frontend accepts user messages and PDF uploads, the backend processes the prompt, and the AI model generates a response.

## Setup Instructions
Prerequisites:
- Docker and Docker Compose
-uv for manual local runs

Environment variables:
- Create a .env file at the repo root with your settings.
- Use the provided .env.example as a template.

Example .env for Docker Compose:
```
BACKEND_URL=http://backend:8000
GEMINI_API_KEY=your_key_here
```

Manual setup (optional):
- Frontend: install deps and run `uv run uvicorn --app-dir src --host 0.0.0.0 --port 8000 app:app`
- Backend: install deps and run `uv run uvicorn --app-dir src --host 0.0.0.0 --port 8000 app:app`

## Usage
Run with Docker Compose:
```
docker compose up --build
```

Access the frontend at:
- http://localhost:3000

Expected inputs:
- A text message
- Optional PDF resume upload

Expected output:
- A chatbot response rendered in the chat history

## API / Function Reference
Backend endpoint:
- POST /chat
	- JSON payload: `{ "message": "...", "pdf_text": "..." }`
	- JSON response: `{ "reply": "..." }`

Frontend endpoints and functions:
- POST /send-message (frontend server)
	- Accepts form-data: `message` and `file`
	- Converts PDF to text and forwards JSON to backend
- Key JS: `sendMessage()` sends form-data, `appendMessage()` updates UI

Service interaction:
- Browser -> frontend `/send-message`
- Frontend -> backend `/chat` over the Docker network

## Data / Assumptions
- JSON messages contain `message` (string) and `pdf_text` (string)
- PDF text extraction is best-effort and may miss complex formatting
- Input size is assumed to be reasonable for a single request
- AI response quality depends on the model integration from Week 2

Data flow:
User message/PDF -> frontend extraction -> backend prompt build -> AI response -> frontend display

## Testing
Frontend:
- Send a text message
- Upload a PDF and verify the response includes resume context

Backend:
- Example curl test:
```
curl -X POST http://localhost:8000/chat \
	-H "Content-Type: application/json" \
	-d '{"message":"Hello","pdf_text":"Sample resume"}'
```

Docker integration:
- Run `docker compose up --build` and send messages in the browser

## Limitations
- No authentication or user accounts
- No persistent chat history
- PDF extraction may fail for scanned or image-based PDFs
- Model responses are limited by the external AI API quality and rate limits

## Architecture Reflection
Design choices:
- Split frontend and backend for clear separation of concerns and easier scaling
- Containerized services for consistent deployment across environments

Trade-offs:
- Prioritized simplicity and Docker-based deployment over advanced UI features
- Kept prompt handling minimal to reduce complexity

Improvements:
- Add a database for chat history
- Use a more robust frontend framework
- Add retries and better error handling for AI calls
