import { postApi } from './api.js';
import { AuthenticatedUser, isClientAuthenticated, setAuthenticatedUser, startGuestSession } from './auth.js';

/**
 * バリナビ ログイン画面
 */

class LoginPage {
  private modalOpener: HTMLElement | null = null;

  constructor() {

    this.init();
  }

  private init(): void {
    this.setupEventListeners();
    this.checkAuthStatus();
  }

  private checkAuthStatus(): void {
    // URLパラメータに ?force=true がない場合のみ、既にログインしている場合はホーム画面にリダイレクト
    const urlParams = new URLSearchParams(window.location.search);
    const force = urlParams.get('force') === 'true';
    
        if (!force && isClientAuthenticated()) {
      window.location.href = '/home';
    }

  }

  private setupEventListeners(): void {
    // ログインフォーム
    const loginForm = document.getElementById('login-form') as HTMLFormElement;
    loginForm?.addEventListener('submit', (e) => this.handleLogin(e));

    // 新規作成ボタン
    const signupBtn = document.getElementById('signup-btn');
    signupBtn?.addEventListener('click', () => this.showSignupModal());

    // ゲストで参加ボタン
    const guestBtn = document.getElementById('guest-btn');
    guestBtn?.addEventListener('click', () => this.handleGuestLogin());

    

    // 新規作成モーダル
    const signupModal = document.getElementById('signup-modal');
    const closeSignupModal = document.getElementById('close-signup-modal');
    closeSignupModal?.addEventListener('click', () => this.hideSignupModal());
    signupModal?.addEventListener('click', (e) => {
      if (e.target === signupModal) {
        this.hideSignupModal();
      }
    });

    // 新規作成フォーム
    const signupForm = document.getElementById('signup-form') as HTMLFormElement;
    signupForm?.addEventListener('submit', (e) => this.handleSignup(e));

        document.addEventListener('keydown', (event) => this.handleModalKeydown(event));

  }

  private async handleLogin(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const username = formData.get('username') as string;
    const password = formData.get('password') as string;

    const errorMessage = document.getElementById('error-message');
    if (errorMessage) {
      errorMessage.style.display = 'none';
      errorMessage.textContent = '';
    }

    try {
      // 実際のAPI呼び出し（バックエンドが実装されていない場合は、ローカルストレージでシミュレート）
      const response = await this.loginUser(username, password);
      
      if (response.success) {
        // ログイン成功
                setAuthenticatedUser(response.user || {}, username);

        window.location.href = '/home';
      } else {
        // ログイン失敗
        this.showError(errorMessage, response.error || 'ログインに失敗しました');
      }
    } catch (error) {
      console.error('Login error:', error);
      this.showError(errorMessage, 'ログイン処理中にエラーが発生しました');
    }
  }

  private async loginUser(username: string, password: string): Promise<{ success: boolean; error?: string; user?: AuthenticatedUser }> {
    const result = await postApi<AuthenticatedUser>('/auth/login', { username, password });
    if (result.body.success) {
      return { success: true, user: result.body.data };
    }
    return { success: false, error: result.body.error || 'ログインに失敗しました' };
  }

  private handleGuestLogin(): void {
    startGuestSession();
    window.location.href = '/home';
  }

  private showSignupModal(): void {
    const modal = document.getElementById('signup-modal');
    if (!modal) return;
    this.modalOpener = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    modal.style.display = 'flex';
    const errorMsg = document.getElementById('signup-error-message');
    if (errorMsg) {
      errorMsg.textContent = '';
      errorMsg.style.display = 'none';
    }
    window.setTimeout(() => (document.getElementById('signup-username') as HTMLInputElement | null)?.focus(), 0);
  }

  private hideSignupModal(): void {
    const modal = document.getElementById('signup-modal');
    if (!modal) return;
    modal.style.display = 'none';
    const form = document.getElementById('signup-form') as HTMLFormElement | null;
    form?.reset();
    const errorMsg = document.getElementById('signup-error-message');
    if (errorMsg) {
      errorMsg.textContent = '';
      errorMsg.style.display = 'none';
    }
    this.modalOpener?.focus();
    this.modalOpener = null;
  }

  private handleModalKeydown(event: KeyboardEvent): void {
    const modal = document.getElementById('signup-modal');
    if (!modal || modal.style.display === 'none') return;
    if (event.key === 'Escape') {
      event.preventDefault();
      this.hideSignupModal();
      return;
    }
    if (event.key !== 'Tab') return;

    const dialog = modal.querySelector<HTMLElement>('[role="dialog"]');
    const focusable = dialog?.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [href]');
    if (!focusable || focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  }

  private async handleSignup(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);
    const username = formData.get('username') as string;
    const email = formData.get('email') as string;
    const password = formData.get('password') as string;
    const passwordConfirm = formData.get('password-confirm') as string;

    const errorMessage = document.getElementById('signup-error-message');
    if (errorMessage) {
      errorMessage.style.display = 'none';
      errorMessage.textContent = '';
    }

    // バリデーション
    if (!username || !email || !password || !passwordConfirm) {
      this.showError(errorMessage, 'すべての項目を入力してください');
      return;
    }

    if (password !== passwordConfirm) {
      this.showError(errorMessage, 'パスワードが一致しません');
      return;
    }

    if (password.length < 8) {
      this.showError(errorMessage, 'パスワードは8文字以上で入力してください');
      return;
    }

    try {
      const response = await this.createUser(username, email, password);
      
            if (response.success) {
        this.hideSignupModal();
        // ログインフォームにユーザー名を設定し、作成完了を画面上で明示する。
        const loginUsername = document.getElementById('username') as HTMLInputElement | null;
        if (loginUsername) loginUsername.value = username;
        const loginStatus = document.getElementById('login-status');
        if (loginStatus) {
          loginStatus.textContent = 'アカウントを作成しました。パスワードを入力してログインしてください。';
          loginStatus.style.display = 'block';
          loginStatus.focus();
        }

      } else {
        this.showError(errorMessage, response.error || 'アカウント作成に失敗しました');
      }
    } catch (error) {
      console.error('Signup error:', error);
      this.showError(errorMessage, 'アカウント作成処理中にエラーが発生しました');
    }
  }

  private async createUser(username: string, email: string, password: string): Promise<{ success: boolean; error?: string }> {
    const result = await postApi('/auth/signup', { username, email, password });
    return result.body.success
      ? { success: true }
      : { success: false, error: result.body.error || 'アカウント作成に失敗しました' };
  }

  

  private showError(element: HTMLElement | null, message: string): void {
    if (element) {
      element.textContent = message;
      element.style.display = 'block';
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  new LoginPage();
});

