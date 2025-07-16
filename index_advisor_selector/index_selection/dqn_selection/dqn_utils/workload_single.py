import json
from dataclasses import dataclass
from typing import Literal, Optional


class Index:
    def __init__(self, table: str, columns: list[str]):
        self.table = table
        self.columns = columns
        self.columns_set = set(columns)
        self.name = f"{self.table}_{'_'.join(self.columns)}_idx"

    def __eq__(self, other) -> bool:
        """
        通过比较索引名称来判断两个索引是否相等。

        Args:
            other: 另一个索引对象

        Returns:
            bool: 如果索引名称相同，则返回True，否则返回False
        """
        if not isinstance(other, Index):
            return False
        return self.name == other.name

    def __hash__(self) -> int:
        """
        返回索引名称的哈希值，使索引可以用于集合操作。

        Returns:
            int: 索引名称的哈希值
        """
        return hash(self.name)

    def __repr__(self) -> str:
        return f"Index({self.table}, {self.columns})"

    def __str__(self) -> str:
        return f"{self.table}({','.join(self.columns)})"

    def is_permutation(self, other: "Index") -> bool:
        """
        检查两个索引是否是相同列的排列组合. 如 (a,b) 和 (b,a).
        """
        return self.table == other.table and set(self.columns) == set(other.columns)

    def is_prefix(self, other: "Index") -> bool:
        """
        检查一个索引是否是另一个索引的前缀. 如 (a,b) 是 (a,b,c) 的前缀.
        """
        if len(self.columns) >= len(other.columns):
            self, other = other, self  # 保证 self 是较短的索引
        return self.table == other.table and other.columns[: len(self.columns)] == self.columns

    def is_subset(self, other: "Index") -> bool:
        """
        检查一个索引是否是另一个索引的子集. 如 (a,c) 是 (a,b,c) 的子集.
        """
        if len(self.columns) >= len(other.columns):
            self, other = other, self
        return self.table == other.table and self.columns_set.issubset(other.columns_set)

    def create_sql(
        self,
        type: Literal["btree", "hash", "gist", "spgist", "gin", "brin"] = "btree",
    ):
        return f"CREATE INDEX IF NOT EXISTS {self.name} ON {self.table} USING {type} ({','.join(self.columns)});"

    def drop_sql(self):
        return f"DROP INDEX IF EXISTS {self.name};"

    def create_hypopg_sql(
        self,
        type: Literal["btree", "hash", "brin"] = "btree",
    ):
        return f"SELECT hypopg_create_index('{self.create_sql(type)}');"


@dataclass
class QueryInfo:
    """表示一个 SQL 查询的相关信息."""

    sql: str
    tables_columns: dict[str, set[str]]  # SQL 语句涉及的表和列
    large_columns: dict[str, set[str]]  # 不能用于索引的大字段及其所属表
    exist_indexes: set[Index]  # 相关列上已存在的索引
    basic_cost_explain: float  # 使用 explain 得到的基础 cost
    basic_cost_real: Optional[float] = None  # 使用 explain analyze 得到的实际查询时间
    frequency: int = 1  # 查询在 workload 中的频率

    def __post_init__(self):
        self.basic_cost = self.basic_cost_real or self.basic_cost_explain

    def with_frequency(self, frequency: int) -> "QueryInfo":
        """返回一个新的 QueryInfo 对象，频率为 frequency."""
        return QueryInfo(
            sql=self.sql,
            tables_columns=self.tables_columns,
            large_columns=self.large_columns,
            exist_indexes=self.exist_indexes,
            basic_cost_explain=self.basic_cost_explain,
            basic_cost_real=self.basic_cost_real,
            frequency=frequency,
        )

    def __hash__(self) -> int:
        return hash(self.sql)

    def to_dict(self):
        """将 QueryInfo 转换为可序列化的字典"""
        result = {
            "sql": self.sql,
            "tables_columns": {k: list(v) for k, v in self.tables_columns.items()},
            "large_columns": {k: list(v) for k, v in self.large_columns.items()},
            "exist_indexes": [{"table": idx.table, "columns": idx.columns} for idx in self.exist_indexes],
            "basic_cost_explain": self.basic_cost_explain,
            "frequency": self.frequency,
        }
        if self.basic_cost_real is not None:
            result["basic_cost_real"] = self.basic_cost_real
        return result

    @classmethod
    def from_dict(cls, data):
        """从字典创建 QueryInfo 对象"""
        tables_columns = {k: set(v) for k, v in data["tables_columns"].items()}
        large_columns = {k: set(v) for k, v in data["large_columns"].items()}
        exist_indexes = {Index(idx["table"], idx["columns"]) for idx in data["exist_indexes"]}
        basic_cost_real = data.get("basic_cost_real")

        return cls(
            sql=data["sql"],
            tables_columns=tables_columns,
            large_columns=large_columns,
            exist_indexes=exist_indexes,
            basic_cost_explain=data["basic_cost_explain"],
            basic_cost_real=basic_cost_real,
            frequency=data["frequency"],
        )


