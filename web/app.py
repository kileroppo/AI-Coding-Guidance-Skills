"""FastAPI web dashboard for the self-evolving AI kernel.

Provides a single-page dashboard with real-time monitoring,
SSE log streaming, and WebSocket state broadcasts.
"""

import asyncio
import json
import threading
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, StreamingResponse
from pydantic import BaseModel

KERNEL_ROOT = Path(__file__).resolve().parent.parent


def create_app(kernel_root: Path | None = None) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        kernel_root: Path to the project root. Defaults to parent of web/.

    Returns:
        Configured FastAPI app instance.
    """
    if kernel_root is None:
        kernel_root = KERNEL_ROOT

    kernel_root = Path(kernel_root)

    app = FastAPI(title="AI Kernel Dashboard")

    # Shared state for execution control
    app.state.kernel_root = kernel_root
    app.state.stop_flag = threading.Event()
    app.state.running = False
    app.state.log_subscribers: list[asyncio.Queue] = []
    app.state.ws_connections: list[WebSocket] = []

    class GoalRequest(BaseModel):
        goal: str

    class StartRequest(BaseModel):
        goal: str = ""
        max_iterations: int = 30

    def _read_yaml(path: Path) -> Any:
        """Read a YAML file, return empty dict/list on failure."""
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                return data if data is not None else {}
        except (OSError, yaml.YAMLError):
            pass
        return {}

    def _read_jsonl(path: Path, limit: int | None = None) -> list[dict]:
        """Read a JSONL file, return list of dicts. Optionally limit to last N."""
        items: list[dict] = []
        try:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                items.append(json.loads(line))
                            except json.JSONDecodeError:
                                continue
        except OSError:
            pass
        if limit is not None:
            return items[-limit:]
        return items

    @app.get("/", response_class=HTMLResponse)
    async def dashboard():
        """Serve the dashboard HTML page."""
        template_path = kernel_root / "web" / "templates" / "dashboard.html"
        try:
            content = template_path.read_text(encoding="utf-8")
            return HTMLResponse(content=content)
        except (OSError, FileNotFoundError):
            return HTMLResponse(content="<h1>Dashboard template not found</h1>", status_code=500)

    @app.get("/api/state")
    async def get_state():
        """Return current kernel state from kernel/state.yaml."""
        state_path = kernel_root / "kernel" / "state.yaml"
        data = _read_yaml(state_path)
        return data

    @app.get("/api/tasks")
    async def get_tasks():
        """Return tasks from memory/tasks.yaml."""
        tasks_path = kernel_root / "memory" / "tasks.yaml"
        data = _read_yaml(tasks_path)
        if isinstance(data, dict):
            return data.get("tasks", [])
        if isinstance(data, list):
            return data
        return []

    @app.get("/api/history")
    async def get_history():
        """Return evolution history from kernel/evolution/history.jsonl."""
        history_path = kernel_root / "kernel" / "evolution" / "history.jsonl"
        return _read_jsonl(history_path)

    @app.get("/api/reflections")
    async def get_reflections():
        """Return recent reflections from memory/reflections.jsonl (last 50)."""
        reflections_path = kernel_root / "memory" / "reflections.jsonl"
        return _read_jsonl(reflections_path, limit=50)

    @app.get("/api/skills")
    async def get_skills():
        """Return skill list from skills/_index.yaml."""
        skills_path = kernel_root / "skills" / "_index.yaml"
        data = _read_yaml(skills_path)
        if isinstance(data, dict):
            return data.get("items", [])
        return []

    @app.post("/api/goal")
    async def set_goal(request: GoalRequest):
        """Set a new goal - writes to state and memory/current_goal.md."""
        if not request.goal.strip():
            return {"error": "Goal cannot be empty"}

        # Update state.yaml
        state_path = kernel_root / "kernel" / "state.yaml"
        state_data = _read_yaml(state_path)
        if not isinstance(state_data, dict):
            state_data = {}
        state_data["goal"] = request.goal.strip()

        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(state_data, f, default_flow_style=False, allow_unicode=True)

        # Write current_goal.md
        memory_dir = kernel_root / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        goal_path = memory_dir / "current_goal.md"
        with open(goal_path, "w", encoding="utf-8") as f:
            f.write(f"# Current Goal\n\n{request.goal.strip()}\n")

        # Broadcast via WebSocket
        await _broadcast_ws({"type": "goal_updated", "goal": request.goal.strip()})

        return {"status": "ok", "goal": request.goal.strip()}

    @app.post("/api/start")
    async def start_execution(request: StartRequest):
        """Start kernel execution in a background thread."""
        if app.state.running:
            return {"status": "already_running"}

        app.state.stop_flag.clear()
        app.state.running = True

        goal = request.goal.strip()
        max_iterations = request.max_iterations

        def _run_kernel():
            try:
                _emit_log(f"Starting kernel with goal: {goal}, max_iterations: {max_iterations}")
                # Simulate execution by reading state
                state_path = kernel_root / "kernel" / "state.yaml"
                state_data = _read_yaml(state_path)
                if not isinstance(state_data, dict):
                    state_data = {}

                if goal:
                    state_data["goal"] = goal
                state_data["status"] = "running"
                state_data["max_iterations"] = max_iterations

                state_path.parent.mkdir(parents=True, exist_ok=True)
                with open(state_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(state_data, f, default_flow_style=False, allow_unicode=True)

                _emit_log("Kernel execution started")

                for i in range(max_iterations):
                    if app.state.stop_flag.is_set():
                        _emit_log("Execution stopped by user")
                        break
                    _emit_log(f"Iteration {i + 1}/{max_iterations}")
                    # In a real implementation this would invoke the runner
                    # For now, just mark as idle after one pass
                    break

                state_data["status"] = "idle"
                with open(state_path, "w", encoding="utf-8") as f:
                    yaml.safe_dump(state_data, f, default_flow_style=False, allow_unicode=True)

                _emit_log("Kernel execution completed")
            except Exception as e:
                _emit_log(f"Error: {e}")
            finally:
                app.state.running = False

        thread = threading.Thread(target=_run_kernel, daemon=True)
        thread.start()

        return {"status": "started", "goal": goal, "max_iterations": max_iterations}

    @app.post("/api/stop")
    async def stop_execution():
        """Stop kernel execution."""
        if not app.state.running:
            return {"status": "not_running"}
        app.state.stop_flag.set()
        return {"status": "stopping"}

    @app.get("/api/logs")
    async def stream_logs():
        """SSE endpoint streaming execution logs."""
        queue: asyncio.Queue = asyncio.Queue()
        app.state.log_subscribers.append(queue)

        async def event_generator():
            try:
                # Send initial connection event
                yield "event: connected\ndata: {}\n\n"
                while True:
                    try:
                        message = await asyncio.wait_for(queue.get(), timeout=30.0)
                        yield f"data: {json.dumps(message)}\n\n"
                    except asyncio.TimeoutError:
                        # Send keepalive
                        yield ": keepalive\n\n"
            except asyncio.CancelledError:
                pass
            finally:
                if queue in app.state.log_subscribers:
                    app.state.log_subscribers.remove(queue)

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for real-time state change broadcasts."""
        await websocket.accept()
        app.state.ws_connections.append(websocket)
        try:
            # Send current state on connection
            state_path = kernel_root / "kernel" / "state.yaml"
            state_data = _read_yaml(state_path)
            await websocket.send_json({"type": "state", "data": state_data})

            while True:
                # Keep connection alive, listen for client messages
                data = await websocket.receive_text()
                # Echo back as acknowledgment
                await websocket.send_json({"type": "ack", "data": data})
        except WebSocketDisconnect:
            pass
        finally:
            if websocket in app.state.ws_connections:
                app.state.ws_connections.remove(websocket)

    def _emit_log(message: str):
        """Emit a log message to all SSE subscribers."""
        log_entry = {"message": message}
        for queue in list(app.state.log_subscribers):
            try:
                queue.put_nowait(log_entry)
            except asyncio.QueueFull:
                pass

    async def _broadcast_ws(data: dict):
        """Broadcast a message to all connected WebSocket clients."""
        disconnected = []
        for ws in list(app.state.ws_connections):
            try:
                await ws.send_json(data)
            except Exception:
                disconnected.append(ws)
        for ws in disconnected:
            if ws in app.state.ws_connections:
                app.state.ws_connections.remove(ws)

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=True)
