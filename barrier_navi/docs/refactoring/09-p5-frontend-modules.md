# P5 フロントエンドモジュールと評価設定の境界

**決定日:** 2026-08-21
**目的:** ESモジュールを使用するTypeScript配布物を全対象ページで正しく読み込み、画面ロジックから評価項目・優先設備対応の設定を分離する。P1のスコア仕様、既存API、プロフィール保存形式、画面構造は変更しない。

## 1. モジュール読込の統一

`frontend/src/login.ts`、`profile.ts`、`index.ts`、`detail.ts` はES2020モジュールとしてビルドされる。これらを読み込むHTMLでは、`type="module"` を必須とする。

| ページ | 配布物 | P5後の読込 |
| --- | --- | --- |
| `/`・`/login` | `/dist/login.js` | `type="module"` |
| `/index`・`/hearing`・`/vision` | `/dist/index.js` | `type="module"` |
| `/profile` | `/dist/profile.js` | `type="module"` |
| `/detail` | `/dist/detail.js` | `type="module"`（P2から維持） |

相対パスを混在させず、静的ページBlueprintが提供する`/dist/*`の絶対パスに統一する。

## 2. 評価設定の分離

`frontend/src/metrics.ts` をフロントエンド側の評価設定モジュールとする。

| エクスポート | 責務 |
| --- | --- |
| `MetricDefinition`、`MetricType`、`DisabilityMode` | 画面ロジックで使う評価項目の型。 |
| `BODY_METRICS`、`HEARING_METRICS`、`VISION_METRICS` | P1の身体12、聴覚4、視覚10項目のキー、表示名、閾値。 |
| `METRICS_BY_MODE` | モード別の評価項目アクセス。 |
| `PREFERRED_FEATURE_TO_METRIC_KEY` | プロフィールの既存`preferred_features`文字列から絞り込みキーへの対応。 |
| `metricKeysForPreferredFeature` | APIから返る未知の優先設備文字列を空配列として安全に扱う変換関数。 |

> `index.ts` は設定値を定義せず、画面状態、DOM操作、API呼出、一覧描画だけを担当する。

## 3. 維持する契約

| 項目 | 維持内容 |
| --- | --- |
| スコア | 身体12、聴覚4、視覚10項目。キー、表示名、閾値はP1仕様と同一。 |
| プロフィール | `preferred_features`は既存の日本語文字列配列を保存・取得する。 |
| API | `/api/*`のURL、リクエスト、レスポンスを変更しない。 |
| 画面 | ページURL、HTMLのDOM構造、表示テキスト、CSSクラスを変更しない。 |
| 配布 | `npm --prefix frontend run build`で`dist/`にJS・型定義・source mapを同期する。 |

## 4. 回帰防止

`test_page_routes.py` を拡張し、API依存の全ページが`type="module"`で対応配布物を読み込むことと、`/dist/metrics.js`が配信されることを確認する。P5完了時点で、Python構文検証、30件の自動テスト、TypeScriptビルドを成功させた。実行中アプリでも対象4ページの`type="module"`属性と`/dist/metrics.js`のHTTP 200を確認した。
