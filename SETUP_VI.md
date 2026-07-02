# Hướng dẫn setup Lab MCP SQLite

**Họ và tên:** Vũ Văn Huy  
**Mã học viên:** 2A202600750

Tài liệu này mô tả cách chuẩn bị môi trường, chạy project, kiểm thử MCP server và kiểm chứng trước khi nộp bài.

## 1. Mục tiêu lab

Xây dựng một MCP server bằng Python, sử dụng FastMCP và SQLite. Server cần expose:

- 3 MCP tools: `search`, `insert`, `aggregate`.
- 1 resource đọc schema toàn bộ database: `schema://database`.
- 1 dynamic resource template đọc schema từng bảng: `schema://table/{table_name}`.
- Validation để chặn request không an toàn hoặc không hợp lệ.
- Quy trình verify bằng MCP Inspector hoặc MCP client tương đương.
- Ví dụ cấu hình ít nhất một MCP client như Codex, Claude Code hoặc Gemini CLI.

## 2. Cấu trúc project

```text
implementation/
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  tests/
    test_server.py
```

Ý nghĩa các file:

- `mcp_server.py`: khai báo FastMCP server, tools và resources.
- `db.py`: xử lý kết nối SQLite, validate table/column và build query an toàn.
- `init_db.py`: tạo database và seed dữ liệu mẫu.
- `verify_server.py`: smoke test để kiểm tra server, tools và resources.
- `tests/`: test tự động bằng `pytest`.

## 3. Điều kiện môi trường

Cần cài:

- Python 3.10 trở lên.
- `pip`.
- Node.js và `npx` nếu muốn dùng MCP Inspector.
- Một MCP client để demo, ví dụ Codex, Claude Code hoặc Gemini CLI.

Kiểm tra nhanh:

```powershell
python --version
pip --version
node --version
npx --version
```

## 4. Tạo virtual environment

Trên Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Nếu PowerShell chặn activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Trên macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 5. Cài dependencies

Project dùng các dependencies trong `requirements.txt`:

```text
fastmcp
pytest
```

Cài bằng:

```powershell
pip install -r requirements.txt
```

## 6. Khởi tạo database

Chạy:

```powershell
python implementation\init_db.py
```

Kết quả mong đợi:

- Tạo file SQLite tại `implementation\data\lab.db`.
- Tạo các bảng `students`, `courses`, `enrollments`.
- Seed sẵn dữ liệu mẫu để demo.

## 7. Chạy MCP server

```powershell
python implementation\mcp_server.py
```

Server chạy STDIO mặc định để kết nối dễ với MCP clients.

## 8. Verify bằng script

```powershell
python implementation\verify_server.py
```

Script này kiểm tra:

- Server start được.
- 3 tools `search`, `insert`, `aggregate` discover được.
- Resource `schema://database` discover được.
- Resource template `schema://table/{table_name}` discover được.
- Valid tool calls chạy thành công.
- Invalid tool call trả lỗi rõ ràng.

## 9. Chạy test tự động

```powershell
pytest
```

Kết quả đã verify:

```text
9 passed
```

## 10. Verify bằng MCP Inspector

Ví dụ trên Windows:

```powershell
npx -y @modelcontextprotocol/inspector python C:\ABSOLUTE\PATH\TO\implementation\mcp_server.py
```

Trong Inspector cần chụp hoặc ghi lại:

- Server kết nối thành công.
- Tools `search`, `insert`, `aggregate` hiển thị.
- Resource `schema://database` hiển thị.
- Resource template `schema://table/{table_name}` đọc được.
- Valid tool call trả kết quả đúng.
- Invalid tool call trả lỗi rõ ràng.

Ảnh chụp đã lưu tại:

```text
deliverables/screenshots/
```

## 11. Ví dụ cấu hình MCP client

### Codex

Ví dụ trong `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "python"
args = ["C:/ABSOLUTE/PATH/TO/implementation/mcp_server.py"]
cwd = "C:/ABSOLUTE/PATH/TO/PROJECT"
startup_timeout_sec = 10
tool_timeout_sec = 60
enabled = true
```

Project đã có file ví dụ:

```text
client_configs/codex_config.example.toml
```

### Claude Code

File `.mcp.json` ví dụ:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "python",
      "args": ["C:/ABSOLUTE/PATH/TO/implementation/mcp_server.py"],
      "env": {}
    }
  }
}
```

Project đã có file ví dụ:

```text
client_configs/claude_mcp.example.json
```

## 12. Checklist trước khi nộp

- [x] FastMCP server start được.
- [x] Project structure rõ ràng.
- [x] SQLite database có schema và seed data reproducible.
- [x] Code tách server logic và database logic.
- [x] Có `search`, `insert`, `aggregate`.
- [x] `search` có filters, ordering, pagination.
- [x] `insert` trả về payload đã insert.
- [x] `aggregate` hỗ trợ các metric cơ bản.
- [x] Expose full schema resource.
- [x] Expose per-table schema resource template.
- [x] Reject table/column/operator/aggregate không hợp lệ.
- [x] SQL dùng parameterized query khi có user input.
- [x] Có verify tool discovery.
- [x] Có verify valid calls và invalid calls.
- [x] Có ví dụ cấu hình MCP client.
- [x] Có README/setup docs với bước setup/test/demo.
- [x] Có screenshots/output kiểm chứng.

## 13. Lưu ý an toàn SQL

Không build SQL bằng cách nối trực tiếp raw input vào query. Implementation hiện tại:

- Validate table name theo danh sách table thật.
- Validate column name theo schema thật.
- Chỉ cho phép operator nằm trong allowlist.
- Dùng placeholder `?` cho values trong SQLite.
- Giới hạn `limit` để tránh output quá lớn.

