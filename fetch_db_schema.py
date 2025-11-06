import pymysql
import json
from datetime import datetime, date
from decimal import Decimal

# 数据库连接配置
DB_CONFIG = {
    'host': '120.26.37.228',
    'port': 9006,
    'user': 'sczs_tmp_query',
    'password': 'KuJL4zQeqcT8.G!EH8pjYc',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

def json_serializer(obj):
    """JSON序列化辅助函数"""
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, bytes):
        return obj.decode('utf-8', errors='ignore')
    return str(obj)

def get_all_databases(connection):
    """获取所有数据库"""
    with connection.cursor() as cursor:
        cursor.execute("SHOW DATABASES")
        databases = [db['Database'] for db in cursor.fetchall()]
        # 过滤掉系统数据库
        databases = [db for db in databases if db not in ['information_schema', 'mysql', 'performance_schema', 'sys']]
    return databases

def get_all_tables(connection, database):
    """获取指定数据库的所有表"""
    with connection.cursor() as cursor:
        cursor.execute(f"USE `{database}`")
        cursor.execute("SHOW TABLES")
        tables = [list(table.values())[0] for table in cursor.fetchall()]
    return tables

def get_table_structure(connection, database, table):
    """获取表结构详细信息"""
    with connection.cursor() as cursor:
        cursor.execute(f"USE `{database}`")

        # 获取列信息（包含注释）
        cursor.execute(f"""
            SELECT
                COLUMN_NAME as 'Field',
                COLUMN_TYPE as 'Type',
                IS_NULLABLE as 'Null',
                COLUMN_KEY as 'Key',
                COLUMN_DEFAULT as 'Default',
                EXTRA as 'Extra',
                COLUMN_COMMENT as 'Comment'
            FROM information_schema.COLUMNS
            WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}'
            ORDER BY ORDINAL_POSITION
        """)
        columns = cursor.fetchall()

        # 获取表注释和引擎信息
        cursor.execute(f"""
            SELECT TABLE_COMMENT, ENGINE, TABLE_ROWS
            FROM information_schema.TABLES
            WHERE TABLE_SCHEMA = '{database}' AND TABLE_NAME = '{table}'
        """)
        table_info = cursor.fetchone()

        # 获取索引信息
        cursor.execute(f"SHOW INDEX FROM `{table}`")
        indexes = cursor.fetchall()

        return {
            'columns': columns,
            'table_comment': table_info['TABLE_COMMENT'] if table_info else '',
            'engine': table_info['ENGINE'] if table_info else '',
            'estimated_rows': table_info['TABLE_ROWS'] if table_info else 0,
            'indexes': indexes
        }

def get_sample_data(connection, database, table, limit=5):
    """获取表的样本数据"""
    with connection.cursor() as cursor:
        cursor.execute(f"USE `{database}`")
        try:
            cursor.execute(f"SELECT * FROM `{table}` LIMIT {limit}")
            return cursor.fetchall()
        except Exception as e:
            print(f"获取表 {database}.{table} 样本数据失败: {str(e)}")
            return []

def main():
    print("开始连接数据库...")

    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        print("✓ 数据库连接成功！\n")

        # 获取所有数据库
        databases = get_all_databases(connection)
        print(f"发现 {len(databases)} 个数据库: {', '.join(databases)}\n")

        all_schema_info = {}

        for database in databases:
            print(f"\n{'='*60}")
            print(f"处理数据库: {database}")
            print(f"{'='*60}")

            tables = get_all_tables(connection, database)
            print(f"发现 {len(tables)} 个表")

            database_info = {
                'database': database,
                'tables': {}
            }

            for table in tables:
                print(f"\n  处理表: {table}")

                # 获取表结构
                structure = get_table_structure(connection, database, table)

                # 获取样本数据
                sample_data = get_sample_data(connection, database, table, limit=5)

                database_info['tables'][table] = {
                    'structure': structure,
                    'sample_data': sample_data
                }

                print(f"    - 列数: {len(structure['columns'])}")
                print(f"    - 样本数据: {len(sample_data)} 条")
                print(f"    - 表注释: {structure['table_comment']}")

            all_schema_info[database] = database_info

        # 保存到JSON文件
        output_file = 'database_schema.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_schema_info, f, ensure_ascii=False, indent=2, default=json_serializer)

        print(f"\n\n{'='*60}")
        print(f"✓ 数据库结构和样本数据已保存到: {output_file}")
        print(f"{'='*60}")

        # 生成简化的schema文件（仅包含表结构，供LLM参考）
        simplified_schema = {}
        for db_name, db_info in all_schema_info.items():
            simplified_schema[db_name] = {}
            for table_name, table_info in db_info['tables'].items():
                simplified_schema[db_name][table_name] = {
                    'comment': table_info['structure']['table_comment'],
                    'columns': [
                        {
                            'name': col['Field'],
                            'type': col['Type'],
                            'null': col['Null'],
                            'key': col['Key'],
                            'default': col['Default'],
                            'extra': col['Extra'],
                            'comment': col.get('Comment', '')  # 添加字段注释
                        }
                        for col in table_info['structure']['columns']
                    ],
                    'sample_data': table_info['sample_data'][:3]  # 只保留3条样本
                }

        simplified_file = 'database_schema_for_llm.json'
        with open(simplified_file, 'w', encoding='utf-8') as f:
            json.dump(simplified_schema, f, ensure_ascii=False, indent=2, default=json_serializer)

        print(f"✓ LLM参考schema已保存到: {simplified_file}")

        # 生成人类可读的markdown文档
        generate_markdown_doc(all_schema_info)

        connection.close()

    except Exception as e:
        print(f"\n✗ 错误: {str(e)}")
        import traceback
        traceback.print_exc()

def generate_markdown_doc(schema_info):
    """生成人类可读的Markdown文档"""
    md_content = "# 数据库结构文档\n\n"
    md_content += f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    for db_name, db_info in schema_info.items():
        md_content += f"## 数据库: {db_name}\n\n"

        for table_name, table_info in db_info['tables'].items():
            structure = table_info['structure']
            md_content += f"### 表: {table_name}\n\n"

            if structure['table_comment']:
                md_content += f"**说明**: {structure['table_comment']}\n\n"

            md_content += f"**预估行数**: {structure['estimated_rows']}\n\n"

            # 字段信息
            md_content += "**字段列表**:\n\n"
            md_content += "| 字段名 | 类型 | 允许NULL | 键 | 默认值 | 额外信息 | 注释 |\n"
            md_content += "|--------|------|----------|-----|--------|----------|------|\n"

            for col in structure['columns']:
                comment = col.get('Comment', '')
                md_content += f"| {col['Field']} | {col['Type']} | {col['Null']} | {col['Key']} | {col['Default']} | {col['Extra']} | {comment} |\n"

            md_content += "\n"

            # 样本数据
            if table_info['sample_data']:
                md_content += "**样本数据**:\n\n```json\n"
                md_content += json.dumps(table_info['sample_data'][:3], ensure_ascii=False, indent=2, default=json_serializer)
                md_content += "\n```\n\n"

            md_content += "---\n\n"

    with open('database_schema.md', 'w', encoding='utf-8') as f:
        f.write(md_content)

    print(f"✓ Markdown文档已保存到: database_schema.md")

if __name__ == '__main__':
    main()
