"""users と users_preferences のDBアクセスを集約するリポジトリ。"""

from typing import Any, Callable, Dict, List, Optional, Sequence


class UserRepository:
    def __init__(self, connection_factory: Callable[..., Any], connection_config: Dict[str, Any]):
        self._connection_factory = connection_factory
        self._connection_config = connection_config

    def _query(self, query: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
        db = self._connection_factory(**self._connection_config)
        try:
            return db.execute_query(query, tuple(params))
        finally:
            db.close()

    def _execute(self, query: str, params: Sequence[Any] = ()) -> None:
        db = self._connection_factory(**self._connection_config)
        try:
            db.execute_non_query(query, tuple(params))
        finally:
            db.close()

    def find_for_login(self, identifier: str) -> Optional[Dict[str, Any]]:
        rows = self._query(
            "SELECT * FROM users WHERE username = %s OR email = %s LIMIT 1",
            (identifier, identifier),
        )
        return rows[0] if rows else None

    def touch_last_login(self, user_id: int, logged_in_at: Any) -> None:
        self._execute("UPDATE users SET last_login_at = %s WHERE id = %s", (logged_in_at, user_id))

    def username_exists(self, username: str, excluding_user_id: int | None = None) -> bool:
        if excluding_user_id is None:
            rows = self._query("SELECT id FROM users WHERE username = %s LIMIT 1", (username,))
        else:
            rows = self._query(
                "SELECT id FROM users WHERE username = %s AND id != %s LIMIT 1",
                (username, excluding_user_id),
            )
        return bool(rows)

    def email_exists(self, email: str) -> bool:
        return bool(self._query("SELECT id FROM users WHERE email = %s LIMIT 1", (email,)))

    def create_user(self, username: str, email: str, password_hash: str) -> None:
        self._execute(
            "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
            (username, email, password_hash),
        )

    def user_exists(self, user_id: int) -> bool:
        return bool(self._query("SELECT id FROM users WHERE id = %s LIMIT 1", (user_id,)))

    def get_public_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = self._query(
            "SELECT id, username, email FROM users WHERE id = %s LIMIT 1",
            (user_id,),
        )
        return rows[0] if rows else None

    def update_username(self, user_id: int, username: str) -> None:
        self._execute("UPDATE users SET username = %s WHERE id = %s", (username, user_id))

    def get_preferences(self, user_id: int) -> Optional[Dict[str, Any]]:
        rows = self._query(
            "SELECT disability_type, favorite_stations, preferred_features FROM users_preferences WHERE user_id = %s LIMIT 1",
            (user_id,),
        )
        return rows[0] if rows else None

    def preference_exists(self, user_id: int) -> bool:
        return bool(self._query("SELECT user_id FROM users_preferences WHERE user_id = %s LIMIT 1", (user_id,)))

    def update_preferences(self, user_id: int, values: Dict[str, Optional[str]]) -> None:
        assignments: List[str] = []
        params: List[Any] = []
        for field, value in values.items():
            if value is None:
                assignments.append(f"{field} = NULL")
            else:
                assignments.append(f"{field} = %s")
                params.append(value)
        params.append(user_id)
        self._execute(
            f"UPDATE users_preferences SET {', '.join(assignments)} WHERE user_id = %s",
            params,
        )

    def create_preferences(self, user_id: int, values: Dict[str, Optional[str]]) -> None:
        self._execute(
            """INSERT INTO users_preferences
               (user_id, disability_type, favorite_stations, preferred_features)
               VALUES (%s, %s, %s, %s)""",
            (
                user_id,
                values.get("disability_type"),
                values.get("favorite_stations"),
                values.get("preferred_features"),
            ),
        )
