# 查询结果显示优化方案

## 当前问题

1. ❌ 日期格式不友好：`2025-11-06T10:24:12`
2. ❌ 状态显示为数字：`state: 13`
3. ❌ 缺少单据类型：`bill_type` 字段
4. ❌ 缺少创建人信息
5. ❌ 显示逻辑简陋

## 解决方案（按优先级）

### 阶段1：添加数据映射和格式化（必做）⭐⭐⭐

**文件**：`text_to_sql.py`

**要添加的代码**：

```python
# ==================== 数据映射 ====================

class DataMapper:
    """数据映射器 - 将数字代码转换为可读文本"""

    # 状态映射
    STATE_MAPPING = {
        1: "未审核时发送人撤回",
        2: "未接受时发送人撤回",
        3: "审核未通过",
        4: "拒绝",
        5: "任务超时未接受自动拒绝",
        6: "任务超时未审核自动拒绝",
        7: "申请撤回",
        101: "同意撤回",
        102: "不同意撤回",
        10: "新建",
        11: "待审核",
        12: "审核通过",
        13: "待接受",
        14: "接受",
        20: "接收人撤回申请",
        21: "接收人申请内容变更",
        # ... 补充完整映射
        70: "已验收（按时完工）",
        71: "已验收（逾期完工）",
        72: "已验收（超时自动验收）",
        73: "结案（发送人）",
        80: "任务终止",
        81: "人员退出任务终止",
    }

    # 单据类型映射
    BILL_TYPE_MAPPING = {
        # 老版本
        0: "无",
        1: "生产入库",
        2: "采购入库",
        3: "生产出库",
        4: "销售出库",
        # ... 更多老版本

        # 新版本
        1001: "仓库初始入库",
        1002: "个人初始入库",
        1101: "仓库盘点",
        1102: "个人盘点",
        1201: "仓库调货",
        1301: "修改品名",
        1302: "修改数量",
        1303: "修改组件单",
        1304: "研发任务",
        1401: "仓库物料报损",
        1402: "仓库物料核销",
        1403: "个人物料报损",
        1404: "个人物料核销",
        1405: "固定资产报损",
        1501: "固定资产领料",
        1502: "固定资产销售",
        1503: "固定资产变更",
        1504: "固定资产初始入库",
        1505: "固定资产折旧",
        1601: "采购入库",
        1602: "采购收货",
        1603: "采购付款",
        1604: "采购退货",
        1605: "采购平账",
        1606: "采购修改",
        1607: "生产计划",
        1608: "备料计划",
        1609: "请购任务",
        1610: "采购挂账",
        1611: "报价",
        1701: "销售出库",
        1702: "销售发货",
        1703: "销售收款",
        1704: "销售退款",
        1705: "销售平账",
        1706: "销售挂账",
        1707: "销售计划",
        1801: "生产出库",
        1802: "调入",
        1901: "生产入库",
        1902: "调出",
        1903: "拆件入库",
        1904: "物品转换",
        2001: "付款",
        2002: "交款",
        2003: "报账",
        2004: "借款",
        2005: "发工资",
        2007: "内部转账",
        2008: "货币转换",
        2009: "付款退款",
        2010: "交款退款",
        2101: "售后发货",
        2102: "售后报损",
        2103: "售后上门服务",
        2201: "罚款申述",
        2301: "模拟打卡",
        2302: "建立团队仓库",
        2303: "建立团队账户",
        # ... 更多新版本
    }

    @classmethod
    def get_state_text(cls, state_code: int) -> str:
        """获取状态文本"""
        return cls.STATE_MAPPING.get(state_code, f"未知状态({state_code})")

    @classmethod
    def get_bill_type_text(cls, bill_type_code: int) -> str:
        """获取单据类型文本"""
        return cls.BILL_TYPE_MAPPING.get(bill_type_code, f"未知类型({bill_type_code})")


# ==================== 结果格式化 ====================

class ResultFormatter:
    """查询结果格式化器"""

    @staticmethod
    def format_datetime(dt_value) -> str:
        """格式化日期时间"""
        if not dt_value:
            return "无"

        # 如果是字符串，尝试解析
        if isinstance(dt_value, str):
            # ISO格式：2025-11-06T10:24:12
            if 'T' in dt_value:
                dt_value = dt_value.replace('T', ' ')
            return dt_value.split('.')[0]  # 去掉毫秒

        # 如果是 datetime 对象
        from datetime import datetime
        if isinstance(dt_value, datetime):
            return dt_value.strftime('%Y-%m-%d %H:%M:%S')

        return str(dt_value)

    @staticmethod
    def format_project_result(row: dict, show_creator: bool = True) -> str:
        """
        格式化 o_project 表的查询结果

        Args:
            row: 查询结果行
            show_creator: 是否显示创建人
        """
        lines = []

        # 标题
        if 'title' in row:
            lines.append(f"📋 {row['title']}")

        # ID
        if 'id' in row:
            lines.append(f"   ID: {row['id']}")

        # 单据类型
        if 'bill_type' in row:
            bill_type_code = row['bill_type']
            bill_type_text = DataMapper.get_bill_type_text(bill_type_code)
            lines.append(f"   类型: {bill_type_text} ({bill_type_code})")

        # 状态
        if 'state' in row:
            state_code = row['state']
            state_text = DataMapper.get_state_text(state_code)
            lines.append(f"   状态: {state_text} ({state_code})")

        # 创建人
        if show_creator:
            if 'creator_name' in row:
                lines.append(f"   创建人: {row['creator_name']}")
            elif 'creator_uid' in row:
                lines.append(f"   创建人ID: {row['creator_uid']}")

        # 创建时间
        if 'createtime' in row:
            createtime = ResultFormatter.format_datetime(row['createtime'])
            lines.append(f"   创建时间: {createtime}")

        # 截止时间
        if 'deadline' in row:
            deadline = ResultFormatter.format_datetime(row['deadline'])
            lines.append(f"   截止时间: {deadline}")

        # 其他字段（可选）
        exclude_fields = {'id', 'title', 'bill_type', 'state', 'creator_name',
                         'creator_uid', 'createtime', 'deadline'}
        for key, value in row.items():
            if key not in exclude_fields and value is not None:
                lines.append(f"   {key}: {value}")

        return '\n'.join(lines)

    @staticmethod
    def format_result_smart(row: dict, table_name: str = None) -> str:
        """
        智能格式化结果（根据表名选择不同格式）

        Args:
            row: 查询结果行
            table_name: 表名（如果知道）
        """
        # 如果结果包含 o_project 的典型字段，使用 project 格式化
        if 'bill_type' in row or ('title' in row and 'state' in row):
            return ResultFormatter.format_project_result(row)

        # 默认格式化
        lines = []
        for key, value in row.items():
            # 格式化日期字段
            if 'time' in key.lower() or 'date' in key.lower():
                value = ResultFormatter.format_datetime(value)

            # 格式化状态字段
            if key == 'state' and isinstance(value, int):
                state_text = DataMapper.get_state_text(value)
                value = f"{state_text} ({value})"

            # 格式化单据类型字段
            if key == 'bill_type' and isinstance(value, int):
                bill_type_text = DataMapper.get_bill_type_text(value)
                value = f"{bill_type_text} ({value})"

            lines.append(f"   {key}: {value}")

        return '\n'.join(lines)
```

