# Week 4 : Independent Project

# Independent System Build, Testing & Deployment

## Objective - Collaborative Project with Another Peer

Up until this point, you have built **individual system components**:

- Week 1 → Data pipeline (ETL)
- Week 2 → AI decision-making module
- Week 3 → Application layer (frontend + backend integration)

Week 4 is no longer an exercise in following instructions. It is a simulation of building a real-world system under constraints. In this module, you will move beyond guided implementation and:

- define your own problem space
- design a complete system architecture
- build, test, and refine a full application
- deploy and present a working solution

## Core Philosophy

A working system is not defined by code alone. A strong system:

- solves a **clear and meaningful problem**
- uses **data and AI intentionally (not for decoration)**
- integrates components cleanly
- handles failure cases
- can be explained, defended, and demonstrated

---

## AI Usage Guidelines

AI can significantly help developers to increase productivity, especially for accelerating repetitive tasks, exploring ideas, and supporting implementation. However, it should be used deliberately with the following awareness: 

- Use AI to assist with repetitive or time-consuming tasks.
- Before using AI, take time to understand the problem you are trying to solve. Clear thinking leads to better prompts, and better prompts lead to more useful results.
- Treat AI-generated code as starting points rather than final answers. Critically review AI output. Test it, question it, and ensure it aligns with your intended logic and requirements.
- Blindly copying or “vibe coding” solutions without understanding will create gaps that become obvious during evaluation, leading to a low score or even failure.
- Seek feedback from peers to validate your work. Discussing ideas, reviewing each other’s work, and challenging assumptions will often provide insights that AI alone cannot offer.

Your growth in this program depends on your ability to reason through problems, collaborate with peers, and build systems with intention. Use AI as a tool to enhance that process, not shortcut it.

---

## General Instructions

- Work in **pairs**
- Create a **new** GitHub repository with a meaningful name.
- All git commit messages must follow Conventional Commits v1.0.0
- Format all Python code with `ruff` version **0.15.***
- Ensure you are running Python version **3.14**.*
- Ensure you are using `uv` version **0.8.***
- All packages are allowed, but unused packages must be removed from `pyproject.toml`, with the exception of OS-specific packages of course.
- Ensure all packages are pinned to exact versions to prevent breaking changes.
- Do not expose API keys or secrets
- **You are free to incorporate additional technologies, frameworks, languages, or services where appropriate, provided the core project remains executable and evaluable by the programme facilitators. (Python is still mandatory)**

---

## **You are free to choose your:**

- problem
- dataset
- system design
- feature scope

However, your project **must** satisfy the following minimum requirements:

- The project must solve a **real and clearly defined problem**
- The project must include:
    - a **data component**
    - an **AI component**
    - a **frontend/backend application**
- The system must process **real input data**
- The AI component must perform a **meaningful task** beyond simple prompt-response interaction
- The project must be realistically achievable within the programme timeframe
- The final system must be:
    - functional
    - testable
    - demo-ready
- Teams are strongly encouraged to prioritize:
    - reliability
    - usability
    - maintainability
    - scope control

---

## Strong Recommendations

Avoid:

- building generic chatbot clones
- over-engineering infrastructure
- excessive feature creep
- choosing datasets that are too large or too complex to process within the timeframe
- depending heavily on paid APIs or unstable services

A smaller but complete system is preferred over an ambitious but unfinished system.

---

# Project Structure (Suggested)

```
week_4/
├── data/                  # Data sources / processed data
├── backend/
│   ├── src/
│   └── week_2/           # Reuse or adapt AI module
├── frontend/
│   └── src/
├── scripts/              # Optional utilities / pipelines
├── tests/                # Testing logic (optional but encouraged)
├── docker-compose.yml
├── .env.example
└── README.md
```

## Timeline (Suggested)

