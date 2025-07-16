# -*- coding: utf-8 -*-
# @Project: index_eab
# @Module: gen_cost_data_from_r1000
# @Author: Generated for local use
# @Time: 2024/12/19

import os
import sys
import json
import configparser
from tqdm import tqdm

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from index_advisor_selector.index_benefit_estimation.benefit_utils.postgres_dbms import PostgresDatabaseConnector


def convert_exist_indexes_to_indexes_format(exist_indexes):
    """
    将 exist_indexes 格式转换为 "table#col1,col2" 格式
    exist_indexes: [{"table": "table_name", "columns": ["col1", "col2"]}, ...]
    """
    indexes = []
    for idx in exist_indexes:
        table = idx["table"]
        columns = idx["columns"]
        index_str = f"{table}#{','.join(columns)}"
        indexes.append(index_str)
    return indexes


def generate_cost_data_from_r1000_workload(
    workload_file_path,
    db_conf_file_path="/home/azrmedit0x/Index_EAB/configuration_loader/database/db_con.conf",
    output_dir="workload_generator/local/lib",
    split_ratio=(0.7, 0.15, 0.15)  # train, valid, test
):
    """
    从 r1000 工作负载文件生成 cost_data
    
    Args:
        workload_file_path: r1000 workload json 文件路径
        db_conf_file_path: 数据库配置文件路径
        output_dir: 输出目录
        split_ratio: 训练/验证/测试集比例
    """
    
    # 读取数据库配置
    db_conf = configparser.ConfigParser()
    db_conf.read(db_conf_file_path)
    connector = PostgresDatabaseConnector(db_conf, autocommit=True)
    
    # 读取 r1000 workload
    print(f"Loading workload from {workload_file_path}")
    with open(workload_file_path, "r") as rf:
        workloads = json.load(rf)
    
    # 收集所有 queries
    all_queries = []
    for workload in tqdm(workloads, desc="Processing workloads"):
        for query in workload["queries"]:
            # 转换 exist_indexes 格式
            indexes = convert_exist_indexes_to_indexes_format(query["exist_indexes"])
            
            # 构建 cost_data 条目
            cost_data_item = {
                "sql": query["sql"],
                "indexes": indexes,
                "frequency": query.get("frequency", 1),
                "basic_cost_explain": query.get("basic_cost_explain", 0)
            }
            all_queries.append(cost_data_item)
    
    print(f"Total queries collected: {len(all_queries)}")
    
    # 生成 cost_data（获取计划和估算代价）
    cost_data = []
    for item in tqdm(all_queries, desc="Generating cost data"):
        try:
            # 获取无索引的计划和代价
            wo_plan = connector.get_ind_plan(item["sql"], [])
            
            # 获取有索引的计划和代价
            w_plan = connector.get_ind_plan(item["sql"], item["indexes"])
            
            # 构建完整的 cost_data 条目
            cost_data_item = {
                "sql": item["sql"],
                "indexes": item["indexes"],
                "w/o estimated cost": wo_plan["Total Cost"],
                "w/ estimated cost": w_plan["Total Cost"],
                "w/o actual cost": item.get("basic_cost_explain", 0),  # 使用 basic_cost_explain 作为实际代价
                "w/ actual cost": item.get("basic_cost_explain", 0),   # 暂时使用相同值
                "w/o plan": wo_plan,
                "w/ plan": w_plan
            }
            cost_data.append(cost_data_item)
            
        except Exception as e:
            print(f"Error processing query: {e}")
            print(f"SQL: {item['sql'][:100]}...")
            continue
    
    print(f"Successfully generated cost data for {len(cost_data)} queries")
    
    # 划分数据集
    total = len(cost_data)
    train_end = int(total * split_ratio[0])
    valid_end = train_end + int(total * split_ratio[1])
    
    train_data = cost_data[:train_end]
    valid_data = cost_data[train_end:valid_end]
    test_data = cost_data[valid_end:]
    
    print(f"Split: train={len(train_data)}, valid={len(valid_data)}, test={len(test_data)}")
    
    # 保存 cost_data
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存为 src 格式（用于 pre_lib_data.py）
    for split_name, split_data in [("train", train_data), ("valid", valid_data), ("test", test_data)]:
        output_file = os.path.join(output_dir, f"job_cost_data_src_{split_name}.json")
        with open(output_file, "w") as wf:
            json.dump(split_data, wf, indent=2)
        print(f"Saved {split_name} data to {output_file}")
    
    # 保存为 tgt 格式（用于 pre_lib_data.py）
    for split_name, split_data in [("train", train_data), ("valid", valid_data), ("test", test_data)]:
        output_file = os.path.join(output_dir, f"job_cost_data_tgt_{split_name}.json")
        with open(output_file, "w") as wf:
            json.dump(split_data, wf, indent=2)
        print(f"Saved {split_name} data to {output_file}")
    
    return cost_data


if __name__ == "__main__":
    # 配置路径
    workload_file = "workload_generator/local/r1000_gt500_5q_300.workload.json"
    db_conf_file = "/home/azrmedit0x/Index_EAB/configuration_loader/database/db_con.conf"
    
    # 生成 cost_data
    generate_cost_data_from_r1000_workload(
        workload_file_path=workload_file,
        db_conf_file_path=db_conf_file,
        output_dir="workload_generator/local/lib"
    ) 