**修改位置**：在 `text_to_sql.py` 文件开头，在 `@dataclass` 的 `UserContext` 之前添加。

### 阶段2：修改显示逻辑（必做）⭐⭐⭐

**修改位置**：`TextToSQLApp.interactive_mode()` 方法（约 975-980 行）

**原代码**：
```python
# 显示结果
if result.get('results'):
    print("\n查询结果:")
    print("-"*60)
    for i, row in enumerate(result['results'], 1):
        print(f"{i}. {json.dumps(row, ensure_ascii=False, indent=2, default=json_serializer)}")
    print("-"*60)
```

**改为**：
```python
# 显示结果
if result.get('results'):
    print("\n查询结果:")
    print("-"*60)
    for i, row in enumerate(result['results'], 1):
        print(f"{i}. ")
        # 使用智能格式化器
        formatted = ResultFormatter.format_result_smart(row)
        print(formatted)
        print()  # 空行分隔
    print("-"*60)
```

### 阶段3：优化 SQL 生成（建议做）⭐⭐

**修改位置**：`TextToSQLEngine._build_system_prompt()` 方法（约 732 行）

**在 System Prompt 中添加**：
```python
prompt = """你是一个专业的SQL查询生成助手。你的任务是根据用户的自然语言问题，生成准确的MySQL查询语句。

【字段选择规则】
1. 查询 o_project 表时，务必包含以下字段：
   - id, title, state, bill_type, createtime, deadline
   - 如需创建人信息，JOIN o_user 表获取 creator_name

2. 如果需要显示创建人姓名，使用以下 SQL 模式：
   SELECT p.*, u.real_name as creator_name
   FROM o_project p
   LEFT JOIN o_user u ON p.creator_uid = u.id

3. 优先选择有业务意义的字段，而不是只选择 *

4. 日期时间字段无需格式化，直接使用原始字段

【重要提示】
- bill_type 字段表示单据类型，必须包含
- state 字段表示任务状态，必须包含
- 如果问题涉及"谁创建"、"发布人"，必须 JOIN o_user 获取姓名

"""
```

