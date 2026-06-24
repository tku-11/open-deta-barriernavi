# 現状 DB 仕様

## 目的

この文書は、Phase 1 時点の実装に基づく DB、環境変数、CSV インポート仕様を固定する。

対象ファイル:

- `database/init.sql`
- `database/DDL.sql`
- `database/import_csv_data.py`
- `docker/docker-compose.yml`
- `backend/database_connection.py`
- `backend/api_server.py`

## 接続設定

Flask API は `barrier_navi/.env` を読み込み、以下の値を使用する。

| Variable | Default | Description |
| --- | --- | --- |
| `MYSQL_HOST` | `localhost` | MySQL ホスト |
| `MYSQL_PORT` | `3306` | MySQL ポート |
| `MYSQL_USER` | `root` | MySQL ユーザー |
| `MYSQL_PASSWORD` | empty | MySQL パスワード |
| `MYSQL_DATABASE` | `station` | DB 名 |

Docker Compose 環境では、web コンテナに以下が設定される。

| Variable | Value |
| --- | --- |
| `MYSQL_HOST` | `db` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `${MYSQL_USER:-barrier_user}` |
| `MYSQL_PASSWORD` | `${MYSQL_PASSWORD:-barrier_password}` |
| `MYSQL_DATABASE` | `${MYSQL_DATABASE:-station}` |

DB コンテナのホスト側ポートは既定で `3307`、コンテナ側ポートは `3306` である。

## `stations` テーブル

`init.sql` の現状定義。

| Column | Type | Description |
| --- | --- | --- |
| `id` | `INTEGER PRIMARY KEY` | ID |
| `railway_operator` | `VARCHAR(255)` | 鉄道事業者名 |
| `station_name` | `VARCHAR(255)` | 駅名 |
| `line_name` | `TEXT` | 路線名 |
| `prefecture` | `VARCHAR(255)` | 都道府県 |
| `city` | `VARCHAR(255)` | 市区町村等 |
| `step_response_status` | `INTEGER` | 段差への対応 |
| `num_platforms` | `INTEGER` | プラットホーム数 |
| `num_step_free_platforms` | `INTEGER` | 段差解消済みプラットホーム数 |
| `num_elevators` | `INTEGER` | エレベーター設置基数 |
| `num_compliant_elevators` | `INTEGER` | 適合エレベーター設置基数 |
| `num_escalators` | `INTEGER` | エスカレーター設置基数 |
| `num_compliant_escalators` | `INTEGER` | 適合エスカレーター設置基数 |
| `num_other_lifts` | `INTEGER` | その他昇降機設置基数 |
| `num_slopes` | `INTEGER` | 傾斜路設置箇所数 |
| `num_compliant_slopes` | `INTEGER` | 適合傾斜路設置箇所数 |
| `has_tactile_paving` | `INTEGER` | 視覚障害者誘導用ブロックの設置有無 |
| `has_guidance_system` | `INTEGER` | 案内設備の設置有無 |
| `has_accessible_restroom` | `INTEGER` | 障害者対応型便所の設置有無 |
| `has_accessible_gate` | `INTEGER` | 障害者対応型改札口の設置有無 |
| `has_accessible_ticket_machine` | `INTEGER` | 障害者対応型券売機の設置有無 |
| `num_wheelchair_accessible_platforms` | `INTEGER` | 車いす乗降可能プラットホーム数 |
| `has_fall_prevention` | `INTEGER` | 転落防止設備の設置有無 |

### フラグ値の扱い

アプリ上では `1` のみを「設置あり」または「達成」と扱う。

README では以下の意味として説明されている。

| Value | Meaning |
| --- | --- |
| `1` | ○、設置あり |
| `2` | ×、設置なし |
| `3` | -、該当なし |

実装上は `2`、`3`、`NULL` は未達成として扱われる。

## `users` テーブル

`init.sql` の現状定義。

| Column | Type | Description |
| --- | --- | --- |
| `id` | `INT AUTO_INCREMENT PRIMARY KEY` | ユーザー ID |
| `username` | `VARCHAR(50) NOT NULL UNIQUE` | ユーザー名 |
| `email` | `VARCHAR(255) NOT NULL UNIQUE` | メールアドレス |
| `password_hash` | `VARCHAR(255) NOT NULL` | bcrypt ハッシュ |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | 作成日時 |
| `last_login_at` | `DATETIME NULL` | 最終ログイン日時 |

## `users_preferences` テーブル

`init.sql` の現状定義。

| Column | Type | Description |
| --- | --- | --- |
| `user_id` | `INT PRIMARY KEY` | ユーザー ID |
| `disability_type` | `TEXT NULL` | JSON 配列形式 |
| `favorite_stations` | `TEXT NULL` | 駅 ID の JSON 配列 |
| `preferred_features` | `TEXT NULL` | 優先機能の JSON 配列 |
| `created_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP` | 作成日時 |
| `updated_at` | `DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP` | 更新日時 |