class Workload:
    def __init__(
        self,
        id: int,
        queries: set[QueryInfo],
        basic_cost_explain: Optional[float] = None,
        basic_cost_real: Optional[float] = None,
    ) -> None:
        self.id = id
        self.queries = queries
        self.sqls = [q.sql for q in queries]
        self.tables_columns: dict[str, set[str]] = {}
        self.large_columns: dict[str, set[str]] = {}
        self.exist_indexes: set[Index] = set()
        self.basic_cost_explain = basic_cost_explain or sum(q.basic_cost_explain * q.frequency for q in queries)
        if basic_cost_real is not None:
            self.basic_cost_real = basic_cost_real
        elif all(q.basic_cost_real is not None for q in queries):
            self.basic_cost_real = sum((q.basic_cost_real or 0) * q.frequency for q in queries)
        else:
            self.basic_cost_real = None
        self.basic_cost = basic_cost_real or basic_cost_explain or sum(q.basic_cost * q.frequency for q in queries)
        for q in queries:
            for table, columns in q.tables_columns.items():
                self.tables_columns.setdefault(table, set()).update(columns)
            for table, columns in q.large_columns.items():
                self.large_columns.setdefault(table, set()).update(columns)
            self.exist_indexes.update(q.exist_indexes)

    def sprint_tables_columns(self) -> str:
        return "\n".join([f"{table}({','.join(columns)})" for table, columns in self.tables_columns.items()])

    def sprint_large_columns(self) -> str:
        return "\n".join([f"{table}({','.join(columns)})" for table, columns in self.large_columns.items()])

    def sprint_exist_indexes(self) -> str:
        return "\n".join([str(index) for index in self.exist_indexes])

    def sprint_sqls(self) -> str:
        return "\n".join(self.sqls)

    def to_dict(self):
        """将 Workload 转换为可序列化的字典"""
        result = {
            "id": self.id,
            "queries": [q.to_dict() for q in self.queries],
            "tables_columns": {k: list(v) for k, v in self.tables_columns.items()},
            "large_columns": {k: list(v) for k, v in self.large_columns.items()},
            "exist_indexes": [{"table": idx.table, "columns": idx.columns} for idx in self.exist_indexes],
            "basic_cost_explain": self.basic_cost_explain,
        }
        if self.basic_cost_real is not None:
            result["basic_cost_real"] = self.basic_cost_real
        return result

    @classmethod
    def from_dict(cls, data):
        """从字典创建 Workload 对象"""
        queries = {QueryInfo.from_dict(q) for q in data["queries"]}
        return cls(
            id=data["id"],
            queries=queries,
            basic_cost_explain=data["basic_cost_explain"],
            basic_cost_real=data.get("basic_cost_real"),
        )


def load_workloads(path: str) -> list[Workload]:
    """从指定路径加载数据集."""
    with open(path, "r", encoding="utf-8") as f:
        workloads_data = json.load(f)

    # 使用 from_dict 方法将序列化的数据转换回 Workload 对象
    workloads = [Workload.from_dict(w_data) for w_data in workloads_data]

    # 检查数据有效性
    assert len(workloads) > 0, "加载的 workloads 数据为空"
    assert all(w.id == i for i, w in enumerate(workloads)), "Workload ID 不连续或不是从0开始"

    # logger.info(f"从 {path} 加载了 {len(workloads)} 个 workloads")
    return workloads
