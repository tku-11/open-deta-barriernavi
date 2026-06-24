# 仕様駆動リファクタリング ロードマップ

## 目的

このロードマップは、バリアナビを現行動作を保ったまま段階的に整理し、仕様に基づいて安全にリファクタリングするための実行計画である。

リファクタリングでは、まず現状仕様を固定し、テストで保護したうえで、責務分割、重複削減、ドキュメント整備を進める。

## 基本方針

- 仕様を先に書き、実装は仕様に追従させる。
- 最初は「理想仕様」ではなく「現状仕様」を正として固定する。
- 挙動変更と構造変更を同じ作業単位に混ぜない。
- 既存の UI、API レスポンス、DB スキーマとの互換性を優先する。
- 変更単位ごとに、仕様、テスト、実装、検証結果を残す。
- TypeScript の `src` と `dist` は、変更時に必ずビルドして同期する。

## 対象範囲

### 対象に含める

- Flask API サーバーの責務分割
- スコア計算ロジックの仕様化と切り出し
- 駅一覧・詳細 API の整理
- 認証・プロフィール API の整理
- フロントエンドの API 呼び出しと画面ロジックの整理
- Docker、DB 初期化、CSV インポート手順の仕様整理
- README と関連ドキュメントの更新

### 対象に含めない

- UI デザインの大幅刷新
- DB スキーマの破壊的変更
- 認証方式の全面変更
- 新機能追加
- AWS 本番構成の再設計

これらは別プロジェクトとして扱う。

## 成果物一覧

| 成果物 | 目的 |
| --- | --- |
| `docs/refactoring/00-current-system.md` | 現在の構成、起動方法、主要ファイルの責務を固定する |
| `docs/refactoring/01-api-spec.md` | 既存 API の入力、出力、エラー形式を固定する |
| `docs/refactoring/02-scoring-spec.md` | 身体・聴覚・視覚のスコア仕様を固定する |
| `docs/refactoring/03-db-spec.md` | テーブル、カラム、CSV インポート仕様を固定する |
| `docs/refactoring/spec-gaps.md` | 仕様書と実装の差分、判断結果を記録する |
| `docs/refactoring/04-refactoring-roadmap.md` | 本ロードマップ |
| `backend/services/scoring.py` | スコア計算ロジックの切り出し先 |
| `backend/repositories/station_repository.py` | 駅データ取得 SQL の切り出し先 |
| `backend/repositories/user_repository.py` | ユーザー・プロフィール SQL の切り出し先 |
| `backend/routes/*.py` | API ルートの分割先 |
| `backend/tests/` | リファクタリングを守るテスト群 |

## 全体フェーズ

| フェーズ | 主目的 | 完了条件 |
| --- | --- | --- |
| Phase 0 | 準備と基準確認 | 作業ツリー、起動方法、検証コマンドが明確になっている |
| Phase 1 | 現状仕様の固定 | API、スコア、DB、画面の現状仕様が文書化されている |
| Phase 2 | 回帰テストの追加 | スコア計算と主要 API のテストが追加されている |
| Phase 3 | スコア計算の切り出し | `api_server.py` からスコア責務が分離されている |
| Phase 4 | 駅 API の分離 | 駅検索、一覧、詳細、路線取得が分離されている |
| Phase 5 | 認証・プロフィール API の分離 | ログイン、登録、プロフィール更新が分離されている |
| Phase 6 | Flask ルート分割 | `api_server.py` がアプリ初期化と Blueprint 登録中心になっている |
| Phase 7 | フロントエンド整理 | API パス、画面モード、重複定義が整理されている |
| Phase 8 | 起動・DB・Docker 整理 | ローカル/Docker 起動仕様が文書と実装で一致している |
| Phase 9 | 最終検証 | テスト、ビルド、スモーク確認、ドキュメント更新が完了している |

## Phase 0: 準備と基準確認

### 目的

リファクタリング前の基準状態を明確にし、以後の差分を安全に追える状態を作る。

### 作業

1. `git status --short --branch` で作業ツリーがクリーンか確認する。
2. 現在の最新コミットを記録する。
3. ローカル起動に必要な `.env` の有無を確認する。
4. Docker 起動の前提を確認する。
5. TypeScript ビルドが通ることを確認する。
6. DB 接続が必要な検証と不要な検証を分ける。

### 成果物

- `docs/refactoring/00-current-system.md` の「検証基準」セクション

### 検証

```powershell
git status --short --branch
git log -1 --oneline
cd barrier_navi/frontend
npm run build
```

### 完了条件

