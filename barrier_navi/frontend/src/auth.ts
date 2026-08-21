const AUTH_STORAGE_KEYS = [
  'isLoggedIn',
  'isGuest',
  'username',
  'rememberMe',
  'userId',
  'userEmail',
] as const;

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

function readPositiveInteger(value: string | null): number | null {
  if (!value) return null;
  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

/** サーバー認可ではなく画面表示に使う端末側状態を取得する。 */
export function getClientAuthState(): ClientAuthState {
  return {
    isLoggedIn: localStorage.getItem('isLoggedIn') === 'true',
    isGuest: localStorage.getItem('isGuest') === 'true',
    username: localStorage.getItem('username'),
    userId: readPositiveInteger(localStorage.getItem('userId')),
    userEmail: localStorage.getItem('userEmail'),
  };
}

export function isClientAuthenticated(): boolean {
  const state = getClientAuthState();
  return state.isLoggedIn || state.isGuest;
}

export function setAuthenticatedUser(user: AuthenticatedUser, fallbackUsername: string): void {
  localStorage.setItem('isLoggedIn', 'true');
  localStorage.removeItem('isGuest');
  localStorage.setItem('username', user.username || fallbackUsername);

  if (user.id && user.id > 0) {
    localStorage.setItem('userId', user.id.toString());
  } else {
    localStorage.removeItem('userId');
  }

  if (user.email) {
    localStorage.setItem('userEmail', user.email);
  } else {
    localStorage.removeItem('userEmail');
  }
}

export function updateClientUsername(username: string): void {
  localStorage.setItem('username', username);
}

export function startGuestSession(): void {
  localStorage.removeItem('isLoggedIn');
  localStorage.removeItem('userId');
  localStorage.removeItem('userEmail');
  localStorage.setItem('isGuest', 'true');
  localStorage.setItem('username', 'ゲスト');
}

/** 端末側の表示状態を消去する。サーバーセッションの失効とは別責務。 */
export function clearClientAuthState(): void {
  AUTH_STORAGE_KEYS.forEach((key) => localStorage.removeItem(key));
}
