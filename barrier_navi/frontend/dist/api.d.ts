/** 同一オリジンで提供されるbarriernavi APIの共通設定。 */
export declare const API_BASE_URL = "/api";
/** APIパスを安全に組み立てる。引数は先頭のスラッシュを含めてもよい。 */
export declare function apiUrl(path: string): string;
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
/**
 * 同一オリジンのJSON APIを要求する。
 * 401などの画面遷移は呼び出し側が判断し、公開APIと認証画面の振る舞いを分離する。
 */
export declare function requestApi<T>(path: string, method?: string, jsonBody?: unknown, options?: JsonRequestOptions): Promise<ApiRequestResult<T>>;
export declare function getApi<T>(path: string, options?: JsonRequestOptions): Promise<ApiRequestResult<T>>;
export declare function postApi<T>(path: string, jsonBody?: unknown, options?: JsonRequestOptions): Promise<ApiRequestResult<T>>;
export declare function patchApi<T>(path: string, jsonBody?: unknown, options?: JsonRequestOptions): Promise<ApiRequestResult<T>>;
export {};
//# sourceMappingURL=api.d.ts.map