- 変更前の基準コミットが分かる。
- TypeScript ビルド可否が記録されている。
- DB 接続なしでできる検証、DB 接続ありで行う検証が分かれている。

## Phase 1: 現状仕様の固定

### 目的

現コードの挙動を仕様として固定し、以後のリファクタリングで守るべき境界を明確にする。

### 作業

1. 現在のディレクトリ構成を整理する。
2. Flask ルート一覧を抽出する。
3. 静的ページの配信ルートを整理する。
4. フロントエンド画面と対応する TypeScript ファイルを整理する。
5. DB テーブルと CSV カラムの対応を整理する。
6. スコア計算仕様を実装から逆算して文書化する。
7. 既存ドキュメントと実装の差分を `spec-gaps.md` に記録する。

### 成果物

- `docs/refactoring/00-current-system.md`
- `docs/refactoring/01-api-spec.md`
- `docs/refactoring/02-scoring-spec.md`
- `docs/refactoring/03-db-spec.md`
- `docs/refactoring/spec-gaps.md`

### 重点確認項目

- README では身体障害向けが 12 項目と説明されている。
- `barianavi_spec.md` では身体障害向けが 15 項目と説明されている。
- 実装上の `BODY_METRIC_DEFINITIONS` は 12 項目である。
- README などでは視覚障害向けが 9 項目と説明されている。
- 実装上の `VISION_METRIC_DEFINITIONS` は 10 項目である。
- `login.ts` は `http://localhost:5000/api` を直接参照している。
- 他の画面は主に `/api` を参照している。
- `.gitignore` はリポジトリ直下ではなく `barrier_navi/.gitignore` に存在する。

### 検証

```powershell
rg -n "@app\.route" barrier_navi/backend/api_server.py
rg -n "fetch\(" barrier_navi/frontend/src
rg -n "BODY_METRIC_DEFINITIONS|HEARING_METRIC_DEFINITIONS|VISION_METRIC_DEFINITIONS" barrier_navi/backend/api_server.py
```

### 完了条件

- 現状の API 仕様が文書化されている。
- 現状のスコア仕様が文書化されている。
- 実装と既存ドキュメントのズレが記録されている。
- 以後のフェーズで「変更してよいもの」と「互換性維持するもの」が明確になっている。

## Phase 2: 回帰テストの追加

### 目的

構造を変えても挙動が変わっていないことを確認できる安全網を作る。

### 作業

1. テスト方針を決める。
2. `backend/tests/` を作成する。
3. スコア計算のユニットテストを追加する。
4. Flask のテストクライアントで主要 API のレスポンス形式を検証する。
5. DB 接続を必要とするテストと不要なテストを分離する。
6. 認証・プロフィール API の最低限のテストを追加する。

### 優先テスト

| 優先度 | 対象 | 理由 |
| --- | --- | --- |
| 高 | `evaluate_metric` | スコア計算の最小単位 |
| 高 | `compute_score` | 一覧・詳細表示の核 |
| 高 | `build_station_response` | API レスポンス互換性に直結 |
| 中 | `/api/body/stations/<id>` | 詳細画面に直結 |
| 中 | `/api/auth/profile` | プロフィールとお気に入り機能に直結 |
| 中 | `/api/stations/search` | プロフィールのお気に入り駅検索に直結 |

### 推奨テストケース

- フラグ型で `1` の場合は達成。
- フラグ型で `2`、`3`、`None` の場合は未達成。
- 割合型で分母が 0 の場合は未達成。
- 割合型で `numerator / denominator >= required` の場合は達成。
- 数値型で required 以上の場合は達成。
- 身体・聴覚・視覚で total_items が現状仕様どおりになる。

### 成果物

- `backend/tests/test_scoring.py`
- `backend/tests/test_api_contract.py`
- 必要に応じて `pytest.ini`

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests
cd frontend
npm run build
```

### 完了条件

- スコア計算の主要ケースがテストで固定されている。
- API レスポンスの主要なキーがテストで固定されている。
- DB 接続がない環境でも一部テストが実行できる。

## Phase 3: スコア計算の切り出し

### 目的

`api_server.py` からスコア定義と計算ロジックを分離し、テストしやすい構造にする。

### 作業

1. `backend/services/` を作成する。
2. `backend/services/scoring.py` を作成する。
3. `BODY_METRIC_DEFINITIONS`、`HEARING_METRIC_DEFINITIONS`、`VISION_METRIC_DEFINITIONS` を移動する。
4. `evaluate_metric`、`compute_score`、`build_station_response` を移動する。
5. `api_server.py` から import する。
6. 既存 API レスポンスが変わらないことを確認する。

### 注意点

- 関数名と戻り値は最初は変えない。
- 型定義の改善は、移動後の別ステップにする。
- スコア項目数は現状仕様を維持する。

### 成果物

- `backend/services/scoring.py`
- `backend/services/__init__.py`
- 更新された `backend/api_server.py`
- 更新された `backend/tests/test_scoring.py`

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests/test_scoring.py
cd frontend
npm run build
```

