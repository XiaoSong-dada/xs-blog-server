from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BuiltQuery:
    data_sql: str
    count_sql: str
    params: tuple[Any, ...]


@dataclass
class QueryParts:
    """
    轻量 SQL 片段收集器：
    - 只负责 WHERE 条件与参数的拼装
    - 不负责执行 SQL
    """

    conditions: list[str] = field(default_factory=list)
    params: list[Any] = field(default_factory=list)

    def where_eq(self, column: str, value: Any) -> None:
        """column = %s（value 不为 None 才加）"""
        if value is not None:
            self.conditions.append(f"{column} = %s")
            self.params.append(value)

    def where_like(
        self, column: str, value: str | None, case_insensitive: bool = True
    ) -> None:
        """column ILIKE/LIKE %s（value 非空才加），自动包裹 %value%"""
        if value:
            op = "ILIKE" if case_insensitive else "LIKE"
            self.conditions.append(f"{column} {op} %s")
            self.params.append(f"%{value}%")

    def where_in_bool(self, column: str) -> None:
        """用于 bool 不筛选的场景：不加条件即可；保留这个函数只是让调用更语义化"""
        # bool 不筛选：什么都不做
        return

    def where_is_null(self, column: str) -> None:
        if column:
            self.conditions.append(f"{column} IS NULL")

    def where_sql(self) -> str:
        """返回拼好的 WHERE ...（无条件则返回空字符串）"""
        return (" WHERE " + " AND ".join(self.conditions)) if self.conditions else ""
