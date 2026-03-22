"""
Unit Tests — app/models.py & app/services.py
測試對象：純商業邏輯，不啟動 HTTP server
"""
import pytest
from app.models import Task
from app.services import TaskService


# ═══════════════════════════════════════════════════════════════
# Task Model
# ═══════════════════════════════════════════════════════════════
class TestTaskModel:
    def test_to_dict_contains_all_fields(self):
        task = Task(id=1, title="Buy milk", description="2% fat")
        d = task.to_dict()
        assert set(d.keys()) == {"id", "title", "description", "completed", "priority", "created_at"}

    def test_default_values(self):
        task = Task(id=1, title="Test", description="")
        assert task.completed is False
        assert task.priority == "medium"
        assert task.created_at is not None

    # ── validate_priority ─────────────────────────────────────
    @pytest.mark.parametrize("priority", ["low", "medium", "high"])
    def test_valid_priorities(self, priority):
        assert Task.validate_priority(priority) is True

    @pytest.mark.parametrize("priority", ["urgent", "", "HIGH", None, 123])
    def test_invalid_priorities(self, priority):
        assert Task.validate_priority(priority) is False

    # ── validate_title ────────────────────────────────────────
    @pytest.mark.parametrize("title", ["A", "Normal title", "x" * 100])
    def test_valid_titles(self, title):
        assert Task.validate_title(title) is True

    @pytest.mark.parametrize("title", ["", "  ", "x" * 101, 123, None])
    def test_invalid_titles(self, title):
        assert Task.validate_title(title) is False


# ═══════════════════════════════════════════════════════════════
# TaskService — CRUD
# ═══════════════════════════════════════════════════════════════
class TestTaskServiceCreate:
    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = TaskService()

    def test_create_returns_task_with_id(self):
        task = self.svc.create("Write tests", "pytest is great")
        assert task.id == 1
        assert task.title == "Write tests"

    def test_ids_are_incremented(self):
        t1 = self.svc.create("First")
        t2 = self.svc.create("Second")
        assert t2.id == t1.id + 1

    def test_create_strips_whitespace_from_title(self):
        task = self.svc.create("  Hello  ")
        assert task.title == "Hello"

    def test_create_with_default_priority(self):
        task = self.svc.create("Task")
        assert task.priority == "medium"

    def test_create_with_custom_priority(self):
        task = self.svc.create("Task", priority="high")
        assert task.priority == "high"

    def test_create_raises_on_empty_title(self):
        with pytest.raises(ValueError, match="Title"):
            self.svc.create("")

    def test_create_raises_on_invalid_priority(self):
        with pytest.raises(ValueError, match="Priority"):
            self.svc.create("Task", priority="critical")


class TestTaskServiceRead:
    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = TaskService()
        self.svc.create("Task A", priority="high")
        self.svc.create("Task B", priority="low")
        self.svc.update(1, completed=True)

    def test_get_all_returns_all_tasks(self):
        assert len(self.svc.get_all()) == 2

    def test_filter_completed(self):
        done = self.svc.get_all(completed=True)
        assert all(t.completed for t in done)
        assert len(done) == 1

    def test_filter_pending(self):
        pending = self.svc.get_all(completed=False)
        assert all(not t.completed for t in pending)

    def test_get_by_id_existing(self):
        task = self.svc.get_by_id(1)
        assert task is not None
        assert task.title == "Task A"

    def test_get_by_id_nonexistent(self):
        assert self.svc.get_by_id(999) is None


class TestTaskServiceUpdate:
    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = TaskService()
        self.svc.create("Original title")

    def test_update_title(self):
        updated = self.svc.update(1, title="New title")
        assert updated.title == "New title"

    def test_update_marks_completed(self):
        updated = self.svc.update(1, completed=True)
        assert updated.completed is True

    def test_update_nonexistent_returns_none(self):
        assert self.svc.update(999, title="X") is None

    def test_update_invalid_priority_raises(self):
        with pytest.raises(ValueError):
            self.svc.update(1, priority="ultra")

    def test_update_invalid_title_raises(self):
        with pytest.raises(ValueError):
            self.svc.update(1, title="")


class TestTaskServiceDelete:
    @pytest.fixture(autouse=True)
    def service(self):
        self.svc = TaskService()
        self.svc.create("To be deleted")

    def test_delete_existing_returns_true(self):
        assert self.svc.delete(1) is True

    def test_deleted_task_not_found(self):
        self.svc.delete(1)
        assert self.svc.get_by_id(1) is None

    def test_delete_nonexistent_returns_false(self):
        assert self.svc.delete(999) is False


class TestTaskServiceStats:
    def test_stats_structure(self):
        svc = TaskService()
        svc.create("A", priority="high")
        svc.create("B", priority="low")
        svc.update(1, completed=True)

        stats = svc.get_stats()
        assert stats["total"] == 2
        assert stats["completed"] == 1
        assert stats["pending"] == 1
        assert stats["by_priority"]["high"] == 1
        assert stats["by_priority"]["low"] == 1

    def test_empty_stats(self):
        svc = TaskService()
        stats = svc.get_stats()
        assert stats["total"] == 0
