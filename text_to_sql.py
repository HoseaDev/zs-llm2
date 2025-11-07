"""
Text-to-SQL 自然语言查询系统
支持从自然语言问题转换为SQL查询并执行
"""
import os
import json
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from sqlalchemy import create_engine, text
import pymysql
from dataclasses import dataclass

# 加载.env文件
load_dotenv()

# ==================== 数据映射和格式化 ====================

class DataMapper:
    """数据映射器 - 将数字代码转换为可读文本"""

    # 状态映射（完整版）
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
        22: "发送人同意内容变更",
        23: "发送人不同意内容变更",
        24: "审核人同意内容变更",
        25: "审核人不同意内容变更",
        26: "接收人申请延期",
        27: "发送人同意延期",
        28: "发送人不同意延期",
        29: "审核人同意延期",
        30: "审核人不同意延期",
        31: "接收人申请终止",
        32: "发送人同意终止",
        33: "发送人不同意终止",
        34: "审核人同意终止",
        35: "审核人不同意终止",
        40: "发送人撤回申请",
        41: "发送人申请变更",
        42: "发送人变更申请审核通过",
        43: "发送人变更申请审核未通过",
        44: "接收人同意发送人申请变更",
        45: "接收人不同意发送人申请变更",
        46: "发送人申请延期",
        47: "发送人延期申请审核通过",
        48: "发送人延期申请审核未通过",
        49: "接收人同意发送人延期",
        50: "接收人不同意发送人延期",
        51: "发送人申请终止",
        52: "发送人终止申请审核通过",
        53: "发送人终止申请审核未通过",
        54: "接收人同意发送人申请终止",
        55: "接收人不同意发送人申请终止",
        60: "验收未通过要求返工",
        61: "申请验收",
        70: "已验收(按时完工)",
        71: "已验收(逾期完工)",
        72: "已验收(超时自动验收)",
        73: "结案(发送人)",
        80: "任务终止",
        81: "人员退出任务终止",
    }

    # 单据类型映射（完整版）
    BILL_TYPE_MAPPING = {
        # 老版本
        0: "无",
        1: "生产入库",
        2: "采购入库",
        3: "生产出库",
        4: "销售出库",
        5: "调入",
        6: "调出",
        7: "库房报损",
        8: "交款",
        9: "付款",
        10: "借款",
        11: "报账",
        12: "销售退款",
        13: "采购退货",
        14: "团队初始录入",
        15: "团队人员初始录入",
        16: "销售发货",
        17: "销售收款",
        18: "销售平账",
        19: "采购收货",
        20: "采购付款",
        21: "采购平账",
        22: "修改品名",
        23: "合并品名",
        24: "更新组件",
        25: "团队人员库存报损",
        26: "库房辅料报损",
        27: "人员辅料报损",
        30: "付款(发工资)",
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
        2304: "学习报账",
        2305: "模拟报账",
        2306: "学习交款",
        2307: "模拟交款",
        2308: "学习付款",
        2309: "模拟付款",
        2310: "引导-设置职务",
        2311: "引导-导入库存",
        2312: "引导-设置组件单",
        2313: "引导-单据识别匹配",
        2314: "引导-发布生产计划",
        2315: "引导-按计划采购",
        2316: "引导-创建收支类型",
        2317: "引导-设置工作态度/任务罚款",
        2318: "引导-设置团队数据应收款预警",
        2319: "引导-设置入库异常",
        2320: "引导-设置库存预警",
        2321: "引导-导入供应商",
        2322: "引导-导入客户",
        2323: "引导-设置团队工作时间",
        2401: "代理任务",
        2402: "代理任务接管",
        2501: "分发任务",
    }

    @classmethod
    def get_state_text(cls, state_code: int) -> str:
        """获取状态文本（不显示数字）"""
        return cls.STATE_MAPPING.get(state_code, f"未知状态({state_code})")

    @classmethod
    def get_bill_type_text(cls, bill_type_code: int) -> str:
        """获取单据类型文本（不显示数字）"""
        return cls.BILL_TYPE_MAPPING.get(bill_type_code, f"未知类型({bill_type_code})")


class ResultFormatter:
    """查询结果格式化器 - 美化显示结果"""

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
            # 去掉毫秒部分
            return dt_value.split('.')[0]

        # 如果是 datetime 对象
        from datetime import datetime
        if isinstance(dt_value, datetime):
            return dt_value.strftime('%Y-%m-%d %H:%M:%S')

        return str(dt_value)

    @staticmethod
    def format_project_result(row: dict) -> str:
        """
        格式化 o_project 表的查询结果

        Args:
            row: 查询结果行

        Returns:
            格式化后的字符串
        """
        lines = []

        # 标题（主要信息）
        if 'title' in row:
            lines.append(f"📋 {row['title']}")

        # ID
        if 'id' in row:
            lines.append(f"   ID: {row['id']}")

        # 单据类型（只显示文字）
        if 'bill_type' in row:
            bill_type_text = DataMapper.get_bill_type_text(row['bill_type'])
            lines.append(f"   类型: {bill_type_text}")

        # 状态（只显示文字）
        if 'state' in row:
            state_text = DataMapper.get_state_text(row['state'])
            lines.append(f"   状态: {state_text}")

        # 创建人
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

        # 单据编码
        if 'bill_code' in row:
            lines.append(f"   单据编码: {row['bill_code']}")

        # 其他字段（排除已显示的）
        exclude_fields = {'id', 'title', 'bill_type', 'state', 'creator_name',
                         'creator_uid', 'createtime', 'deadline', 'team_id'}
        for key, value in row.items():
            if key not in exclude_fields and value is not None:
                # 格式化日期类型字段
                if 'time' in key.lower() or 'date' in key.lower():
                    value = ResultFormatter.format_datetime(value)
                lines.append(f"   {key}: {value}")

        return '\n'.join(lines)

    @staticmethod
    def format_result_smart(row: dict) -> str:
        """
        智能格式化结果（根据字段自动判断表类型）

        Args:
            row: 查询结果行

        Returns:
            格式化后的字符串
        """
        # 如果包含 o_project 的典型字段，使用 project 格式化
        if 'bill_type' in row or ('title' in row and 'state' in row and 'createtime' in row):
            return ResultFormatter.format_project_result(row)

        # 默认格式化
        lines = []
        for key, value in row.items():
            if value is None:
                continue

            # 格式化日期字段
            if 'time' in key.lower() or 'date' in key.lower():
                value = ResultFormatter.format_datetime(value)

            # 格式化状态字段（只显示文字）
            elif key == 'state' and isinstance(value, int):
                value = DataMapper.get_state_text(value)

            # 格式化单据类型字段（只显示文字）
            elif key == 'bill_type' and isinstance(value, int):
                value = DataMapper.get_bill_type_text(value)

            lines.append(f"   {key}: {value}")

        return '\n'.join(lines) if lines else "   (无数据)"