### 阶段4：添加查询后处理（可选）⭐

如果 SQL 没有包含某些字段，自动补充。

**修改位置**：`TextToSQLEngine.query()` 方法，在返回结果前添加后处理。

```python
# 在 return 之前添加
results = self._enrich_results(results, relevant_tables)
```

**添加方法**：
```python
def _enrich_results(self, results: List[Dict], tables: List[str]) -> List[Dict]:
    """
    丰富查询结果，补充缺失的关联信息

    Args:
        results: 原始查询结果
        tables: 查询涉及的表

    Returns:
        丰富后的结果
    """
    if not results:
        return results

    # 检查是否是 o_project 查询且缺少创建人信息
    if 'o_project' in tables:
        first_row = results[0]
        if 'creator_uid' in first_row and 'creator_name' not in first_row:
            # 缺少创建人姓名，补充查询
            creator_uids = [r['creator_uid'] for r in results if r.get('creator_uid')]
            if creator_uids:
                # 批量查询创建人信息
                creator_map = self._fetch_user_names(creator_uids)
                for row in results:
                    uid = row.get('creator_uid')
                    if uid and uid in creator_map:
                        row['creator_name'] = creator_map[uid]

    return results

def _fetch_user_names(self, user_ids: List[int]) -> Dict[int, str]:
    """
    批量获取用户姓名

    Args:
        user_ids: 用户ID列表

    Returns:
        {user_id: real_name} 映射
    """
    if not user_ids:
        return {}

    try:
        ids_str = ','.join(str(uid) for uid in user_ids)
        sql = f"SELECT id, real_name FROM o_user WHERE id IN ({ids_str})"

        connection = self.db_manager.get_connection()
        result = connection.execute(text(sql))
        rows = result.fetchall()

        return {row[0]: row[1] for row in rows}
    except Exception as e:
        print(f"⚠️  获取用户姓名失败: {str(e)}")
        return {}
```

## 实施顺序建议

1. **第一步**：添加 `DataMapper` 和 `ResultFormatter` 类（5分钟）
2. **第二步**：修改 `interactive_mode()` 显示逻辑（2分钟）
3. **第三步**：测试效果，看看是否满意（3分钟）
4. **第四步**（可选）：如果 SQL 经常缺少字段，再做阶段3和4

## 预期效果

### 修改前：
```
1. {
  "id": 334955,
  "title": "康雷",
  "state": 13,
  "createtime": "2025-11-06T10:24:12",
  "deadline": "2025-12-06T10:23:13"
}
```

### 修改后：
```
1.
📋 康雷
   ID: 334955
   类型: 销售出库 (1701)
   状态: 待接受 (13)
   创建人: 文云安
   创建时间: 2025-11-06 10:24:12
   截止时间: 2025-12-06 10:23:13
```

## 注意事项

1. **映射数据完整性**：确保补全所有 state 和 bill_type 的映射
2. **性能考虑**：如果查询结果很多（>100条），后处理可能影响性能
3. **兼容性**：修改后要测试各种查询，确保不破坏现有功能
4. **verbose 模式**：考虑在 verbose=False 时使用友好格式，verbose=True 时保留原始 JSON

## 进一步优化

- 添加配置文件存储映射关系（不要硬编码）
- 支持自定义字段显示顺序
- 支持导出为 Excel/CSV 格式
- 添加分页显示（结果太多时）
