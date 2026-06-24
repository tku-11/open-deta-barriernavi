# 現状 API 仕様

## 目的

この文書は、Phase 1 時点の実装に基づく API と静的ページ配信の現状仕様を固定する。

対象実装は `backend/api_server.py` である。ここでは理想仕様ではなく、現在の挙動を記録する。

## 共通仕様

### ベース URL

Flask アプリは既定で以下に起動する。

```text
http://localhost:5000
```

API は `/api` 配下に配置される。

### レスポンス形式

通常の成功レスポンスは概ね以下の形式である。

```json
{
  "success": true,
  "data": {}
}
```

一覧系 API では `count` や `total_count` が追加される。

```json
{
  "success": true,
  "data": [],
  "count": 0,
  "total_count": 0
}
```

エラーレスポンスは概ね以下の形式である。

```json
{
  "success": false,
  "error": "error message"
}
```

ただし、エラー文言は Python 例外文字列をそのまま返す箇所がある。

### CORS

`flask_cors.CORS(app)` により、アプリ全体で CORS が有効化されている。

### DB 接続

API はリクエストごとに `DatabaseConnection(**MYSQL_CONFIG)` を作成し、処理後に `db.close()` を呼ぶ実装である。

`MYSQL_CONFIG` は `barrier_navi/.env` から読み込まれる。

```text
MYSQL_HOST
MYSQL_PORT
MYSQL_USER
MYSQL_PASSWORD
MYSQL_DATABASE
```

## 静的ページ配信

| Method | Path | 配信ファイル |
| --- | --- | --- |
| GET | `/` | `frontend/view/login.html` |
| GET | `/login` | `frontend/view/login.html` |
| GET | `/home` | `frontend/view/home.html` |
| GET | `/index` | `frontend/view/index.html` |
| GET | `/hearing` | `frontend/view/hearing.html` |
| GET | `/vision` | `frontend/view/vision.html` |
| GET | `/profile` | `frontend/view/profile.html` |
| GET | `/detail` | `frontend/view/detail.html` |
| GET | `/styles.css` | `frontend/styles.css` |
| GET | `/dist/<path:filename>` | `frontend/dist/<filename>` |

## 認証 API

### POST `/api/auth/login`

ログイン処理。

#### Request Body

```json
{
  "username": "username or email",
  "password": "password"
}
```

`username` はユーザー名またはメールアドレスとして検索される。

#### Success

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "created_at": "...",
    "last_login_at": "..."
  }
}
```

`password` と `password_hash` はレスポンスから除外される。

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | `username` または `password` が空 |
| 401 | ユーザーが存在しない、またはパスワード不一致 |
| 500 | パスワード情報がない、DB 例外など |

#### 現状の注意

- bcrypt 検証に失敗した場合、開発用フォールバックとして平文比較が行われる。
- `last_login_at` カラムが存在する場合は更新される。存在しない場合は例外を握りつぶす。

### POST `/api/auth/signup`

新規ユーザー登録。

#### Request Body

```json
{
  "username": "user",
  "email": "user@example.com",
  "password": "password123"
}
```

#### Success

```json
{
  "success": true,
  "message": "アカウントが作成されました"
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | 必須項目不足 |
| 400 | パスワードが 8 文字未満 |
| 400 | ユーザー名重複 |
| 400 | メールアドレス重複 |
| 500 | 登録失敗、DB 例外など |

#### 現状の注意

- パスワードは bcrypt でハッシュ化して `users.password_hash` に保存する。
- 登録時に `users_preferences` は作成されない。

### POST `/api/auth/reset-password`

パスワードリセット要求。

#### Request Body

```json
{
  "email": "user@example.com"
}
```

#### Success

```json
{
  "success": true,
  "message": "パスワードリセット用のリンクをメールアドレスに送信しました"
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | `email` が空 |
| 500 | DB 例外など |

#### 現状の注意

- メール送信は未実装。
- メールアドレスが存在しない場合も成功レスポンスを返す。

### GET `/api/auth/profile`

プロフィール情報を取得する。

#### Query

| Name | Type | Required | Description |
| --- | --- | --- | --- |
| `user_id` | int | yes | ユーザー ID |

#### Success

```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "user",
    "email": "user@example.com",
    "disability_type": [],
    "favorite_stations": [],
    "preferred_features": []
  }
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | `user_id` がない |
| 404 | ユーザーが存在しない |
| 500 | DB 例外など |