class TableFieldConfig:
    """
    表字段配置 - 定义每个表查询时应返回哪些字段

    使用方法：
    1. 在 FIELD_CONFIGS 中添加表配置
    2. System Prompt 会自动使用这些配置
    3. LLM 生成的 SQL 会包含这些字段
    """

    # 表字段配置字典
    # 格式: {表名: {"fields": [字段列表], "description": "说明"}}
    FIELD_CONFIGS = {
        'o_project': {
            'fields': [
                'id',
                'title',
                'bill_type',
                'state',
                'createtime',
                'deadline',
                'creator_uid',
                "bill_code"
            ],
            'joins': {
                'creator_name': {
                    'join': 'LEFT JOIN o_user ON o_project.creator_uid = o_user.id',
                    'select': 'o_user.real_name as creator_name'
                }
            },
            'description': '任务/项目表，必须包含单据类型、状态、创建人单据编码信息'
        },
        'o_user_clock': {
            'fields': [
                'id',
                'uid',
                'start_time',
                'end_time'
            ],
            'joins': {
                'user_name': {
                    'join': 'LEFT JOIN o_user ON o_user_clock.uid = o_user.id',
                    'select': 'o_user.real_name as user_name'
                }
            },
            'description': '打卡记录表，包含打卡时间和用户信息'
        },
        'o_user': {
            'fields': [
                'id',
                'real_name',
                'mobile',
                'team_id',
                'position',
                'status',
            ],
            'description': '用户表，包含基本信息'
        },
        'o_team': {
            'fields': [
                'id',
                'name',
                'leader_uid',
                'create_time',
                'status',
            ],
            'joins': {
                'leader_name': {
                    'join': 'LEFT JOIN o_user ON o_team.leader_uid = o_user.id',
                    'select': 'o_user.real_name as leader_name'
                }
            },
            'description': '团队表，包含团队名称和负责人'
        },
        # 在这里添加更多表的配置...
        # 例如：
        # 'o_bill_team_customer': {
        #     'fields': ['id', 'name', 'contact', 'mobile', 'address'],
        #     'description': '客户表'
        # },
    }

    @classmethod
    def get_table_config(cls, table_name: str) -> Optional[Dict]:
        """
        获取指定表的字段配置

        Args:
            table_name: 表名

        Returns:
            配置字典，如果没有配置则返回 None
        """
        return cls.FIELD_CONFIGS.get(table_name)

    @classmethod
    def get_select_fields(cls, table_name: str) -> Optional[List[str]]:
        """
        获取表应该 SELECT 的字段列表

        Args:
            table_name: 表名

        Returns:
            字段列表，如果没有配置则返回 None
        """
        config = cls.get_table_config(table_name)
        if config:
            return config.get('fields', [])
        return None

    @classmethod
    def get_join_config(cls, table_name: str) -> Optional[Dict]:
        """
        获取表的 JOIN 配置

        Args:
            table_name: 表名

        Returns:
            JOIN 配置字典
        """
        config = cls.get_table_config(table_name)
        if config:
            return config.get('joins', {})
        return {}

    @classmethod
    def build_field_selection_prompt(cls, table_name: str) -> str:
        """
        为指定表生成字段选择的 Prompt

        Args:
            table_name: 表名

        Returns:
            Prompt 字符串
        """
        config = cls.get_table_config(table_name)
        if not config:
            return ""

        prompt = f"\n【{table_name} 表必须返回以下字段】\n"

        # 基础字段
        fields = config.get('fields', [])
        prompt += f"基础字段: {', '.join(fields)}\n"

        # JOIN 字段
        joins = config.get('joins', {})
        if joins:
            prompt += "关联字段（需要 JOIN）:\n"
            for field_name, join_config in joins.items():
                prompt += f"  - {field_name}: {join_config['select']}\n"
                prompt += f"    JOIN 语句: {join_config['join']}\n"

        # 说明
        if config.get('description'):
            prompt += f"说明: {config['description']}\n"

        return prompt

    @classmethod
    def get_all_configured_tables(cls) -> List[str]:
        """获取所有已配置的表名列表"""
        return list(cls.FIELD_CONFIGS.keys())


# ==================== 权限管理 ====================

@dataclass
class UserContext:
    """用户上下文信息"""
    user_id: int  # 用户ID
    team_id: int  # 团队ID
    is_admin: bool = False  # 是否是管理员（在团队内部）

    def __repr__(self):
        role = "管理员" if self.is_admin else "普通用户"
        return f"UserContext(user_id={self.user_id}, team_id={self.team_id}, role={role})"


