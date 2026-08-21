export interface AuthenticatedUser {
    id?: number;
    username?: string;
    email?: string;
}
export interface ClientAuthState {
    isLoggedIn: boolean;
    isGuest: boolean;
    username: string | null;
    userId: number | null;
    userEmail: string | null;
}
/** サーバー認可ではなく画面表示に使う端末側状態を取得する。 */
export declare function getClientAuthState(): ClientAuthState;
export declare function isClientAuthenticated(): boolean;
export declare function setAuthenticatedUser(user: AuthenticatedUser, fallbackUsername: string): void;
export declare function updateClientUsername(username: string): void;
export declare function startGuestSession(): void;
/** 端末側の表示状態を消去する。サーバーセッションの失効とは別責務。 */
export declare function clearClientAuthState(): void;
//# sourceMappingURL=auth.d.ts.map