# Student & JobSeeker Copilot

Student & JobSeeker Copilot is a multi-agent AI productivity assistant built with Google Agent Development Kit (ADK), Gemini, and Cloud Run.

It helps students and jobseekers manage study plans, track job applications, save notes, and organize weekly action items through a coordinated multi-agent workflow.

## Features

- Multi-agent orchestration using a root agent and specialist sub-agents
- Study planning support for learning tasks and revision goals
- Job tracking support for applications, interviews, and follow-ups
- Notes capture and retrieval for preparation and planning
- API-based deployment on Cloud Run
- Ready to extend with Firestore and MCP integrations

## Architecture

This project uses a multi-agent design:

- **Root Agent**: Receives the user request and coordinates execution
- **Study Agent**: Creates study tasks and preparation plans
- **Job Agent**: Tracks job applications, interview prep, and follow-ups
- **Notes Agent**: Stores and summarizes useful notes
- **Workflow Agent**: Runs the specialist agents in sequence

This architecture follows ADK multi-agent and workflow patterns such as `SequentialAgent`. [web:52][web:55]

## Project Structure

```text
student-jobseeker-copilot/
├── __init__.py
├── agent.py
├── requirements.txt
├── .env
└── README.md
```

The ADK deployment flow expects a Python package with an `agent.py` file containing the `root_agent` definition, along with dependency and environment configuration files. [web:33][web:75]

## Example Use Cases

- “Plan my week for DSA, DBMS, and React practice.”
- “Track my frontend job applications and remind me to follow up.”
- “Help me prepare for an interview and save revision notes.”
- “Create study tasks and job search action items for the next 3 days.”

## Tech Stack

- Python
- Google ADK
- Gemini via Vertex AI
- Cloud Run
- Optional Firestore for persistent storage
- Optional Google Calendar MCP integration

Cloud Run can deploy ADK agents directly from source, and ADK supports multi-agent workflows that are suitable for this use case. [web:33][web:55]

## Prerequisites

Before deploying, make sure you have:

- A Google Cloud project
- Billing enabled
- Google Cloud CLI installed and authenticated
- Required APIs enabled:
  - Cloud Run API
  - Cloud Build API
  - Artifact Registry API
  - Vertex AI API
  - Compute Engine API

These services are required in the codelab and Cloud Run deployment documentation for ADK-based agents. [web:52][web:33]

## Installation

Clone or create the project folder, then install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file like this:

```env
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID
GOOGLE_CLOUD_LOCATION=europe-west1
MODEL=gemini-2.5-flash
```

The ADK Cloud Run documentation uses project and region environment variables for Vertex AI-backed agents. [web:26][web:33]

## Run Locally

You can test the agent locally before deploying:

```bash
adk web
```

ADK also supports local development and testing workflows before Cloud Run deployment. [web:75]

## Deploy to Cloud Run

Example deployment command:

```bash
export PROJECT_ID="YOUR_PROJECT_ID"
export REGION="europe-west1"
export SERVICE_ACCOUNT="adk-runner@${PROJECT_ID}.iam.gserviceaccount.com"

uvx --from google-adk==1.14.0 \
adk deploy cloud_run \
--project=$PROJECT_ID \
--region=$REGION \
--service_name=student-jobseeker-copilot \
--with_ui \
. \
-- \
--service-account=$SERVICE_ACCOUNT
```

ADK provides a direct `deploy cloud_run` command for packaging and deploying agents to Cloud Run, including an optional built-in UI for testing. [web:55][web:52]

## Example Prompt

```text
Plan my next 5 days for Java revision, DSA practice, and 3 frontend job applications. Also save notes for interview preparation.
```

## Future Improvements

- Firestore integration for persistent tasks and job application records
- Google Calendar MCP integration for scheduling
- REST endpoints for frontend integration
- Follow-up reminders and interview timeline generation
- Dashboard UI for tasks, applications, and notes

## Why This Project

Students and jobseekers often struggle to balance study goals, preparation tasks, applications, deadlines, and notes in one place. This project uses a multi-agent approach to coordinate those activities through one assistant.

## License

This project is for educational and hackathon use.