class PermissionManager:
    """权限管理器 - 负责SQL权限过滤"""

    # 包含team_id字段的表（团队相关表）
    TEAM_TABLES = {
        'o_team', 'o_team_user', 'o_team_apply', 'o_team_authentication',
        'o_team_img', 'o_team_industry', 'o_team_invite', 'o_team_notice',
        'o_team_praise', 'o_team_statistic', 'o_team_tag', 'o_team_wifi',
        'o_bill_team_account', 'o_bill_team_customer', 'o_bill_team_dict',
        'o_bill_team_stock', 'o_bill_team_warehouse', 'o_bill_team_report',
        'o_bill_team_sale_plan', 'o_bill_team_sale_performance',
        'o_bill_team_produce_plan', 'o_bill_team_supplier',
        'o_project',  # 任务表
        'o_user_clock',  # 打卡表
    }

    # 包含uid字段的表（用户相关表）
    USER_TABLES = {
        'o_user', 'o_user_statistic', 'o_user_config', 'o_user_dynamic',
        'o_user_friend', 'o_user_score', 'o_user_device', 'o_user_leave',
        'o_user_table', 'o_user_contacts', 'o_user_hours',
    }

    # 团队ID字段映射表（处理字段名不一致的情况）
    # 格式：{表名: 团队ID字段名}
    TEAM_ID_FIELD_MAPPING = {
        'o_team': 'id',  # o_team表特殊，使用id字段而不是team_id
        # 如果有其他表使用不同的字段名，在这里添加
        # 例如：
        # 'o_organization': 'org_id',
        # 'o_company': 'company_id',
    }

    # 默认的团队ID字段名（如果表不在映射表中，使用这个默认值）
    DEFAULT_TEAM_ID_FIELD = 'team_id'

    # 用户ID字段映射表（处理字段名不一致的情况）
    # 格式：{表名: 用户ID字段名}
    USER_ID_FIELD_MAPPING = {
        'o_user': 'id',  # o_user表特殊，使用id字段而不是uid
        # 如果有其他表使用不同的字段名，在这里添加
        # 例如：
        # 'o_special_table': 'user_id',
        # 'o_another_table': 'member_id',
    }

    # 默认的用户ID字段名（如果表不在映射表中，使用这个默认值）
    DEFAULT_USER_ID_FIELD = 'uid'

    def __init__(self):
        """初始化权限管理器"""
        pass

    def get_team_id_field(self, table_name: str) -> str:
        """
        获取指定表的团队ID字段名

        Args:
            table_name: 表名

        Returns:
            团队ID字段名（例如：'id', 'team_id', 'org_id'）
        """
        return self.TEAM_ID_FIELD_MAPPING.get(table_name, self.DEFAULT_TEAM_ID_FIELD)

    def get_user_id_field(self, table_name: str) -> str:
        """
        获取指定表的用户ID字段名

        Args:
            table_name: 表名

        Returns:
            用户ID字段名（例如：'id', 'uid', 'user_id'）
        """
        return self.USER_ID_FIELD_MAPPING.get(table_name, self.DEFAULT_USER_ID_FIELD)

    def should_filter_by_team(self, table_name: str) -> bool:
        """判断表是否需要按团队过滤"""
        return 'team' in table_name.lower() or table_name in self.TEAM_TABLES

    def should_filter_by_user(self, table_name: str) -> bool:
        """判断表是否需要按用户过滤"""
        return 'user' in table_name.lower() or table_name in self.USER_TABLES

    def get_filter_conditions(self, sql: str, user_context: UserContext) -> str:
        """
        为SQL添加权限过滤条件

        规则：
        1. **仅过滤FROM的主表**，不过滤JOIN的表（JOIN表只是用来做条件匹配）
        2. 团队表：添加团队ID过滤（字段名通过TEAM_ID_FIELD_MAPPING配置）
        3. 用户表：添加用户ID过滤（字段名通过USER_ID_FIELD_MAPPING配置）
        4. 管理员在团队内可查所有数据，但在非团队表中也只能查自己的
        5. 不同表的字段名可能不同，通过映射表自动适配

        字段映射示例：
        - o_team表使用 id 而不是 team_id
        - o_user表使用 id 而不是 uid
        - 其他表使用默认字段名
        """
        # 只提取FROM的主表，不包括JOIN的表
        main_table_info = self._extract_main_table_from_sql(sql)
        if not main_table_info:
            return sql

        table_name, alias = main_table_info
        conditions = []

        if self.should_filter_by_team(table_name):
            # 团队表：根据表名获取正确的团队ID字段名
            team_id_field = self.get_team_id_field(table_name)
            conditions.append(f"`{alias}`.`{team_id_field}` = {user_context.team_id}")
        elif self.should_filter_by_user(table_name):
            # 用户表：根据表名获取正确的用户ID字段名
            user_id_field = self.get_user_id_field(table_name)
            conditions.append(f"`{alias}`.`{user_id_field}` = {user_context.user_id}")

        if not conditions:
            return sql

        return self._inject_where_conditions(sql, conditions)

    def _extract_main_table_from_sql(self, sql: str) -> tuple:
        """
        从SQL中提取FROM的主表（不包括JOIN的表）
        返回: (表名, 别名) 元组
        例如: ('o_project', 'p') 或 ('o_project', 'o_project')

        只过滤FROM的主表，因为JOIN的表只是用来做条件匹配的，不应该被权限过滤
        """
        import re

        # 先移除子查询
        cleaned_sql = self._remove_subqueries(sql)

        # 只匹配FROM后面的第一个表（主表）
        # 支持: FROM table, FROM table alias, FROM `table` `alias`, FROM table AS alias
        pattern = r'FROM\s+`?(\w+)`?(?:\s+(?:AS\s+)?`?(\w+)`?)?'
        match = re.search(pattern, cleaned_sql, re.IGNORECASE)

        if match:
            table = match.group(1)
            alias = match.group(2) if match.group(2) else table

            # 过滤SQL关键字
            SQL_KEYWORDS = {'SELECT', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER', 'ON'}
            if alias and alias.upper() in SQL_KEYWORDS:
                alias = table

            return (table, alias)

        return None

    def _extract_tables_from_sql(self, sql: str) -> dict:
        """
        从SQL中提取表名和别名（只提取主查询的表，不包括子查询）
        返回: {表名: 别名} 字典，如果没有别名则别名=表名
        例如: {'o_project': 'p', 'o_project_user': 'pu'}
        """
        import re

        # SQL关键字列表（不能作为表名或别名）
        SQL_KEYWORDS = {
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'OUTER',
            'ON', 'AND', 'OR', 'NOT', 'IN', 'EXISTS', 'BETWEEN', 'LIKE',
            'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
            'INSERT', 'UPDATE', 'DELETE', 'INTO', 'VALUES', 'SET'
        }

        # 先移除所有子查询（括号内的内容），只保留主查询
        # 使用简单的括号计数方法移除嵌套子查询
        cleaned_sql = self._remove_subqueries(sql)

        # 匹配表名和可选的别名
        # 支持: FROM table, FROM table alias, FROM `table` `alias`, JOIN table AS alias
        patterns = [
            r'FROM\s+`?(\w+)`?(?:\s+(?:AS\s+)?`?(\w+)`?)?',
            r'JOIN\s+`?(\w+)`?(?:\s+(?:AS\s+)?`?(\w+)`?)?',
            r'INTO\s+`?(\w+)`?(?:\s+(?:AS\s+)?`?(\w+)`?)?',
            r'UPDATE\s+`?(\w+)`?(?:\s+(?:AS\s+)?`?(\w+)`?)?',
        ]

        table_aliases = {}
        for pattern in patterns:
            matches = re.finditer(pattern, cleaned_sql, re.IGNORECASE)
            for match in matches:
                table = match.group(1)
                alias = match.group(2) if match.group(2) else table

                # 过滤掉SQL关键字和非表名
                if table.upper() not in SQL_KEYWORDS and '.' not in table:
                    # 如果别名是SQL关键字，使用表名作为别名
                    if alias and alias.upper() in SQL_KEYWORDS:
                        alias = table
                    table_aliases[table] = alias

        return table_aliases

    def _remove_subqueries(self, sql: str) -> str:
        """
        移除SQL中的子查询（括号内的内容）
        保留主查询的结构
        """
        result = []
        depth = 0

        for char in sql:
            if char == '(':
                depth += 1
            elif char == ')':
                depth -= 1
            elif depth == 0:
                # 只保留不在括号内的字符
                result.append(char)

        return ''.join(result)

    def _inject_where_conditions(self, sql: str, conditions: list) -> str:
        """在SQL中注入WHERE条件"""
        import re
        filter_clause = " AND ".join(conditions)

        if re.search(r'\bWHERE\b', sql, re.IGNORECASE):
            sql = re.sub(
                r'(\bWHERE\b\s+)',
                f'\\1({filter_clause}) AND ',
                sql,
                count=1,
                flags=re.IGNORECASE
            )
        else:
            insert_patterns = [
                r'\s+(ORDER\s+BY)',
                r'\s+(GROUP\s+BY)',
                r'\s+(LIMIT\s+)',
                r'\s*;?\s*$',
            ]
            inserted = False
            for pattern in insert_patterns:
                match = re.search(pattern, sql, re.IGNORECASE)
                if match:
                    pos = match.start()
                    sql = sql[:pos] + f" WHERE {filter_clause}" + sql[pos:]
                    inserted = True
                    break
            if not inserted:
                sql = sql.rstrip(';').rstrip() + f" WHERE {filter_clause};"
        return sql

    def validate_query_permission(self, sql: str, user_context: UserContext) -> tuple[bool, str]:
        """验证查询权限"""
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'UPDATE', 'INSERT', 'ALTER']
        sql_upper = sql.upper()
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False, f"不允许执行 {keyword} 操作"
        return True, "权限验证通过"