#### 現状の注意

- `users_preferences` が存在しない、または取得に失敗した場合は空配列を返す。
- `favorite_stations` は駅名ではなく、整数化された駅 ID 配列として返る。

### PUT `/api/auth/profile`

プロフィール情報を更新する。

#### Request Body

```json
{
  "user_id": 1,
  "username": "new-user",
  "disability_type": ["身体障害"],
  "favorite_stations": [1, 2],
  "preferred_features": ["エレベーター"]
}
```

#### Success

```json
{
  "success": true,
  "message": "プロフィールを更新しました"
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | `user_id` がない |
| 400 | ユーザー名重複 |
| 404 | ユーザーが存在しない |
| 500 | ユーザー名更新失敗、プロフィール更新失敗、DB 例外など |

#### 現状の注意

- `username` がある場合のみ `users.username` を更新する。
- `disability_type`、`favorite_stations`、`preferred_features` はリストの場合 JSON 文字列として保存する。
- 空配列は `NULL` として保存する。
- 既存の `users_preferences` がある場合、リクエストで省略された preference 項目も `NULL` 更新対象になる実装である。

## 駅データ API

### GET `/api/stations`

駅の生データ一覧を取得する。

#### Query

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `limit` | int | 100 | 取得件数 |
| `offset` | int | 0 | 開始位置 |
| `prefecture` | string | none | 都道府県完全一致 |

#### Success

```json
{
  "success": true,
  "data": [],
  "count": 0
}
```

`data` は `stations` テーブルの全カラムを含む。

### GET `/api/stations/<station_id>`

指定駅の生データを取得する。

#### Success

```json
{
  "success": true,
  "data": {}
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 404 | 駅が存在しない |
| 500 | DB 例外など |

### GET `/api/stations/count`

駅件数を取得する。

#### Success

```json
{
  "success": true,
  "count": 0
}
```

### GET `/api/stations/prefectures`

都道府県別の駅件数を取得する。

#### Success

```json
{
  "success": true,
  "data": [
    {
      "prefecture": "東京都",
      "count": 10
    }
  ]
}
```

`count DESC` で並ぶ。

### GET `/api/stations/statistics`

バリアフリー設備の集計を取得する。

#### Success

```json
{
  "success": true,
  "data": {
    "total_stations": 0,
    "with_tactile_paving": 0,
    "with_guidance_system": 0,
    "with_accessible_restroom": 0,
    "with_accessible_gate": 0,
    "with_elevators": 0
  }
}
```

### GET `/api/stations/search`

駅名で生データを検索する。

#### Query

| Name | Type | Default | Required | Description |
| --- | --- | --- | --- | --- |
| `keyword` | string | empty | yes | 駅名部分一致 |
| `limit` | int | 50 | no | 取得件数 |

#### Success

```json
{
  "success": true,
  "data": [],
  "count": 0
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 400 | `keyword` が空 |
| 500 | DB 例外など |

### GET `/api/lines`

路線名一覧を取得する。

#### Success

```json
{
  "success": true,
  "data": ["山手線"]
}
```

#### 現状の注意

- `stations.line_name` を `・` で分割し、重複排除してソートする。

## スコア付き駅 API

### GET `/api/body/stations`

身体障害向けスコア付き駅一覧を取得する。

### GET `/api/hearing/stations`

聴覚障害向けスコア付き駅一覧を取得する。

### GET `/api/vision/stations`

視覚障害向けスコア付き駅一覧を取得する。

#### Query

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `keyword` | string | empty | 駅名部分一致 |
| `prefecture` | string | none | 都道府県完全一致 |
| `line_name` | string | none | 路線名部分一致。検索前に `線` を除去する |
| `limit` | int | 20 | ページング件数 |
| `offset` | int | 0 | ページング開始位置 |
| `filters` | JSON string | none | 評価項目キーの配列 |
| `sort` | string | `none` | `none`, `score-asc`, `score-desc` |

#### Filter Behavior

`filters` は JSON 配列として解釈される。JSON として不正、または配列でない場合は空配列扱いになる。

```text
filters=["has_accessible_gate","platform_ratio"]
```

評価項目タイプ別の絞り込み:

| Type | SQL 条件 |
| --- | --- |
| `flag` | 対象カラム `= 1` |
| `ratio` | 分母 `> 0` かつ 分子 / 分母 `>= required` |
| `number` | 対象カラム `> 0` |

#### Sort Behavior

- `score-asc`: `score.percentage` 昇順
- `score-desc`: `score.percentage` 降順
- `none`: DB 取得時の `station_name` 昇順

#### Success

```json
{
  "success": true,
  "data": [
    {
      "station_id": 1,
      "station_name": "東京",
      "prefecture": "東京都",
      "city": "千代田区",
      "operator": "JR",
      "line_name": "山手線",
      "score": {
        "met_items": 8,
        "total_items": 12,
        "percentage": 66.7,
        "label": "8/12点"
      }
    }
  ],
  "count": 1,
  "total_count": 100
}
```

### GET `/api/body/stations/<station_id>`

身体障害向けスコア付き駅詳細を取得する。

### GET `/api/hearing/stations/<station_id>`

聴覚障害向けスコア付き駅詳細を取得する。

### GET `/api/vision/stations/<station_id>`

視覚障害向けスコア付き駅詳細を取得する。

#### Success

```json
{
  "success": true,
  "data": {
    "station_id": 1,
    "station_name": "東京",
    "prefecture": "東京都",
    "city": "千代田区",
    "operator": "JR",
    "line_name": "山手線",
    "score": {
      "met_items": 8,
      "total_items": 12,
      "percentage": 66.7,
      "label": "8/12点"
    },
    "metrics": [
      {
        "key": "has_accessible_gate",
        "label": "障害者対応型改札口の設置の有無",
        "value": "○",
        "raw_value": 1,
        "ratio": 1,
        "met": true,
        "type": "flag",
        "required": 1
      }
    ]
  }
}
```

#### Errors

| Status | 条件 |
| --- | --- |
| 404 | 駅が存在しない |
| 500 | DB 例外など |

## 平均・中央値 API

### GET `/api/stations/averages`

全駅の評価項目平均を取得する。

#### Query

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `mode` | string | `body` | `body`, `hearing`, `vision` |

#### Success

```json
{
  "success": true,
  "data": {
    "total_stations": 0,
    "mode": "body",
    "metric_averages": {},
    "raw_averages": {}
  }
}
```

### GET `/api/stations/medians`

全駅の評価項目中央値を取得する。

#### Query

| Name | Type | Default | Description |
| --- | --- | --- | --- |
| `mode` | string | `body` | `body`, `hearing`, `vision` |

#### Success

```json
{
  "success": true,
  "data": {
    "total_stations": 0,
    "mode": "body",
    "metric_medians": {},
    "raw_medians": {}
  }
}

```

## フロントエンド利用状況

| 画面 | TS | 主な API |
| --- | --- | --- |
| ログイン | `frontend/src/login.ts` | `/api/auth/login`, `/api/auth/signup`, `/api/auth/reset-password` |
| ホーム | `frontend/src/home.ts` | なし |
| 一覧 | `frontend/src/index.ts` | `/api/body/stations`, `/api/hearing/stations`, `/api/vision/stations`, `/api/stations/prefectures`, `/api/auth/profile`, `/api/lines` |
| 詳細 | `frontend/src/detail.ts` | `/api/{mode}/stations/<id>` |
| プロフィール | `frontend/src/profile.ts` | `/api/auth/profile`, `/api/stations/search`, `/api/stations/<id>` |

## 現状の互換性維持対象

リファクタリング中は以下を維持する。

- URL パス
- HTTP メソッド
- `success` / `data` / `error` / `count` / `total_count` のレスポンスキー
- スコア付き駅レスポンスの `station_id`、`station_name`、`score.label`
- プロフィールレスポンスの `disability_type`、`favorite_stations`、`preferred_features`
- 静的ページ配信パス
