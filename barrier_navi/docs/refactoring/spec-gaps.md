# 仕様差分メモ

## 目的

この文書は、Phase 1 で確認した「既存ドキュメント」「現状実装」「今後の判断が必要な点」の差分を記録する。

リファクタリング中は、ここにある差分を勝手に仕様変更せず、現状実装を守る。

## G-001: 身体障害向け評価項目数

### Existing Docs

- `README.md` と `docs/README.md`: 身体障害向け 12 項目
- `docs/スコア計算ロジック説明.txt`: 身体障害向け 12 項目
- `docs/WEBアプリケーション概要.txt`: 身体障害向け 12 項目
- `docs/barianavi_spec.md`: 身体障害向け 15 項目
- `docs/プログラム概要.txt`: 身体障害向け 15 項目

### Implementation

`BODY_METRIC_DEFINITIONS` は 12 項目。

### Phase 1 Decision

現状仕様は 12 項目として固定する。

### Follow-up

15 項目へ拡張するかは、リファクタリング完了後の仕様変更として別途判断する。

## G-002: 視覚障害向け評価項目数

### Existing Docs

- `README.md` と `docs/README.md`: 視覚障害向け 9 項目
- `docs/スコア計算ロジック説明.txt`: 視覚障害向け 9 項目
- `docs/WEBアプリケーション概要.txt`: 視覚障害向け 9 項目

### Implementation

`VISION_METRIC_DEFINITIONS` は 10 項目。

### Phase 1 Decision

現状仕様は 10 項目として固定する。

### Follow-up

ドキュメント側を実装に合わせるか、実装を 9 項目へ戻すか判断が必要。

## G-003: API パス表記

### Existing Docs

`docs/barianavi_spec.md` では以下の API がドラフトとして記載されている。

```text
GET /api/stations/body
GET /api/stations/{id}/body
```

### Implementation

実装されている API は以下。

```text
GET /api/body/stations
GET /api/body/stations/<id>
```

聴覚・視覚も同様に `/api/hearing/stations`、`/api/vision/stations`。

### Phase 1 Decision

現状実装の URL を固定する。

### Follow-up

旧ドラフト表記は docs 更新時に修正する。

## G-004: 重み付けスコア

### Existing Docs

`docs/barianavi_spec.md` では `weight_i` を使う加重平均が記載されている。

`README.md` でも `/api/body/stations` のクエリとして `weights` が記載されている。

### Implementation

`weights` は読み取られていない。

現状のスコアは達成項目数の単純カウント。

```text
met_items / total_items
```

### Phase 1 Decision

重み付けなしの単純カウントを現状仕様として固定する。

### Follow-up

重み付けスコアを導入する場合は、仕様変更としてテスト追加後に実装する。

## G-005: 絞り込みパラメータ

### Existing Docs

README では `weights` が記載されている。

### Implementation

実装されている絞り込みパラメータは `filters`。

```text
filters=["has_accessible_gate","platform_ratio"]
```

### Phase 1 Decision

`filters` を現状仕様として固定する。

### Follow-up

README/API docs のクエリ説明を実装に合わせる。

## G-006: 数値型フィルタ条件

### Expected From Scoring

数値型スコアは `required` 以上で達成。

例:

```text
num_slopes >= 2
```

### Implementation

数値型フィルタは `> 0`。

```text
num_slopes > 0
```

### Phase 1 Decision

現状の絞り込み仕様は `> 0` として固定する。

### Follow-up

スコア達成条件とフィルタ条件を一致させるか判断する。

## G-007: `users_preferences` の部分更新

### Expected From Comments

コードコメント上は、リクエストで preference 項目が省略された場合、既存値を保持する意図が読み取れる。

### Implementation

既存レコード更新時、`disability_type`、`favorite_stations`、`preferred_features` は、値が `None` の場合に `NULL` 更新される。

そのため、省略フィールドもクリアされる可能性がある。

### Phase 1 Decision

現状挙動を仕様として記録するが、要注意事項とする。

### Follow-up

プロフィール更新 API の部分更新 semantics を明確にする。

## G-008: `.gitignore` の配置

### Existing Docs

README のファイル構成では `.gitignore` がプロジェクト直下にあるように記載されている。

### Implementation

実際には `barrier_navi/.gitignore` が存在する。

リポジトリ直下には `.gitignore` が存在しない。

### Phase 1 Decision

現状配置を記録する。

### Follow-up

ルート `.gitignore` を追加するか、README の構成を修正するか判断する。

## G-009: `.env` の配置

### Existing Docs

README では `.env` を作成する説明がある。

Docker README では `barrier_navi` フォルダをプロジェクトルートとして `.env` を置く説明になっている。

### Implementation

`api_server.py` は `BASE_DIR/.env` を読み込む。`BASE_DIR` は `barrier_navi`。

### Phase 1 Decision

`.env` の現状配置は `barrier_navi/.env` として固定する。

### Follow-up

`.env.example` を追加するか判断する。

## G-010: Python 実行コマンド

### Existing Docs

README では以下が記載されている。

```text
py backend/api_server.py
```

### Phase 0 Environment

Codex 実行環境では `py` と `python` が PATH 上で見つからなかった。

### Phase 1 Decision

ドキュメント上は現状のまま記録する。

### Follow-up

開発環境セットアップ手順に Python の導入確認を追加する。

## G-011: `init.sql` と `DDL.sql`

### Existing Files

- `database/init.sql`
- `database/DDL.sql`

### Difference

`init.sql` の `users` には `created_at` と `last_login_at` がある。

`DDL.sql` の `users` には `created_at` と `last_login_at` がない。

### Phase 1 Decision

Docker 初期化に使われる `init.sql` を現状基準として扱う。

### Follow-up

DDL を統一するか、用途別ファイルとして明記するか判断する。

## G-012: `login.ts` の API ベース URL

### Implementation

`login.ts` は以下を使用する。

```ts
private apiBaseUrl = 'http://localhost:5000/api';
```

他の主要 TS ファイルは `/api` を使用する。

### Phase 1 Decision

現状仕様として記録する。

### Follow-up

Phase 7 で `/api` に統一するか判断する。

## G-013: パスワードリセット

### Existing Docs

メール送信は未実装と記載されている。

### Implementation

メール送信せず、成功レスポンスを返す。

存在しないメールアドレスでも成功扱いにする。

### Phase 1 Decision

未実装仕様として固定する。

### Follow-up

メール送信を実装する場合は認証機能追加として別途扱う。

## G-014: 平文パスワード比較

### Implementation

bcrypt 検証時の例外時に、開発用として平文比較を行う。

### Phase 1 Decision

現状仕様として記録するが、セキュリティ上の要注意事項とする。

### Follow-up

本番向けリファクタリング時に削除するか判断する。