def create_user_context(user_id: int, team_id: int, is_admin: bool = False) -> UserContext:
    """
    创建用户上下文

    Args:
        user_id: 用户ID
        team_id: 团队ID
        is_admin: 是否是管理员

    Returns:
        UserContext对象
    """
    return UserContext(user_id=user_id, team_id=team_id, is_admin=is_admin)

# ==================== 配置部分 ====================

class Config:
    """配置类"""
    # 数据库配置
    DB_CONFIG = {
        'host': '120.26.37.228',
        'port': 9006,
        'user': 'sczs_tmp_query',
        'password': 'KuJL4zQeqcT8.G!EH8pjYc',
        'database': 'sczsv4.4.1',
        'charset': 'utf8mb4'
    }

    # LLM配置 - 需要设置API Key
    # 支持多种LLM：OpenAI, DeepSeek, 阿里云等
    @staticmethod
    def get_llm_config():
        """动态获取LLM配置，从.env文件读取"""
        config = {
            'model': os.getenv('OPENAI_MODEL', 'deepseek-chat'),  # 默认使用deepseek
            'temperature': 0,
            'api_key': os.getenv('OPENAI_API_KEY'),
        }

        # 如果设置了base_url，添加它
        base_url = os.getenv('OPENAI_BASE_URL')
        if base_url:
            config['base_url'] = base_url

        return config

    LLM_CONFIG = None  # 将在运行时通过get_llm_config()获取

    # Schema文件路径
    SCHEMA_FILE = 'database_schema_for_llm.json'