| Day | Focus |
| --- | --- |
| Day 1 | • Clear problem statement
• Identified target users and use cases
• Selected dataset(s) or data sources
• Initial system architecture and component breakdown
• Defined MVP feature scope
• Explanation of where and why AI is used
• Validation of problem relevance and project feasibility |
| Day 2 | • Working data ingestion/transformation component
• Functional AI component
• Database integration
• Frontend ↔ backend communication
• Initial end-to-end pipeline
• Modular architecture with structured AI outputs
• Validation and fallback handling |
| Day 3 | • Error handling and edge case handling
• UI/UX refinement
• Environment variable handling
• Docker/Docker Compose setup (optional)
• Deployment preparation
• README improvements
• Awareness of hallucinations, invalid outputs, scalability, cost, and reliability concerns |
| Day 4 | • Fully working integrated application
• Final README/documentation
• Architecture explanation
• Presentation/demo preparation
• Final testing and debugging |
| Final | Demo & evaluation
• Problem and impact clearly communicated
• Core features functional end-to-end
• AI usage is meaningful and validated
• Clear separation of data, AI, and application layers
• Working frontend, backend, and integration flow
• Proper configuration and error handling
• Ability to explain architecture, AI logic, trade-offs, and limitations
• Awareness of deployment, privacy, cost, and scaling considerations |

---

Mandatory Components

Example Project Themes

Submission Guidelines

Evaluation Rubric

#### **The bonus is intended to be enhancements rather than using them as main components**

# Mandatory Components

## Your system must include **all of the following**:

### 1. Data Component

- ingestion, transformation, or external API usage
- structured input → processed output
- must be reusable and modular

### 2. AI Component

- meaningful use of LLM or model-based logic
- not just raw prompt-response
- must include:
    - validation
    - structured output
    - fallback handling

### 3. Application Layer

- user interface (web-based)
- backend API
- interaction flow between user and system

### 4. Integration Layer

- environment variables handled properly
- all modules must work together
- clear separation of concerns:
    - data logic
    - AI logic
    - application logic

---

## Functional Requirements

Your system must:

- accept real user input
- process input through your pipeline (data → AI → output)
- return meaningful, structured results
- handle invalid input and errors gracefully
- be usable without reading your code

## Non-Functional Requirements

Your system must demonstrate:

- modular design
- readability and maintainability
- basic performance awareness
- error handling and resilience
- security awareness (no exposed secrets)

# Example Project Themes

### You are strongly encouraged to choose a **clear problem domain**. Below are suggested directions (not mandatory):

## 1. Real-World Insight System (Data → AI → Decision)

### Concept

Build a system that transforms messy real-world data into **actionable insights for users**.

### Example Directions

- Cost of living estimator (based on location + lifestyle)
- Job market trend analyzer (skills demand, salary signals)
- Public dataset explorer (health, transport, economy)

### Focus

- Data pipeline quality (Week 1)
- AI interpretation layer (Week 2)
- Clear output for user decisions (Week 3)

### Common Pitfalls

- dumping raw charts instead of insights
- using AI to “summarize” instead of **reason**
- no clear user decision outcome

---

## 2. Decision Support System (Structured Reasoning Engine)

### Concept

Build a system that helps users make **better decisions under constraints**. This is not “advice.” This is **structured reasoning backed by data and logic**.

### Example Directions

- Budget planner with trade-off analysis
- Career path simulator (skills vs market demand)
- Study planner with time/resource constraints

### Focus

- combining:
    - user input
    - data sources
    - AI reasoning
- producing **ranked or justified outputs**
- explain *why* a recommendation is made
- handle multiple factors (not single-variable logic)

### Common Pitfalls

- producing generic suggestions
- no reasoning trace
- no real constraints in decision-making

---

## 3. Intelligent Workflow Automation System (AI as Core Logic)

### Concept

Build a system that **automates a real task**, where AI is responsible for transforming input into structured, usable output.

### Example Directions

- Meeting notes → action items + task tracker
- Documents → classification + recommendation system
- Emails/messages → priority + response drafting

