# P3 API境界 — 認証・駅アクセスの分離

**決定日:** 2026-08-21
**目的:** P0の認証安全性とP1のレスポンス契約を維持したまま、認証・プロフィールと主要な駅アクセスを `api_server.py` から分離する。

## 1. P3で追加した境界

| 境界 | 実装 | 責務 |
| --- | --- | --- |
| ユーザーリポジトリ | `backend/repositories/user_repository.py` | ユーザー検索、登録、最終ログイン更新、ユーザー名更新、選好設定の取得・作成・部分更新。 |
| プロフィールサービス | `backend/services/profile.py` | 選好値の配列検証、駅ID正規化、JSON直列化、DB行からのプロフィールレスポンス構築。 |
| 認証Blueprint | `backend/routes/auth.py` | `/api/auth/*` の入力検証、bcrypt、セッション、レート制限、HTTP応答。 |
| スコア駅Blueprint | `backend/routes/scored_stations.py` | 身体・聴覚・視覚カテゴリの一覧・詳細URL、クエリ解釈、ページング、スコア順ソート。 |
| 駅リポジトリの拡張 | `backend/repositories/station_repository.py` | 生データ一覧・詳細、件数、都道府県、統計、駅名検索、路線一覧のSQL。 |

## 2. 維持する互換性

| 項目 | 維持内容 |
| --- | --- |
| 認証URL | `POST /api/auth/login`、`/logout`、`/signup`、`/reset-password`、`GET/PATCH/PUT /profile`。 |
| 認証動作 | bcrypt、署名付きCookieセッション、本人だけのプロフィール操作、ログイン試行制限、リセット501。 |
| スコアURL | `/api/{body|hearing|vision}/stations` と `.../stations/<id>`。 |
| スコア契約 | 身体12、聴覚4、視覚10項目、`score`・`metrics`レスポンス、P1のフィルタ・ページング。 |
| 生データURL | `/api/stations`、`/api/stations/<id>`、`/count`、`/prefectures`、`/statistics`。 |
| DB形式 | `users_preferences` のJSON配列保存、stationsカラム、既存のMySQL環境変数。 |

## 3. 依存注入方針

`api_server.py` は `user_repository_factory` と `station_repository_factory` を保持し、実行時に `DatabaseConnection` と `MYSQL_CONFIG` をリポジトリへ渡す。この遅延生成により、テストは `api_server.DatabaseConnection` を差し替えたまま実行できる。

> BlueprintはFlaskのHTTP依存を持つ。一方でリポジトリとプロフィールサービスはFlaskをimportせず、DBアクセス・データ変換に限定する。

## 4. 回帰テスト

P3では、生データ一覧・件数・都道府県・統計のレスポンスキーを固定する `test_raw_station_routes.py` を追加した。既存の認証、プロフィール、スコア、ページ配信のテストと合わせ、Blueprint移行後もURLとJSON形状が保たれることを検証する。

## 5. 後続に残す分割

P3では互換性リスクを抑えるため、平均値・中央値、検索・路線取得などの残るレガシー駅ルートは `api_server.py` に残している。ただしSQLの受け皿は `StationRepository` に用意した。次段階では、これらのルートを同リポジトリへ順に委譲し、生データ・統計APIのBlueprint化を完了する。