# ==================== 数据库连接 ====================

class DatabaseManager:
    """数据库管理器"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.engine = None
        self.db = None

    def connect(self):
        """建立数据库连接"""
        try:
            # 创建SQLAlchemy引擎
            connection_string = (
                f"mysql+pymysql://{self.config['user']}:{self.config['password']}"
                f"@{self.config['host']}:{self.config['port']}/{self.config['database']}"
                f"?charset={self.config['charset']}"
            )

            self.engine = create_engine(connection_string)

            # 创建LangChain的SQLDatabase对象
            self.db = SQLDatabase(self.engine)

            print("✓ 数据库连接成功！")
            return self.db

        except Exception as e:
            print(f"✗ 数据库连接失败: {str(e)}")
            raise

    def test_connection(self):
        """测试数据库连接"""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                return result.fetchone()[0] == 1
        except Exception as e:
            print(f"连接测试失败: {str(e)}")
            return False

    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            print("✓ 数据库连接已关闭")

# ==================== Schema管理 ====================

class SchemaManager:
    """Schema管理器 - 负责加载和管理数据库表结构"""

    def __init__(self, schema_file: str):
        self.schema_file = schema_file
        self.schema_data = None

    def load_schema(self) -> Dict:
        """加载schema文件"""
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                self.schema_data = json.load(f)
            print(f"✓ Schema文件加载成功: {self.schema_file}")
            return self.schema_data
        except Exception as e:
            print(f"✗ Schema文件加载失败: {str(e)}")
            raise

    def get_table_info(self, table_name: str) -> Dict:
        """获取指定表的信息"""
        if not self.schema_data:
            self.load_schema()

        for db_name, tables in self.schema_data.items():
            if table_name in tables:
                return tables[table_name]
        return None

    def search_tables_by_keyword(self, keyword: str) -> List[str]:
        """根据关键字搜索相关表"""
        if not self.schema_data:
            self.load_schema()

        matching_tables = []
        keyword_lower = keyword.lower()

        for db_name, tables in self.schema_data.items():
            for table_name, table_info in tables.items():
                # 在表名、表注释、列名中搜索
                if keyword_lower in table_name.lower():
                    matching_tables.append(table_name)
                elif table_info.get('comment') and keyword_lower in table_info['comment'].lower():
                    matching_tables.append(table_name)
                else:
                    # 在列名和列注释中搜索
                    for col in table_info.get('columns', []):
                        if keyword_lower in col.get('name', '').lower():
                            matching_tables.append(table_name)
                            break

        return list(set(matching_tables))  # 去重

    def get_schema_prompt(self, relevant_tables: List[str] = None) -> str:
        """
        生成用于LLM的Schema描述
        如果指定relevant_tables，只返回相关表的信息
        """
        if not self.schema_data:
            self.load_schema()

        prompt = "# 数据库表结构信息\n\n"

        for db_name, tables in self.schema_data.items():
            for table_name, table_info in tables.items():
                # 如果指定了相关表，只包含这些表
                if relevant_tables and table_name not in relevant_tables:
                    continue

                prompt += f"## 表名: {table_name}\n"
                if table_info.get('comment'):
                    prompt += f"说明: {table_info['comment']}\n"

                prompt += "字段:\n"
                cols = table_info.get('columns', [])
                for col in cols:
                    prompt += f"  - {col['name']} ({col['type']})"
                    if col.get('key') == 'PRI':
                        prompt += " [主键]"
                    if col.get('null') == 'NO':
                        prompt += " [NOT NULL]"
                    # 添加字段注释（非常重要！）
                    if col.get('comment'):
                        prompt += f" // {col['comment']}"
                    prompt += "\n"

                if len(table_info.get('columns', [])) > 10:
                    prompt += f"  ... (还有 {len(table_info.get('columns', [])) - 10} 个字段)\n"

                # 只添加1条样本数据（减少token）
                if table_info.get('sample_data'):
                    prompt += "样本数据（仅1条）:\n"
                    prompt += json.dumps(table_info['sample_data'][:1], ensure_ascii=False, indent=2)
                    prompt += "\n"

                prompt += "\n"

        return prompt

    def table_exists(self, table_name: str) -> bool:
        """检查表是否存在"""
        if not self.schema_data:
            self.load_schema()

        for db_name, tables in self.schema_data.items():
            if table_name in tables:
                return True
        return False

    def get_all_tables_summary(self) -> str:
        """
        获取所有表的简要信息（表名+注释）
        用于LLM进行表选择
        """
        if not self.schema_data:
            self.load_schema()

        summary_lines = []
        for db_name, tables in self.schema_data.items():
            for table_name, table_info in tables.items():
                comment = table_info.get('comment', '无说明')
                summary_lines.append(f"- {table_name}: {comment}")

        return "\n".join(summary_lines)

# ==================== Text-to-SQL引擎 ====================

class TextToSQLEngine:
    """Text-to-SQL核心引擎"""

    def __init__(self, db_manager: DatabaseManager, schema_manager: SchemaManager, llm_config: Dict, user_context: Optional[UserContext] = None):
        self.db_manager = db_manager
        self.schema_manager = schema_manager
        self.llm_config = llm_config
        self.llm = None
        self.chain = None

        # 权限管理
        self.user_context = user_context
        self.permission_manager = PermissionManager()

    def initialize(self):
        """初始化LLM和Chain"""
        try:
            # 检查API Key
            if not self.llm_config.get('api_key'):
                raise ValueError("请设置OPENAI_API_KEY环境变量或在配置中提供api_key")

            # 初始化LLM
            llm_params = {
                'model': self.llm_config['model'],
                'temperature': self.llm_config['temperature'],
                'api_key': self.llm_config['api_key']
            }

            # 如果有base_url，添加它
            if 'base_url' in self.llm_config:
                llm_params['base_url'] = self.llm_config['base_url']

            self.llm = ChatOpenAI(**llm_params)

            print(f"✓ LLM初始化成功: {self.llm_config['model']}")

        except Exception as e:
            print(f"✗ LLM初始化失败: {str(e)}")
            raise

    def generate_sql(self, question: str, relevant_tables: List[str] = None, is_user_specified: bool = False) -> str:
        """
        从自然语言问题生成SQL查询

        Args:
            question: 用户的自然语言问题
            relevant_tables: 相关的表名列表（可选）
            is_user_specified: 是否是用户手动指定的表（True=手动指定，False=自动识别）

        Returns:
            生成的SQL查询语句
        """
        try:
            # 构建System Prompt
            system_prompt = self._build_system_prompt(relevant_tables, is_user_specified)

            # 构建完整的Prompt
            full_prompt = f"""{system_prompt}

