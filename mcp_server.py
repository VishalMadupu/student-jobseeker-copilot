from __future__ import annotations

import asyncio
import json
from typing import Any

from dotenv import load_dotenv
from mcp import types as mcp_types
from mcp.server.lowlevel import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio

from storage import get_storage

load_dotenv()

app = Server("student-jobseeker-productivity-mcp")
storage = get_storage()

TOOL_DEFINITIONS = [
    mcp_types.Tool(
        name="create_task",
        description="Create a study task, preparation task, or general to-do for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "title": {"type": "string"},
                "details": {"type": "string"},
                "due_date": {"type": "string"},
                "priority": {"type": "string"},
                "category": {"type": "string"},
                "status": {"type": "string"},
            },
            "required": ["user_id", "title"],
        },
    ),
    mcp_types.Tool(
        name="list_tasks",
        description="List the most recent tasks for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    ),
    mcp_types.Tool(
        name="track_application",
        description="Store a job application record for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "company": {"type": "string"},
                "role": {"type": "string"},
                "stage": {"type": "string"},
                "next_step": {"type": "string"},
                "job_url": {"type": "string"},
                "notes": {"type": "string"},
            },
            "required": ["user_id", "company", "role"],
        },
    ),
    mcp_types.Tool(
        name="list_applications",
        description="List the most recent job applications for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    ),
    mcp_types.Tool(
        name="save_note",
        description="Save a structured note for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["user_id", "title", "content"],
        },
    ),
    mcp_types.Tool(
        name="list_notes",
        description="List the most recent saved notes for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    ),
    mcp_types.Tool(
        name="schedule_event",
        description="Save a calendar-style event for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "title": {"type": "string"},
                "event_date": {"type": "string"},
                "event_time": {"type": "string"},
                "description": {"type": "string"},
            },
            "required": ["user_id", "title", "event_date"],
        },
    ),
    mcp_types.Tool(
        name="list_events",
        description="List the most recent scheduled events for a user.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    ),
    mcp_types.Tool(
        name="get_dashboard",
        description="Get a compact dashboard view for a user's tasks, applications, notes, and events.",
        inputSchema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "limit": {"type": "integer"},
            },
            "required": ["user_id"],
        },
    ),
]


def _text_response(payload: Any) -> list[mcp_types.Content]:
    return [
        mcp_types.TextContent(
            type="text",
            text=json.dumps(payload, indent=2),
        )
    ]


def _dispatch(name: str, arguments: dict[str, Any]) -> Any:
    if name == "create_task":
        return storage.create_task(
            user_id=arguments["user_id"],
            title=arguments["title"],
            details=arguments.get("details"),
            due_date=arguments.get("due_date"),
            priority=arguments.get("priority", "medium"),
            category=arguments.get("category", "general"),
            status=arguments.get("status", "open"),
        )

    if name == "list_tasks":
        return storage.list_tasks(
            user_id=arguments["user_id"],
            limit=int(arguments.get("limit", 10)),
        )

    if name == "track_application":
        return storage.track_application(
            user_id=arguments["user_id"],
            company=arguments["company"],
            role=arguments["role"],
            stage=arguments.get("stage", "applied"),
            next_step=arguments.get("next_step"),
            job_url=arguments.get("job_url"),
            notes=arguments.get("notes"),
        )

    if name == "list_applications":
        return storage.list_applications(
            user_id=arguments["user_id"],
            limit=int(arguments.get("limit", 10)),
        )

    if name == "save_note":
        return storage.save_note(
            user_id=arguments["user_id"],
            title=arguments["title"],
            content=arguments["content"],
            tags=list(arguments.get("tags", [])),
        )

    if name == "list_notes":
        return storage.list_notes(
            user_id=arguments["user_id"],
            limit=int(arguments.get("limit", 10)),
        )

    if name == "schedule_event":
        return storage.schedule_event(
            user_id=arguments["user_id"],
            title=arguments["title"],
            event_date=arguments["event_date"],
            event_time=arguments.get("event_time"),
            description=arguments.get("description"),
        )

    if name == "list_events":
        return storage.list_events(
            user_id=arguments["user_id"],
            limit=int(arguments.get("limit", 10)),
        )

    if name == "get_dashboard":
        return storage.get_dashboard(
            user_id=arguments["user_id"],
            limit=int(arguments.get("limit", 5)),
        )

    raise ValueError(f"Unknown tool: {name}")


@app.list_tools()
async def list_tools() -> list[mcp_types.Tool]:
    return TOOL_DEFINITIONS


@app.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[mcp_types.Content]:
    try:
        result = _dispatch(name, arguments or {})
        return _text_response({"ok": True, "result": result})
    except Exception as exc:
        return _text_response({"ok": False, "error": str(exc)})


async def run_mcp_stdio_server() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=app.name,
                server_version="0.1.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(run_mcp_stdio_server())
