"""stationsテーブルへのアクセスを集約するリポジトリ。"""

from typing import Any, Callable, Dict, Iterable, List, Sequence


class StationRepository:
    """駅一覧・詳細取得に必要なSQLと接続の責務を担う。"""

    def __init__(self, connection_factory: Callable[..., Any], connection_config: Dict[str, Any]):
        self._connection_factory = connection_factory
        self._connection_config = connection_config

    def _execute_query(self, query: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        db = self._connection_factory(**self._connection_config)
        try:
            return db.execute_query(query, tuple(params))
        finally:
            db.close()

    def list_scored_rows(
        self,
        columns: Iterable[str],
        definitions: Dict[str, Dict[str, Any]],
        *,
        keyword: str = "",
        prefecture: str | None = None,
        line_name: str | None = None,
        filters: Iterable[str] = (),
    ) -> List[Dict[str, Any]]:
        """P1のフィルタ契約を適用した、スコア計算用の駅行を取得する。"""
        where_clause = "FROM stations WHERE 1=1"
        params: List[Any] = []

        if keyword:
            where_clause += " AND station_name LIKE %s"
            params.append(f"%{keyword}%")
        if prefecture:
            where_clause += " AND prefecture = %s"
            params.append(prefecture)
        if line_name:
            search_line = line_name.replace("線", "")
            where_clause += " AND line_name LIKE %s"
            params.append(f"%{search_line}%")

        for filter_key in filters:
            if filter_key not in definitions:
                continue
            metric_def = definitions[filter_key]
            metric_type = metric_def.get("type")
            if metric_type == "flag":
                where_clause += f" AND {filter_key} = %s"
                params.append(1)
            elif metric_type == "ratio":
                numerator_key = metric_def.get("numerator")
                denominator_key = metric_def.get("denominator")
                if numerator_key and denominator_key:
                    where_clause += (
                        f" AND {denominator_key} > 0"
                        f" AND ({numerator_key} / NULLIF({denominator_key}, 0)) >= %s"
                    )
                    params.append(metric_def.get("required", 0.8))
            elif metric_type == "number":
                where_clause += f" AND {filter_key} >= %s"
                params.append(metric_def.get("required", 0))

        selected_columns = ", ".join(columns)
        query = f"SELECT {selected_columns} {where_clause} ORDER BY station_name"
        return self._execute_query(query, params)

    def get_scored_row(self, station_id: int, columns: Iterable[str]) -> Dict[str, Any] | None:
        """詳細スコア用に駅を1件取得する。"""
        selected_columns = ", ".join(columns)
        rows = self._execute_query(
            f"SELECT {selected_columns} FROM stations WHERE id = %s",
            (station_id,),
        )
        return rows[0] if rows else None

    def list_raw_stations(self, limit: int, offset: int, prefecture: str | None = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM stations WHERE 1=1"
        params: List[Any] = []
        if prefecture:
            query += " AND prefecture = %s"
            params.append(prefecture)
        query += " LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        return self._execute_query(query, params)

    def get_raw_station(self, station_id: int) -> Dict[str, Any] | None:
        rows = self._execute_query("SELECT * FROM stations WHERE id = %s", (station_id,))
        return rows[0] if rows else None

    def count_stations(self) -> int:
        rows = self._execute_query("SELECT COUNT(*) as total FROM stations")
        return int(rows[0]["total"]) if rows else 0

    def list_prefectures(self) -> List[Dict[str, Any]]:
        return self._execute_query(
            """SELECT prefecture, COUNT(*) as count
               FROM stations WHERE prefecture IS NOT NULL
               GROUP BY prefecture ORDER BY count DESC"""
        )

    def get_statistics(self) -> Dict[str, Any]:
        rows = self._execute_query(
            """SELECT
                 COUNT(*) as total_stations,
                 SUM(CASE WHEN has_tactile_paving = 1 THEN 1 ELSE 0 END) as with_tactile_paving,
                 SUM(CASE WHEN has_guidance_system = 1 THEN 1 ELSE 0 END) as with_guidance_system,
                 SUM(CASE WHEN has_accessible_restroom = 1 THEN 1 ELSE 0 END) as with_accessible_restroom,
                 SUM(CASE WHEN has_accessible_gate = 1 THEN 1 ELSE 0 END) as with_accessible_gate,
                 SUM(CASE WHEN num_elevators > 0 THEN 1 ELSE 0 END) as with_elevators
               FROM stations"""
        )
        return rows[0] if rows else {}

    def search_by_station_name(self, keyword: str, limit: int) -> List[Dict[str, Any]]:
        return self._execute_query(
            "SELECT * FROM stations WHERE station_name LIKE %s LIMIT %s",
            (f"%{keyword}%", limit),
        )

    def list_lines(self) -> List[str]:
        rows = self._execute_query(
            "SELECT DISTINCT line_name FROM stations WHERE line_name IS NOT NULL AND line_name != ''"
        )
        lines: set[str] = set()
        for row in rows:
            line_value = row.get("line_name")
            if isinstance(line_value, str):
                lines.update(part.strip() for part in line_value.split("・") if part.strip())
        return sorted(lines)
