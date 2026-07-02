# SQLite FastMCP Lab Server

Project nay implement mot MCP server bang FastMCP de expose database SQLite nho qua 3 tools bat buoc:

- `search`
- `insert`
- `aggregate`

Server cung expose schema database qua MCP resources:

- `schema://database`
- `schema://table/{table_name}`

Dataset demo gom 3 bang: `students`, `courses`, `enrollments`.

## 1. Setup

Yeu cau:

- Python 3.10+ (da test voi Python 3.11)
- `pip`
- Node.js va `npx` neu dung MCP Inspector
- Codex, Claude Code, hoac MCP client khac neu muon demo client rieng

Tao virtual environment tren Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Neu PowerShell chan activate script:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## 2. Khoi tao database

```powershell
python implementation\init_db.py
```

Lenh nay tao database tai:

```text
implementation/data/lab.db
```

File database sinh ra duoc ignore, nen co the chay lai de reset seed data.

## 3. Chay MCP server

```powershell
python implementation\mcp_server.py
```

Server chay STDIO mac dinh, phu hop cho MCP clients nhu Codex, Claude Code, Gemini CLI va MCP Inspector.

## 4. Tool descriptions

### `search`

Search rows trong mot table hop le.

Input chinh:

- `table`: ten table
- `filters`: object hoac list filters
- `columns`: list columns hoac comma string
- `limit`: gioi han rows, max 100
- `offset`: pagination offset
- `order_by`: column de sort
- `descending`: sort giam dan neu `true`

Vi du:

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

Insert mot row moi vao table hop le. `values` khong duoc rong va moi column phai ton tai trong schema.

Vi du:

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

Tinh aggregate tren table hop le.

Metrics ho tro:

- `count`
- `avg`
- `sum`
- `min`
- `max`

Vi du:

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## 5. Validation va SQL safety

Implementation reject:

- table khong ton tai
- column khong ton tai
- filter operator khong duoc support
- aggregate metric khong hop le
- aggregate thieu column khi metric can column
- insert rong

Values trong filters va insert dung SQLite placeholders `?`. Table/column/order/group identifiers duoc validate theo schema that truoc khi dua vao SQL.

Filter operators ho tro:

```text
=, ==, eq, !=, <>, ne, <, lt, <=, lte, >, gt, >=, gte, like, in
```

## 6. Verify nhanh

Chay smoke verification:

```powershell
python implementation\verify_server.py
```

Script nay kiem tra:

- server khoi tao duoc
- 3 tools discoverable
- schema resource discoverable
- table schema template discoverable
- doc duoc `schema://database`
- doc duoc `schema://table/students`
- valid `search` call thanh cong
- valid `insert` call thanh cong
- valid `aggregate` call thanh cong
- invalid `search` call tra loi ro rang

## 7. Chay tests

```powershell
pytest
```

Tests dung database tam trong `tmp_path`, nen khong phu thuoc vao database local.

## 8. MCP Inspector

Lenh mau tren Windows:

```powershell
npx -y @modelcontextprotocol/inspector python C:\Users\Admin\Desktop\CODE\VinAI\Week6\2A202600750-VuVanHuy-Day26\implementation\mcp_server.py
```

Trong Inspector, can verify:

- tools `search`, `insert`, `aggregate` hien ra
- resource `schema://database` hien ra
- resource template `schema://table/{table_name}` hien ra
- valid tool call tra ket qua dung
- invalid tool call, vi du `{"table": "missing"}`, tra loi `unknown table`

## 9. Codex MCP client config

Codex doc cau hinh MCP server trong `config.toml` bang `[mcp_servers.<name>]`.

Example da co tai:

```text
client_configs/codex_config.example.toml
```

Copy block trong file do vao `~/.codex/config.toml`, hoac `.codex/config.toml` neu repo da duoc Codex trust.
Repo cung co `AGENTS.md` de huong dan Codex dung `sqlite_lab` khi can schema hoac lookup database.

Sau khi cau hinh, restart Codex hoac mo session moi, roi dung `/mcp` trong TUI de xem server active. Co the hoi Codex:

```text
Use the sqlite_lab MCP server. Read schema://database, then search the top 2 students by score.
```

## 10. Claude Code config example

Example co tai:

```text
client_configs/claude_mcp.example.json
```

Claude Code co the doc resource bang cu phap tuong tu:

```text
@sqlite-lab:schema://database
```

## 11. Suggested demo flow

Video demo khoang 2 phut:

1. Chay `python implementation\verify_server.py`.
2. Mo Inspector va show 3 tools.
3. Doc `schema://database`.
4. Goi `search` students cohort `A1`.
5. Goi `insert` them mot student moi.
6. Goi `aggregate` average score by cohort.
7. Goi invalid request voi table sai de show clear error.
8. Show Codex/Claude config example.

## 12. Submission checklist

- [x] FastMCP server starts successfully
- [x] Project structure clean and understandable
- [x] SQLite database initialized with reproducible schema/data
- [x] Code separated into server logic and database logic
- [x] `search` supports filters, ordering, pagination
- [x] `insert` works and returns inserted payload
- [x] `aggregate` supports `count`, `avg`, `sum`, `min`, `max`
- [x] Full database schema resource exposed
- [x] Per-table schema resource template exposed
- [x] Invalid table and column names rejected
- [x] Unsupported operators and bad aggregate requests rejected
- [x] SQL uses validation plus parameterized values
- [x] Tool discovery verified
- [x] Successful tool calls demonstrated
- [x] Failing tool calls demonstrated with clear errors
- [x] Codex MCP client config example included
- [x] Setup and test steps documented
- [x] Inspector command documented
