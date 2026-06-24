import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

DB_PATH = Path("tasks.db")


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(lifespan=lifespan)


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            quadrant TEXT,
            due_date TEXT,
            created_at TEXT NOT NULL,
            completed INTEGER NOT NULL DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            archived INTEGER NOT NULL DEFAULT 0
        )
    """)
    try:
        conn.execute("ALTER TABLE tasks ADD COLUMN project_id INTEGER")
    except Exception:
        pass
    conn.commit()
    conn.close()


class TaskCreate(BaseModel):
    text: str
    due_date: Optional[str] = None


class TaskUpdate(BaseModel):
    text: Optional[str] = None
    quadrant: Optional[str] = None
    due_date: Optional[str] = None
    project_id: Optional[int] = None  # 0 = clear to null


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    archived: Optional[int] = None


@app.get("/tasks")
def list_tasks():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE completed = 0 ORDER BY due_date IS NULL, due_date ASC, created_at ASC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/tasks", status_code=201)
def create_task(body: TaskCreate):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO tasks (text, due_date, created_at) VALUES (?, ?, ?)",
        (body.text, body.due_date, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.patch("/tasks/{task_id}")
def update_task(task_id: int, body: TaskUpdate):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")

    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    raw = body.model_dump()
    for key in ("quadrant", "due_date"):
        if raw[key] == "":
            fields[key] = None
    if raw.get("project_id") == 0:
        fields["project_id"] = None

    if fields:
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE tasks SET {set_clause} WHERE id = ?",
            (*fields.values(), task_id),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return dict(row)


@app.get("/tasks/completed")
def list_completed_tasks():
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM tasks WHERE completed = 1 ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.patch("/tasks/{task_id}/complete")
def complete_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.patch("/tasks/{task_id}/uncomplete")
def uncomplete_task(task_id: int):
    conn = get_db()
    task = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    if not task:
        conn.close()
        raise HTTPException(status_code=404, detail="Task not found")
    conn.execute("UPDATE tasks SET completed = 0 WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return {"ok": True}


@app.get("/projects")
def list_projects(include_archived: bool = False):
    conn = get_db()
    if include_archived:
        rows = conn.execute("SELECT * FROM projects ORDER BY created_at ASC").fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM projects WHERE archived = 0 ORDER BY created_at ASC"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


@app.post("/projects", status_code=201)
def create_project(body: ProjectCreate):
    now = datetime.now(timezone.utc).isoformat()
    conn = get_db()
    cur = conn.execute(
        "INSERT INTO projects (name, created_at) VALUES (?, ?)",
        (body.name, now),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return dict(row)


@app.patch("/projects/{project_id}")
def update_project(project_id: int, body: ProjectUpdate):
    conn = get_db()
    project = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    if not project:
        conn.close()
        raise HTTPException(status_code=404, detail="Project not found")

    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    if fields:
        set_clause = ", ".join(f"{k} = ?" for k in fields)
        conn.execute(
            f"UPDATE projects SET {set_clause} WHERE id = ?",
            (*fields.values(), project_id),
        )
        conn.commit()

    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return dict(row)


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
