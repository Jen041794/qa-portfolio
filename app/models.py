from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    description: str
    completed: bool = False
    priority: str = "medium"  # low, medium, high
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "completed": self.completed,
            "priority": self.priority,
            "created_at": self.created_at,
        }

    @staticmethod
    def validate_priority(priority: str) -> bool:
        return priority in ("low", "medium", "high")

    @staticmethod
    def validate_title(title: str) -> bool:
        return isinstance(title, str) and 1 <= len(title.strip()) <= 100
