# Báo cáo Lab MCP SQLite

**Họ và tên:** Vũ Văn Huy  
**Mã học viên:** 2A202600750

## 1. Mục tiêu

Xây dựng MCP server bằng FastMCP kết nối SQLite, expose dữ liệu qua 3 tools `search`, `insert`, `aggregate`, đồng thời expose schema qua MCP resources.

## 2. Kết quả đã hoàn thành

- Đã xây dựng FastMCP server chạy bằng STDIO.
- Đã tạo SQLite database với schema và seed data reproducible.
- Đã implement `search`, `insert`, `aggregate`.
- Đã expose `schema://database`.
- Đã expose `schema://table/{table_name}`.
- Đã validate table, column, operator, aggregate request và insert rỗng.
- Đã dùng parameterized query cho user input.
- Đã viết smoke verification script.
- Đã viết test tự động bằng `pytest`.
- Đã chuẩn bị ví dụ cấu hình Codex MCP client.
- Đã chụp screenshot MCP Inspector và lưu trong `deliverables/screenshots/`.

## 3. Minh chứng kiểm thử

Lệnh smoke verification:

```powershell
python implementation\verify_server.py
```

Kết quả:

```text
All MCP verification checks passed.
```

Lệnh test tự động:

```powershell
pytest
```

Kết quả:

```text
9 passed
```

## 4. Minh chứng Inspector

Các file ảnh đã lưu:

- `deliverables/screenshots/04_inspector_noauth_connected.png`
- `deliverables/screenshots/05_resources_discovered.png`
- `deliverables/screenshots/06_schema_database_read.png`
- `deliverables/screenshots/08_search_tool_result.png`
- `deliverables/screenshots/09_invalid_table_error.png`
- `deliverables/screenshots/10_verify_server_output.png`

## 5. Checklist nộp bài

- [x] Server start được.
- [x] Tools discover được.
- [x] Resources discover được.
- [x] Valid tool calls chạy thành công.
- [x] Invalid tool calls trả lỗi rõ ràng.
- [x] Có setup instructions.
- [x] Có testing steps.
- [x] Có client configuration example.
- [x] Có screenshots/output làm minh chứng.

