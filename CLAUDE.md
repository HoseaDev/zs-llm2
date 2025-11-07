# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Text-to-SQL natural language query system built with Python 3.11, LangChain, and LLM. It allows users to query a MySQL database using natural language questions in Chinese.

**Key Features:**
- Natural language to SQL conversion
- Automatic table identification based on keywords
- Support for multiple LLM providers (OpenAI, DeepSeek, Alibaba Cloud, etc.)
- Interactive query mode
- Database schema extraction and management

## Environment Setup

The project uses a conda environment installed locally:

```bash
# Activate the conda environment
conda activate ./.conda

# Or using the full path
source .conda/bin/activate
```

## Running Python Code

```bash
# Run Python files using the local environment's interpreter
./.conda/bin/python <file>.py

# Or activate the environment first, then use python directly
python <file>.py
```

## Common Commands

### Database Schema Extraction

```bash
# Fetch database schema and sample data
./.conda/bin/python fetch_db_schema.py
```

This generates:
- `database_schema.json` - Full schema with sample data
- `database_schema_for_llm.json` - Simplified version for LLM context
- `database_schema.md` - Human-readable documentation

### Running Text-to-SQL System

```bash
# Interactive mode (default: simple output)
./.conda/bin/python text_to_sql.py

# Or set API key explicitly
export OPENAI_API_KEY="your_api_key"
./.conda/bin/python text_to_sql.py
```

### Testing Queries

```bash
# Test a single query programmatically
./.conda/bin/python -c "
from text_to_sql import TextToSQLApp
app = TextToSQLApp(verbose=False)
app.initialize()
result = app.query('列出所有团队')
print(result)
app.close()
"
```

### Installing Dependencies

```bash
# 方式1: 使用requirements.txt (推荐)
./.conda/bin/pip install -r requirements.txt

# 方式2: 手动安装
./.conda/bin/pip install langchain langchain-community langchain-openai sqlalchemy pymysql cryptography python-dotenv
```

## Project Structure

- `.conda/` - Local conda environment (Python 3.11.14)
- `requirements.txt` - Python dependencies list
- `fetch_db_schema.py` - Database schema extraction script
- `text_to_sql.py` - Main Text-to-SQL query system
- `example_usage.py` - Usage examples
- `database_schema.json` - Complete database schema and sample data
- `database_schema_for_llm.json` - Simplified schema for LLM (used as context)
- `database_schema.md` - Human-readable schema documentation
- `.env` - Environment variables (API keys, etc.)
- `.env.example` - Environment variable template
- `README_TEXT_TO_SQL.md` - Detailed usage guide
- `CLAUDE.md` - This file

## Architecture

The system follows this flow:

1. **User Question** (Natural language in Chinese)
2. **Keyword Identification** (Identify relevant database tables using LLM)
3. **Schema Loading** (Load table structures and sample data)
4. **SQL Generation** (LLM generates SQL using prompt engineering)
5. **Permission Filtering** (Apply row-level data permissions if user context is set)
6. **SQL Validation** (Prevent dangerous operations: DELETE, UPDATE, DROP, etc.)
7. **SQL Execution** (Execute on MySQL database)
8. **Results Return** (JSON format with metadata)

### Key Components

All components are in [text_to_sql.py](text_to_sql.py):

- **UserContext** - Dataclass storing user_id, team_id, is_admin
- **PermissionManager** - Handles row-level data permissions, auto-injects WHERE clauses
  - `TEAM_TABLES`: Tables with team_id field (auto-filter by team_id)
  - `USER_TABLES`: Tables with uid field (auto-filter by uid)
  - `apply_permission_filter()`: Injects WHERE conditions into SQL
- **Config** - Database and LLM configuration
- **DatabaseManager** - MySQL connections using SQLAlchemy
- **SchemaManager** - Loads database_schema_for_llm.json and searches tables by keywords
- **TextToSQLEngine** - Core engine using LangChain
  - `identify_relevant_tables()`: Uses LLM to identify tables from natural language
  - `generate_sql()`: Generates SQL using LangChain with schema context
  - `validate_sql()`: Prevents dangerous SQL operations
  - `execute_query()`: Executes SQL and returns results
- **TextToSQLApp** - Main application class
  - `query()`: Main entry point for queries
  - `set_user_context()`: Dynamically switch users
  - `interactive_mode()`: Interactive CLI
- **create_user_context()** - Helper function to create UserContext

### Database Configuration

Target database: `sczsv4.4.1` with 206 tables
- Host: 120.26.37.228:9006
- Read-only user for safety

### LLM Configuration

Currently configured to use **DeepSeek** (see [.env](.env)).

Supports multiple providers via OpenAI-compatible API:
- **DeepSeek** (deepseek-chat) - Currently used, recommended for Chinese
- **OpenAI** (gpt-4o, gpt-4, gpt-3.5-turbo)
- **Alibaba Cloud Qwen** (via DashScope)
- **Zhipu AI** (via BigModel)
- Any OpenAI-compatible endpoint

