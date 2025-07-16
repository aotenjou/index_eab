# -*- coding: utf-8 -*-
# @Project: index_eab
# @Module: pre_lib_data_local
# @Author: Wei Zhou (Modified for local use)
# @Time: 2023/10/5 16:11

import os
import sys
import json
import numpy as np
from tqdm import tqdm

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

from index_advisor_selector.index_benefit_estimation.benefit_utils.get_plan_info import tra_plan_ite
from index_advisor_selector.index_benefit_estimation.benefit_utils.benefit_const import ops_join_dict, ops_sort_dict, \
    ops_group_dict, ops_scan_dict


def pre_lib_plan_local():
    """
    本地化版本的 pre_lib_plan，使用本地生成的 stats 文件
    """
    benchmarks = ["job"]  # 只处理 job 基准
    for bench in tqdm(benchmarks):
        for fid in ["src", "tgt"]:
            for did in ["train", "valid", "test"]:
                # 本地化的输入路径
                data_load = f"workload_generator/local/lib/{bench}_cost_data_{fid}_{did}.json"
                
                if not os.path.exists(data_load):
                    print(f"Warning: {data_load} not found, skipping...")
                    continue
                
                with open(data_load, "r") as rf:
                    data = json.load(rf)

                # 加载 stats 文件
                stats_load = f"workload_generator/local/lib/db_stats_{bench}.json"
                if os.path.exists(stats_load):
                    with open(stats_load, "r") as rf:
                        stats = json.load(rf)
                    print(f"Loaded stats from {stats_load}")
                else:
                    print(f"Warning: {stats_load} not found, using default values")
                    stats = {}

                print(f"Processing {bench}_{fid}_{did} with {len(data)} items")

                total_data = list()
                for item in tqdm(data, desc=f"Processing {bench}_{fid}_{did}"):
                    indexes = item["indexes"]
                    wo_plan = item["w/o plan"]
                    nodes = tra_plan_ite(wo_plan)

                    index_ops = list()
                    for ind in indexes:
                        if "#" not in ind:
                            print(f"Warning: Invalid index format: {ind}, skipping...")
                            continue
                            
                        tbl, cols = ind.split("#")[0], ind.split("#")[1].split(",")

                        for no, col in enumerate(cols):
                            for node in nodes:
                                if col in str(node["detail"]):
                                    # 1. operation information (5)
                                    # join, sort, group, scan_range, scan_equal
                                    vec = [0 for _ in range(5)]
                                    typ = node["type"]
                                    if typ in ops_join_dict:
                                        vec[0] = 1
                                    elif typ in ops_sort_dict:
                                        vec[1] = 1
                                    elif typ in ops_group_dict:
                                        vec[2] = 1
                                    elif typ in ops_scan_dict:
                                        # (1005): to be improved. columns with the same name.
                                        if f"{col} =" in str(node["detail"]):
                                            vec[3] = 1
                                        else:
                                            vec[4] = 1

                                    # 2. database statistics (4) - 使用 stats 文件或默认值
                                  
                                    card = np.log(node["detail"]["Plan Rows"])
                                    # except:
                                    #     card = 0.0
                                    
                                    # 使用 stats 数据或默认值
                                    stats_key = f"{tbl}.{col}"
                                    if stats_key in stats:
                                        row = np.log(stats[stats_key]["rows"])
                                        null = stats[stats_key]["null"]
                                        dist = stats[stats_key]["dist"]
                                    # else:
                                    #     # 默认值
                                    #     row = 10.0
                                    #     null = 0.0
                                    #     dist = 100.0

                                    vec.extend([card, row, null, dist])

                                    # 3. index information (3)
                                    if len(cols) == 1:
                                        vec.extend([1, 0, 0])
                                    else:
                                        vec.extend([0, 1, no + 1])

                                    index_ops.append(vec)
                    
                    total_data.append({"feat": index_ops,
                                       "w/o estimated cost": item["w/o estimated cost"],
                                       "w/ estimated cost": item["w/ estimated cost"],
                                       "w/o actual cost": item["w/o actual cost"],
                                       "w/ actual cost": item["w/ actual cost"]})

                # 本地化的输出路径
                data_save = f"workload_generator/local/lib/lib_{bench}_cost_data_{fid}_{did}.json"
                if not os.path.exists(os.path.dirname(data_save)):
                    os.makedirs(os.path.dirname(data_save))
                with open(data_save, "w") as wf:
                    json.dump(total_data, wf, indent=2)
                
                print(f"Saved lib_{bench}_cost_data_{fid}_{did}.json with {len(total_data)} items")


if __name__ == "__main__":
    pre_lib_plan_local() 