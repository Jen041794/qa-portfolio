"""
E2E Tests — tests/e2e/
測試對象：真實啟動的 Flask server（localhost:5000）
工具：Playwright (pytest-playwright)

執行前請先啟動 server：
    python run.py
然後執行：
    pytest tests/e2e/ -v
"""
import re
import pytest
import requests
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:5000"


@pytest.fixture(autouse=True)
def reset_server():
    """每個 E2E 測試前，透過直接呼叫 service 重置資料（或重啟 server）"""
    # 此處用 requests 確認 server 是否在線
    try:
        requests.get(f"{BASE_URL}/health", timeout=2)
    except Exception:
        pytest.skip("Flask server is not running. Start it with: python run.py")
    yield


# ═══════════════════════════════════════════════════════════════
# API smoke tests via real HTTP（不需要瀏覽器）
# ═══════════════════════════════════════════════════════════════
class TestE2ESmoke:
    """真實 HTTP 請求的 E2E smoke test（驗證部署後端正常）"""

    def test_health_check(self):
        res = requests.get(f"{BASE_URL}/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_full_task_lifecycle(self):
        """建立 → 讀取 → 更新 → 刪除 的完整流程"""
        # 建立
        create_res = requests.post(
            f"{BASE_URL}/tasks",
            json={"title": "E2E Test Task", "priority": "high"},
        )
        assert create_res.status_code == 201
        task_id = create_res.json()["id"]

        # 讀取
        get_res = requests.get(f"{BASE_URL}/tasks/{task_id}")
        assert get_res.status_code == 200
        assert get_res.json()["title"] == "E2E Test Task"

        # 更新（完成任務）
        patch_res = requests.patch(
            f"{BASE_URL}/tasks/{task_id}", json={"completed": True}
        )
        assert patch_res.status_code == 200
        assert patch_res.json()["completed"] is True

        # 驗證 stats 更新
        stats_res = requests.get(f"{BASE_URL}/tasks/stats")
        assert stats_res.json()["completed"] >= 1

        # 刪除
        delete_res = requests.delete(f"{BASE_URL}/tasks/{task_id}")
        assert delete_res.status_code == 204

        # 確認已刪除
        assert requests.get(f"{BASE_URL}/tasks/{task_id}").status_code == 404

    def test_bulk_create_and_filter(self):
        """批次建立多個任務並驗證篩選功能"""
        tasks = [
            {"title": "High priority task", "priority": "high"},
            {"title": "Low priority task", "priority": "low"},
            {"title": "Another task", "priority": "medium"},
        ]
        created_ids = []
        for t in tasks:
            res = requests.post(f"{BASE_URL}/tasks", json=t)
            assert res.status_code == 201
            created_ids.append(res.json()["id"])

        # 完成第一個
        requests.patch(f"{BASE_URL}/tasks/{created_ids[0]}", json={"completed": True})

        # 篩選未完成
        pending = requests.get(f"{BASE_URL}/tasks?completed=false").json()
        pending_ids = [t["id"] for t in pending]
        assert created_ids[0] not in pending_ids
        assert created_ids[1] in pending_ids

        # 清理
        for tid in created_ids:
            requests.delete(f"{BASE_URL}/tasks/{tid}")

    def test_error_handling_end_to_end(self):
        """驗證 API 錯誤回應格式一致"""
        cases = [
            (requests.get(f"{BASE_URL}/tasks/99999"), 404),
            (requests.delete(f"{BASE_URL}/tasks/99999"), 404),
            (requests.post(f"{BASE_URL}/tasks", json={}), 400),
            (requests.post(f"{BASE_URL}/tasks", json={"title": "X", "priority": "bad"}), 422),
        ]
        for res, expected_status in cases:
            assert res.status_code == expected_status
            body = res.json()
            assert "error" in body, f"Missing 'error' key for status {expected_status}"


# ═══════════════════════════════════════════════════════════════
# Browser-based E2E（需要前端，示範 Playwright Page API）
# ═══════════════════════════════════════════════════════════════
class TestE2EBrowser:
    """
    若有前端頁面可瀏覽，Playwright 會自動操控瀏覽器。
    此處以 API 回傳的 JSON 頁面為示範（無需額外 UI）。
    """

    def test_tasks_endpoint_returns_json_array(self, page: Page):
        page.goto(f"{BASE_URL}/tasks")
        content = page.locator("body").inner_text()
        # JSON array 必定以 [ 開頭
        assert content.strip().startswith("[")

    def test_health_page_shows_ok_status(self, page: Page):
        page.goto(f"{BASE_URL}/health")
        content = page.locator("body").inner_text()
        assert "ok" in content.lower()