用户问题：{question}

请生成对应的SQL查询语句。

【重要】注意事项：
1. 只返回SQL语句，不要包含任何解释或markdown标记
2. **必须使用上面提供的表名**，不要猜测或使用其他表名
3. **不要在表名前加数据库名前缀**（错误示例：`sczsv4.4.1`.`users`，正确示例：`o_team_user`）
4. 使用反引号包裹表名和字段名
5. 确保SQL语法正确
6. 考虑样本数据的格式
7. 如果涉及时间查询，注意时间字段的格式
8. 优先使用索引字段进行查询

【表名参考】
- 团队成员/员工/公司人数：使用 `o_team_user` 表
- 用户信息：使用 `o_user` 表
- 打卡记录：使用 `o_user_clock` 表
- 任务/项目：使用 `o_project` 表
"""

            # 使用LLM生成SQL
            response = self.llm.invoke(full_prompt)

            # 提取内容
            if hasattr(response, 'content'):
                sql = response.content
            else:
                sql = str(response)

            # 清理SQL（移除可能的markdown标记）
            sql = self._clean_sql(sql)

            return sql

        except Exception as e:
            print(f"✗ SQL生成失败: {str(e)}")
            raise

    def execute_sql(self, sql: str, limit: int = 10) -> List[Dict]:
        """
        执行SQL查询

        Args:
            sql: SQL查询语句
            limit: 返回结果的最大行数

        Returns:
            查询结果列表
        """
        try:
            # 1. 权限验证
            if self.user_context:
                is_valid, message = self.permission_manager.validate_query_permission(sql, self.user_context)
                if not is_valid:
                    raise PermissionError(f"权限不足: {message}")

                # 2. 应用数据权限过滤
                original_sql = sql
                sql = self.permission_manager.get_filter_conditions(sql, self.user_context)

                # 打印权限过滤信息（调试用）
                if sql != original_sql:
                    print(f"  🔒 应用数据权限过滤")
                    print(f"     用户: {self.user_context.user_id}, 团队: {self.user_context.team_id}")

            # 3. 添加LIMIT限制（如果SQL中没有）
            if 'LIMIT' not in sql.upper():
                sql = sql.rstrip(';') + f' LIMIT {limit}'

            # 4. 执行查询
            with self.db_manager.engine.connect() as conn:
                result = conn.execute(text(sql))

                # 获取列名
                columns = result.keys()

                # 转换为字典列表
                rows = []
                for row in result:
                    rows.append(dict(zip(columns, row)))

                return rows

        except Exception as e:
            print(f"✗ SQL执行失败: {str(e)}")
            raise

    def query(self, question: str, relevant_tables: List[str] = None, limit: int = 10) -> Dict:
        """
        完整的查询流程：自然语言 -> SQL -> 执行 -> 结果

        Args:
            question: 用户的自然语言问题
            relevant_tables: 相关的表名列表（可选）
                - 如果指定：使用指定的表（手动模式，加载所有指定的表）
                - 如果不指定：自动识别相关表（自动模式，最多加载10个表）
            limit: 返回结果的最大行数

        Returns:
            包含SQL、结果和元信息的字典
        """
        try:
            print(f"\n问题: {question}")
            print("="*60)

            # 判断是否是用户手动指定的表
            is_user_specified = bool(relevant_tables)

            # 如果没有指定相关表，尝试自动识别
            if not relevant_tables:
                relevant_tables = self._identify_relevant_tables(question)
                if relevant_tables:
                    print(f"🔍 识别到相关表: {', '.join(relevant_tables)}")

            # 生成SQL
            print("正在生成SQL...")
            sql = self.generate_sql(question, relevant_tables, is_user_specified)
            print(f"生成的SQL:\n{sql}\n")

            # 执行SQL
            print("正在执行查询...")
            results = self.execute_sql(sql, limit)
            print(f"✓ 查询成功，返回 {len(results)} 条结果\n")

            return {
                'question': question,
                'sql': sql,
                'results': results,
                'count': len(results),
                'relevant_tables': relevant_tables
            }

        except Exception as e:
            print(f"✗ 查询失败: {str(e)}")
            return {
                'question': question,
                'error': str(e),
                'sql': None,
                'results': []
            }

    def _build_system_prompt(self, relevant_tables: List[str] = None, is_user_specified: bool = False) -> str:
        """
        构建System Prompt

        Args:
            relevant_tables: 相关的表名列表
            is_user_specified: 是否是用户手动指定的表
                - True: 用户手动指定，加载所有表（不限制数量）
                - False: 自动识别，限制最多10个表（避免token超限）
        """
        prompt = """你是一个专业的SQL查询生成助手。你的任务是根据用户的自然语言问题，生成准确的MySQL查询语句。