### 完了条件

- スコア計算のテストが通る。
- API レスポンスの `score.label`、`score.met_items`、`score.total_items`、`metrics` の形式が変わっていない。
- `api_server.py` のスコア責務が削減されている。

## Phase 4: 駅 API と SQL の分離

### 目的

駅データ取得、検索、集計、路線取得の SQL を API ルートから分離する。

### 作業

1. `backend/repositories/` を作成する。
2. `station_repository.py` を作成する。
3. `DatabaseConnection` の生成と close の扱いを整理する。
4. 駅一覧取得 SQL を repository に移動する。
5. 駅詳細取得 SQL を repository に移動する。
6. 都道府県、統計、平均、中央値、路線取得を段階的に移動する。
7. API レイヤーは request パラメータ解釈と JSON レスポンス生成に寄せる。

### 推奨分割

```text
backend/repositories/station_repository.py
  search_stations(...)
  get_station_by_id(...)
  list_prefectures(...)
  list_lines(...)
  count_stations(...)
  get_statistics(...)
  get_averages(...)
  get_medians(...)
```

### 注意点

- 一度に全 SQL を移動しない。
- `/api/body/stations` などスコア付き API と `/api/stations` など生データ API を混ぜすぎない。
- 既存の `line_name` 検索仕様は現状どおり維持する。

### 成果物

- `backend/repositories/station_repository.py`
- `backend/repositories/__init__.py`
- 更新された `backend/api_server.py`
- API contract テストの追加

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests
```

DB 環境がある場合:

```powershell
py backend/api_server.py
```

ブラウザまたは API クライアントで以下を確認する。

- `/api/stations/prefectures`
- `/api/body/stations`
- `/api/hearing/stations`
- `/api/vision/stations`
- `/api/lines`

### 完了条件

- 駅関連 SQL が repository に移動している。
- API の URL、クエリ、レスポンス形式が維持されている。
- 一覧画面と詳細画面が従来どおり表示できる。

## Phase 5: 認証・プロフィール API の分離

### 目的

ログイン、ユーザー登録、パスワードリセット、プロフィール取得・更新を分離し、認証関連の責務を明確にする。

### 作業

1. `backend/repositories/user_repository.py` を作成する。
2. `backend/services/profile.py` を作成する。
3. ユーザー検索、登録、更新 SQL を repository に移動する。
4. `users_preferences` の JSON 変換処理を service に移動する。
5. bcrypt 処理の境界を整理する。
6. 開発用の平文パスワード比較の扱いを仕様として明記する。

### 注意点

- 既存の localStorage 連携に影響するため、API レスポンスキーは維持する。
- パスワードリセットは「メール送信未実装」という現状仕様を維持する。
- セッションや JWT 導入はこのフェーズでは行わない。

### 成果物

- `backend/repositories/user_repository.py`
- `backend/services/profile.py`
- 更新された `backend/api_server.py`
- 認証・プロフィール API のテスト

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests
cd frontend
npm run build
```

DB 環境がある場合は以下を確認する。

- 新規登録
- ログイン
- プロフィール取得
- プロフィール更新
- お気に入り駅保存
- 優先機能保存

### 完了条件

- 認証・プロフィール関連の SQL と JSON 処理が分離されている。
- 既存のログイン、プロフィール画面が壊れていない。
- ゲストモードの挙動が維持されている。

## Phase 6: Flask ルート分割

### 目的

`api_server.py` をアプリケーション起動と Blueprint 登録中心に縮小する。

### 作業

1. `backend/routes/` を作成する。
2. `routes/pages.py` に静的 HTML 配信を移動する。
3. `routes/stations.py` に駅 API を移動する。
4. `routes/auth.py` に認証 API を移動する。
5. Flask Blueprint を導入する。
6. `api_server.py` は app 作成、CORS、Blueprint 登録、起動に寄せる。

### 推奨構成

```text
backend/
  api_server.py
  config.py
  database_connection.py
  routes/
    __init__.py
    auth.py
    pages.py
    stations.py
  services/
    __init__.py
    scoring.py
    profile.py
  repositories/
    __init__.py
    station_repository.py
    user_repository.py
```

### 注意点

