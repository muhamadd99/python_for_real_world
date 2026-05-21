import sys
import os
from dotenv import load_dotenv
from google import genai
from google.genai.errors import APIError

load_dotenv()

def prompt_model(model: str, prompt: str) -> str:
    """
    Prompts a specified Gemini model with an input string and returns the response text.
    Smartly matches partial model names to their canonical Google identifier strings.
    """
    # 1. Map flexible inputs to the strict API model IDs
    model_lower = model.lower()
    if "lite" in model_lower or "flash-lite" in model_lower:
        target_model = "gemini-2.5-flash-lite"
    elif "preview" in model_lower or "gemini-3" in model_lower:
        target_model = "gemini-3-flash-preview"
    elif "flash" in model_lower:
        target_model = "gemini-2.5-flash"
    elif "tts" in model_lower:
        target_model = "gemini-2.5-flash-tts"
    else:
        # Fallback to whatever string the user passed directly if no keywords match
        target_model = model

    # 2. Safely call the Google GenAI SDK
    try:
        # Client automatically picks up the GEMINI_API_KEY environment variable
        client = genai.Client()
        
        response = client.models.generate_content(
            model=target_model,
            contents=prompt,
        )
        
        # Return the extracted string text response
        if response.text:
            return response.text
        return "Error: Received an empty response from the model."

    except APIError as api_err:
        return f"Google API Error encountered: {api_err.message}"
    except Exception as e:
        return f"An unexpected system error occurred: {str(e)}"

def main():
    if len(sys.argv) >= 3:
        model = sys.argv[1]
        prompt = sys.argv[2]
    else:
        model = "flash"
        prompt = "Tell me a joke."

    response = prompt_model(model, prompt)
    print(response)

if __name__ == "__main__":
    main()