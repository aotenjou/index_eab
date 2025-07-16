# -*- coding: utf-8 -*-
# @Project: index_eab
# @Module: get_db_stats
# @Author: Wei Zhou
# @Time: 2023/10/5 16:15

import os
import sys
import json
from decimal import Decimal

from tqdm import tqdm
import configparser

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from index_advisor_selector.index_benefit_estimation.benefit_utils.postgres_dbms import PostgresDatabaseConnector


class IndexEncoder(json.JSONEncoder):
    def default(self, obj):
        # 👇️ if passed in object is instance of Decimal
        # convert it to a float
        if isinstance(obj, Decimal):
            return float(obj)

        # 👇️ otherwise use the default behavior
        return json.JSONEncoder.default(self, obj)


def get_row_null_distinct(db_conf):
    connector = PostgresDatabaseConnector(db_conf, autocommit=True)

    tables = connector.get_tables()
    print(f"Found tables: {tables}")
    
    # 获取每个表的行数
    rows = []
    for table in tables:
        try:
            row_count = connector.exec_fetch(f"SELECT COUNT(*) FROM {table}")
            rows.append([row_count[0]])
        except Exception as e:
            print(f"Error getting row count for table {table}: {e}")
            rows.append([0])

    tbl_info, col_info = dict(), dict()
    for tbl, row in tqdm(zip(tables, rows), desc="Processing tables"):
        try:
            columns = connector.get_cols(tbl)
            tbl_info[tbl] = {"columns": columns, "rows": row[0]}

            # 获取每列的空值比例和唯一值比例
            for col in columns:
                try:
                    # 获取空值比例
                    null_query = f"SELECT COUNT(*) * 1.0 / (SELECT COUNT(*) FROM {tbl}) FROM {tbl} WHERE {col} IS NULL"
                    null_result = connector.exec_fetch(null_query)
                    null_frac = null_result[0] if null_result else 0.0
                    
                    # 获取唯一值比例
                    dist_query = f"SELECT COUNT(DISTINCT {col}) * 1.0 / (SELECT COUNT(*) FROM {tbl}) FROM {tbl}"
                    dist_result = connector.exec_fetch(dist_query)
                    dist_frac = dist_result[0] if dist_result else 0.0
                    
                    col_info[f"{tbl}.{col}"] = {"rows": row[0], "null": null_frac, "dist": dist_frac}
                except Exception as e:
                    print(f"Error processing column {tbl}.{col}: {e}")
                    col_info[f"{tbl}.{col}"] = {"rows": row[0], "null": 0.0, "dist": 0.0}
        except Exception as e:
            print(f"Error processing table {tbl}: {e}")
            continue

    return col_info


if __name__ == "__main__":
    benchmarks = ["job"]  # "tpch", "tpcds", "job"
    for bench in benchmarks:
        if bench == "job":
            db_conf_file = f"/home/azrmedit0x/Index_EAB/configuration_loader/database/db_con.conf"
        else:
            db_conf_file = f"/data/wz/index/index_eab/eab_data/db_info_conf/local_db103_{bench}_1gb.conf"
        db_conf = configparser.ConfigParser()
        db_conf.read(db_conf_file)

        # db_conf["postgresql"]["host"] = "10.26.42.166"
        # db_conf["postgresql"]["database"] = "tpch_1gb103_skew"
        # db_conf["postgresql"]["port"] = "5432"
        # db_conf["postgresql"]["user"] = "wz"
        # db_conf["postgresql"]["password"] = "ai4db2021"

        col_info = get_row_null_distinct(db_conf)

        data_save = f"workload_generator/local/lib/db_stats_{bench}.json"
        if not os.path.exists(os.path.dirname(data_save)):
            os.makedirs(os.path.dirname(data_save))
        with open(data_save, "w") as wf:
            json.dump(col_info, wf, indent=2, cls=IndexEncoder)
        
        print(f"Saved db_stats to {data_save}")
