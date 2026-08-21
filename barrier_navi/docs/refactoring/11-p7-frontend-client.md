# P7 フロントエンドAPIクライアントと認証表示状態

**決定日:** 2026-08-21
**目的:** 画面ごとに分散していたAPI URL組立、JSON解析、通信例外、認証表示状態の操作を共通モジュールへ集約し、Flask署名付きセッションを唯一の認証根拠として維持する。

## 1. 責務境界

| モジュール | 責務 | 非責務 |
| --- | --- | --- |
| `frontend/src/api.ts` | `/api` URL組立、同一オリジンJSON要求、HTTPステータス、非JSON応答・通信失敗の共通変換。 | 画面遷移、DOM表示、401時の画面別判断。 |
| `frontend/src/auth.ts` | UI表示のための`localStorage`読み書き、ログインユーザー保存、ゲスト開始、表示状態消去。 | サーバー認可、Cookieセッションの作成・検証、ユーザーIDの信頼根拠。 |
| 各ページ | 成功・失敗文言、DOM更新、画面遷移、プロフィール401時のログイン遷移。 | `fetch`の直接呼出、認証表示キーの直接操作。 |

> Flaskの署名付きセッションが認証・認可の唯一の根拠である。`localStorage`は、ログイン済み表示や表示名などを補助するUI状態であり、保護APIへのアクセス権を与えない。

## 2. 共通APIクライアント

`requestApi<T>()`、`getApi<T>()`、`postApi<T>()`、`patchApi<T>()`を提供する。要求は`credentials: 'same-origin'`を明示して既存の同一オリジンCookieセッションを維持する。

| 状況 | 共通クライアントの結果 |
| --- | --- |
| HTTP成功かつ`success: true` | そのまま`status`と`body`を返す。 |
| 401を含む業務エラー | `status`と既存APIの`error`を返す。画面が遷移を判断する。 |
| JSONでない応答 | `success: false`と安全なJSON応答エラーを返す。 |
| 通信失敗 | `status: 0`と汎用的な通信失敗メッセージを返す。 |

このため、プロフィール画面だけが401を検出して端末側の表示状態を消去し、`/login`へ遷移する。駅検索・駅詳細の公開APIやログイン失敗には、クライアントが一律にリダイレクトしない。

## 3. 認証表示状態

`auth.ts`は次の既存キーを一箇所で管理する。

| キー | 用途 |
| --- | --- |
| `isLoggedIn` | UI上のログイン済み表示。 |
| `isGuest` | UI上のゲスト利用表示。 |
| `username` | 表示名。 |
| `userId` | UI補助用途のID。プロフィール取得時の認可判断には使用しない。 |
| `userEmail` | 表示用メールアドレス。 |
| `rememberMe` | 既存キーとの互換のため、表示状態消去時に削除する。 |

`login.ts`はログイン成功時に`setAuthenticatedUser()`、ゲスト利用時に`startGuestSession()`を使う。`home.ts`のログアウトと`profile.ts`の401処理は`clearClientAuthState()`を使う。

## 4. ページ移行

| ページ | P7の移行内容 |
| --- | --- |
| `login.ts` | ログイン・登録・リセットのPOSTとログイン／ゲスト表示状態を共通化。 |
| `profile.ts` | プロフィール、駅検索、駅詳細、保存のGET/PATCHと401処理を共通化。 |
| `index.ts` | P6のページング・お気に入り要求、プロフィール、路線取得を共通GETへ移行。 |
| `detail.ts` | 駅詳細のGETと失敗応答を共通化。 |
| `home.ts` | ログアウトPOSTと表示状態消去を共通化。モジュールimportのため`home.html`も`type="module"`へ移行。 |

## 5. 回帰防止

フロントエンドには依存追加なしでNode組込みテストを導入した。`npm --prefix frontend test`はTypeScriptビルド後、URL組立、JSON POST、`credentials: 'same-origin'`、401、非JSON応答、通信失敗、認証表示状態を4件のテストで確認する。

ページBlueprintの回帰テストには`/dist/auth.js`の配信と`/home`の`type="module"`読込を追加した。P7完了時点でPython構文検証、32件のバックエンドテスト、4件のフロントエンド単体テストが成功している。
