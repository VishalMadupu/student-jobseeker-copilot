from __future__ import annotations

import inspect
from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Query
from google.adk.apps import App as AdkApp
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel, Field

from student_jobseeker_copilot.agent import root_agent
from storage import get_storage

load_dotenv()

APP_NAME = "student-jobseeker-copilot"


async def maybe_await(value: Any) -> Any:
    if inspect.isawaitable(value):
        return await value
    return value


def extract_text_from_content(content: Any) -> str:
    if not content:
        return ""

    parts = getattr(content, "parts", None) or []
    text_parts: list[str] = []
    for part in parts:
        text = getattr(part, "text", None)
        if text:
            text_parts.append(text)
    return "\n".join(text_parts).strip()


async def get_or_create_session(
    *,
    session_service: InMemorySessionService,
    user_id: str,
    session_id: str | None,
    initial_state: dict[str, Any],
):
    session = None
    if session_id:
        session = await maybe_await(
            session_service.get_session(
                app_name=APP_NAME,
                user_id=user_id,
                session_id=session_id,
            )
        )

    if session is not None:
        return session

    created_session = await maybe_await(
        session_service.create_session(
            app_name=APP_NAME,
            user_id=user_id,
            session_id=session_id or str(uuid4()),
            state=initial_state,
        )
    )
    return created_session


@asynccontextmanager
async def lifespan(app: FastAPI):
    session_service = InMemorySessionService()
    adk_app = AdkApp(
        name=APP_NAME,
        root_agent=root_agent,
    )
    runner = Runner(
        app=adk_app,
        session_service=session_service,
    )

    app.state.session_service = session_service
    app.state.runner = runner
    yield

    close_method = getattr(runner, "close", None)
    if callable(close_method):
        await maybe_await(close_method())


app = FastAPI(
    title="Student JobSeeker Copilot API",
    version="1.0.0",
    lifespan=lifespan,
)


class ChatRequest(BaseModel):
    user_id: str = Field(..., min_length=1)
    message: str = Field(..., min_length=1)
    session_id: str | None = None
    timezone: str | None = "Asia/Calcutta"


class ChatResponse(BaseModel):
    user_id: str
    session_id: str
    reply: str
    dashboard: dict[str, Any]


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {
        "status": "ok",
        "storage_backend": get_storage().backend_name,
        "app_name": APP_NAME,
    }


@app.get("/dashboard/{user_id}")
def dashboard(user_id: str, limit: int = Query(default=5, ge=1, le=25)) -> dict[str, Any]:
    return get_storage().get_dashboard(user_id=user_id, limit=limit)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    session_service = app.state.session_service
    runner = app.state.runner

    initial_state = {
        "user_id": request.user_id,
        "request_context": {
            "timezone": request.timezone,
            "channel": "fastapi",
        },
    }
    session = await get_or_create_session(
        session_service=session_service,
        user_id=request.user_id,
        session_id=request.session_id,
        initial_state=initial_state,
    )

    user_message = types.Content(
        role="user",
        parts=[types.Part(text=request.message)],
    )

    final_reply = ""
    try:
        events = runner.run_async(
            user_id=request.user_id,
            session_id=session.id,
            new_message=user_message,
        )

        if hasattr(events, "__aiter__"):
            async for event in events:
                if hasattr(event, "is_final_response") and event.is_final_response():
                    final_reply = extract_text_from_content(getattr(event, "content", None)) or final_reply
                elif not final_reply:
                    final_reply = extract_text_from_content(getattr(event, "content", None)) or final_reply
        else:
            for event in events:
                if hasattr(event, "is_final_response") and event.is_final_response():
                    final_reply = extract_text_from_content(getattr(event, "content", None)) or final_reply
                elif not final_reply:
                    final_reply = extract_text_from_content(getattr(event, "content", None)) or final_reply
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {exc}") from exc

    dashboard_snapshot = get_storage().get_dashboard(user_id=request.user_id, limit=5)
    return ChatResponse(
        user_id=request.user_id,
        session_id=session.id,
        reply=final_reply or "The workflow completed, but no final response text was returned.",
        dashboard=dashboard_snapshot,
    )
