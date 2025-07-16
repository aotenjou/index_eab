import os
import csv
import re

# 解析表结构
schema_file = 'schematext.sql'
schema = {}
current_table = None
with open(schema_file, 'r', encoding='utf-8') as f:
    for line in f:
        line = line.strip()
        # 匹配表名
        m = re.match(r'CREATE TABLE (\w+) \(', line)
        if m:
            current_table = m.group(1)
            schema[current_table] = []
            continue
        # 匹配字段
        if current_table and line and not line.startswith(')') and not line.startswith('PRIMARY KEY'):
            # 只取字段名
            field = line.split()[0].strip(',')
            schema[current_table].append(field)
        # 结束表
        if line.startswith(');'):
            current_table = None

# 检查csv文件
for table, fields in schema.items():
    csv_file = f'{table}.csv'
    if not os.path.exists(csv_file):
        print(f'[未找到] {csv_file}')
        continue
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        csv_col_count = len(header)
        schema_col_count = len(fields)
        if csv_col_count != schema_col_count:
            print(f'[字段数不一致] 表: {table} | schema: {schema_col_count} | csv: {csv_col_count} | 文件: {csv_file}')
        else:
            print(f'[OK] {table} 字段数一致: {csv_col_count}') 