from flask import Flask, jsonify, request
from app.services import TaskService

app = Flask(__name__)
service = TaskService()


def error_response(message: str, status: int):
    return jsonify({"error": message}), status


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return jsonify({"status": "ok", "version": "1.0.0"})


# ── Tasks ─────────────────────────────────────────────────────────────────────
@app.get("/tasks")
def list_tasks():
    completed_param = request.args.get("completed")
    completed_filter = None
    if completed_param is not None:
        completed_filter = completed_param.lower() == "true"
    tasks = service.get_all(completed=completed_filter)
    return jsonify([t.to_dict() for t in tasks])


@app.get("/tasks/<int:task_id>")
def get_task(task_id: int):
    task = service.get_by_id(task_id)
    if not task:
        return error_response("Task not found", 404)
    return jsonify(task.to_dict())


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    title = data.get("title", "").strip()
    if not title:
        return error_response("Field 'title' is required", 400)

    try:
        task = service.create(
            title=title,
            description=data.get("description", ""),
            priority=data.get("priority", "medium"),
        )
    except ValueError as e:
        return error_response(str(e), 422)

    return jsonify(task.to_dict()), 201


@app.patch("/tasks/<int:task_id>")
def update_task(task_id: int):
    data = request.get_json(silent=True)
    if not data:
        return error_response("Request body must be JSON", 400)

    try:
        task = service.update(task_id, **data)
    except ValueError as e:
        return error_response(str(e), 422)

    if not task:
        return error_response("Task not found", 404)
    return jsonify(task.to_dict())


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id: int):
    if not service.delete(task_id):
        return error_response("Task not found", 404)
    return "", 204


# ── Stats ─────────────────────────────────────────────────────────────────────
@app.get("/tasks/stats")
def stats():
    return jsonify(service.get_stats())
