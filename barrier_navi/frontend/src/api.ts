/** 同一オリジンで提供されるbarriernavi APIの共通設定。 */
export const API_BASE_URL = '/api';

/** APIパスを安全に組み立てる。引数は先頭のスラッシュを含めてもよい。 */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}/${path.replace(/^\/+/, '')}`;
}

/** 既存APIが返す成功・失敗形式。 */
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  count?: number;
  total_count?: number;
}

/** HTTPステータスを含む共通要求結果。 */
export interface ApiRequestResult<T> {
  status: number;
  body: ApiResponse<T>;
}

type JsonRequestOptions = Omit<RequestInit, 'body' | 'headers' | 'method'> & {
  headers?: HeadersInit;
};

function buildFailure<T>(status: number, error: string): ApiRequestResult<T> {
  return { status, body: { success: false, error } };
}

function isApiResponse<T>(value: unknown): value is ApiResponse<T> {
  return typeof value === 'object' && value !== null && 'success' in value && typeof value.success === 'boolean';
}

/**
 * 同一オリジンのJSON APIを要求する。
 * 401などの画面遷移は呼び出し側が判断し、公開APIと認証画面の振る舞いを分離する。
 */
export async function requestApi<T>(
  path: string,
  method = 'GET',
  jsonBody?: unknown,
  options: JsonRequestOptions = {},
): Promise<ApiRequestResult<T>> {
  const headers = new Headers(options.headers);
  headers.set('Accept', 'application/json');

  let body: string | undefined;
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

    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      return buildFailure<T>(response.status, `サーバーから有効なJSON応答を取得できませんでした（${response.status}）`);
    }

    if (!isApiResponse<T>(payload)) {
      return buildFailure<T>(response.status, `サーバーから想定外の応答を受け取りました（${response.status}）`);
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
  } catch (error) {
    console.error(`API request failed: ${method} ${path}`, error);
    return buildFailure<T>(0, '通信に失敗しました。ネットワーク接続を確認してください。');
  }
}

export function getApi<T>(path: string, options: JsonRequestOptions = {}): Promise<ApiRequestResult<T>> {
  return requestApi<T>(path, 'GET', undefined, options);
}

export function postApi<T>(path: string, jsonBody?: unknown, options: JsonRequestOptions = {}): Promise<ApiRequestResult<T>> {
  return requestApi<T>(path, 'POST', jsonBody, options);
}

export function patchApi<T>(path: string, jsonBody?: unknown, options: JsonRequestOptions = {}): Promise<ApiRequestResult<T>> {
  return requestApi<T>(path, 'PATCH', jsonBody, options);
}