【重要规则】
1. 严格按照下方的【表字段配置】选择字段，不要随意选择
2. 如果表有字段配置，必须包含配置中的所有基础字段
3. 如果需要关联信息（如创建人姓名），必须使用配置中的 JOIN 语句
4. 不要使用 SELECT *，明确列出所有需要的字段
5. 日期时间字段直接返回，不需要格式化（系统会自动处理）

"""
        # 添加用户上下文信息
        if self.user_context:
            prompt += f"""
当前用户信息：
- 用户ID: {self.user_context.user_id}
- 团队ID: {self.user_context.team_id}
- 角色: {'管理员' if self.user_context.is_admin else '普通用户'}

重要说明：
1. 当用户问"我"、"我的"相关问题时，需要根据表结构使用正确的用户ID字段
2. 例如："我今天打卡了吗" 应该基于当前用户ID查询
3. 数据权限会自动添加，你只需要关注业务逻辑条件

"""

        # 添加Schema信息
        if relevant_tables:
            # 如果是用户手动指定的表，加载所有表；否则限制最多10个表
            if is_user_specified:
                limited_tables = relevant_tables  # 用户指定：不限制数量
                print(f"📋 加载用户指定的 {len(limited_tables)} 个表")
            else:
                limited_tables = relevant_tables[:10]  # 自动识别：限制最多10个
                if len(relevant_tables) > 10:
                    print(f"⚠️  识别到 {len(relevant_tables)} 个表，仅加载前 10 个（避免token超限）")

            schema_info = self.schema_manager.get_schema_prompt(limited_tables)
            prompt += schema_info

            # 添加表字段配置信息
            prompt += "\n" + "="*60 + "\n"
            prompt += "【表字段配置】\n"
            prompt += "以下表有固定的字段返回要求，查询时必须严格遵守：\n"

            has_config = False
            for table_name in limited_tables:
                field_prompt = TableFieldConfig.build_field_selection_prompt(table_name)
                if field_prompt:
                    prompt += field_prompt
                    has_config = True

            if not has_config:
                prompt += "（当前查询的表没有特殊字段配置，请根据问题选择合适的字段）\n"

            prompt += "="*60 + "\n\n"
        else:
            # 如果没有相关表，给一个简短的说明
            prompt += "数据库: sczsv4.4.1 (包含206个表)\n"
            prompt += "请根据问题推测需要查询的表名。\n\n"

        return prompt

    def _identify_relevant_tables(self, question: str) -> List[str]:
        """
        根据问题自动识别相关的表
        使用LLM进行智能识别（而不是简单的关键字匹配）
        """
        try:
            # 获取所有表的简要信息（表名+注释）
            all_tables_info = self.schema_manager.get_all_tables_summary()

            # 构建表识别的prompt
            table_selection_prompt = f"""你是一个数据库表选择专家。根据用户问题，从数据库表列表中选择最相关的表。

数据库中的所有表：
{all_tables_info}

用户问题：{question}

请分析这个问题，选择最相关的表名。

【选择规则】
1. 只选择与问题直接相关的表（最多5个）
2. 优先选择核心业务表
3. 如果问题涉及用户信息/姓名/微信/手机/联系方式，选择 o_user 表
4. 如果问题涉及团队/公司/成员，选择 o_team, o_team_user 表
5. 如果问题涉及打卡/考勤，选择 o_user_clock 表
6. 如果问题涉及任务/项目，选择 o_project 相关表
7. 仔细阅读表的注释，理解表的用途

【输出格式】
只输出表名，用逗号分隔，不要有任何其他内容。
例如：o_user,o_team_user,o_user_clock