To switch models, edit `.env`:
```bash
# For OpenAI
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
# Remove or comment out OPENAI_BASE_URL

# For DeepSeek (current)
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

## Common Query Examples

- "列出所有团队信息" - List all team information
- "我今天打卡了吗" - Did I clock in today
- "显示未完成的任务" - Show incomplete tasks
- "团主是谁" - Who is the team leader
- "当月的销售任务有哪些" - What are this month's sales tasks

## Usage Patterns

### Verbose Mode

The system supports two output modes controlled by `verbose` parameter:

**Simple Mode (verbose=False, default)** - For end users:
- Hides technical details (SQL, table identification)
- User-friendly output format
- Clean error messages

**Verbose Mode (verbose=True)** - For debugging:
- Shows generated SQL
- Shows table identification process
- Shows permission filtering details
- Full JSON output

```python
# Simple mode (production)
app = TextToSQLApp(verbose=False)

# Verbose mode (debugging)
app = TextToSQLApp(verbose=True)
```

### Permission Control

**Without permissions** (testing/admin):
```python
app = TextToSQLApp()  # No user_context
result = app.query("查询所有数据")  # Returns all data
```

**With permissions** (production):
```python
from text_to_sql import create_user_context

# Create user context
user_ctx = create_user_context(user_id=200287, team_id=666666, is_admin=False)
app = TextToSQLApp(user_context=user_ctx)
result = app.query("今天的打卡记录")  # Auto-filtered by team_id and user_id
```

**Dynamic user switching**:
```python
app = TextToSQLApp()
app.set_user_context(user_id=200287, team_id=666666)
result1 = app.query("我的打卡记录")  # User 200287's data

app.set_user_context(user_id=200288, team_id=666666)
result2 = app.query("我的打卡记录")  # User 200288's data
```

### Modifying main() for Default User

Edit [text_to_sql.py:1014](text_to_sql.py#L1014) `main()` function to set default user:

```python
def main():
    # Set default user context
    user_ctx = create_user_context(
        user_id=200287,
        team_id=666666,
        is_admin=False
    )
    app = TextToSQLApp(user_context=user_ctx, verbose=False)
    # ... rest of main
```

## Security Features

- **SQL Injection Prevention**: Uses parameterized queries via SQLAlchemy
- **Query Validation**: Blocks DELETE, UPDATE, INSERT, DROP, TRUNCATE, ALTER operations
- **Row-Level Permissions**: Auto-injects WHERE clauses based on user context
- **Read-Only Database User**: Connection uses read-only credentials

## Troubleshooting

### Common Issues

**"No module named 'langchain'"**
```bash
./.conda/bin/pip install -r requirements.txt
```

**"LLM identifies wrong tables"**
- Use verbose mode to see table identification process
- Manually specify tables: `app.query("question", relevant_tables=['o_user', 'o_team'])`
- Consider using a more powerful model (GPT-4 instead of GPT-3.5)

**"SQL generation is inaccurate"**
- Check if table comments and column comments are clear in database
- Regenerate schema: `./.conda/bin/python fetch_db_schema.py`
- Add more sample data to help LLM understand data patterns

**"Permission filtering not working"**
- Verify user context is set: `app.user_context` should not be None
- Check if table is in `PermissionManager.TEAM_TABLES` or `USER_TABLES`
- For new tables, add them to the appropriate set in [text_to_sql.py:38-55](text_to_sql.py#L38-L55)

**"Database connection failed"**
- Check `.env` file exists and has correct credentials
- Verify network access to database host (120.26.37.228:9006)
- Test connection: `./.conda/bin/python -c "from text_to_sql import DatabaseManager; db = DatabaseManager(); print(db.get_connection())"`

### Adding New Permission Tables

Edit [text_to_sql.py](text_to_sql.py) `PermissionManager` class:

```python
class PermissionManager:
    TEAM_TABLES = {
        'o_team', 'o_project', 'o_user_clock',
        'your_new_table_with_team_id',  # Add here
    }

    USER_TABLES = {
        'o_user', 'o_user_statistic',
        'your_new_table_with_uid',  # Add here
    }
```

### Debugging Tips

1. **Enable verbose mode**: See full SQL and execution details
2. **Check generated SQL**: `result['sql']` contains the generated query
3. **Verify table identification**: Look for "识别到相关表" in verbose output
4. **Test individual components**:
```python
from text_to_sql import SchemaManager
sm = SchemaManager()
sm.load_schema()
tables = sm.search_tables_by_keyword('打卡')  # Search for tables
print(tables)
```

## Notes

- The conda environment is stored locally in the repository (`.conda/`)
- Python version: 3.11.14
- Database queries are automatically limited to prevent large result sets
- Schema files are regenerated by running `fetch_db_schema.py`
- API keys should be stored in `.env` file or environment variables
- All core functionality is in a single file: [text_to_sql.py](text_to_sql.py)
- The system is designed for Chinese natural language queries
