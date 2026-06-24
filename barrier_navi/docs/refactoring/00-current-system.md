# 現状システム基準

## 目的

この文書は、仕様駆動リファクタリングを始める前の基準状態を記録する。

Phase 0 では、実装変更は行わず、リファクタリング前のリポジトリ状態、実行環境、検証可能なコマンド、DB 接続が必要な確認項目を整理する。

## 基準日時

- 確認日: 2026-06-24
- 対象ブランチ: `main`
- 追跡先: `origin/main`
- 基準コミット: `2098e96 Merge pull request #5 from toki224/docker_test`

## Git 状態

Phase 0 開始時点では、前段で追加した refactoring docs のみ未追跡だった。

```text
## main...origin/main
?? barrier_navi/docs/refactoring/
```

既存のアプリケーションコード、DB、Docker、フロントエンド生成物には、Phase 0 の意図した変更はない。

## プロジェクト配置

リポジトリ直下:

```text
README.md
barrier_navi/
```

アプリ本体:

```text
barrier_navi/
  backend/
  config/
  database/
  docker/
  docs/
  frontend/
  scripts/
```

主な入口:

| 項目 | パス |
| --- | --- |
| Flask API | `barrier_navi/backend/api_server.py` |
| DB 接続 | `barrier_navi/backend/database_connection.py` |
| フロント TS | `barrier_navi/frontend/src/` |
| フロント生成物 | `barrier_navi/frontend/dist/` |
| HTML | `barrier_navi/frontend/view/` |
| CSS | `barrier_navi/frontend/styles.css` |
| DB 初期化 | `barrier_navi/database/init.sql` |
| CSV インポート | `barrier_navi/database/import_csv_data.py` |
| Docker Compose | `barrier_navi/docker/docker-compose.yml` |
| Windows 起動スクリプト | `barrier_navi/scripts/start.bat` |

## 環境確認

### Node.js / npm

```text
node --version -> v24.12.0
npm.cmd --version -> 11.6.2
```

### TypeScript ビルド

実行コマンド:

```powershell
cd barrier_navi/frontend
npm.cmd run build
```

結果:

```text
成功
```

注意:

`npm run build` は成功するが、現時点の `frontend/src` と追跡済み `frontend/dist` が同期しておらず、ビルド後に `frontend/dist` に生成差分が出る。

Phase 0 では挙動確認のみを目的とするため、生成差分は戻した。今後 TypeScript を変更するフェーズでは、`src` と `dist` の同期を明示的な作業として扱う。

### Python

確認コマンド:

```powershell
py --version
python --version
```

結果:

```text
py: 見つからない
python: 見つからない
```

現状、この Codex 実行環境の PATH 上では Python コマンドを確認できなかった。

ただし、プロジェクトは Python/Flask を前提にしているため、次フェーズ以降でテストを追加する前に Python 実行環境の準備が必要である。

### MySQL クライアント

確認コマンド:

```powershell
mysql --version
```

結果:

```text
C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe  Ver 8.0.43 for Win64 on x86_64 (MySQL Community Server - GPL)
```

### Docker Compose

確認コマンド:

```powershell
cd barrier_navi/docker
docker compose version
docker compose config --quiet
```

結果:

```text
Docker Compose version v2.40.0-desktop.1
```

`docker compose config --quiet` は exit code 0 で完了した。

注意:

Docker CLI 実行時に以下の警告が出る。

```text
WARNING: Error loading config file: open C:\Users\USER\.docker\config.json: Access is denied.
```

Compose ファイル自体の構文確認はできているが、Docker config の読み取り権限については、Docker を使うフェーズで再確認する。

## `.env` 状態

確認コマンド:

```powershell
Test-Path barrier_navi\.env
```

結果:

```text
False
```

現時点で `barrier_navi/.env` は存在しない。

ローカル Flask 起動や DB 接続を伴う検証には、少なくとも以下が必要になる。

```text
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password_here
MYSQL_DATABASE=station
```

Docker Compose 利用時は `docker-compose.yml` 内のデフォルト値により、DB コンテナは以下の値で起動できる想定である。

```text
MYSQL_DATABASE=station
MYSQL_USER=barrier_user
MYSQL_PASSWORD=barrier_password
MYSQL_ROOT_PASSWORD=rootpassword
```

ホスト側ポートはデフォルトで `3307:3306` になる。

## 検証分類

### DB 接続なしで確認できるもの

- Git 状態確認
- ドキュメント確認
- TypeScript ビルド
- Flask ルート定義の静的確認
- フロントエンド API 呼び出し箇所の静的確認
- Docker Compose ファイルの構文確認

推奨コマンド:

```powershell
git status --short --branch
git log -1 --oneline
rg -n "@app\.route" barrier_navi/backend/api_server.py
rg -n "fetch\(" barrier_navi/frontend/src
cd barrier_navi/frontend
npm.cmd run build
cd ../docker
docker compose config --quiet
```

### DB 接続が必要なもの

- Flask アプリの実起動
- `/api/stations` 系 API の実レスポンス確認
- `/api/body/stations`、`/api/hearing/stations`、`/api/vision/stations` の確認
- ログイン、新規登録、プロフィール取得・更新
- お気に入り駅保存
- CSV インポート結果確認
- 主要画面の実データ表示

推奨確認:

```powershell
cd barrier_navi/docker
docker compose up --build
```

または、ローカル MySQL と `.env` を用意したうえで:

```powershell
cd barrier_navi
python backend/api_server.py
```

現時点では Python コマンドが PATH 上で確認できていないため、ローカル起動は未検証である。

## Phase 0 完了条件の確認

| 条件 | 結果 |
| --- | --- |
| 変更前の基準コミットが分かる | 完了 |
| TypeScript ビルド可否が記録されている | 完了 |
| DB 接続なしでできる検証が整理されている | 完了 |
| DB 接続ありで行う検証が整理されている | 完了 |
| `.env` の有無が確認されている | 完了 |
| Docker Compose の構文確認ができる | 完了 |
| Python 実行環境の状態が記録されている | 完了 |

## 次フェーズへの引き継ぎ

Phase 1 では、現状仕様の固定を行う。

優先して作成する文書:

- `docs/refactoring/01-api-spec.md`
- `docs/refactoring/02-scoring-spec.md`
- `docs/refactoring/03-db-spec.md`
- `docs/refactoring/spec-gaps.md`

Phase 1 開始時に再確認すること:

- Python 実行環境をどう用意するか。
- `npm run build` 後に `dist` 差分が出る状態を、どのフェーズで正式に同期するか。
- `.env.example` を追加するか。
- Docker config 警告が実起動に影響するか。
