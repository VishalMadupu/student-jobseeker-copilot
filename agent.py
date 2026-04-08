from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.adk.agents import LlmAgent, SequentialAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.adk.tools.tool_context import ToolContext
from mcp import StdioServerParameters

load_dotenv()

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT") or os.getenv("PROJECT_ID")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION") or os.getenv("REGION") or "us-central1"
MODEL = os.getenv("MODEL", "gemini-2.5-flash")
MCP_SERVER_PATH = Path(__file__).with_name("mcp_server.py")

if PROJECT_ID:
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", PROJECT_ID)

os.environ.setdefault("GOOGLE_CLOUD_LOCATION", LOCATION)
os.environ.setdefault("GOOGLE_GENAI_USE_VERTEXAI", os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "TRUE"))


def capture_request(tool_context: ToolContext, prompt: str) -> dict[str, str]:
    """Store the latest prompt and user identity in session state."""
    cleaned_prompt = " ".join(prompt.strip().split())
    tool_context.state["request_prompt"] = cleaned_prompt
    tool_context.state["request_received_at"] = datetime.now(timezone.utc).isoformat()

    if not tool_context.state.get("user_id"):
        invocation_context = getattr(tool_context, "_invocation_context", None)
        inferred_user_id = getattr(invocation_context, "user_id", None) or "anonymous"
        tool_context.state["user_id"] = inferred_user_id

    return {
        "status": "captured",
        "user_id": str(tool_context.state["user_id"]),
        "request_prompt": cleaned_prompt,
    }


def build_productivity_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[str(MCP_SERVER_PATH)],
            )
        )
    )


productivity_mcp_toolset = build_productivity_toolset()

planning_agent = LlmAgent(
    name="planning_agent",
    model=MODEL,
    description="Breaks a productivity request into structured actions.",
    instruction="""
You are the planning specialist for a student and jobseeker productivity assistant.

Use the latest state to build an execution plan:
- user_id: {user_id}
- request_prompt: {request_prompt}

Return valid JSON only.

Your JSON must contain these top-level keys:
- intent
- tasks
- applications
- notes
- events
- retrieval_queries
- assumptions

Rules:
- Use tasks for study plans, preparation items, reminders, and to-dos.
- Use applications for job tracking items.
- Use notes for reusable preparation notes or saved context.
- Use events for time-bound calendar-style items.
- Use retrieval_queries when the user wants to review or summarize what is already stored.
- Make reasonable assumptions when the user is underspecified, and record them in assumptions.
- Do not add markdown or commentary outside the JSON object.
""",
    output_key="workflow_plan",
)

execution_agent = LlmAgent(
    name="execution_agent",
    model=MODEL,
    description="Uses MCP tools to store and retrieve structured productivity data.",
    instruction="""
You are the execution specialist for a multi-agent productivity assistant.

You must use tools to complete the plan.

State you can rely on:
- user_id: {user_id}
- request_prompt: {request_prompt}
- workflow_plan: {workflow_plan}

Available MCP tools:
- create_task
- list_tasks
- track_application
- list_applications
- save_note
- list_notes
- schedule_event
- list_events
- get_dashboard

Rules:
- Always pass user_id = {user_id} in every tool call.
- If workflow_plan includes retrieval_queries, run the relevant list tools before summarizing.
- If workflow_plan includes tasks, applications, notes, or events, persist them with the MCP tools.
- Prefer storing concrete, useful records rather than vague placeholders.
- Never invent a tool result. Use the real tool output.

Return valid JSON only with these top-level keys:
- actions_completed
- created_records
- retrieved_records
- assumptions
""",
    tools=[productivity_mcp_toolset],
    output_key="execution_report",
)

summary_agent = LlmAgent(
    name="summary_agent",
    model=MODEL,
    description="Summarizes the workflow result into a concise user-facing response.",
    instruction="""
You are the user-facing response specialist.

Use this state:
- request_prompt: {request_prompt}
- workflow_plan: {workflow_plan}
- execution_report: {execution_report}

Write a concise, practical response that:
- confirms what was stored or retrieved
- highlights any assumptions
- suggests the next best action if helpful

Do not mention internal state keys or JSON formatting.
""",
)

productivity_workflow = SequentialAgent(
    name="productivity_workflow",
    description="Runs planning, tool execution, and summarization in a fixed order.",
    sub_agents=[planning_agent, execution_agent, summary_agent],
)

root_agent = LlmAgent(
    name="controller_agent",
    model=MODEL,
    description="Primary coordinator agent for the student-jobseeker productivity assistant.",
    instruction="""
You are the controller agent for a multi-agent productivity assistant.

For every new user message:
1. Call the capture_request tool with the user's full latest message.
2. Transfer control to the productivity_workflow sub-agent.

Do not answer directly before the workflow runs.
""",
    tools=[capture_request],
    sub_agents=[productivity_workflow],
)