- Blueprint 導入時も URL は変えない。
- `send_file` のパス解決は `BASE_DIR`、`FRONTEND_DIR`、`VIEW_DIR`、`DIST_DIR` と整合させる。
- import 循環に注意する。

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests
cd frontend
npm run build
```

DB 環境がある場合:

- `/`
- `/login`
- `/home`
- `/index`
- `/hearing`
- `/vision`
- `/profile`
- `/detail`
- `/styles.css`
- `/dist/index.js`

### 完了条件

- `api_server.py` が大幅に短くなっている。
- 既存 URL が維持されている。
- 静的ファイル配信と API がどちらも動作する。

## Phase 7: フロントエンド整理

### 目的

フロントエンドの重複定義、API ベース URL、画面モード判定を整理する。

### 作業

1. `login.ts` の API ベース URL を `/api` に統一するか、仕様として固定する。
2. 身体・聴覚・視覚の metric 定義を整理する。
3. バックエンドのスコア定義との重複を `spec-gaps.md` に記録する。
4. `StationApp` のページング、ソート、お気に入り優先表示の責務を整理する。
5. 詳細画面の mode 判定を仕様化する。
6. `npm run build` で `dist` を更新する。

### 注意点

- フロントの整理はバックエンド API 分割後に行う。
- UI 見た目の大幅変更は行わない。
- 画面遷移 URL は維持する。

### 成果物

- 更新された `frontend/src/*.ts`
- 更新された `frontend/dist/*`
- 必要に応じて `frontend/src/api.ts`
- 必要に応じて `frontend/src/metrics.ts`

### 検証

```powershell
cd barrier_navi/frontend
npm run build
```

DB 環境がある場合:

- ログイン画面
- ゲストログイン
- ホーム画面
- 身体一覧
- 聴覚一覧
- 視覚一覧
- 詳細画面
- プロフィール画面

### 完了条件

- API ベース URL の扱いが一貫している。
- TypeScript ビルドが通る。
- `src` と `dist` が同期している。
- 画面遷移が維持されている。

## Phase 8: 起動・DB・Docker 整理

### 目的

ローカル起動、Docker 起動、DB 初期化、CSV インポートの仕様と実装を揃える。

### 作業

1. `.env` の配置場所を明確にする。
2. ルート README と `barrier_navi/docs/README.md` の記述差分を整理する。
3. Docker Compose の起動手順を確認する。
4. `init.sql` と `DDL.sql` の差分を確認する。
5. CSV インポートの実行条件を仕様化する。
6. `.gitignore` の配置と対象を確認する。

### 注意点

- Docker の DB ポートは compose 上では `${MYSQL_PORT:-3307}:3306`。
- アプリ内の MySQL 接続ポートはコンテナ間通信では `3306`。
- `import_csv_data.py` は既存データがある場合にインポートをスキップする。
- `import_csv_to_mysql` 自体は既存データを削除するため、呼び出し条件を明確にする。

### 成果物

- 更新された README
- 更新された Docker ドキュメント
- `docs/refactoring/03-db-spec.md` の更新
- 必要に応じて `.env.example`

### 検証

```powershell
cd barrier_navi/docker
docker compose up --build
```

起動後に以下を確認する。

- `http://localhost:5000`
- stations データ件数
- ログイン画面表示
- 一覧画面表示

### 完了条件

- ローカル起動手順が明確である。
- Docker 起動手順が明確である。
- DB 初期化と CSV インポートの責務が文書化されている。

## Phase 9: 最終検証と仕上げ

### 目的

仕様、実装、テスト、ドキュメントの整合を確認し、リファクタリング完了状態にする。

### 作業

1. 全テストを実行する。
2. TypeScript ビルドを実行する。
3. DB 環境ありのスモークテストを行う。
4. ドキュメントのリンク切れ、古い記述を修正する。
5. `spec-gaps.md` の未決定項目を整理する。
6. 残課題を `docs/refactoring/follow-up.md` に記録する。

### 検証

```powershell
cd barrier_navi
py -m pytest backend/tests
cd frontend
npm run build
git status --short
```

### 完了条件

- 全テストが通る。
- TypeScript ビルドが通る。
- 主要画面が表示できる。
- 主要 API が現状仕様どおり応答する。
- ドキュメントが実装と一致している。
- 残課題が明文化されている。

## 推奨ブランチ戦略

各フェーズは小さな PR またはコミットに分ける。

```text
codex/spec-refactor-docs
codex/spec-refactor-tests
codex/spec-refactor-scoring
codex/spec-refactor-stations
codex/spec-refactor-auth
codex/spec-refactor-frontend
codex/spec-refactor-docs-final
```

大きくしすぎないため、1 ブランチあたりの目安は以下とする。

- 変更ファイル 10 個以内
- レビュー観点が 1 つに絞れること
- 挙動変更がある場合は仕様書に明記すること

## コミット単位の推奨

### 仕様追加

```text
docs: add current system specification
docs: add scoring specification
docs: document API contract
```

### テスト追加

```text
test: add scoring regression tests
test: add API contract tests
```

### リファクタリング

```text
refactor: extract scoring service
refactor: extract station repository
refactor: split auth routes
```

### フロント整理

```text
refactor: normalize frontend API base path
refactor: extract frontend metric definitions
```

## リスクと対策

| リスク | 影響 | 対策 |
| --- | --- | --- |
| スコア項目数の仕様差分 | 表示点数が変わる | Phase 1 で現状仕様として固定し、別課題化する |
| DB 接続必須のテストが増える | CI やローカル検証が重くなる | ユニットテストと DB 結合テストを分ける |
| `api_server.py` 分割で import 循環が起きる | 起動不能になる | config、service、repository、route の依存方向を固定する |
| `src` と `dist` がズレる | ブラウザ挙動が古くなる | フロント変更時は必ず `npm run build` を実行する |
| Docker とローカルの環境差分 | 起動手順が混乱する | `.env.example` と Docker docs を整備する |
| 仕様整理中に新機能が混ざる | レビュー不能になる | 新機能は follow-up に送る |

## 依存関係の順序

```text
Phase 0
  -> Phase 1
    -> Phase 2
      -> Phase 3
        -> Phase 4
          -> Phase 5
            -> Phase 6
              -> Phase 7
                -> Phase 8
                  -> Phase 9
```

Phase 7 のフロント整理は、Phase 3 から Phase 6 のバックエンド分割が安定してから行う。

## 判断待ちにする項目

以下はロードマップ上では扱うが、リファクタリング中に勝手に仕様変更しない。

1. 身体障害向けスコアを 12 項目のままにするか、仕様書に合わせて 15 項目へ拡張するか。
2. 視覚障害向けスコアを実装どおり 10 項目にするか、既存ドキュメントどおり 9 項目にするか。
3. `login.ts` の API ベース URL を `/api` に統一するか、ローカル固定 URL を維持するか。
4. パスワードリセットのメール送信を実装するか、未実装仕様として維持するか。
5. 平文パスワード比較の開発用フォールバックを削除するか。
6. `.gitignore` をリポジトリ直下にも追加するか。
7. `DDL.sql` と `init.sql` を統合するか、用途別に維持するか。

## 最初の 3 スプリント案

### Sprint 1: 仕様固定

- `00-current-system.md` を作成する。
- `01-api-spec.md` を作成する。
- `02-scoring-spec.md` を作成する。
- `spec-gaps.md` を作成する。
- TypeScript ビルドの基準状態を記録する。

完了条件:

- 実装に基づく現状仕様が読める。
- 仕様差分が未決定事項として記録されている。

### Sprint 2: テスト導入

- `backend/tests/test_scoring.py` を追加する。
- `evaluate_metric` と `compute_score` の主要ケースを固定する。
- API レスポンスの最小 contract test を追加する。
- テスト実行手順を README または refactoring docs に追記する。

完了条件:

- スコア計算を移動しても壊れたか分かる。
- DB なしで動くテストが用意されている。

### Sprint 3: スコア計算分離

- `backend/services/scoring.py` を作成する。
- スコア定義と計算関数を移動する。
- `api_server.py` から import する。
- テストと TypeScript ビルドを通す。

完了条件:

- スコア責務が `api_server.py` から分離されている。
- API レスポンスの点数表示が変わっていない。

## 各作業の完了チェックリスト

各 PR または作業単位で以下を確認する。

- 仕様書を更新した。
- テストを追加または更新した。
- 実装変更の範囲が仕様に対応している。
- TypeScript を変更した場合は `npm run build` を実行した。
- DB 接続が必要な確認と不要な確認を分けて記録した。
- `git status --short` で意図しない差分がない。
- 残課題がある場合は follow-up に書いた。

## 完了の定義

このリファクタリングは、以下を満たした時点で完了とする。

- `api_server.py` がアプリ初期化と route 登録中心になっている。
- スコア計算、DB アクセス、認証・プロフィール処理が分離されている。
- 主要仕様が `docs/refactoring` に文書化されている。
- スコア計算と主要 API の回帰テストがある。
- フロントエンドのビルドが通る。
- ローカルまたは Docker で主要画面を確認できる。
- 仕様差分と未決定事項が明文化されている。
