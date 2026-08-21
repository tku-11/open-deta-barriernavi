"""旧来の平文パスワードをbcryptへ一度だけ移行する管理スクリプト。"""

import argparse
import os
import sys

import bcrypt
from dotenv import load_dotenv

from database_connection import DatabaseConnection


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, ".env"))

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
    "database": os.getenv("MYSQL_DATABASE", "station"),
}


def is_bcrypt_hash(value: object) -> bool:
    if not isinstance(value, str):
        return False
    return value.startswith(("$2a$", "$2b$", "$2y$"))


def main() -> int:
    parser = argparse.ArgumentParser(description="users.password_hashの旧形式をbcryptへ移行します。")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="実際に更新を実行します。指定しない場合は件数確認のみです。",
    )
    args = parser.parse_args()

    db = DatabaseConnection(**MYSQL_CONFIG)
    try:
        users = db.execute_query("SELECT id, password_hash FROM users")
        legacy_users = [
            user for user in users
            if user.get("password_hash") and not is_bcrypt_hash(user.get("password_hash"))
        ]

        print(f"確認対象ユーザー数: {len(users)}")
        print(f"移行が必要な旧形式パスワード数: {len(legacy_users)}")

        if not args.apply:
            print("確認のみで終了しました。更新する場合は --apply を指定してください。")
            return 0

        for user in legacy_users:
            legacy_password = user["password_hash"]
            new_hash = bcrypt.hashpw(
                legacy_password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")
            db.execute_non_query(
                "UPDATE users SET password_hash = %s WHERE id = %s",
                (new_hash, user["id"]),
            )

        print(f"bcryptへ移行したユーザー数: {len(legacy_users)}")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
