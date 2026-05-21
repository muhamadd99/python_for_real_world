import sqlite3
import time
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

# 1. Define the structural schema we require from the LLM
class JobTagging(BaseModel):
    source_id: int = Field(description="The unique ID of the job row processed.")
    tech_stack: List[str] = Field(description="List of technical keywords used in the job description (e.g. ['Java', 'SQL', 'APIs']).")

class BatchResponse(BaseModel):
    jobs: List[JobTagging] = Field(description="Array of all processed and tagged jobs.")

def tag_data(db_url: str):
    start_time = time.perf_counter() # Start global execution timer
    total_tokens_used = 0

    # Establish a reliable database context connection
    try:
        conn = sqlite3.connect(db_url)
        cursor = conn.cursor()
    except Exception as db_init_err:
        print(f"Database Connection Error: {str(db_init_err)}")
        return

    # Verify that the destination column exists in our SQLite schema
    try:
        cursor.execute("SELECT source_id, description, tech_stack FROM jobs LIMIT 1;")
    except sqlite3.OperationalError:
        print("Initialization Error: The 'jobs' table or expected columns do not exist.")
        conn.close()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"Total tokens used: 0, took {elapsed_ms:.3f}ms")
        return

    # 1. Gather rows missing an updated tech_stack values
    cursor.execute("SELECT source_id, description FROM jobs WHERE tech_stack IS NULL OR tech_stack = '' LIMIT 12;")
    unprocessed_rows = cursor.fetchall()

    if not unprocessed_rows:
        print("No data to tag")
        conn.close()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"Total tokens used: 0, took {elapsed_ms:.3f}ms")
        return

    # 2. Batch Parameters (Configured for tier limits)
    BATCH_SIZE = 3
    RETRY_DELAY = 5.0 # Seconds to sleep if an error occurs
    
    #batches is a list of lists
    batches = [unprocessed_rows[i:i + BATCH_SIZE] for i in range(0, len(unprocessed_rows), BATCH_SIZE)] 
    
    try:
        client = genai.Client()
    except Exception as client_err:
        print(f"Failed to initialize Gemini Client: {client_err}")
        conn.close()
        elapsed_ms = (time.perf_counter() - start_time) * 1000
        print(f"Total tokens used: 0, took {elapsed_ms:.3f}ms")
        return
    
    # 3. Process batches 1 by 1
    for batch_idx, batch in enumerate(batches):
        # Format the current data block into a clean layout for the model
        prompt_content = "Analyze the following job listings and extract their technical stack characteristics:\n\n"
        for source_id, description in batch:
            prompt_content += f"--- SOURCE ID: {source_id} ---\nDescription: {description}\n\n"
    
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt_content,
                    config=types.GenerateContentConfig(
                        system_instruction="You are an automated backend parser. Extract technical stacks from job descriptions. Return only valid tech stack entries. Do not include vague corporate jargon like 'communication' or 'teamwork'. Ensure every source ID in the input prompt is accounted for.",
                        response_mime_type="application/json",
                        response_schema=BatchResponse,
                        temperature=0.1 # Low temperature enforces higher determinism
                    )
                )

                if not response.text:
                    raise ValueError("Received an empty content chunk from remote servers.")

                if response.usage_metadata and response.usage_metadata.total_token_count:
                    total_tokens_used += response.usage_metadata.total_token_count

                # Curate the batchresponse object
                parsed_data = BatchResponse.model_validate_json(response.text)

                # 4. Perform database updates and log updates to standard output
                # change from list to comma separated string
                for job in parsed_data.jobs:
                    comma_separated_stack = ", ".join(job.tech_stack)

                    cursor.execute(
                        "UPDATE jobs SET tech_stack = ? WHERE source_id = ?;",
                        (comma_separated_stack, job.source_id)
                    )
                conn.commit() # Flush transaction to physical storage files
                
                # print(f"[Batch {batch_idx}] Successfully updated database changes.")
                for job in parsed_data.jobs:
                    print(f"Analyzed Job {job.source_id}: {', '.join(job.tech_stack)}")
                
                break

            except Exception as batch_exception:
                conn.rollback()

                # Gracefully report failure context and sleep without dropping runtime threads
                print(f"[Batch {batch_idx}] Attempt {attempt + 1} failed: {batch_exception}")
                if attempt == max_retries - 1:  # (On the 3rd attempt, attempt equals 2)
                    print(f"[Batch {batch_idx}] Permanently skipped...")
                    break
                time.sleep(RETRY_DELAY) #to cope with RPMin. if too fast,  it will reject first second third in just miliseconds duration. so we let it sleep a while so it can refresh on the next min

    conn.close()

    # Calculate final terminal specs for successful run
    elapsed_ms = (time.perf_counter() - start_time) * 1000
    print(f"Total tokens used: {total_tokens_used}, took {elapsed_ms:.3f}ms")
    
if __name__ == "__main__":
    TARGET_DATABASE = "./data/resources/jobs_d1.db"
    
    # Ensure our environment values exist 
    if not os.environ.get("GEMINI_API_KEY"):
        print("Runtime Blocked: Set your GEMINI_API_KEY inside your environment variables before execution.")
    else:
        tag_data(TARGET_DATABASE)