`user_id` は `users(id)` を参照し、`ON DELETE CASCADE` が設定される。

## CSV インポート

対象ファイル:

```text
database/tokyo_stations.csv
```

インポートスクリプト:

```text
database/import_csv_data.py
```

### 実行タイミング

Docker 環境では `docker-entrypoint.sh` から Flask 起動前に実行される。

### 接続設定

`import_csv_data.py` は以下を既定値として使う。

| Variable | Default |
| --- | --- |
| `MYSQL_HOST` | `db` |
| `MYSQL_PORT` | `3306` |
| `MYSQL_USER` | `barrier_user` |
| `MYSQL_PASSWORD` | `barrier_password` |
| `MYSQL_DATABASE` | `station` |
| `CSV_FILE_PATH` | `/app/database/tokyo_stations.csv` |

### 既存データの扱い

`main()` は `stations` の件数を確認し、1 件以上存在する場合はインポートをスキップする。

```text
stationsテーブルには既に{count}件のデータが存在します。インポートをスキップします。
```

一方、`import_csv_to_mysql()` は実行されると最初に `DELETE FROM stations` を行う。

そのため、通常運用では `main()` の件数チェックがデータ削除を防ぐ前提である。

### 対応エンコーディング

CSV 読み込みは以下の順で試行される。

```text
utf-8-sig
utf-8
shift_jis
cp932
latin-1
```

### CSV カラムマッピング

CSV ヘッダーは日本語名、英語名、または順序ベースで DB カラムにマッピングされる。

| DB Column | CSV Header Candidates |
| --- | --- |
| `id` | `ID`, `id`, `Id` |
| `railway_operator` | `鉄道事業者名`, `railway_operator`, `Railway Operator` |
| `station_name` | `鉄道駅の名称`, `station_name`, `Station Name` |
| `line_name` | `路線名`, `line_name`, `Line Name` |
| `prefecture` | `都道府県`, `prefecture`, `Prefecture` |
| `city` | `市`, `city`, `City` |
| `step_response_status` | `段差への対応`, `step_response_status` |
| `num_platforms` | `プラットホームの数`, `num_platforms` |
| `num_step_free_platforms` | `段差が解消されているプラットホームの数`, `num_step_free_platforms` |
| `num_elevators` | `エレベーターの設置基数`, `num_elevators` |
| `num_compliant_elevators` | `移動等円滑化基準に適合しているエレベーターの設置基数`, `num_compliant_elevators` |
| `num_escalators` | `エスカレーターの設置基数`, `num_escalators` |
| `num_compliant_escalators` | `移動等円滑化基準に適合しているエスカレーターの設置基数`, `num_compliant_escalators` |
| `num_other_lifts` | `その他の昇降機の設置基数`, `num_other_lifts` |
| `num_slopes` | `傾斜路の設置箇所数`, `num_slopes` |
| `num_compliant_slopes` | `移動等円滑化基準に適合している傾斜路の設置箇所数`, `num_compliant_slopes` |
| `has_tactile_paving` | `視覚障害者誘導用ブロックの設置の有無`, `has_tactile_paving` |
| `has_guidance_system` | `案内設備の設置の有無`, `has_guidance_system` |
| `has_accessible_restroom` | `障害者対応型便所の設置の有無`, `has_accessible_restroom` |
| `has_accessible_gate` | `障害者対応型改札口の設置の有無`, `has_accessible_gate` |
| `has_accessible_ticket_machine` | `障害者対応型券売機の設置の有無`, `has_accessible_ticket_machine` |
| `num_wheelchair_accessible_platforms` | `車いす使用者の円滑な乗降が可能なプラットホームの数`, `num_wheelchair_accessible_platforms` |
| `has_fall_prevention` | `転落防止のための設備の設置の有無`, `has_fall_prevention` |

## `init.sql` と `DDL.sql`

現状、テーブル定義は複数ファイルに存在する。

| File | 用途 |
| --- | --- |
| `database/init.sql` | Docker コンテナ初期化用 |
| `database/DDL.sql` | 手動作成、参照用 |

現状差分:

- `init.sql` の `users` には `created_at` と `last_login_at` がある。
- `DDL.sql` の `users` には `created_at` と `last_login_at` がない。
- `users_preferences` はどちらにも存在するが、実運用では `init.sql` が Docker 初期化に使われる。

## 現状の互換性維持対象

リファクタリング中は以下を維持する。

- `stations` のカラム名
- `users` の `username`、`email`、`password_hash`
- `users_preferences` の JSON 文字列保存形式
- CSV インポートのカラム順序
- Docker Compose のサービス名 `db` と `web`
- Flask API の環境変数名

## Phase 2 以降で確認すること

- Python 実行環境を用意して DB なしテストを走らせる。
- `.env.example` を追加するか判断する。
- `init.sql` と `DDL.sql` の差分をどちらに寄せるか判断する。
- `users_preferences` 更新時に省略フィールドを保持するか、現状どおり NULL にするか判断する。
