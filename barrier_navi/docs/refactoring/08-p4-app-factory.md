# P4 アプリファクトリと駅API境界

**決定日:** 2026-08-21
**目的:** P3で残した駅関連APIを `api_server.py` から移し、Flask初期化を `create_app()` に集約する。既存URL、HTTPメソッド、JSON形式、`from api_server import app`、`py backend/api_server.py` の起動方式は維持する。

## 1. 駅APIの責務境界

| 層 | 実装 | 責務 |
| --- | --- | --- |
| HTTP | `backend/routes/stations.py` | 生データ一覧・詳細、件数、都道府県、通常統計、平均値、中央値、駅名検索、路線一覧の入力解釈とJSON応答。 |
| データ変換 | `backend/services/station_statistics.py` | 平均値・中央値の計算、メトリクス定義に対応するレスポンス整形。 |
| DBアクセス | `backend/repositories/station_repository.py` | 生データ、通常統計、平均値集計、中央値の正規化済み元行、検索、路線一覧のSQL。 |

`routes/stations.py` は `DatabaseConnection` を直接importせず、注入された `StationRepository` ファクトリだけを使用する。統計サービスはFlaskとDB接続をimportせず、辞書・数値の変換に限定する。

## 2. アプリケーションファクトリ

`api_server.py` は `create_app() -> Flask` を提供する。ファクトリは次の組み立てだけを担当する。

| 初期化対象 | 役割 |
| --- | --- |
| Flask設定 | 署名付きセッションCookie設定と静的ファイル設定。 |
| CORS | `CORS_ALLOWED_ORIGINS` が明示された場合だけ `/api/*` に適用。 |
| Limiter | IP単位のレート制限ストレージと429の統一エラー応答。 |
| 依存注入 | ユーザー・駅リポジトリファクトリ、認証デコレータ、統一エラー関数をBlueprintへ渡す。 |
| Blueprint登録 | ページ、認証、スコア駅、生データ・統計駅の各Blueprintを登録。 |

> モジュール末尾の `app = create_app()` は、既存テストの `from api_server import app` と従来のスクリプト起動を後方互換に保つために残す。

## 3. 維持するAPI契約

| URL | 維持内容 |
| --- | --- |
| `/api/stations`、`/api/stations/<id>` | 生データの一覧・詳細と既存の`success`、`data`、`count`構造。 |
| `/api/stations/count`、`/prefectures`、`/statistics` | P3からの生データ・通常統計のJSON構造。 |
| `/api/stations/averages`、`/medians` | `mode`、`metric_averages`／`metric_medians`、`raw_averages`／`raw_medians`構造。 |
| `/api/stations/search` | 空の`keyword`で400、検索結果に`data`と`count`。 |
| `/api/lines` | 分割・重複除去・ソート済み路線名の`data`配列。 |
| `/api/auth/*`、`/api/{body|hearing|vision}/stations*` | P0〜P3の認証・プロフィール・スコア契約を変更しない。 |

## 4. 回帰防止

`test_raw_station_routes.py` を拡張し、平均値・中央値・検索・路線一覧の成功／失敗レスポンスを固定した。加えて `test_app_factory.py` は、`create_app()` が新しい独立アプリを作り、認証・スコア・駅APIの既存ルールを全て登録することを確認する。

P4の完了時点で、Python構文検証、29件の自動テスト、TypeScript配布ビルドを成功させた。実行中アプリでは平均値APIと中央値APIが200、空検索が400、路線一覧が200であることを確認した。
