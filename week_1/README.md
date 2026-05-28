# Data Engineering Pipeline: Medallion Architecture

## Project Description

This project implements a local data pipeline following the **Medallion Architecture** to process job postings or web-based data. The goal is to move data through a multi-stage refinement process—from raw `.mhtml` files to a structured SQLite "Gold" warehouse—ensuring data integrity, idempotency, and clean transformations along the way.

## Setup Instructions

Follow these steps to set up the environment and local pipeline.

### Prerequisites

* **Python**: 3.14
* **uv**: A fast Python package installer and resolver.

### Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd <your-repo-name>

```


2. **Sync dependencies**:
Using `uv`, run the following to create a virtual environment and install requirements:
```bash
uv sync

```

Based on your script's logic, here is the **Usage** section formatted clearly for your README.

---

## Usage

The project uses a command-based orchestrator. You can run the entire pipeline or execute specific modules individually using the following syntax:

```bash
uv run main.py [command]

```

### Commands

| Command | Action | Description |
| --- | --- | --- |
| **`ingest`** | `0_source` → `1_bronze` | Extracts raw `.mhtml` files and saves them as raw content. |
| **`process`** | `1_bronze` → `2_silver` | Parses and cleans HTML files into structured JSON data. |
| **`load`** | `2_silver` → `3_gold` | Ingests the structured JSON data into the SQLite database. |
| **`profile`** | `3_gold` | Analyzes the database to generate a data quality report. |
| **`all`** | **Full Pipeline** | Runs all the above steps in sequence. |

### Examples

**To run the full automated sequence:**

```bash
uv run main.py all

```

**To only clean the data (after ingestion is already done):**

```bash
uv run main.py process

```

### Expected Flow

1. **Bronze**: Raw `.mhtml` files are collected.
2. **Silver**: Data is cleaned, parsed, and converted to structured format (e.g., JSON or CSV).
3. **Gold**: Final validated data is persisted into the SQLite database.

---

## Technical Reflections

### Module 1: The Extractor (Medallion & Lakehouses)

**Why is it useful to keep the original raw HTML files instead of directly inserting processed data into the database? What problems become easier to debug or recover from?**

* **Answer**: Keeping the raw files (the "Source of Truth") allows for **re-processing** without re-fetching data. If your parsing logic improves or you discover a bug in how you extracted data three months ago, you can simply re-run the pipeline on the original files. It also helps debug extraction errors by allowing you to inspect the exact state of the page at the time of capture, ensuring that data loss during transformation can always be recovered.

### Module 2: Treatment Plant (ETL vs ELT & Scale)

**Why do cloud systems prefer loading raw data first before cleaning it (ELT)? What problems happen when processing files sequentially, and how does distributed processing help?**

* **Answer**: Cloud systems favor **ELT** because modern cloud warehouses (like Snowflake) are designed to scale computation independently. By loading raw data first, you minimize the "wait time" for ingestion. Sequential processing creates a bottleneck; if one file takes 10 seconds, 1,000 files take nearly 3 hours. Distributed processing (like Spark) breaks these files into chunks processed simultaneously across multiple nodes, reducing total execution time from hours to minutes.

### Module 3: The Blueprint & The Vault (Storage & Contracts)

**What should happen if an important field like job_title disappears? Why fail early instead of silently inserting nulls into DB? How does INSERT OR IGNORE help prevent duplicate records?**

* **Answer**: If a critical field like `job_title` is missing, the pipeline should **fail early (or quarantine the record)**. Silently inserting nulls pollutes downstream analytics and leads to "silent failures" where dashboards show incorrect totals that are hard to trace. `INSERT OR IGNORE` ensures **idempotency**; it allows the pipeline to be re-run multiple times without creating duplicate entries, ensuring that the Gold layer remains a clean, unique set of records regardless of how many times the script is executed.

### Module 4: The QA Inspector & Orchestrator (Orchestration & DAGs)

**What happens if processor.py crashes halfway? How are automated orchestration tools more reliable than manual retries with Python scripts?**

* **Answer**: If a script crashes halfway, the state is often left in "limbo," potentially leaving partial data in folders or databases. Automated tools like **Airflow** use Directed Acyclic Graphs (DAGs) to track the state of each task. They provide built-in retries, alerting, and "atomic" task execution, meaning they can pick up exactly where they left off or roll back changes, providing a level of resilience that a simple `main.py` script cannot handle manually.

```

```