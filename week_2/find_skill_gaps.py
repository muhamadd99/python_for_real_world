import sqlite3
import time
import os
from typing import List, Set
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()

# --- MANDATORY PYDANTIC OUTPUT SCHEMA ---
class SkillGapResult(BaseModel):
    gaps: List[str] = Field(description="Sorted list of missing technical skills in lowercase.")

# Minimal internal schema to parse the resume safely
class ExtractedResumeSkills(BaseModel):
    skills: List[str] = Field(description="List of technical skills found in the resume.")

def find_skill_gaps(input_file_path: str, db_url: str) -> SkillGapResult:
    """
    Finds the technical skill gaps between a job database and a resume.
    """

    resume_content = ""
    prompt_tokens = 0
    completion_tokens = 0

    # 1. Gracefully handle file-reading or missing file errors
    if not os.path.exists(input_file_path):
        print(f"gaps=[] time=0 tokens=0 reason=No input file exists")
        return SkillGapResult(gaps=[])

    try:
        with open(input_file_path, "r", encoding="utf-8") as f:
            resume_content = f.read()
    except Exception as e:
        # Prevent stack trace on read error
        print(f"gaps=[] time=0 tokens=0 reason='Read error: {e}'")
        return SkillGapResult(gaps=[])

    # 2. Extract unique non-empty tech skills from your SQLite database
    db_skills: Set[str] = set()
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
        cursor.execute("SELECT tech_stack FROM jobs WHERE tech_stack IS NOT NULL AND tech_stack != '';")
        for row in cursor.fetchall():
            for tech_skill in row[0].split(","):
                clean_tech_skill = tech_skill.strip().lower()  # Split comma-separated skills from Day 1-2
                if clean_tech_skill:
                    db_skills.add(clean_tech_skill)
        conn.close()
    except Exception as e:
        # Gracefully handle database locking or read errors
        print(f"gaps=[] time=0 tokens=0 reason='Database error: {e}'")
        return SkillGapResult(gaps=[])

    # If the database has no skills, there are automatically zero gaps
    if not db_skills:
        print(f"gaps=[] time=0 tokens=0")
        return SkillGapResult(gaps=[])

    # 3. Setup Gemini client safely
    try:
        client = genai.Client()
    except Exception as e:
        print(f"Client initialization failed: {e}")
        return SkillGapResult(gaps=[])

    # 4. Prompt Gemini to map the resume contents directly to your DB skills list
    # This solves the "Direct match inaccuracy" constraint perfectly.
    db_reference_string = ", ".join(sorted(list(db_skills)))
    
    system_instruction = (
        "You are a technical matching system. Look at the provided candidate resume and compare it against the "
        f"following master list of required database skills: [{db_reference_string}]. "
        "Extract any technical skills from the resume that match the items in the master list. "
        "You MUST map synonyms to match the exact spelling in the database list (e.g., if the resume says "
        "'Amazon Web Services' or 'AWS cloud', map it to 'aws' if 'aws' is in the master list). "
        "Ignore soft skills, certifications, and management roles."
    )

    max_retries = 3
    retry_delay = 1.0
    resume_skills: Set[str] = set()
    start_time = time.time()

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content( #generatecontentresponse object
                model="gemini-2.5-flash",
                contents=f"Candidate Resume Text:\n\n{resume_content}",
                config=types.GenerateContentConfig(
                    system_instruction=system_instruction,
                    response_mime_type="application/json",
                    response_schema=ExtractedResumeSkills,
                    temperature=0.0, # Enforces strict determinism across multiple runs
                )
            )
            
            if response.usage_metadata:
                prompt_tokens = response.usage_metadata.prompt_token_count
                completion_tokens = response.usage_metadata.candidates_token_count

            if response.text:
                parsed_output = ExtractedResumeSkills.model_validate_json(response.text)
                # Convert everything to lowercase and clean whitespace
                resume_skills = {s.strip().lower() for s in parsed_output.skills if s.strip()}
                break
                
            raise ValueError("Empty response text received.")

        except Exception as err:
            if attempt == max_retries - 1:
                print(f"Attempt {attempt + 1} failed: {err}")
                break
            else:
                print(f"Attempt {attempt + 1} failed: {err}")
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)

    # 5. Compute the final gaps using clean Python sets
    # (Database Skills) minus (Standardized Resume Skills)
    skill_gaps_set = db_skills - resume_skills
    
    # Sort and structure exactly as required
    final_sorted_gaps = sorted(list(skill_gaps_set))
    
    total_time = round(time.time() - start_time, 2)
    total_tokens = prompt_tokens + completion_tokens

    # Match the exact required terminal print example format
    print(f"gaps={final_sorted_gaps} time={total_time} tokens={total_tokens}")

    return SkillGapResult(gaps=final_sorted_gaps)


if __name__ == "__main__":
    TEST_RESUME_PATH = "./data/resources/resume_d3.txt"
    TARGET_DATABASE = "./data/resources/jobs_d1.db"
    
    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: Please export your GEMINI_API_KEY before running.")
    else:
        find_skill_gaps(TEST_RESUME_PATH, TARGET_DATABASE)