如果没有相关表，输出：NONE
"""

            # 调用LLM识别表
            print("🤖 使用LLM智能识别相关表...")
            response = self.llm.invoke(table_selection_prompt)
            result = response.content.strip() if hasattr(response, 'content') else str(response).strip()

            # 解析结果
            if result == 'NONE' or not result:
                print("⚠️  LLM未识别到相关表")
                return None

            # 提取表名（清理可能的markdown标记）
            result = result.strip('`').strip()
            table_names = [t.strip().strip('`').strip() for t in result.split(',')]

            # 验证表名是否存在
            valid_tables = []
            for table_name in table_names:
                if table_name and self.schema_manager.table_exists(table_name):
                    valid_tables.append(table_name)
                else:
                    print(f"⚠️  忽略无效表名: {table_name}")

            return valid_tables if valid_tables else None

        except Exception as e:
            print(f"⚠️  LLM表识别失败: {str(e)}")
            print("⚠️  回退到关键字匹配模式")
            # 如果LLM识别失败，回退到简单的关键字匹配
            return self._identify_relevant_tables_by_keywords(question)

    def _identify_relevant_tables_by_keywords(self, question: str) -> List[str]:
        """
        使用关键字匹配识别相关表（作为LLM识别失败时的fallback）
        """
        keyword_mapping = {
            '任务': ['o_project', 'o_project_user', 'o_project_apply'],
            '团队': ['o_team', 'o_team_user'],
            '公司': ['o_team', 'o_team_user'],
            '成员': ['o_team_user', 'o_user'],
            '员工': ['o_team_user', 'o_user'],
            '人员': ['o_team_user', 'o_user'],
            '多少人': ['o_team_user'],
            '用户': ['o_user', 'o_user_statistic'],
            '打卡': ['o_user_clock'],
            '微信': ['o_user'],
            '微信号': ['o_user'],
            '手机': ['o_user'],
            '电话': ['o_user'],
            '邮箱': ['o_user'],
            '联系方式': ['o_user'],
            '姓名': ['o_user'],
            '单据': ['o_bill', 'o_bill_list', 'o_bill_order'],
            '销售': ['o_bill_order', 'o_bill_team_sale_plan', 'o_bill_team_sale_performance'],
            '库存': ['o_bill_team_stock', 'o_bill_team_user_stock'],
            '采购': ['o_bill_team_produce_plan', 'o_bill_order'],
            '客户': ['o_bill_team_customer'],
            '供应商': ['o_bill_team_supplier'],
            '仓库': ['o_bill_team_warehouse', 'o_bill_team_stock'],
            '报表': ['o_bill_team_report'],
            '售后': ['o_bill_sale_order', 'o_bill_sale_evaluate'],
        }

        relevant_tables = []
        for keyword, tables in keyword_mapping.items():
            if keyword in question:
                relevant_tables.extend(tables)

        # 去重
        return list(set(relevant_tables)) if relevant_tables else None

    def _clean_sql(self, sql: str) -> str:
        """清理SQL语句"""
        # 移除markdown代码块标记
        sql = sql.replace('```sql', '').replace('```', '')
        # 移除多余的空白
        sql = sql.strip()
        return sql

# ==================== 主程序 ====================

class TextToSQLApp:
    """Text-to-SQL应用主类"""

    def __init__(self, user_context: Optional[UserContext] = None):
        self.db_manager = None
        self.schema_manager = None
        self.engine = None
        self.user_context = user_context

    def set_user_context(self, user_id: int, team_id: int, is_admin: bool = False):
        """
        设置用户上下文（权限控制）

        Args:
            user_id: 用户ID
            team_id: 团队ID
            is_admin: 是否是管理员
        """
        self.user_context = create_user_context(user_id, team_id, is_admin)

        # 如果引擎已初始化，更新引擎的用户上下文
        if self.engine:
            self.engine.user_context = self.user_context

        print(f"✓ 用户上下文已设置: {self.user_context}")

    def initialize(self):
        """初始化应用"""
        print("="*60)
        print("Text-to-SQL 自然语言查询系统")
        print("="*60)
        print()
        # self.set_user_context(200278, 666666,True)
        self.set_user_context(200287, 666666,True)

        # 显示权限模式
        if self.user_context:
            role = "管理员" if self.user_context.is_admin else "普通用户"
            print(f"🔒 权限模式: {role} (用户{self.user_context.user_id}, 团队{self.user_context.team_id})")
        else:
            print("⚠️  警告: 未设置用户上下文，将以无权限限制模式运行")

        # 初始化数据库管理器
        print("\n1. 正在连接数据库...")
        self.db_manager = DatabaseManager(Config.DB_CONFIG)
        self.db_manager.connect()

        # 初始化Schema管理器
        print("\n2. 正在加载数据库Schema...")
        self.schema_manager = SchemaManager(Config.SCHEMA_FILE)
        self.schema_manager.load_schema()
      

        # 初始化查询引擎
        print("\n3. 正在初始化LLM...")
        self.engine = TextToSQLEngine(
            self.db_manager,
            self.schema_manager,
            Config.get_llm_config(),
            self.user_context  # 传入用户上下文
        )
        self.engine.initialize()

        print("\n" + "="*60)
        print("✓ 系统初始化完成！")
        print("="*60)

    def query(self, question: str, **kwargs):
        """执行查询"""
        return self.engine.query(question, **kwargs)

    def interactive_mode(self):
        """交互式查询模式"""
        print("\n进入交互式查询模式 (输入 'quit' 或 'exit' 退出)\n")

        while True:
            try:
                question = input("请输入您的问题: ").strip()

                if question.lower() in ['quit', 'exit', 'q']:
                    print("再见！")
                    break

                if not question:
                    continue

                # 执行查询
                result = self.query(question)

                # 显示结果
                if result.get('results'):
                    print("\n查询结果:")
                    print("-"*60)
                    for i, row in enumerate(result['results'], 1):
                        print(f"{i}.")
                        # 使用智能格式化器美化输出
                        formatted = ResultFormatter.format_result_smart(row)
                        print(formatted)
                        print()  # 空行分隔
                    print("-"*60)
                elif result.get('error'):
                    print(f"\n错误: {result['error']}")
                else:
                    print("\n没有找到结果")

                print()

            except KeyboardInterrupt:
                print("\n\n再见！")
                break
            except Exception as e:
                print(f"\n发生错误: {str(e)}\n")

    def close(self):
        """关闭应用"""
        if self.db_manager:
            self.db_manager.close()

# ==================== 使用示例 ====================

def json_serializer(obj):
    """JSON序列化辅助函数"""
    from datetime import datetime, date
    from decimal import Decimal

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    return str(obj)

def main():
    """主函数"""
    # 创建应用实例
    app = TextToSQLApp()

    try:
        # 初始化
        app.initialize()

        # 示例查询（可以注释掉进入交互模式）
        examples = [
            "列出所有团队信息",
            "查询今天的打卡记录",
            "显示未完成的任务",
            "团主是谁",
            "当月的销售任务有哪些"
        ]

        print("\n" + "="*60)
        print("示例查询:")
        print("="*60)

        for question in examples[:2]:  # 只运行前2个示例
            result = app.query(question, limit=5)
            if result.get('results'):
                print(f"\n结果预览 (前5条):")
                for row in result['results'][:3]:
                    print(json.dumps(row, ensure_ascii=False, indent=2, default=json_serializer))
            print("\n" + "-"*60 + "\n")

        # 进入交互模式
        app.interactive_mode()

    finally:
        # 清理资源
        app.close()

if __name__ == '__main__':
    main()
