/** 同一オリジンで提供されるbarriernavi APIの共通設定。 */
export const API_BASE_URL = '/api';
/** APIパスを安全に組み立てる。引数は先頭のスラッシュを含めてもよい。 */
export function apiUrl(path) {
    return `${API_BASE_URL}/${path.replace(/^\/+/, '')}`;
}
function buildFailure(status, error) {
    return { status, body: { success: false, error } };
}
function isApiResponse(value) {
    return typeof value === 'object' && value !== null && 'success' in value && typeof value.success === 'boolean';
}
/**
 * 同一オリジンのJSON APIを要求する。
 * 401などの画面遷移は呼び出し側が判断し、公開APIと認証画面の振る舞いを分離する。
 */
export async function requestApi(path, method = 'GET', jsonBody, options = {}) {
    const headers = new Headers(options.headers);
    headers.set('Accept', 'application/json');
    let body;
    if (jsonBody !== undefined) {
        headers.set('Content-Type', 'application/json');
        body = JSON.stringify(jsonBody);
    }
    try {
        const response = await fetch(apiUrl(path), {
            ...options,
            method,
            headers,
            body,
            credentials: 'same-origin',
        });
        let payload;
        try {
            payload = await response.json();
        }
        catch {
            return buildFailure(response.status, `サーバーから有効なJSON応答を取得できませんでした（${response.status}）`);
        }
        if (!isApiResponse(payload)) {
            return buildFailure(response.status, `サーバーから想定外の応答を受け取りました（${response.status}）`);
        }
        if (response.ok && payload.success) {
            return { status: response.status, body: payload };
        }
        return {
            status: response.status,
            body: {
                success: false,
                error: payload.error || `リクエストに失敗しました（${response.status}）`,
            },
        };
    }
    catch (error) {
        console.error(`API request failed: ${method} ${path}`, error);
        return buildFailure(0, '通信に失敗しました。ネットワーク接続を確認してください。');
    }
}
export function getApi(path, options = {}) {
    return requestApi(path, 'GET', undefined, options);
}
export function postApi(path, jsonBody, options = {}) {
    return requestApi(path, 'POST', jsonBody, options);
}
export function patchApi(path, jsonBody, options = {}) {
    return requestApi(path, 'PATCH', jsonBody, options);
}
//# sourceMappingURL=api.js.map