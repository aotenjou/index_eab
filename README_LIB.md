## lib

lib是一个用来评估**新索引对于工作负载性能提升**的工具。
输入一个​​查询工作负载 W​​（包含多个查询）和​​候选索引配置集合 C​​。输出每个候选配置对​​整个工作负载​​的成本缩减比例。

### prepare
- Env:ubuntu22.04.
- torch,numpy,sklearn
- **imdb dataset** in **POSTGRES**
- formatted workloads(build within cost/frequency...,you can infer`workload_generator/local/r1000_gt500_5q_300.workload.json` )
- candidate indexes 


### procedure

1. 我们需要从数据库统计信息中各个列的**总行数、dist_frac（唯一值比例）、null_frac（空值比例）**。

2. 对于每个查询，我们从它的执行计划和目前的候选索引，得到**操作类型、操作影响到的基数、索引信息**。

3. 对于每个query plan按node分出来的12维特征向量，使用lib中提供的model进行训练。

### existed work

我在本地实现的cost、stat等数据生成代码都放在了`workload_generator/local`下，其中`/lib`下面是根据本地负载(r1000_gt500_5q_300.workload.json，imdb数据集)通过lib中的方法解析出的相关数据。

我的实现中直接使用workload中现存的物理索引，没有单独生成candidate indexes进行测试，如果需要修改索引集合则替换`workload_generator/local/gen_cost_data_from_r1000.py`中line 65的`query["exist_indexes"]`即可。

