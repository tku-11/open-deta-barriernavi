# P2 アーキテクチャ — 責務分離と互換性境界

**決定日:** 2026-08-21
**目的:** P1で固定したAPI・スコア・プロフィール契約を維持しながら、`api_server.py`へ集中していた設定、スコア、駅取得、静的配信、フロントエンドAPI基底URLの責務を分離する。

## 1. 依存方向

```text
routes / api_server
  -> services
  -> repositories
  -> database_connection

routes / api_server
  -> config

frontend page scripts
  -> frontend/src/api.ts
  -> /api
```

上位層は下位層へ依存するが、サービス・リポジトリは Flask のリクエストやレスポンスを直接扱わない。これにより、スコア計算と駅SQLを Flask テストクライアントなしで検証できる。

## 2. 分離した責務

| 層 | ファイル | 責務 | 維持する互換性 |
| --- | --- | --- | --- |
| 設定 | `backend/config.py` | `.env`読み込み、パス、MySQL設定、Cookie、CORS、レート制限設定 | 既存の環境変数名と既定値 |
| スコアサービス | `backend/services/scoring.py` | 評価定義、単一項目評価、スコア計算、駅レスポンス構築 | P1の12/4/10項目、`score`・`metrics`構造 |
| 駅リポジトリ | `backend/repositories/station_repository.py` | スコア付き一覧・詳細のSQL、接続の生成とクローズ | `filters`、検索、路線・都道府県条件、駅列 |
| ページルート | `backend/routes/pages.py` | 既存HTML、CSS、`dist`の提供 | `/`、`/login`、`/home`、`/index`、`/hearing`、`/vision`、`/profile`、`/detail`、`/styles.css`、`/dist/*` |
| API入口 | `backend/api_server.py` | Flask初期化、セキュリティ、リクエスト解釈、JSON応答、既存認証・生データAPI | 既存のURL、HTTPメソッド、レスポンスキー |
| フロント共通 | `frontend/src/api.ts` | 同一オリジンAPIの基底URLとURL組立 | `/api` 基底URL |

## 3. P2で意図的に変更しないもの

P2は構造変更であり、以下を変更しない。

| 対象 | 維持する内容 |
| --- | --- |
| スコア仕様 | 身体12、聴覚4、視覚10項目。重み付けなし。 |
| 一覧フィルタ | 評価基準を満たす駅をAND条件で残す。 |
| プロフィール更新 | `PATCH`が正規、`PUT`は同じ部分更新として互換維持。 |
| 認証 | 署名付きCookieセッション、bcrypt検証、ログイン試行制限。 |
| UI | ページURL、画面構成、表示デザインは変更しない。 |
| DBスキーマ | テーブル・カラム・JSON保存形式は変更しない。 |

## 4. 回帰防止

P1のスコア・一覧・詳細・プロフィール契約テストに加え、P2ではページURLと新しいESモジュール配布を確認するテストを追加した。TypeScriptをESモジュールとしてビルドし、`login`、`index`、`profile`、`detail`のHTMLは `type="module"` で読み込む。

## 5. 次段階で扱う候補

P2では互換性を優先して、認証・プロフィールと生データ統計APIの全面分割は後続へ残す。次の改善段階では、`UserRepository` と `ProfileService` の導入、残る駅統計SQLのリポジトリ移動、認証・駅APIのBlueprint分割、フロントエンドの評価項目定義共通化を小さなコミット単位で進める。
