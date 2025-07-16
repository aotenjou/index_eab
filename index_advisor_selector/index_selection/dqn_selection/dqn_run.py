# -*- coding: utf-8 -*-
# @Project: index_eab
# @Module: dqn_run
# @Author: Wei Zhou
# @Time: 2023/8/16 16:15

import os
import time
import pickle
import logging
import json
import Model as model
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

from index_advisor_selector.index_selection.dqn_selection.dqn_utils import Encoding as en
from index_advisor_selector.index_selection.dqn_selection.dqn_utils import ParserForIndex as pi
from index_advisor_selector.index_selection.dqn_selection.dqn_utils.Common import get_parser, set_logger, gen_cands
from index_advisor_selector.index_selection.dqn_selection.dqn_utils.workload_single import *

conf = {"LR": 0.002, "EPSILON": 0.97, "Q_ITERATION": 200, "U_ITERATION": 5, "BATCH_SIZE": 64,
        "GAMMA": 0.95, "EPISODES": 1000, "LEARNING_START": 600, "DECAY_EP": 50, "MEMORY_CAPACITY": 20000}


def train_dqn(args):
    conf["NAME"] = args.exp_id
    conf["EPISODES"] = args.epoch

    time_start = time.time()

    index_mode = "hypo"
    if not os.path.exists(os.path.dirname(args.logdir.format(args.exp_id))):
        os.makedirs(os.path.dirname(args.logdir.format(args.exp_id)))
    if not os.path.exists(os.path.dirname(args.model_save.format(args.exp_id, 0))):
        os.makedirs(os.path.dirname(args.model_save.format(args.exp_id, 0)))
    set_logger(args.runlog.format(args.exp_id))

    logging.info(f"Load workload from `{args.work_load}`.")



    # if args.work_load.endswith(".pickle"):
    #     with open(args.work_load, "rb") as rf:
    #         workload = pickle.load(rf)
    # elif args.work_load.endswith(".sql"):
    #     with open(args.work_load, "r") as rf:
    #         workload = rf.readlines()
    # elif args.work_load.endswith(".json"):  # 新增json文件解析
    #     with open(args.work_load, "r", encoding="utf-8") as rf:
    #         workload = json.load(rf)

    workloads = load_workloads(args.work_load)# 加载出来是一个以workload_single中的workload类为元素的list
    # 合并所有workload中的所有queries
    all_queries = []
    all_frequencies = []
    for w in workloads:
        for q in w.queries:
            all_queries.append(q.sql)
            all_frequencies.append(q.frequency if hasattr(q, 'frequency') else 1)
    
    workload = all_queries
    frequency = all_frequencies
    # print(workload)

    if os.path.exists(args.cand_load):
        logging.info(f"Load candidate from `{args.cand_load}`.")
        with open(args.cand_load, "rb") as rf:
            index_candidates = pickle.load(rf)
    else:
        logging.info(f"Generate candidate based on `{args.work_load}`.")
        enc = en.encoding_schema(args.conf_load)
        sql_parser = pi.Parser(enc["attr"])
        print(sql_parser)
        index_candidates = gen_cands(workload, sql_parser)
        # print(index_candidates)

    agent = model.DQN(args, workload, frequency, index_candidates, index_mode,
                      conf, args.is_dnn, args.is_ps, args.is_double, args.a, args.action_mode)
    best_indexes, last_indexes = agent.train()

    time_end = time.time()

    indexes = list()
    for _i, _idx in enumerate(last_indexes):
        if _idx == 1.0:
            indexes.append(index_candidates[_i])

    no_cost, ind_cost = list(), list()
    total_no_cost, total_ind_cost = 0, 0

    agent.envx.pg_client2.delete_indexes()
    for query in workload:
        cost = agent.envx.pg_client2.get_queries_cost([query])[0]
        no_cost.append(cost)
        total_no_cost += cost

    for index in indexes:
        agent.envx.pg_client2.execute_create_hypo(index)
    for query in workload:
        cost = agent.envx.pg_client2.get_queries_cost([query])[0]
        ind_cost.append(cost)
        total_ind_cost += cost
    agent.envx.pg_client2.delete_indexes()

    data = {"workload": workload,
            "indexes": indexes,
            "no_cost": no_cost,
            "total_no_cost": total_no_cost,
            "ind_cost": ind_cost,
            "total_ind_cost": total_ind_cost,
            "sel_info": {"time_duration": time_end - time_start}}
    return data


def get_dqn_res(args):
    time_start = time.time()

    index_mode = "hypo"

    # if args.work_load.endswith(".pickle"):
    #     with open(args.work_load, "rb") as rf:
    #         workload = pickle.load(rf)
    # elif args.work_load.endswith(".sql"):
    #     with open(args.work_load, "r") as rf:
    #         workload = rf.readlines()
    workloads = load_workloads(args.work_load)# 加载出来是一个以workload_single中的workload类为元素的list
    # 合并所有workload中的所有queries
    all_queries = []
    all_frequencies = []
    for w in workloads:
        for q in w.queries:
            all_queries.append(q.sql)
            all_frequencies.append(q.frequency if hasattr(q, 'frequency') else 1)
    
    workload = all_queries
    frequency = all_frequencies

    if os.path.exists(args.cand_load):
        with open(args.cand_load, "rb") as rf:
            index_candidates = pickle.load(rf)
    else:
        enc = en.encoding_schema(args.conf_load)
        sql_parser = pi.Parser(enc["attr"])

        index_candidates = gen_cands(workload, sql_parser)

    agent = model.DQN(args, workload, frequency, index_candidates, index_mode,
                      conf, args.is_dnn, args.is_ps, args.is_double, args.a, args.action_mode)
    _indexes = agent.infer()

    time_end = time.time()

    indexes = list()
    for _i, _idx in enumerate(_indexes):
        if _idx == 1.0:
            indexes.append(index_candidates[_i])

    no_cost, ind_cost = list(), list()
    total_no_cost, total_ind_cost = 0, 0

    agent.envx.pg_client2.delete_indexes()
    for query in workload:
        cost = agent.envx.pg_client2.get_queries_cost([query])[0]
        no_cost.append(cost)
        total_no_cost += cost

    for index in indexes:
        agent.envx.pg_client2.execute_create_hypo(index)
    for query in workload:
        cost = agent.envx.pg_client2.get_queries_cost([query])[0]
        ind_cost.append(cost)
        total_ind_cost += cost
    agent.envx.pg_client2.delete_indexes()

    data = {"workload": workload,
            "indexes": indexes,
            "no_cost": no_cost,
            "total_no_cost": total_no_cost,
            "ind_cost": ind_cost,
            "total_ind_cost": total_ind_cost,
            "sel_info": {"time_duration": time_end - time_start}}
    return data


if __name__ == "__main__":
    parser = get_parser()
    args = parser.parse_args()

    # (0813): newly added.
    logging.disable(logging.DEBUG)

    if args.action_mode == "train":
        train_dqn(args)
    elif args.action_mode == "infer":
        data = get_dqn_res(args)
        print(data)
