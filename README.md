# Lab MCP SQLite với FastMCP

**Họ và tên:** Vũ Văn Huy  
**Mã học viên:** 2A202600750

## 1. Giới thiệu

Dự án này xây dựng một MCP server bằng Python, sử dụng FastMCP và SQLite. Server cung cấp một cơ sở dữ liệu nhỏ cho MCP client thông qua 3 tool bắt buộc:

- `search`
- `insert`
- `aggregate`

Server cũng cung cấp schema của database thông qua MCP resources:

- `schema://database`
- `schema://table/{table_name}`

Dataset demo gồm 3 bảng:

- `students`
- `courses`
- `enrollments`

## 2. Cấu trúc dự án

```text
implementation/
  __init__.py
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  tests/
    test_server.py

client_configs/
  codex_config.example.toml
  claude_mcp.example.json

deliverables/
  screenshots/
  verify_output.txt
```

Trong đó:

- `implementation/db.py`: xử lý SQLite, validate table/column/operator và build query an toàn.
- `implementation/init_db.py`: tạo database và seed dữ liệu mẫu.
- `implementation/mcp_server.py`: khai báo FastMCP server, tools và resources.
- `implementation/verify_server.py`: smoke test MCP server bằng FastMCP client.
- `implementation/tests/test_server.py`: test tự động bằng `pytest`.
- `client_configs/`: ví dụ cấu hình MCP client.
- `deliverables/`: ảnh chụp Inspector và output kiểm chứng.

## 3. Setup môi trường

Yêu cầu:

- Python 3.10 trở lên
- `pip`
- Node.js và `npx` nếu dùng MCP Inspector
- Codex, Claude Code hoặc một MCP client tương đương để demo client integration

Tạo virtual environment trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Nếu PowerShell chặn activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 4. Khởi tạo database

```powershell
python implementation\init_db.py
```

Lệnh này tạo file SQLite tại:

```text
implementation/data/lab.db
```

File database sinh ra được ignore bằng `.gitignore`, vì vậy có thể chạy lại script để reset dữ liệu seed.

## 5. Chạy MCP server

```powershell
python implementation\mcp_server.py
```

Server chạy bằng STDIO mặc định, phù hợp với Codex, Claude Code, Gemini CLI và MCP Inspector.

## 6. Mô tả tools

### `search`

Tìm kiếm dữ liệu trong một bảng hợp lệ.

Input chính:

- `table`: tên bảng.
- `filters`: object hoặc list filters.
- `columns`: list columns hoặc comma string.
- `limit`: giới hạn số dòng, tối đa 100.
- `offset`: vị trí bắt đầu để phân trang.
- `order_by`: cột dùng để sắp xếp.
- `descending`: sắp xếp giảm dần nếu bằng `true`.

Ví dụ:

```json
{
  "table": "students",
  "filters": { "cohort": "A1" },
  "columns": ["name", "cohort", "score"],
  "order_by": "score",
  "descending": true,
  "limit": 3
}
```

### `insert`

Thêm một dòng mới vào bảng hợp lệ. `values` không được rỗng và mọi column phải tồn tại trong schema.

Ví dụ:

```json
{
  "table": "students",
  "values": {
    "name": "Do Minh",
    "cohort": "A3",
    "email": "minh.do@example.com",
    "score": 84.0,
    "active": 1
  }
}
```

### `aggregate`

Tính toán aggregate trên một bảng hợp lệ.

Metric được hỗ trợ:

- `count`
- `avg`
- `sum`
- `min`
- `max`

Ví dụ:

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## 7. Validation và an toàn SQL

Implementation đã xử lý reject các request không hợp lệ:

- Table không tồn tại.
- Column không tồn tại.
- Filter operator không được hỗ trợ.
- Aggregate metric không hợp lệ.
- Aggregate thiếu column khi metric yêu cầu column.
- Insert rỗng.

Các giá trị trong filters và insert dùng SQLite placeholders `?`. Table, column, order và group identifiers được validate theo schema thật trước khi đưa vào SQL.

Filter operators được hỗ trợ:

```text
=, ==, eq, !=, <>, ne, <, lt, <=, lte, >, gt, >=, gte, like, in
```

## 8. Kiểm chứng nhanh

Chạy smoke verification:

```powershell
python implementation\verify_server.py
```

Script kiểm tra:

- Server khởi tạo được.
- 3 tools được discover.
- Schema resource được discover.
- Table schema template được discover.
- Đọc được `schema://database`.
- Đọc được `schema://table/students`.
- Valid `search` call thành công.
- Valid `insert` call thành công.
- Valid `aggregate` call thành công.
- Invalid `search` call trả lỗi rõ ràng.

## 9. Chạy test tự động

```powershell
pytest
```

Tests sử dụng database tạm trong `tmp_path`, nên không phụ thuộc vào database local.

## 10. Kiểm chứng bằng MCP Inspector

Lệnh mẫu trên Windows:

```powershell
npx -y @modelcontextprotocol/inspector python C:\Users\Admin\Desktop\CODE\VinAI\Week6\2A202600750-VuVanHuy-Day26\implementation\mcp_server.py
```

Trong Inspector cần kiểm chứng:

- Server hiển thị trạng thái `Connected`.
- Tools `search`, `insert`, `aggregate` xuất hiện.
- Resource `schema://database` xuất hiện.
- Resource template `schema://table/{table_name}` xuất hiện.
- Valid tool call trả kết quả đúng.
- Invalid tool call, ví dụ `{"table": "missing"}`, trả lỗi `unknown table`.

Ảnh chụp bằng chứng nằm trong:

```text
deliverables/screenshots/
```

## 11. Cấu hình Codex MCP client

Ví dụ cấu hình đã có tại:

```text
client_configs/codex_config.example.toml
```

Copy block trong file đó vào `~/.codex/config.toml`, hoặc `.codex/config.toml` nếu repo đã được Codex trust.

Repo cũng có `AGENTS.md` để hướng dẫn Codex dùng MCP server `sqlite_lab` khi cần schema hoặc lookup database.

Sau khi cấu hình, restart Codex hoặc mở session mới, rồi dùng `/mcp` trong TUI để xem server active. Có thể hỏi Codex:

```text
Use the sqlite_lab MCP server. Read schema://database, then search the top 2 students by score.
```

## 12. Cấu hình Claude Code

Ví dụ có tại:

```text
client_configs/claude_mcp.example.json
```

Claude Code có thể đọc resource bằng cú pháp tương tự:

```text
@sqlite-lab:schema://database
```

## 13. Checklist nộp bài

- [x] FastMCP server start thành công.
- [x] Cấu trúc project rõ ràng.
- [x] SQLite database có schema và seed data reproducible.
- [x] Code tách server logic và database logic.
- [x] `search` hỗ trợ filters, ordering, pagination.
- [x] `insert` hoạt động và trả payload đã insert.
- [x] `aggregate` hỗ trợ `count`, `avg`, `sum`, `min`, `max`.
- [x] Expose full database schema resource.
- [x] Expose per-table schema resource template.
- [x] Reject invalid table và column.
- [x] Reject unsupported operators và bad aggregate requests.
- [x] SQL dùng validation và parameterized values.
- [x] Tool discovery đã được verify.
- [x] Successful tool calls đã được verify.
- [x] Failing tool calls trả clear errors.
- [x] Có ví dụ cấu hình Codex MCP client.
- [x] Có hướng dẫn setup, test và demo.
- [x] Có command MCP Inspector.
- [x] Có screenshots/output kiểm chứng trong `deliverables/`.

