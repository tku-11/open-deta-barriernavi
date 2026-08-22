import { ApiResponse, getApi, patchApi } from './api.js';
import { clearClientAuthState, getClientAuthState, updateClientUsername } from './auth.js';

/**
 * バリアナビ プロフィール画面
 */

interface ProfileData {
  username: string;
  email: string;
  disability_type?: string[];
  favorite_stations?: number[];  // APIからは駅IDの配列が返される（保存時も駅IDの配列を送信）
  preferred_features?: string[];
}

interface Station {
  id: number;
  station_name: string;
  prefecture?: string;
  city?: string;
}



class ProfilePage {
  
  
  private favoriteStations: Array<{ id: number; name: string }> = [];
  private stationSearchTimeout: number | null = null;
  private stationSearchResults: Station[] = [];
  private activeStationOptionIndex = -1;

  constructor() {
    this.init();
  }

  private init(): void {
    this.checkAuthStatus();
    this.setupEventListeners();
    this.loadProfile();
  }

  private checkAuthStatus(): void {
    if (!getClientAuthState().isLoggedIn) {
      window.location.href = '/login';
    }
  }

  private setupEventListeners(): void {
    // 戻るボタン
    const backBtn = document.getElementById('back-btn');
    backBtn?.addEventListener('click', () => {
      window.location.href = '/home';
    });

    // キャンセルボタン
    const cancelBtn = document.getElementById('cancel-btn');
    cancelBtn?.addEventListener('click', () => {
      if (confirm('変更を破棄しますか？')) {
        window.location.href = '/home';
      }
    });

    // フォーム送信
    const form = document.getElementById('profile-form') as HTMLFormElement;
    form?.addEventListener('submit', (e) => this.handleSubmit(e));

    // 駅検索
    const stationSearchInput = document.getElementById('station-search-input') as HTMLInputElement;
    stationSearchInput?.addEventListener('input', (e) => {
      const keyword = (e.target as HTMLInputElement).value.trim();
      if (keyword.length >= 2) {
        this.debounceSearch(keyword);
      } else {
        this.stationSearchResults = [];
        this.hideStationSearchResults();
        this.announceStationSearch('駅名を2文字以上入力してください。');
      }
    });
    stationSearchInput?.addEventListener('keydown', (e) => this.handleStationSearchKeydown(e));

    // 駅検索結果外をクリックしたら閉じる
    document.addEventListener('click', (e) => {
      const results = document.getElementById('station-search-results');
      const input = document.getElementById('station-search-input');
      if (results && input && 
          !results.contains(e.target as Node) && 
          !input.contains(e.target as Node)) {
        this.hideStationSearchResults();
      }
    });

    // お気に入り駅の削除ボタン（イベント委譲を使用）
    const favoriteStationsList = document.getElementById('favorite-stations-list');
    favoriteStationsList?.addEventListener('click', (e) => {
      const target = e.target as HTMLElement;
      if (target.classList.contains('remove-station-btn')) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = target as HTMLButtonElement;
        const stationIdAttr = btn.getAttribute('data-station-id');
        const stationIndexAttr = btn.getAttribute('data-station-index');
        const stationId = stationIdAttr ? parseInt(stationIdAttr) : 0;
        const stationIndex = stationIndexAttr ? parseInt(stationIndexAttr) : -1;
        
        console.log('Delete button clicked (delegated), stationId:', stationId, 'index:', stationIndex);
        
        // インデックスが有効な場合は、インデックスで削除（最も確実）
        if (!isNaN(stationIndex) && stationIndex >= 0 && stationIndex < this.favoriteStations.length) {
          console.log('Removing station by index:', stationIndex);
                    this.favoriteStations.splice(stationIndex, 1);
          this.renderFavoriteStations();
          this.announceFavoriteStations('お気に入りの駅を削除しました。保存すると反映されます。');
          return;

        }
        
        // 駅IDが有効な場合は、IDで削除
        if (!isNaN(stationId) && stationId > 0) {
          console.log('Removing station by ID:', stationId);
                    this.removeFavoriteStation(stationId);
          this.announceFavoriteStations('お気に入りの駅を削除しました。保存すると反映されます。');
          return;

        }
        
        // 駅名で削除を試みる（フォールバック）
        const stationItem = btn.closest('.favorite-station-item');
        if (stationItem) {
          let stationName = stationItem.querySelector('.station-name')?.textContent || '';
          stationName = stationName.replace(/^駅ID:\s*/, '').trim();
          console.log('Removing station by name:', stationName);
          if (stationName) {
            this.removeFavoriteStationByName(stationName);
          }
        }
      }
    });

  }

  private debounceSearch(keyword: string): void {
    if (this.stationSearchTimeout) {
      clearTimeout(this.stationSearchTimeout);
    }
    this.stationSearchTimeout = window.setTimeout(() => {
      this.searchStations(keyword);
    }, 300);
  }

  private async searchStations(keyword: string): Promise<void> {
    try {
      const { body: data } = await getApi<Station[]>(`/stations/search?keyword=${encodeURIComponent(keyword)}&limit=10`);
      if (data.success && data.data) {
        this.showStationSearchResults(data.data);
      } else {
        this.stationSearchResults = [];
        this.showStationSearchResults([]);
      }
    } catch (error) {
      console.error('Station search error:', error);
      this.stationSearchResults = [];
      this.hideStationSearchResults();
      this.announceStationSearch('駅候補の検索に失敗しました。時間をおいて再試行してください。');
    }
  }

  private showStationSearchResults(stations: Station[]): void {
    const resultsContainer = document.getElementById('station-search-results');
    const input = document.getElementById('station-search-input') as HTMLInputElement | null;
    if (!resultsContainer || !input) return;

    this.stationSearchResults = stations.filter((station) => !this.favoriteStations.some((fav) => fav.id === station.id));
    this.activeStationOptionIndex = -1;
    resultsContainer.replaceChildren();

    if (this.stationSearchResults.length === 0) {
      const option = document.createElement('div');
      option.className = 'search-result-item search-result-item--empty';
      option.setAttribute('role', 'option');
      option.setAttribute('aria-disabled', 'true');
      option.textContent = '追加できる駅が見つかりませんでした';
      resultsContainer.appendChild(option);
      resultsContainer.style.display = 'block';
      input.setAttribute('aria-expanded', 'true');
      input.removeAttribute('aria-activedescendant');
      this.announceStationSearch('追加できる駅の候補は見つかりませんでした。');
      return;
    }

    this.stationSearchResults.forEach((station, index) => {
      const option = document.createElement('div');
      option.id = `station-search-option-${index}`;
      option.className = 'search-result-item';
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', 'false');
      const name = document.createElement('span');
      name.className = 'station-name';
      name.textContent = station.station_name;
      option.appendChild(name);
      if (station.prefecture) {
        const location = document.createElement('span');
        location.className = 'station-location';
        location.textContent = `${station.prefecture}${station.city ? ` ${station.city}` : ''}`;
        option.appendChild(location);
      }
      option.addEventListener('mousedown', (event) => event.preventDefault());
      option.addEventListener('click', () => this.selectStationSearchResult(index));
      resultsContainer.appendChild(option);
    });

    resultsContainer.style.display = 'block';
    input.setAttribute('aria-expanded', 'true');
    input.removeAttribute('aria-activedescendant');
    this.announceStationSearch(`${this.stationSearchResults.length}件の駅候補を表示しています。上下矢印キーで選び、Enterキーで追加できます。`);
  }

  private handleStationSearchKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      this.hideStationSearchResults();
      return;
    }
    if (this.stationSearchResults.length === 0) return;

    if (event.key === 'ArrowDown') {
      event.preventDefault();
      this.setActiveStationOption((this.activeStationOptionIndex + 1) % this.stationSearchResults.length);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      this.setActiveStationOption((this.activeStationOptionIndex - 1 + this.stationSearchResults.length) % this.stationSearchResults.length);
    } else if (event.key === 'Enter' && this.activeStationOptionIndex >= 0) {
      event.preventDefault();
      this.selectStationSearchResult(this.activeStationOptionIndex);
    }
  }

  private setActiveStationOption(index: number): void {
    const input = document.getElementById('station-search-input') as HTMLInputElement | null;
    const previous = document.getElementById(`station-search-option-${this.activeStationOptionIndex}`);
    previous?.classList.remove('search-result-item--active');
    previous?.setAttribute('aria-selected', 'false');
    this.activeStationOptionIndex = index;
    const current = document.getElementById(`station-search-option-${index}`);
    current?.classList.add('search-result-item--active');
    current?.setAttribute('aria-selected', 'true');
    current?.scrollIntoView({ block: 'nearest' });
    input?.setAttribute('aria-activedescendant', `station-search-option-${index}`);
  }

  private selectStationSearchResult(index: number): void {
    const station = this.stationSearchResults[index];
    if (!station) return;
    this.addFavoriteStation(station.id, station.station_name);
    const input = document.getElementById('station-search-input') as HTMLInputElement | null;
    if (input) {
      input.value = '';
      input.focus();
    }
    this.hideStationSearchResults();
    this.announceFavoriteStations(`${station.station_name}をお気に入りへ追加しました。保存すると反映されます。`);
  }

  private hideStationSearchResults(): void {
    const resultsContainer = document.getElementById('station-search-results');
    const input = document.getElementById('station-search-input') as HTMLInputElement | null;
    if (resultsContainer) resultsContainer.style.display = 'none';
    input?.setAttribute('aria-expanded', 'false');
    input?.removeAttribute('aria-activedescendant');
    this.activeStationOptionIndex = -1;
  }

  private announceStationSearch(message: string): void {
    const status = document.getElementById('station-search-status');
    if (status) status.textContent = message;
  }

  private announceFavoriteStations(message: string): void {
    const status = document.getElementById('favorite-stations-status');
    if (status) status.textContent = message;
  }

  private addFavoriteStation(stationId: number, stationName: string): void {
    if (this.favoriteStations.some(fav => fav.id === stationId)) {
      return;
    }

    this.favoriteStations.push({ id: stationId, name: stationName });
    this.renderFavoriteStations();
  }

  private removeFavoriteStation(stationId: number): void {
    console.log('Before remove:', this.favoriteStations.length);
    this.favoriteStations = this.favoriteStations.filter(fav => fav.id !== stationId);
    console.log('After remove:', this.favoriteStations.length);
    this.renderFavoriteStations();
  }

  private removeFavoriteStationByName(stationName: string): void {
    console.log('Before remove by name:', this.favoriteStations.length, 'name:', stationName);
    // 駅名が「駅ID: X」の形式の場合も考慮して削除
    const cleanStationName = stationName.replace(/^駅ID:\s*/, '').trim();
    this.favoriteStations = this.favoriteStations.filter(fav => {
      const cleanFavName = fav.name.replace(/^駅ID:\s*/, '').trim();
      return cleanFavName !== cleanStationName && fav.name !== stationName;
    });
    console.log('After remove by name:', this.favoriteStations.length);
    this.renderFavoriteStations();
  }

  private renderFavoriteStations(): void {
    const container = document.getElementById('favorite-stations-list');
    if (!container) return;

    if (this.favoriteStations.length === 0) {
      container.innerHTML = '<p class="empty-message">お気に入りの駅が登録されていません</p>';
      return;
    }

    container.innerHTML = this.favoriteStations.map((fav, index) => `
      <div class="favorite-station-item" data-station-index="${index}">
        <span class="station-name">${this.escapeHtml(fav.name)}</span>
        <button type="button" class="remove-station-btn" data-station-id="${fav.id}" data-station-index="${index}">削除</button>
      </div>
    `).join('');

    // イベント委譲を使用しているため、ここで個別にイベントハンドラーを追加する必要はない
    // setupEventListeners()で設定済み
  }

  private async loadProfile(): Promise<void> {
    const loadingEl = document.getElementById('loading');
    const formEl = document.getElementById('profile-form') as HTMLElement;
    const errorEl = document.getElementById('error-message');

    

    try {
      const { status, body: data } = await getApi<ProfileData>('/auth/profile');

      if (loadingEl) {
        loadingEl.style.display = 'none';
        loadingEl.setAttribute('aria-busy', 'false');
      }

                  if (status === 401) {
        clearClientAuthState();

        window.location.href = '/login';
        return;
      }

      if (data.success && data.data) {
        this.populateForm(data.data);
        if (formEl) formEl.style.display = 'block';
      } else {

        // プロフィールが存在しない場合、ユーザー情報のみ表示
        await this.loadUserInfo();
        if (formEl) formEl.style.display = 'block';
      }
    } catch (error) {
      console.error('Load profile error:', error);
            if (loadingEl) {
        loadingEl.style.display = 'none';
        loadingEl.setAttribute('aria-busy', 'false');
      }
      if (errorEl) {

        errorEl.textContent = 'プロフィールの読み込みに失敗しました';
        errorEl.style.display = 'block';
      }
      // エラーでもフォームは表示
      await this.loadUserInfo();
      if (formEl) formEl.style.display = 'block';
    }
  }

    private async loadUserInfo(): Promise<void> {
    const authState = getClientAuthState();
    const username = authState.username || '';

    const usernameInput = document.getElementById('username') as HTMLInputElement;
    if (usernameInput) {
      usernameInput.value = username;
    }

        const email = authState.userEmail || '';

    const emailInput = document.getElementById('email') as HTMLInputElement;
    if (emailInput) {
      emailInput.value = email;
    }
  }

  private populateForm(data: ProfileData): void {
    // 基本情報
    const usernameInput = document.getElementById('username') as HTMLInputElement;
    const emailInput = document.getElementById('email') as HTMLInputElement;

    if (usernameInput) usernameInput.value = data.username || '';
    if (emailInput) emailInput.value = data.email || '';

    // 障害情報（最初の1つを選択状態にする）
    if (data.disability_type && Array.isArray(data.disability_type) && data.disability_type.length > 0) {
      const select = document.getElementById('disability_type') as HTMLSelectElement;
      if (select && data.disability_type[0]) {
        select.value = data.disability_type[0];
      }
    }

    // お気に入りの駅（APIからは駅IDの配列が返される）
    if (data.favorite_stations && Array.isArray(data.favorite_stations) && data.favorite_stations.length > 0) {
      // APIから駅IDの配列が返されるので、駅IDから駅名を取得して表示用に使用
      const stationIds = data.favorite_stations.map(id => parseInt(String(id))).filter(id => !isNaN(id) && id > 0);
      if (stationIds.length > 0) {
        this.loadFavoriteStationNamesFromIds(stationIds);
      } else {
        this.favoriteStations = [];
        this.renderFavoriteStations();
      }
    } else {
      this.favoriteStations = [];
      this.renderFavoriteStations();
    }

    // 優先したい設備
    if (data.preferred_features && Array.isArray(data.preferred_features)) {
      data.preferred_features.forEach(feature => {
        const checkbox = document.querySelector(`input[name="preferred_features"][value="${feature}"]`) as HTMLInputElement;
        if (checkbox) checkbox.checked = true;
      });
    }
  }

  private async loadFavoriteStationNamesFromIds(stationIds: number[]): Promise<void> {
    // 各駅IDから駅名を取得
    const stations: Array<{ id: number; name: string }> = [];
    for (const id of stationIds) {
      try {
                const { body: data } = await getApi<Station>(`/stations/${id}`);

        if (data.success && data.data) {
          stations.push({ id: data.data.id, name: data.data.station_name });
        } else {
          console.warn(`Station not found: ${id}`);
          stations.push({ id, name: `駅ID: ${id}` });
        }
      } catch (error) {
        console.error(`Failed to load station ${id}:`, error);
        stations.push({ id, name: `駅ID: ${id}` });
      }
    }
    this.favoriteStations = stations;
    this.renderFavoriteStations();
  }

  private async loadFavoriteStationNamesFromNames(stationNames: string[]): Promise<void> {
    // 各駅名から駅IDを取得（完全一致で検索）
    const stations: Array<{ id: number; name: string }> = [];
    for (const name of stationNames) {
      // 「駅ID: X」の形式の場合は除去して駅名のみを使用
      const cleanName = name.replace(/^駅ID:\s*/, '').trim();
      
      // 駅名から駅IDを検索（完全一致）
      try {
                const { body: data } = await getApi<Station[]>(`/stations/search?keyword=${encodeURIComponent(cleanName)}&limit=50`);

        if (data.success && data.data && data.data.length > 0) {
          // 完全一致する駅を探す
          const exactMatch = data.data.find(station => station.station_name === cleanName);
          if (exactMatch) {
            stations.push({ id: exactMatch.id, name: exactMatch.station_name });
          } else {
            // 完全一致が見つからない場合は最初の1件を使用
            stations.push({ id: data.data[0].id, name: data.data[0].station_name });
          }
        } else {
          // 見つからない場合は駅名のみを使用（IDは0、「駅ID:」プレフィックスなしで表示）
          console.warn(`Station not found: ${cleanName}`);
          stations.push({ id: 0, name: cleanName });
        }
      } catch (error) {
        console.error(`Failed to load station ${cleanName}:`, error);
        stations.push({ id: 0, name: cleanName });
      }
    }
    this.favoriteStations = stations;
    this.renderFavoriteStations();
  }

  private async handleSubmit(e: Event): Promise<void> {
    e.preventDefault();
    const form = e.target as HTMLFormElement;
    const formData = new FormData(form);

    // ユーザー名のバリデーション
    const username = formData.get('username') as string;
    if (!username || username.trim().length === 0) {
      this.showError('ユーザー名を入力してください');
      return;
    }

    // フォームデータを収集
    const disabilitySelect = document.getElementById('disability_type') as HTMLSelectElement;
    const selectedDisability = disabilitySelect?.value || '';
    const disabilityTypes = selectedDisability ? [selectedDisability] : [];

    // 駅IDが0のもの（駅名からIDを取得できなかったもの）を除外
    const favoriteStationIds = this.favoriteStations
      .map(fav => fav.id)
      .filter(id => id > 0);

    const featureCheckboxes = document.querySelectorAll<HTMLInputElement>('input[name="preferred_features"]:checked');
    const preferredFeatures = Array.from(featureCheckboxes).map(cb => cb.value);

    const profileData: Partial<ProfileData> = {
      username: username.trim(),
      disability_type: disabilityTypes.length > 0 ? disabilityTypes : [],
      favorite_stations: favoriteStationIds, // 空の配列でも明示的に送信（削除を反映するため）
      preferred_features: preferredFeatures, // 空の配列でも明示的に送信（全てのチェックを外した場合に対応）
    };

    // APIに送信
    await this.saveProfile(profileData);
  }

  private async saveProfile(data: Partial<ProfileData>): Promise<void> {
    const saveBtn = document.querySelector('.save-btn') as HTMLButtonElement;
    const successEl = document.getElementById('save-success');

    

    if (saveBtn) {
      saveBtn.disabled = true;
      saveBtn.setAttribute('aria-busy', 'true');
      saveBtn.textContent = '保存中...';
    }

    try {
      const requestData = { ...data };

      const { body: result } = await patchApi<ProfileData>('/auth/profile', requestData);

      if (result.success) {
        // ユーザー名が変更された場合、localStorageも更新
        if (data.username) {
                    updateClientUsername(data.username);

        }
        
                // 保存成功を画面上に残し、利用者が確認してから次の操作を選べるようにする。
        if (successEl) {
          successEl.textContent = 'プロフィールを保存しました。変更は次回の駅検索に反映されます。';
          successEl.style.display = 'block';
          successEl.focus();
        }

      } else {
        this.showError(result.error || 'プロフィールの保存に失敗しました');
      }
    } catch (error) {
      console.error('Save profile error:', error);
      this.showError('プロフィールの保存に失敗しました');
    } finally {
            if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.setAttribute('aria-busy', 'false');
        saveBtn.textContent = '保存';
      }

    }
  }

    

  private showError(message: string): void {

    const errorEl = document.getElementById('error-message');
    if (errorEl) {
      errorEl.textContent = message;
      errorEl.style.display = 'block';
      setTimeout(() => {
        errorEl.style.display = 'none';
      }, 5000);
    }
  }

  private isValidEmail(email: string): boolean {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  }

  private escapeHtml(text: string): string {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

}

document.addEventListener('DOMContentLoaded', () => {
  new ProfilePage();
});

