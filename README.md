# Student & JobSeeker Copilot

Student & JobSeeker Copilot is a hackathon-ready multi-agent productivity assistant built with Google ADK, MCP, AlloyDB, and Cloud Run compatible deployment patterns.

It helps students and jobseekers plan study work, track job applications, save notes, and schedule follow-ups through an agent workflow that coordinates tools and structured storage.

## What Changed

This project now implements the hackathon requirements in code:

- A primary ADK controller agent coordinates specialist sub-agents
- Structured records are stored and retrieved from a database
- Multiple tools are exposed through MCP
- Requests run as multi-step workflows
- The project can be exposed as an API system

## Architecture

The runtime is split into four parts:

1. `root_agent` in `student_jobseeker_copilot/agent.py`
   - Primary controller agent
   - Captures the user prompt
   - Delegates to a sequential workflow

2. Specialist sub-agents in `agent.py`
   - `planning_agent`: turns a prompt into a structured workflow plan
   - `execution_agent`: uses MCP tools to persist and retrieve records
   - `summary_agent`: turns the execution result into a user-facing reply

3. MCP tool server in `mcp_server.py`
   - Exposes task, application, note, event, and dashboard tools over MCP

4. Structured storage in `storage.py`
   - AlloyDB backend for hackathon and deployment use
   - JSON-file fallback for local development without a running database

## Project Structure

```text
student-jobseeker-copilot/
|-- __init__.py
|-- agent.py
|-- main.py
|-- mcp_server.py
|-- storage.py
|-- student_jobseeker_copilot/
|   |-- __init__.py
|   |-- agent.py
|-- requirements.txt
|-- .env.example
|-- README.md
```

## Hackathon Requirement Mapping

### 1. Primary agent coordinating sub-agents

- `root_agent` is the main coordinator
- `productivity_workflow` is a `SequentialAgent`
- The workflow runs `planning_agent -> execution_agent -> summary_agent`
- `student_jobseeker_copilot/` provides the importable ADK package required for deployment

### 2. Store and retrieve structured data from a database

- Structured tables:
  - tasks
  - applications
  - notes
  - events
- AlloyDB is the primary backend
- JSON fallback exists only for local development convenience

### 3. Integrate multiple tools via MCP

The MCP server exposes these tools:

- `create_task`
- `list_tasks`
- `track_application`
- `list_applications`
- `save_note`
- `list_notes`
- `schedule_event`
- `list_events`
- `get_dashboard`

### 4. Handle multi-step workflows and task execution

Every request follows this sequence:

1. Capture user prompt
2. Create a structured workflow plan
3. Execute MCP tool calls
4. Summarize the final outcome

### 5. Deploy as an API-based system

You have two API options:

- ADK native API server: `adk api_server`
- Custom FastAPI wrapper: `uvicorn main:app --reload`

## Setup

Create a virtual environment and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Create `.env` from `.env.example` and set your values.

## Environment Variables

Example:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=your-project-id
PROJECT_ID=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
MODEL=gemini-2.5-flash
DATA_BACKEND=alloydb
ALLOYDB_INSTANCE_URI=projects/your-project-id/locations/us-central1/clusters/your-cluster/instances/your-instance
ALLOYDB_DB=student_jobseeker_copilot
ALLOYDB_USER=postgres
ALLOYDB_PASSWORD=your-db-password
ALLOYDB_IP_TYPE=PRIVATE
ALLOYDB_ENABLE_IAM_AUTH=false
ALLOYDB_REFRESH_STRATEGY=lazy
LOCAL_DATA_FILE=data/local_data.json
```

Notes:

- Use `DATA_BACKEND=alloydb` for hackathon and Cloud Run deployment
- Use `DATA_BACKEND=json` for local development without AlloyDB
- `ALLOYDB_REFRESH_STRATEGY=lazy` is the recommended serverless-friendly default
- The AlloyDB Python connector handles authentication and TLS, but you still need a valid network path to the instance

## Run Locally

### Option 1: ADK native API server

From the repo root, which acts as the parent directory for the `student_jobseeker_copilot/` agent package:

```bash
adk api_server
```

### Option 2: Custom FastAPI API

```bash
uvicorn main:app --reload
```

Endpoints:

- `POST /chat`
- `GET /dashboard/{user_id}`
- `GET /healthz`

## Example Request

`POST /chat`

```json
{
  "user_id": "demo-user",
  "message": "Plan my next 3 days for DSA revision, save interview notes, and track my application to Google for frontend engineer."
}
```

## Deploy to Cloud Run

This repo remains compatible with the ADK deployment flow described in the Google Cloud codelab:

```bash
uvx --from google-adk==1.14.0 adk deploy cloud_run \
  --project=$PROJECT_ID \
  --region=$REGION \
  --service_name=student-jobseeker-copilot \
  --with_ui \
  . \
  -- \
  --service-account=$SERVICE_ACCOUNT
```

Because the repo includes an importable `student_jobseeker_copilot/agent.py` package wrapper with `root_agent`, it fits the ADK agent package structure used by the Cloud Run codelab.

For AlloyDB on Cloud Run, make sure the service has network connectivity to the database instance, such as a supported private path or another documented AlloyDB connection option.

## Suggested Demo Prompts

- `Plan my week for DBMS, DSA, and React interview prep.`
- `Track my applications to Google, Amazon, and Razorpay, then show me the dashboard.`
- `Save interview notes for system design and schedule a mock interview on 2026-04-10 at 19:00.`
- `Show me my latest tasks, notes, and application follow-ups.`

## Submission Notes

For a hackathon submission, the strongest setup is:

- `DATA_BACKEND=alloydb`
- deployed through Cloud Run
- demoed with a prompt that stores data and then retrieves the dashboard in a second request

## Sources

- Google Cloud codelab: https://codelabs.developers.google.com/codelabs/production-ready-ai-with-gc/5-deploying-agents/deploy-an-adk-agent-to-cloud-run
- AlloyDB language connectors overview: https://cloud.google.com/alloydb/docs/language-connectors-overview
- AlloyDB Cloud Run quickstart: https://cloud.google.com/alloydb/docs/quickstart/integrate-cloud-run
- ADK sequential agents: https://adk.dev/agents/workflow-agents/sequential-agents/
- ADK MCP tools: https://adk.dev/tools-custom/mcp-tools/
