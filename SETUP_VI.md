# Huong dan setup lab MCP SQLite

Tai lieu nay tom tat viec can lam trong lab va cac buoc setup du an. File nay chi la huong dan chuan bi, chua bao gom code implementation.

## 1. Muc tieu lab

Can xay dung mot MCP server bang Python, su dung FastMCP va SQLite. Server phai expose:

- 3 MCP tools: `search`, `insert`, `aggregate`
- 1 resource doc schema toan bo database: `schema://database`
- 1 dynamic resource template cho schema tung bang: `schema://table/{table_name}`
- Co validation de chan request khong an toan hoac khong hop le
- Co cach verify bang MCP Inspector hoac client MCP khac
- Co vi du cau hinh it nhat mot client nhu Claude Code, Codex hoac Gemini CLI

## 2. Yeu cau chinh can implement sau nay

### MCP server

Tao thu muc implementation theo goi y:

```text
implementation/
  db.py
  init_db.py
  mcp_server.py
  verify_server.py
  tests/
    test_server.py
```

Trong do:

- `mcp_server.py`: khai bao FastMCP server, tools va resources
- `db.py`: xu ly ket noi SQLite, validate table/column, build query an toan
- `init_db.py`: tao database va seed data mau
- `verify_server.py`: script smoke test de kiem tra server/tools/resources
- `tests/`: test tu dong neu co thoi gian

### Tools bat buoc

`search` nen ho tro:

- chon table
- chon columns
- filters
- order by
- limit va offset

`insert` nen ho tro:

- insert row moi vao table
- reject insert rong
- tra ve payload da insert, kem id neu co

`aggregate` nen ho tro:

- `count`
- `avg`
- `sum`
- `min`
- `max`
- filters
- group by

### Database goi y

Dung dataset nho de demo de:

- `students`
- `courses`
- `enrollments`

Vi du demo:

- tim tat ca students trong cohort `A1`
- insert mot student moi
- dem so row trong mot table
- tinh diem trung binh theo cohort
- doc `schema://database`
- doc `schema://table/students`
- goi request sai, vi du search table khong ton tai

## 3. Dieu kien moi truong

Can cai:

- Python 3.10 tro len
- `pip`
- Node.js va `npx` neu muon dung MCP Inspector
- Mot MCP client de demo, vi du Gemini CLI, Claude Code hoac Codex

Kiem tra nhanh:

```powershell
python --version
pip --version
node --version
npx --version
```

## 4. Tao virtual environment

Tren Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Neu PowerShell chan activate script, co the chay:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Tren macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
```

## 5. Cai dependencies du kien

Sau khi co code, nen tao `requirements.txt`. Goi toi thieu du kien:

```text
fastmcp
pytest
```

Cai bang:

```powershell
pip install -r requirements.txt
```

Neu chua co `requirements.txt`, co the cai tam:

```powershell
pip install fastmcp pytest
```

## 6. Khoi tao database sau khi code xong

Sau khi implement `implementation/init_db.py`, chay:

```powershell
python implementation\init_db.py
```

Ket qua mong doi:

- Tao file SQLite, vi du `implementation\data\lab.db`
- Tao cac bang `students`, `courses`, `enrollments`
- Seed san mot so dong data mau de demo

## 7. Chay MCP server

Sau khi implement `implementation/mcp_server.py`, chay thu:

```powershell
python implementation\mcp_server.py
```

Server nen chay stdio mac dinh de de ket noi voi MCP clients.

## 8. Verify bang MCP Inspector

Dung duong dan tuyet doi cho Python va file server neu Inspector yeu cau.

Vi du tren Windows:

```powershell
npx -y @modelcontextprotocol/inspector python C:\ABSOLUTE\PATH\TO\implementation\mcp_server.py
```

Can chup hoac ghi lai cac muc sau:

- server start thanh cong
- tools `search`, `insert`, `aggregate` hien ra
- resource `schema://database` hien ra
- resource template `schema://table/{table_name}` doc duoc
- valid tool call tra ket qua dung
- invalid tool call tra loi ro rang

## 9. Vi du cau hinh MCP client

### Claude Code

File `.mcp.json` vi du:

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

### Codex

Vi du trong `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "python"
args = ["C:/ABSOLUTE/PATH/TO/implementation/mcp_server.py"]
```

### Gemini CLI

Vi du:

```powershell
gemini mcp add sqlite-lab C:\ABSOLUTE\PATH\TO\.venv\Scripts\python.exe C:\ABSOLUTE\PATH\TO\implementation\mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
```

Smoke test mau:

```powershell
gemini --allowed-mcp-server-names sqlite-lab --yolo -p "Use the sqlite-lab MCP server and show me the top 2 students by score."
```

## 10. Checklist cham diem

Truoc khi nop bai, can dam bao:

- FastMCP server start duoc
- Cac file du an nam trong structure ro rang
- SQLite database co schema va seed data reproducible
- Co `search`, `insert`, `aggregate`
- `search` co filters, ordering, pagination
- `insert` tra ve payload da insert
- `aggregate` ho tro cac metric co ban
- Expose full schema resource
- Expose per-table schema resource template
- Reject table/column/operator/aggregate khong hop le
- SQL dung parameterized query khi co user input
- Co verify tool discovery
- Co verify valid calls va invalid calls
- Co it nhat mot client MCP ket noi duoc
- README hoac setup docs co buoc setup/test/demo
- Co demo video ngan hoac screenshots

## 11. Goi y thu tu lam bai

1. Tao `implementation/` va file skeleton.
2. Implement `init_db.py` de tao SQLite database va seed data.
3. Implement `db.py` voi adapter SQLite va validation.
4. Implement 3 tools trong `mcp_server.py`.
5. Implement 2 schema resources.
6. Viet `verify_server.py` hoac tests.
7. Chay Inspector de verify.
8. Cau hinh mot MCP client va quay demo.
9. Cap nhat README voi lenh setup/test chinh xac.

## 12. Luu y an toan SQL

Khong build SQL bang cach noi truc tiep raw input vao query. Nen:

- validate table name theo danh sach table that
- validate column name theo schema that
- chi cho phep operator nam trong allowlist, vi du `=`, `!=`, `<`, `<=`, `>`, `>=`, `like`, `in`
- dung placeholder `?` cho values trong SQLite
- gioi han `limit` de tranh output qua lon

