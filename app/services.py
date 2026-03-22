from typing import Optional
from app.models import Task


class TaskService:
    """Business logic layer for Task management."""

    def __init__(self):
        self._tasks: dict[int, Task] = {}
        self._next_id: int = 1

    def get_all(self, completed: Optional[bool] = None) -> list[Task]:
        tasks = list(self._tasks.values())
        if completed is not None:
            tasks = [t for t in tasks if t.completed == completed]
        return tasks

    def get_by_id(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def create(self, title: str, description: str = "", priority: str = "medium") -> Task:
        if not Task.validate_title(title):
            raise ValueError("Title must be between 1 and 100 characters.")
        if not Task.validate_priority(priority):
            raise ValueError(f"Priority must be one of: low, medium, high.")

        task = Task(
            id=self._next_id,
            title=title.strip(),
            description=description,
            priority=priority,
        )
        self._tasks[self._next_id] = task
        self._next_id += 1
        return task

    def update(self, task_id: int, **kwargs) -> Optional[Task]:
        task = self._tasks.get(task_id)
        if not task:
            return None

        if "title" in kwargs:
            if not Task.validate_title(kwargs["title"]):
                raise ValueError("Title must be between 1 and 100 characters.")
            task.title = kwargs["title"].strip()

        if "description" in kwargs:
            task.description = kwargs["description"]

        if "priority" in kwargs:
            if not Task.validate_priority(kwargs["priority"]):
                raise ValueError("Priority must be one of: low, medium, high.")
            task.priority = kwargs["priority"]

        if "completed" in kwargs:
            task.completed = bool(kwargs["completed"])

        return task

    def delete(self, task_id: int) -> bool:
        if task_id not in self._tasks:
            return False
        del self._tasks[task_id]
        return True

    def get_stats(self) -> dict:
        all_tasks = list(self._tasks.values())
        return {
            "total": len(all_tasks),
            "completed": sum(1 for t in all_tasks if t.completed),
            "pending": sum(1 for t in all_tasks if not t.completed),
            "by_priority": {
                "high": sum(1 for t in all_tasks if t.priority == "high"),
                "medium": sum(1 for t in all_tasks if t.priority == "medium"),
                "low": sum(1 for t in all_tasks if t.priority == "low"),
            },
        }
