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

### 方式1: 简洁模式（推荐给最终用户）

```python
from text_to_sql import TextToSQLApp

# 创建应用（默认简洁模式，适合普通用户）
app = TextToSQLApp(verbose=False)
app.initialize()

# 查询 - 输出简洁、友好
result = app.query("今天的打卡记录", limit=10)
# 输出示例：
# 找到 3 条记录：
# 1. 张三
#    Id: 12345
#    Start Time: 2025-11-06 09:00:00
#    End Time: 2025-11-06 18:00:00

app.close()
```

### 方式2: 详细模式（适合开发调试）

```python
from text_to_sql import TextToSQLApp

# 创建应用（详细模式，显示SQL和调试信息）
app = TextToSQLApp(verbose=True)
app.initialize()

result = app.query("今天的打卡记录", limit=10)
# 输出示例：
# 🤖 使用LLM智能识别相关表...
# 🔍 识别到相关表: o_user_clock
# 正在生成SQL...
# 生成的SQL: SELECT * FROM o_user_clock...
# 正在执行查询...
# 🔒 应用数据权限过滤
# ✓ 查询成功，返回 3 条结果

print(result['sql'])      # 生成的SQL
print(result['results'])  # 查询结果（完整JSON）

app.close()
```

### 方式3: 带权限控制（生产环境）

```python
from text_to_sql import TextToSQLApp, create_user_context

# 创建用户上下文
user_ctx = create_user_context(
    user_id=200287,    # 用户ID
    team_id=666666,    # 团队ID
    is_admin=False     # 是否管理员
)

# 创建应用（简洁模式 + 权限控制）
app = TextToSQLApp(user_context=user_ctx, verbose=False)
app.initialize()

# 查询（自动过滤为本团队/本用户数据）
result = app.query("今天的打卡记录")
# SQL自动添加: WHERE team_id = 666666

app.close()
```

### 方式4: 动态切换用户

```python
app = TextToSQLApp(verbose=False)
app.initialize()

# 用户1登录
app.set_user_context(user_id=200287, team_id=666666)
result1 = app.query("我的打卡记录")

# 用户2登录
app.set_user_context(user_id=200288, team_id=666666)
result2 = app.query("我的打卡记录")

app.close()
```

## 📺 输出模式

系统支持两种输出模式，可根据使用场景选择：

### 简洁模式（verbose=False，默认）

**适用场景：** 生产环境、最终用户、API接口

**特点：**
- ✅ 隐藏技术细节（SQL、表识别过程等）
- ✅ 用户友好的输出格式
- ✅ 自动格式化数据，突出重要字段
- ✅ 友好的错误提示

**输出示例：**
```
请输入您的问题: 文云安今天发销售任务了吗

找到 3 条记录：

1. 康雷
   Id: 334955
   Create Time: 2025-11-06 10:24:35
   Status: 1

2. 九龙香格里拉大酒店
   Id: 335021
   Create Time: 2025-11-06 11:20:15
   Status: 1
```

### 详细模式（verbose=True）

**适用场景：** 开发调试、问题排查、学习理解

**特点：**
- ✅ 显示完整的SQL语句
- ✅ 显示表识别过程
- ✅ 显示权限过滤信息
- ✅ 完整的JSON格式输出
- ✅ 详细的错误堆栈

**输出示例：**
```
问题: 文云安今天发销售任务了吗
============================================================
🤖 使用LLM智能识别相关表...
🔍 识别到相关表: o_project, o_user
正在生成SQL...
生成的SQL:
SELECT `o_project`.* FROM `o_project`
INNER JOIN `o_user` ON `o_project`.`creator_uid` = `o_user`.`id`
WHERE `o_user`.`real_name` = '文云安' AND DATE(`o_project`.`create_time`) = CURDATE()

正在执行查询...
🔒 应用数据权限过滤
   用户: 200287, 团队: 666666
✓ 查询成功，返回 3 条结果

查询结果:
------------------------------------------------------------
1. {
  "id": 334955,
  "name": "康雷",
  "creator_uid": 200298,
  ...
}
```

### 如何切换模式

```python
# 简洁模式（推荐给最终用户）
app = TextToSQLApp(verbose=False)

# 详细模式（推荐给开发者）
app = TextToSQLApp(verbose=True)
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