### Focus

- AI as a **processing engine**, not UI gimmick
- structured outputs (JSON, validated results)
- reliability (fallbacks, error handling)

### Common Pitfalls

- wrapping GPT in a UI and calling it a system
- no validation or determinism
- outputs that are not usable programmatically

---

## 4. Open Topic

Any idea is allowed if:

- the problem is clearly defined
- the system architecture is coherent
- AI and data are used meaningfully
- The project clearly demonstrates a full pipeline:

```
input → processing (data/AI) → structured output → user-facing result
```

# Submission Guidelines

## General submission guidelines

**You need to create a new repository.** Remember to push your work into your git repository. Only the work inside your git repository will be evaluated. Double-check file names. It is encouraged to submit before the cutoff period. Make sure your **NEW** git repository is **publicly** accessible!

## 1. Working Application

- fully functional system
- runnable locally or deployed

## 2. Git Repository

Must include:
* clean project structure
* meaningful commit history
* no secrets or unnecessary files

## 3. README.md

Must include:

### Project Overview

- problem statement
- target users
- system goal

### System Architecture

- data flow (input → processing → output)
- module breakdown

### Setup & Installation

- how to run the system
- dependencies and environment setup

### Features

- list of implemented features
- explanation of each

### Technical Decisions

- architecture choices
- trade-offs made

### Limitations

- known issues
- future improvements

## 4. Demo Presentation (15 mins pitch, 15 mins QnA)

You are expected to prepare a pitching deck that does the following:
* explain the problem → solution clearly
* walk through the system flow
* demonstrate key features
* answer technical questions

# Evaluation Rubric

Your project will be evaluated based on the following areas in **15 minutes**:

| Category | Weight |
| --- | --- |
| Problem & Impact | 15% |
| Solution Quality | 20% |
| Innovation & Creativity | 10% |
| Technical Implementation | 25% |
| Presentation & Demo | 10% |
| Feasibility & Realism | 5% |
| Technical Understanding | 15% |
| Bonus | +25% |

---

## 1. Problem & Impact (15%)

We will evaluate:

- Is the problem clearly defined?
- Who are the intended users?
- Is there evidence that the problem actually exists?
- Is AI genuinely useful for solving the problem?

Strong projects solve a real problem for real users.

---

## 2. Solution Quality (20%)

We will evaluate:

- Are the core features working?
- Does the system function end-to-end?
- Are AI outputs structured and usable?
- Does the application provide a reasonable user experience?
- Are common failure cases handled appropriately?

Strong projects are reliable and complete.

---

## 3. Innovation & Creativity (10%)

We will evaluate:

- Is the idea differentiated from common chatbot demos?
- Does the project apply AI in a meaningful way?
- Is there evidence of creative thinking in the workflow or solution design?

Strong projects demonstrate thoughtful problem solving.

---

## 4. Technical Implementation (25%)

We will evaluate:

- Separation between Data, AI, and Application layers
- Data ingestion and processing pipeline
- AI validation and fallback handling
- Frontend and backend integration
- Environment variable handling
- Error handling and resilience
- Code quality and maintainability
- Docker Compose orchestration

Strong projects demonstrate sound engineering practices.

---

## 5. Presentation & Demo (10%)

We will evaluate:

- Clarity of explanation
- Ability to demonstrate the project successfully
- Ability to explain architecture and technical decisions

Strong projects communicate ideas effectively.

---

## 6. Feasibility & Realism (5%)

We will evaluate:

- Whether the solution is realistic
- Awareness of deployment challenges
- Awareness of hallucinations, privacy, cost, and scalability concerns

Strong projects understand real-world constraints.

---

## 7. Technical Understanding (15%)

Every participant should be able to explain:

- System flow from input to output
- How the AI component works
- Architectural decisions and trade-offs
- Major implementation choices

Understanding your project is part of the evaluation.

Being unable to explain significant portions of your own code may negatively affect your score.