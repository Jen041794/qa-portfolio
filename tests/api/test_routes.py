"""
API Integration Tests — tests/api/
測試對象：Flask HTTP endpoints（不啟動真實 server，使用 test client）
涵蓋：正常流程、邊界條件、錯誤情境
"""
import pytest
from app.routes import app


@pytest.fixture()
def client():
    """每個測試函式都拿到全新的 app + client（隔離狀態）"""
    app.config["TESTING"] = True
    # 重置 service 狀態（讓每個測試獨立）
    from app import routes
    from app.services import TaskService
    routes.service = TaskService()
    with app.test_client() as client:
        yield client


# ═══════════════════════════════════════════════════════════════
# Health endpoint
# ═══════════════════════════════════════════════════════════════
class TestHealth:
    def test_returns_200(self, client):
        res = client.get("/health")
        assert res.status_code == 200

    def test_response_contains_status_ok(self, client):
        data = client.get("/health").get_json()
        assert data["status"] == "ok"

    def test_response_contains_version(self, client):
        data = client.get("/health").get_json()
        assert "version" in data


# ═══════════════════════════════════════════════════════════════
# POST /tasks  — 建立任務
# ═══════════════════════════════════════════════════════════════
class TestCreateTask:
    def test_create_returns_201(self, client):
        res = client.post("/tasks", json={"title": "Write unit tests"})
        assert res.status_code == 201

    def test_create_response_has_correct_fields(self, client):
        res = client.post("/tasks", json={"title": "Deploy app", "priority": "high"})
        data = res.get_json()
        assert data["title"] == "Deploy app"
        assert data["priority"] == "high"
        assert data["completed"] is False
        assert "id" in data
        assert "created_at" in data

    def test_create_without_title_returns_400(self, client):
        res = client.post("/tasks", json={"description": "No title"})
        assert res.status_code == 400
        assert "error" in res.get_json()

    def test_create_with_empty_body_returns_400(self, client):
        res = client.post("/tasks", data="not json", content_type="text/plain")
        assert res.status_code == 400

    def test_create_with_invalid_priority_returns_422(self, client):
        res = client.post("/tasks", json={"title": "X", "priority": "critical"})
        assert res.status_code == 422

    def test_create_with_whitespace_only_title_returns_400(self, client):
        res = client.post("/tasks", json={"title": "   "})
        assert res.status_code == 400

    @pytest.mark.parametrize("priority", ["low", "medium", "high"])
    def test_create_accepts_all_valid_priorities(self, client, priority):
        res = client.post("/tasks", json={"title": "Task", "priority": priority})
        assert res.status_code == 201
        assert res.get_json()["priority"] == priority


# ═══════════════════════════════════════════════════════════════
# GET /tasks  — 列表與篩選
# ═══════════════════════════════════════════════════════════════
class TestListTasks:
    @pytest.fixture(autouse=True)
    def seed(self, client):
        """建立測試資料"""
        self.client = client
        client.post("/tasks", json={"title": "Task 1"})
        client.post("/tasks", json={"title": "Task 2"})
        client.patch("/tasks/1", json={"completed": True})

    def test_list_returns_all_tasks(self):
        data = self.client.get("/tasks").get_json()
        assert len(data) == 2

    def test_filter_completed_true(self):
        data = self.client.get("/tasks?completed=true").get_json()
        assert len(data) == 1
        assert data[0]["completed"] is True

    def test_filter_completed_false(self):
        data = self.client.get("/tasks?completed=false").get_json()
        assert len(data) == 1
        assert data[0]["completed"] is False

    def test_empty_list_returns_empty_array(self):
        # 使用全新的 app + service，不受 seed fixture 影響
        from app import routes
        from app.services import TaskService
        routes.service = TaskService()
        app.config["TESTING"] = True
        with app.test_client() as fresh_client:
            data = fresh_client.get("/tasks").get_json()
        assert data == []


# ═══════════════════════════════════════════════════════════════
# GET /tasks/<id>  — 單筆查詢
# ═══════════════════════════════════════════════════════════════
class TestGetTask:
    def test_get_existing_task(self, client):
        client.post("/tasks", json={"title": "Find me"})
        res = client.get("/tasks/1")
        assert res.status_code == 200
        assert res.get_json()["title"] == "Find me"

    def test_get_nonexistent_task_returns_404(self, client):
        res = client.get("/tasks/999")
        assert res.status_code == 404
        assert "error" in res.get_json()


# ═══════════════════════════════════════════════════════════════
# PATCH /tasks/<id>  — 更新任務
# ═══════════════════════════════════════════════════════════════
class TestUpdateTask:
    @pytest.fixture(autouse=True)
    def seed(self, client):
        self.client = client
        client.post("/tasks", json={"title": "Original"})

    def test_update_title(self):
        res = self.client.patch("/tasks/1", json={"title": "Updated"})
        assert res.status_code == 200
        assert res.get_json()["title"] == "Updated"

    def test_mark_as_completed(self):
        res = self.client.patch("/tasks/1", json={"completed": True})
        assert res.get_json()["completed"] is True

    def test_update_nonexistent_returns_404(self):
        res = self.client.patch("/tasks/999", json={"title": "Ghost"})
        assert res.status_code == 404

    def test_update_invalid_priority_returns_422(self):
        res = self.client.patch("/tasks/1", json={"priority": "extreme"})
        assert res.status_code == 422

    def test_partial_update_does_not_reset_other_fields(self):
        self.client.patch("/tasks/1", json={"priority": "high"})
        data = self.client.get("/tasks/1").get_json()
        assert data["title"] == "Original"   # 不受影響
        assert data["priority"] == "high"


# ═══════════════════════════════════════════════════════════════
# DELETE /tasks/<id>
# ═══════════════════════════════════════════════════════════════
class TestDeleteTask:
    def test_delete_returns_204(self, client):
        client.post("/tasks", json={"title": "Bye"})
        res = client.delete("/tasks/1")
        assert res.status_code == 204

    def test_deleted_task_is_gone(self, client):
        client.post("/tasks", json={"title": "Bye"})
        client.delete("/tasks/1")
        assert client.get("/tasks/1").status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        res = client.delete("/tasks/999")
        assert res.status_code == 404


# ═══════════════════════════════════════════════════════════════
# GET /tasks/stats
# ═══════════════════════════════════════════════════════════════
class TestStats:
    def test_stats_keys(self, client):
        data = client.get("/tasks/stats").get_json()
        assert "total" in data
        assert "completed" in data
        assert "pending" in data
        assert "by_priority" in data

    def test_stats_accuracy(self, client):
        client.post("/tasks", json={"title": "A", "priority": "high"})
        client.post("/tasks", json={"title": "B", "priority": "low"})
        client.patch("/tasks/1", json={"completed": True})

        data = client.get("/tasks/stats").get_json()
        assert data["total"] == 2
        assert data["completed"] == 1
        assert data["pending"] == 1
        assert data["by_priority"]["high"] == 1
