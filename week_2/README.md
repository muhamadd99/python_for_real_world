# Week 2: Job-to-Resume Skill Gap Analysis

## Project Overview

This project analyzes job market technical requirements and identifies skill gaps in a candidate resume. It integrates three components:

- **prompt_model.py**: Utility wrapper for flexible Gemini model API calls with model aliasing
- **tag_data.py**: Extracts technical stacks from job descriptions using the Gemini API
- **find_skill_gaps.py**: Compares resume skills against a job database to identify missing technical skills

**Goal**: Help candidates identify which technical skills they need to learn to match job market demands.

---

## Setup Instructions

### Prerequisites

- Python >= 3.14
- `uv` package manager ([install here](https://docs.astral.sh/uv/getting-started/installation/))
- Gemini API key (get from [Google AI Studio](https://aistudio.google.com/apikey))

### Installation

1. Clone or navigate to the project directory:
   ```bash
   cd week_2
   ```

2. Install dependencies using `uv sync`:
   ```bash
   uv sync
   ```

3. Create a `.env` file in the project root with your API key:
   ```bash
   echo "GEMINI_API_KEY=your_api_key_here" > .env
   ```

4. Download the required resources folder from notion and put into `data/`:
   - `jobs_d1.db` - SQLite database with job listings
   - `resume_d3.txt` - Sample resume in plain text

   Note: These files are not committed to the repository.

---

## Usage

### Run Skill Gap Analysis

Find skills missing from your resume compared to the job database:

```bash
uv run find_skill_gaps.py
```

**Expected output:**
```
gaps=['a/b testing', 'ai', 'alerting', 'algorithm', 'alibaba cloud', 'api', 
...
tensorflow', 'testing', 'version control', 'web automation'] time=5.57 tokens=0

```

### Tag Job Data with Technical Skills

Automatically extract and tag technical skills from job descriptions:

```bash
uv run tag_data.py
```

**Expected output:**
```
Analyzed Job 1: Java, Spring Boot, SQL
Analyzed Job 2: Python, FastAPI, PostgreSQL
Total tokens used: 5000, took 12345.500ms
```

### Call Gemini Models Directly

Use the prompt_model utility with flexible model names:

```bash
uv run prompt_model.py "flash" "What is machine learning?"
uv run prompt_model.py "lite" "What is machine learning?"
```

Supported model aliases: `flash`, `lite`, `flash-lite`, `preview`, `gemini-3`, `tts`

---

## API / Function Reference

### `find_skill_gaps(input_file_path: str, db_url: str) → SkillGapResult`

**Purpose**: Compares a candidate resume against the job skills database to identify missing technical skills.

**Inputs**:
- `input_file_path` (str): Path to resume file in plain text
- `db_url` (str): Path to SQLite database containing job listings

**Outputs**:
- `SkillGapResult`: Pydantic model with `gaps` field (sorted list of missing skills in lowercase)
- Prints: `gaps=[...] time=X.XX tokens=Y` to stdout

**Example**:
```python
from find_skill_gaps import find_skill_gaps
result = find_skill_gaps("./data/resources/resume_d3.txt", "./data/resources/jobs_d1.db")
print(result.gaps)  # ['aws', 'docker', 'kubernetes']
```

---

### `tag_data(db_url: str) → None`

**Purpose**: Extracts technical stacks from job descriptions and updates the database.

**Inputs**:
- `db_url` (str): Path to SQLite database

**Outputs**:
- Updates `tech_stack` column in database
- Prints processing logs and token usage to stdout

**Implementation details**:
- Processes jobs in batches of 3
- Retries failed batches up to 2 times with 5-second delay
- Uses `temperature=0.1` for deterministic output

---

### `prompt_model(model: str, prompt: str) → str`

**Purpose**: Wrapper to call Gemini models with flexible model name aliasing.

**Inputs**:
- `model` (str): Model identifier or alias (`flash`, `lite`, `preview`, etc.)
- `prompt` (str): User query or instruction

**Outputs**:
- `str`: Model response text, or error message if API call fails

---

## Data / Assumptions

### Database Schema

The SQLite database contains a `jobs` table with:
- `source_id` (INTEGER PRIMARY KEY): Unique job identifier
- `description` (TEXT): Full job description
- `tech_stack` (TEXT): Comma-separated technical skills

### Input Format

- **Resume**: Plain text file with one skill/experience per line or mixed in paragraphs
- **Job Descriptions**: Unstructured text descriptions

### Key Assumptions

1. **Case-insensitive matching**: "AWS" in resume matches "aws" in database
2. **Synonym mapping**: System maps synonyms to database spellings (e.g., "Amazon Web Services" → "aws")
3. **Soft skills excluded**: Management roles, communication, teamwork are filtered out
4. **Skills are comma-separated** in database output
5. **Rate limits apply** (see section below)

### Data Flow

```
Resume (TXT)
    ↓
[Gemini API extracts skills]
    ↓
Resume Skills Set
    ↓
[Compare against Database]
    ↓
Database Skills - Resume Skills = Gaps
    ↓
Output: Sorted list of missing skills
```

### Rate Limits (from Gemini API)

| Model                   | RPM | TPM  | Batch Size |
|-------------------------|-----|------|------------|
| `gemini-2.5-flash`      | 5   | 250K |     3      |
| `gemini-2.5-flash-lite` | 10  | 250K |     3      |
| `gemini-3-flash`        | 5   | 250K |     3      |

See rate_limits.txt for details.

---

## Testing

### Test Scenarios

1. **Determinism Test**
   - Run `find_skill_gaps.py` twice with same input
   - Expected: Identical gaps list (temperature=0.0 ensures this)

2. **Error Handling**
   - Test with missing resume file → returns empty gaps
   - Test with missing database → returns empty gaps with error message
   - Test with invalid API key → graceful error message

3. **Integration Test**
   - Run full pipeline: tag_data → find_skill_gaps
   - Verify gaps are subset of database skills
   - Verify all gaps are in lowercase

4. **Batch Processing**
   - Run tag_data with untagged jobs
   - Verify batches process in groups of 3
   - Verify retry logic triggers on API rate limit

### How to Reproduce Tests

```bash
# Test 1: Determinism
uv run find_skill_gaps.py
uv run find_skill_gaps.py
# Compare output: gaps lists should be identical

# Test 2: Error handling
uv run find_skill_gaps.py  # With missing file
# Should print: gaps=[] time=0 tokens=0

# Test 3: Integration
uv run tag_data.py && uv run find_skill_gaps.py
# Verify output format and no errors
```

---

## Limitations

### Known Constraints

1. **Skill matching limited to database**: Only skills in `jobs_d1.db` are recognized
2. **Soft skills filtered out**: Certifications, management roles, and vague terms excluded by design
3. **Rate-limited by API quotas**: See rate limits table above; batch size of 3 respects RPM limits
4. **Determinism vs. diversity**: `temperature=0.0` prioritizes consistency, not creative responses
5. **No local caching**: Each run re-queries the API (could be optimized)
6. **Batch size fixed at 3**: Not tuned per model; could improve throughput
7. **Resume parsing basic**: No special handling for PDFs, formatted resumes, or non-English text

---

## Architecture Reflection

### Design Choices

**Modularity**: Each script has a single responsibility (tagging, gap analysis, API calls). This allows independent testing and reuse.

**Pydantic Schemas**: Structured output validation (`SkillGapResult`, `JobTagging`, `BatchResponse`) ensures LLM responses conform to expected format, reducing parsing errors.

**Deterministic output**: Setting `temperature=0.0` ensures identical results across multiple runs with same input, critical for reliability in career planning.

### Trade-offs Made

| Choice | Prioritized | Sacrificed |
|--------|------------|-----------|
| Determinism (temperature=0.0) | Consistency | Diverse skill suggestions |
| Batch size of 3 | API rate compliance | Throughput speed |
| Soft skills filtering | Precision (no noise) | Completeness (some skills missed) |
| Comma-separated storage | Simple schema | Query flexibility |

### Future Improvements

1. **Response caching**: Store API responses locally to avoid re-processing
2. **Parallel batch processing**: Process multiple batches concurrently instead of sequentially
3. **Local embedding models**: Replace Gemini calls with local models for privacy and cost
4. **PDF resume support**: Parse formatted resumes, not just plain text
5. **Skill hierarchy**: Recognize skill categories (e.g., "Python" ⊃ "Django")
6. **Personalized scoring**: Weight gaps by job market demand and salary impact
7. **Database indexing**: Add indexes on `tech_stack` for faster searches

---

## License

Educational project for K-youth programme.
```

---
