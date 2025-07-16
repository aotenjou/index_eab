#!/bin/bash

# 获取所有表格名称
TABLES=$(echo "\dt" | psql -t -A -d azrmedit0x)

# 遍历每个表格并获取其记录数
for table in $TABLES; do
	table=$(echo "${table}" | cut -d '|' -f 2)
    count=$(echo "SELECT COUNT(*) FROM $table" | psql -t -A -d imdbload)
    echo "$table: $count"
done

