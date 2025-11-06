# Text-to-SQL 自然语言查询系统

> 🚀 用中文问问题，自动生成SQL查询并返回结果

## 📖 简介

基于LangChain和LLM的Text-to-SQL系统，支持**中文自然语言**查询MySQL数据库。

**核心特性：**
- ✅ 中文自然语言查询
- ✅ 自动识别相关数据表
- ✅ 智能生成SQL语句
- ✅ 行级数据权限控制
- ✅ 支持多种LLM（OpenAI、DeepSeek等）
- ✅ 交互式查询界面

## 🚀 快速开始

### 1. 安装依赖

```bash
./.conda/bin/pip install -r requirements.txt
```

### 2. 配置API Key

编辑`.env`文件：
```env
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
```

### 3. 运行系统

```bash
# 无权限模式
./.conda/bin/python text_to_sql.py

# 或编辑main()函数设置用户权限
```

## 💻 使用方式

### 方式1: 无权限模式（测试用）

```python
from text_to_sql import TextToSQLApp

app = TextToSQLApp()
app.initialize()

result = app.query("今天的打卡记录", limit=10)
print(result['sql'])      # 生成的SQL
print(result['results'])  # 查询结果

app.close()
```

### 方式2: 带权限控制（生产环境）

```python
from text_to_sql import TextToSQLApp, create_user_context

# 创建用户上下文
user_ctx = create_user_context(
    user_id=200287,    # 用户ID
    team_id=666666,    # 团队ID
    is_admin=False     # 是否管理员
)

# 创建应用
app = TextToSQLApp(user_context=user_ctx)
app.initialize()

# 查询（自动过滤为本团队/本用户数据）
result = app.query("今天的打卡记录")
# SQL自动添加: WHERE team_id = 666666

app.close()
```

### 方式3: 动态切换用户

```python
app = TextToSQLApp()
app.initialize()

# 用户1登录
app.set_user_context(user_id=200287, team_id=666666)
result1 = app.query("我的打卡记录")

# 用户2登录
app.set_user_context(user_id=200288, team_id=666666)
result2 = app.query("我的打卡记录")

app.close()
```

## 🔒 权限控制

系统支持行级数据权限，确保用户只能查询自己团队/自己的数据。

### 自动过滤规则

| 表类型 | 字段 | 过滤条件 |
|--------|------|----------|
| 团队表（有team_id） | team_id | `WHERE team_id = 当前团队ID` |
| 用户表（有uid） | uid | `WHERE uid = 当前用户ID` |

### 权限示例

```python
# 用户查询: "今天的打卡记录"
# 生成SQL: SELECT * FROM o_user_clock WHERE DATE(start_time) = CURDATE()
# 自动过滤: SELECT * FROM o_user_clock WHERE (team_id = 666666) AND DATE(start_time) = CURDATE()
```

### 安全保护

系统自动拦截以下操作：
- ❌ DELETE, UPDATE, INSERT
- ❌ DROP, TRUNCATE, ALTER
- ✅ 只允许 SELECT 查询

## 📁 项目结构

```
.
├── text_to_sql.py              # 主程序（包含所有功能）
├── fetch_db_schema.py          # Schema提取工具
├── requirements.txt            # Python依赖
├── .env                        # 配置文件（API Key）
│
├── database_schema.json        # 完整Schema
├── database_schema_for_llm.json
└── database_schema.md
```

## 🔧 核心组件

`text_to_sql.py`包含所有核心类：

- **UserContext** - 用户上下文（权限）
- **PermissionManager** - 权限管理器
- **Config** - 配置管理
- **DatabaseManager** - 数据库连接
- **SchemaManager** - Schema管理
- **TextToSQLEngine** - SQL生成引擎
- **TextToSQLApp** - 应用主类

## ⚙️ 配置

### 切换LLM模型

编辑`.env`：

**OpenAI:**
```env
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=gpt-4o
```

**DeepSeek (当前):**
```env
OPENAI_API_KEY=sk-xxx
OPENAI_MODEL=deepseek-chat
OPENAI_BASE_URL=https://api.deepseek.com/v1
```

### 修改数据库

编辑`text_to_sql.py`中的`Config.DB_CONFIG`。

### 添加权限表

编辑`text_to_sql.py`中的`PermissionManager.TEAM_TABLES`和`USER_TABLES`。

## 📚 查询示例

```
# 团队管理
列出所有团队
团队成员有哪些人

# 考勤打卡
今天的打卡记录
本周打卡统计

# 任务管理
显示未完成的任务
本月的任务列表

# 销售业务
本月的销售订单
查询客户信息

# 库存管理
查询库存情况
哪些物品库存不足
```

## 🐛 常见问题

**Q: 如何切换用户？**
```python
app.set_user_context(user_id=200288, team_id=666666)
```

**Q: 如何禁用权限？**
```python
app = TextToSQLApp()  # 不传user_context
```
⚠️ 生产环境必须设置用户上下文！

**Q: 管理员有什么特殊权限？**

管理员可以查询本团队所有数据，但在非团队表也只能查自己的数据。

**Q: SQL生成不准确？**

1. 使用更强大的模型（GPT-4）
2. 在问题中明确指定表名
3. 指定`relevant_tables`参数

## 📊 技术栈

- **Python**: 3.11.14
- **LangChain**: 1.0.3
- **LLM**: DeepSeek（可切换OpenAI等）
- **Database**: MySQL
- **ORM**: SQLAlchemy 2.0.44

## 📝 更新日志

### v1.2.0 (2025-11-06)
- ✅ 添加行级数据权限控制
- ✅ 整合代码为单文件
- ✅ 简化项目结构

### v1.0.0 (2025-11-06)
- ✅ 初始版本发布
- ✅ 支持中文自然语言查询
- ✅ 206个表的Schema支持
- ✅ DeepSeek LLM集成

---

⭐ 如果这个项目对你有帮助，请给个Star！
