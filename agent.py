import os
from google.adk.agents import Agent, SequentialAgent
from google.adk.tools.tool_context import ToolContext

MODEL = os.getenv("MODEL", "gemini-2.5-flash")

def save_user_goal(tool_context: ToolContext, goal: str) -> dict:
    tool_context.state["user_goal"] = goal
    return {"status": "saved", "goal": goal}

def create_study_task(task: str) -> dict:
    return {"type": "study_task", "task": task, "status": "created"}

def add_job_application(company: str, role: str) -> dict:
    return {"type": "job_application", "company": company, "role": role, "status": "saved"}

def save_note(note: str) -> dict:
    return {"type": "note", "note": note, "status": "saved"}

study_agent = Agent(
    name="study_agent",
    model=MODEL,
    instruction="Read the saved user goal and create study tasks for a student.",
    tools=[create_study_task],
    output_key="study_output",
)

job_agent = Agent(
    name="job_agent",
    model=MODEL,
    instruction="Read the saved user goal and create job search or interview preparation actions.",
    tools=[add_job_application],
    output_key="job_output",
)

notes_agent = Agent(
    name="notes_agent",
    model=MODEL,
    instruction="Read the saved user goal and create a helpful summary note.",
    tools=[save_note],
    output_key="notes_output",
)

workflow_agent = SequentialAgent(
    name="workflow_agent",
    sub_agents=[study_agent, job_agent, notes_agent],
)

root_agent = Agent(
    name="student_jobseeker_copilot",
    model=MODEL,
    instruction=(
        "You are a productivity assistant for students and jobseekers. "
        "First capture the user's goal using save_user_goal, then hand off to workflow_agent. "
        "Return a final action plan with study steps, job search steps, and notes."
    ),
    tools=[save_user_goal],
    sub_agents=[workflow_agent],
)