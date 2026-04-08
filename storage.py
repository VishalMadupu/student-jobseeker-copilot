from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

import sqlalchemy
from sqlalchemy import text


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class BaseRepository:
    backend_name = "base"

    def create_task(
        self,
        *,
        user_id: str,
        title: str,
        details: str | None = None,
        due_date: str | None = None,
        priority: str = "medium",
        category: str = "general",
        status: str = "open",
    ) -> dict[str, Any]:
        raise NotImplementedError

    def list_tasks(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def track_application(
        self,
        *,
        user_id: str,
        company: str,
        role: str,
        stage: str = "applied",
        next_step: str | None = None,
        job_url: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def list_applications(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def save_note(
        self,
        *,
        user_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def list_notes(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def schedule_event(
        self,
        *,
        user_id: str,
        title: str,
        event_date: str,
        event_time: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    def list_events(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    def get_dashboard(
        self,
        *,
        user_id: str,
        limit: int = 5,
    ) -> dict[str, Any]:
        return {
            "tasks": self.list_tasks(user_id=user_id, limit=limit),
            "applications": self.list_applications(user_id=user_id, limit=limit),
            "notes": self.list_notes(user_id=user_id, limit=limit),
            "events": self.list_events(user_id=user_id, limit=limit),
            "storage_backend": self.backend_name,
        }


class JsonFileRepository(BaseRepository):
    backend_name = "json"

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self._write_db(
                {
                    "tasks": [],
                    "applications": [],
                    "notes": [],
                    "events": [],
                }
            )

    def _read_db(self) -> dict[str, list[dict[str, Any]]]:
        return json.loads(self.path.read_text(encoding="utf-8"))

    def _write_db(self, payload: dict[str, list[dict[str, Any]]]) -> None:
        temp_path = self.path.with_suffix(".tmp")
        temp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        temp_path.replace(self.path)

    def _insert(self, collection: str, record: dict[str, Any]) -> dict[str, Any]:
        db = self._read_db()
        db[collection].append(record)
        self._write_db(db)
        return record

    def _list(self, collection: str, user_id: str, limit: int) -> list[dict[str, Any]]:
        db = self._read_db()
        results = [item for item in db[collection] if item["user_id"] == user_id]
        results.sort(key=lambda item: item["created_at"], reverse=True)
        return results[:limit]

    def create_task(
        self,
        *,
        user_id: str,
        title: str,
        details: str | None = None,
        due_date: str | None = None,
        priority: str = "medium",
        category: str = "general",
        status: str = "open",
    ) -> dict[str, Any]:
        return self._insert(
            "tasks",
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "details": details,
                "due_date": due_date,
                "priority": priority,
                "category": category,
                "status": status,
                "created_at": _utc_now_iso(),
            },
        )

    def list_tasks(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._list("tasks", user_id, limit)

    def track_application(
        self,
        *,
        user_id: str,
        company: str,
        role: str,
        stage: str = "applied",
        next_step: str | None = None,
        job_url: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        return self._insert(
            "applications",
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "company": company,
                "role": role,
                "stage": stage,
                "next_step": next_step,
                "job_url": job_url,
                "notes": notes,
                "created_at": _utc_now_iso(),
            },
        )

    def list_applications(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._list("applications", user_id, limit)

    def save_note(
        self,
        *,
        user_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        return self._insert(
            "notes",
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "content": content,
                "tags": tags or [],
                "created_at": _utc_now_iso(),
            },
        )

    def list_notes(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._list("notes", user_id, limit)

    def schedule_event(
        self,
        *,
        user_id: str,
        title: str,
        event_date: str,
        event_time: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        return self._insert(
            "events",
            {
                "id": str(uuid.uuid4()),
                "user_id": user_id,
                "title": title,
                "event_date": event_date,
                "event_time": event_time,
                "description": description,
                "created_at": _utc_now_iso(),
            },
        )

    def list_events(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._list("events", user_id, limit)


class AlloyDbRepository(BaseRepository):
    backend_name = "alloydb"

    def __init__(
        self,
        *,
        instance_uri: str,
        database: str,
        user: str,
        password: str | None,
        ip_type: str = "PRIVATE",
        enable_iam_auth: bool = False,
        refresh_strategy: str = "lazy",
    ) -> None:
        from google.cloud.alloydbconnector import Connector, IPTypes

        self.connector = Connector(refresh_strategy=refresh_strategy)

        normalized_ip_type = (ip_type or "PRIVATE").upper()
        ip_type_map = {
            "PRIVATE": None,
            "PUBLIC": IPTypes.PUBLIC,
            "PSC": IPTypes.PSC,
        }
        if normalized_ip_type not in ip_type_map:
            raise ValueError("ALLOYDB_IP_TYPE must be one of PRIVATE, PUBLIC, or PSC.")

        def getconn():
            connect_kwargs: dict[str, Any] = {
                "user": user,
                "db": database,
            }
            if password:
                connect_kwargs["password"] = password
            if enable_iam_auth:
                connect_kwargs["enable_iam_auth"] = True
            selected_ip_type = ip_type_map[normalized_ip_type]
            if selected_ip_type is not None:
                connect_kwargs["ip_type"] = selected_ip_type
            return self.connector.connect(
                instance_uri,
                "pg8000",
                **connect_kwargs,
            )

        self.engine = sqlalchemy.create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_pre_ping=True,
            pool_recycle=1800,
        )
        self._initialize_schema()

    def _initialize_schema(self) -> None:
        ddl = [
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT,
                due_date TEXT,
                priority TEXT NOT NULL,
                category TEXT NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_user_created
            ON tasks (user_id, created_at DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS applications (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                company TEXT NOT NULL,
                role TEXT NOT NULL,
                stage TEXT NOT NULL,
                next_step TEXT,
                job_url TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_applications_user_created
            ON applications (user_id, created_at DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS notes (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_notes_user_created
            ON notes (user_id, created_at DESC)
            """,
            """
            CREATE TABLE IF NOT EXISTS events (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT NOT NULL,
                event_date TEXT NOT NULL,
                event_time TEXT,
                description TEXT,
                created_at TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_events_user_created
            ON events (user_id, created_at DESC)
            """,
        ]

        with self.engine.begin() as conn:
            for statement in ddl:
                conn.execute(text(statement))

    def _fetch_all(self, statement: str, params: dict[str, Any]) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            rows = conn.execute(text(statement), params).mappings().all()
        return [self._normalize_record(dict(row)) for row in rows]

    def _insert_and_return(self, statement: str, params: dict[str, Any]) -> dict[str, Any]:
        with self.engine.begin() as conn:
            row = conn.execute(text(statement), params).mappings().one()
        return self._normalize_record(dict(row))

    def _normalize_record(self, record: dict[str, Any]) -> dict[str, Any]:
        if "tags_json" in record:
            record["tags"] = json.loads(record.pop("tags_json"))
        return record

    def create_task(
        self,
        *,
        user_id: str,
        title: str,
        details: str | None = None,
        due_date: str | None = None,
        priority: str = "medium",
        category: str = "general",
        status: str = "open",
    ) -> dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "details": details,
            "due_date": due_date,
            "priority": priority,
            "category": category,
            "status": status,
            "created_at": _utc_now_iso(),
        }
        return self._insert_and_return(
            """
            INSERT INTO tasks (id, user_id, title, details, due_date, priority, category, status, created_at)
            VALUES (:id, :user_id, :title, :details, :due_date, :priority, :category, :status, :created_at)
            RETURNING id, user_id, title, details, due_date, priority, category, status, created_at
            """,
            payload,
        )

    def list_tasks(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id, user_id, title, details, due_date, priority, category, status, created_at
            FROM tasks
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {"user_id": user_id, "limit": limit},
        )

    def track_application(
        self,
        *,
        user_id: str,
        company: str,
        role: str,
        stage: str = "applied",
        next_step: str | None = None,
        job_url: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "company": company,
            "role": role,
            "stage": stage,
            "next_step": next_step,
            "job_url": job_url,
            "notes": notes,
            "created_at": _utc_now_iso(),
        }
        return self._insert_and_return(
            """
            INSERT INTO applications (id, user_id, company, role, stage, next_step, job_url, notes, created_at)
            VALUES (:id, :user_id, :company, :role, :stage, :next_step, :job_url, :notes, :created_at)
            RETURNING id, user_id, company, role, stage, next_step, job_url, notes, created_at
            """,
            payload,
        )

    def list_applications(
        self,
        *,
        user_id: str,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id, user_id, company, role, stage, next_step, job_url, notes, created_at
            FROM applications
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {"user_id": user_id, "limit": limit},
        )

    def save_note(
        self,
        *,
        user_id: str,
        title: str,
        content: str,
        tags: list[str] | None = None,
    ) -> dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "content": content,
            "tags_json": json.dumps(tags or []),
            "created_at": _utc_now_iso(),
        }
        return self._insert_and_return(
            """
            INSERT INTO notes (id, user_id, title, content, tags_json, created_at)
            VALUES (:id, :user_id, :title, :content, :tags_json, :created_at)
            RETURNING id, user_id, title, content, tags_json, created_at
            """,
            payload,
        )

    def list_notes(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id, user_id, title, content, tags_json, created_at
            FROM notes
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {"user_id": user_id, "limit": limit},
        )

    def schedule_event(
        self,
        *,
        user_id: str,
        title: str,
        event_date: str,
        event_time: str | None = None,
        description: str | None = None,
    ) -> dict[str, Any]:
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": title,
            "event_date": event_date,
            "event_time": event_time,
            "description": description,
            "created_at": _utc_now_iso(),
        }
        return self._insert_and_return(
            """
            INSERT INTO events (id, user_id, title, event_date, event_time, description, created_at)
            VALUES (:id, :user_id, :title, :event_date, :event_time, :description, :created_at)
            RETURNING id, user_id, title, event_date, event_time, description, created_at
            """,
            payload,
        )

    def list_events(self, *, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        return self._fetch_all(
            """
            SELECT id, user_id, title, event_date, event_time, description, created_at
            FROM events
            WHERE user_id = :user_id
            ORDER BY created_at DESC
            LIMIT :limit
            """,
            {"user_id": user_id, "limit": limit},
        )


@lru_cache(maxsize=1)
def get_storage() -> BaseRepository:
    requested_backend = os.getenv("DATA_BACKEND", "").strip().lower()

    if requested_backend in {"json", "file"}:
        return JsonFileRepository(Path(os.getenv("LOCAL_DATA_FILE", "data/local_data.json")))

    alloydb_instance_uri = os.getenv("ALLOYDB_INSTANCE_URI")
    alloydb_db = os.getenv("ALLOYDB_DB")
    alloydb_user = os.getenv("ALLOYDB_USER")
    alloydb_password = os.getenv("ALLOYDB_PASSWORD")
    alloydb_ip_type = os.getenv("ALLOYDB_IP_TYPE", "PRIVATE")
    alloydb_enable_iam_auth = os.getenv("ALLOYDB_ENABLE_IAM_AUTH", "false").lower() == "true"
    alloydb_refresh_strategy = os.getenv("ALLOYDB_REFRESH_STRATEGY", "lazy")

    if requested_backend == "alloydb":
        missing = [
            name
            for name, value in {
                "ALLOYDB_INSTANCE_URI": alloydb_instance_uri,
                "ALLOYDB_DB": alloydb_db,
                "ALLOYDB_USER": alloydb_user,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(
                "DATA_BACKEND=alloydb requires these environment variables: "
                + ", ".join(missing)
            )
        return AlloyDbRepository(
            instance_uri=alloydb_instance_uri,
            database=alloydb_db,
            user=alloydb_user,
            password=alloydb_password,
            ip_type=alloydb_ip_type,
            enable_iam_auth=alloydb_enable_iam_auth,
            refresh_strategy=alloydb_refresh_strategy,
        )

    if alloydb_instance_uri and alloydb_db and alloydb_user:
        try:
            return AlloyDbRepository(
                instance_uri=alloydb_instance_uri,
                database=alloydb_db,
                user=alloydb_user,
                password=alloydb_password,
                ip_type=alloydb_ip_type,
                enable_iam_auth=alloydb_enable_iam_auth,
                refresh_strategy=alloydb_refresh_strategy,
            )
        except Exception:
            pass

    return JsonFileRepository(Path(os.getenv("LOCAL_DATA_FILE", "data/local_data.json")))
