/** 同一オリジンで提供されるbarriernavi APIの共通設定。 */
export const API_BASE_URL = '/api';

/** APIパスを安全に組み立てる。引数は先頭のスラッシュを含めてもよい。 */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}/${path.replace(/^\/+/, '')}`;
}
