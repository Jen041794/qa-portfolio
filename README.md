# QA Automation Portfolio — Task Manager API

> 一個展示 **軟體測試工程師** 核心能力的作品集專案。
> 包含自建 REST API、三層測試架構、覆蓋率報告與 CI/CD Pipeline。

---

## 📐 專案架構

```
qa-portfolio/
├── app/
│   ├── models.py        # 資料模型（Task dataclass）
│   ├── services.py      # 商業邏輯層（TaskService）
│   └── routes.py        # Flask HTTP 路由
│
├── tests/
│   ├── unit/
│   │   └── test_models_and_services.py   # 40 個 Unit Tests
│   ├── api/
│   │   └── test_routes.py                # 28 個 API Integration Tests
│   └── e2e/
│       └── test_e2e.py                   # E2E Smoke + Browser Tests
│
├── .github/
│   └── workflows/
│       └── qa-pipeline.yml   # CI/CD：Unit → API → E2E 循序執行
│
├── pyproject.toml       # pytest 設定、coverage 閾值
├── requirements.txt
└── run.py               # 啟動 Flask server
```

---

## 🧪 測試策略

### 測試金字塔

```
          /\
         /E2E\          ← 少量，驗證系統整合正常
        /──────\
       /  API   \       ← 中量，驗證 HTTP 行為與錯誤處理
      /──────────\
     /  Unit Test \     ← 大量，快速驗證商業邏輯
    ──────────────────
```

### 各層測試涵蓋重點

| 層級 | 工具 | 測試數 | 涵蓋重點 |
|------|------|--------|----------|
| Unit | pytest | 40 | Model 驗證、Service CRUD、邊界值、異常拋出 |
| API  | pytest + Flask test client | 28 | HTTP 狀態碼、回應格式、錯誤情境、篩選功能 |
| E2E  | pytest + requests + Playwright | 6 | 完整業務流程、跨請求狀態驗證、瀏覽器測試 |

---

## ⚡ 快速開始

```bash
# 1. 安裝依賴
pip install -r requirements.txt

# 2. 執行 Unit + API 測試（含 Coverage 報告）
pytest tests/unit/ tests/api/ --cov=app --cov-report=term-missing

# 3. 啟動 server 後執行 E2E
python run.py &
pytest tests/e2e/ -v

# 4. 執行全部測試
pytest -v
```

---

## 🌐 API 文件

Base URL: `http://localhost:5000`

| Method | Endpoint | 說明 |
|--------|----------|------|
| GET | `/health` | 健康檢查 |
| GET | `/tasks` | 列出所有任務（支援 `?completed=true/false` 篩選）|
| GET | `/tasks/<id>` | 取得單一任務 |
| POST | `/tasks` | 建立任務 |
| PATCH | `/tasks/<id>` | 更新任務（部分更新）|
| DELETE | `/tasks/<id>` | 刪除任務 |
| GET | `/tasks/stats` | 取得任務統計 |

### 建立任務範例

```bash
curl -X POST http://localhost:5000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "撰寫測試計畫", "priority": "high", "description": "涵蓋所有 API endpoints"}'
```

### 回應

```json
{
  "id": 1,
  "title": "撰寫測試計畫",
  "description": "涵蓋所有 API endpoints",
  "completed": false,
  "priority": "high",
  "created_at": "2024-01-15T09:30:00.000000"
}
```

---

## ✅ 測試成果

```
68 passed in 1.44s

Coverage Report:
Name              Stmts   Miss  Cover
-------------------------------------
app/models.py        19      0   100%
app/routes.py        56      1    98%
app/services.py      47      1    98%
-------------------------------------
TOTAL               122      2    98%
```

---

## 🔄 CI/CD Pipeline

每次 push 或 PR 自動觸發 GitHub Actions：

```
push/PR
  │
  ├── [Job 1] Unit Tests + Coverage ≥ 80%
  │         │  ✅ 通過才繼續
  ├── [Job 2] API Integration Tests
  │         │  ✅ 通過才繼續
  ├── [Job 3] E2E Tests（啟動真實 server）
  │
  └── [Job 4] Summary Report
```

---

## 🎯 測試設計亮點

1. **Fixture 隔離**：每個測試函式都有獨立的 Service 實例，避免測試間狀態汙染
2. **Parametrize**：用 `@pytest.mark.parametrize` 對邊界值做矩陣測試，減少重複程式碼
3. **分層驗證**：Unit 驗證邏輯、API 驗證 HTTP 行為、E2E 驗證完整業務流程
4. **錯誤情境涵蓋**：400 / 404 / 422 等錯誤路徑都有對應的 Test Case
5. **Coverage Gate**：CI 強制要求覆蓋率 ≥ 80%，目前達到 **98%**
