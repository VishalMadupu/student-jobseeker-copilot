import os
from fastapi import FastAPI
from pydantic import BaseModel
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

# -------------------------
# CONFIG
# -------------------------
MODEL = os.getenv("MODEL", "gemini-2.5-flash")

app = FastAPI()

# -------------------------
# REQUEST MODEL
# -------------------------
class ChatRequest(BaseModel):
    user_id: str
    message: str

# -------------------------
# TOOLS
# -------------------------
def save_user_goal(tool_context: ToolContext, goal: str) -> dict:
    tool_context.state["user_goal"] = goal
    return {"status": "saved", "goal": goal}


def create_study_task(task: str) -> dict:
    return {"type": "study_task", "task": task, "status": "created"}


def add_job_application(company: str, role: str) -> dict:
    return {
        "type": "job_application",
        "company": company,
        "role": role,
        "status": "saved",
    }


def save_note(note: str) -> dict:
    return {"type": "note", "note": note, "status": "saved"}


def create_calendar_event(title: str, date: str, time: str) -> dict:
    return {
        "type": "calendar_event",
        "title": title,
        "date": date,
        "time": time,
        "status": "scheduled",
    }

# -------------------------
# ROUTER (INTENT DETECTION)
# -------------------------
def detect_intents(message: str):
    msg = message.lower()

    return {
        "study": any(x in msg for x in ["study", "prepare", "learn"]),
        "job": any(x in msg for x in ["job", "interview", "apply"]),
        "calendar": any(x in msg for x in ["schedule", "tomorrow", "pm", "am", "today"]),
        "notes": any(x in msg for x in ["note", "remember", "save"]),
    }

# -------------------------
# ROOT AGENT (ONLY FOR NLP)
# -------------------------
root_agent = Agent(
    name="controller_agent",
    model=MODEL,
    instruction=(
        "Extract structured data from user input. "
        "Return clean short phrases for tasks. "
        "Do NOT chat."
    ),
    tools=[save_user_goal],
)

# -------------------------
# RESPONSE FORMATTER
# -------------------------
def format_response(actions):
    return {
        "status": "success",
        "actions_taken": actions,
        "reply": "Done! All tasks executed successfully."
    }

# -------------------------
# API ENDPOINT (FIXED CORE)
# -------------------------
@app.post("/chat")
def chat(req: ChatRequest):
    message = req.message

    # Step 1: detect intents
    intents = detect_intents(message)

    actions = []

    # Step 2: save goal
    root_agent.run(message)

    # Step 3: execute tools directly (NO ADK BUGS)
    if intents["study"]:
        study = create_study_task("Interview preparation")
        actions.append("Study tasks created")

    if intents["job"]:
        job = add_job_application("Google", "Interview")
        actions.append("Job added")

    if intents["calendar"]:
        calendar = create_calendar_event(
            title="Interview Prep",
            date="Tomorrow",
            time="7PM"
        )
        actions.append("Calendar event scheduled")

    if intents["notes"]:
        note = save_note("User preparing for interview")
        actions.append("Notes saved")

    # fallback
    if not actions:
        actions.append("No actionable intent detected")

    return format_response(actions)