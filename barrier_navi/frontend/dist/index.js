import { getApi } from './api.js';
import { getClientAuthState } from './auth.js';
import { BODY_METRICS, HEARING_METRICS, metricKeysForPreferredFeature, VISION_METRICS, } from './metrics.js';
class StationApp {
    constructor() {
        this.currentPage = 1;
        this.pageSize = 10;
        this.selectedPrefecture = null;
        this.keyword = '';
        this.totalCount = 0; // ★追加：全件数を保存
        this.selectedFilters = [];
        this.sortOrder = 'none';
        this.currentMode = 'body';
        this.favoriteStationIds = []; // お気に入り駅IDのリスト
        const mode = document.body.dataset.mode;
        if (mode === 'hearing') {
            this.currentMode = 'hearing';
            this.currentMetrics = HEARING_METRICS;
        }
        else if (mode === 'vision') {
            this.currentMode = 'vision';
            this.currentMetrics = VISION_METRICS;
        }
        else {
            this.currentMode = 'body';
            this.currentMetrics = BODY_METRICS;
        }
        this.init();
    }
    async init() {
        this.renderFilterControls();
        this.setupEventListeners();
        await this.loadPrefectures();
        await this.fetchLines();
        // プロフィールの優先機能を自動的に適用
        await this.applyPreferredFeatures();
        // お気に入り駅を取得
        await this.loadFavoriteStations();
        await this.loadStations();
    }
    renderFilterControls() {
        const container = document.getElementById('filter-list');
        if (!container)
            return;
        container.innerHTML = '';
        this.currentMetrics.forEach((metric) => {
            const item = document.createElement('div');
            item.className = 'filter-item';
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `filter-${metric.key}`;
            checkbox.dataset.metricKey = metric.key;
            checkbox.className = 'filter-checkbox';
            const label = document.createElement('label');
            label.htmlFor = `filter-${metric.key}`;
            label.textContent = metric.label;
            checkbox.addEventListener('change', () => {
                this.currentPage = 1;
                this.loadStations();
            });
            item.appendChild(checkbox);
            item.appendChild(label);
            container.appendChild(item);
        });
    }
    setupEventListeners() {
        const searchButton = document.getElementById('search-btn');
        const searchInput = document.getElementById('search-input');
        const prefectureSelect = document.getElementById('prefecture-select');
        const sortSelect = document.getElementById('sort-select');
        // ページネーションボタン
        const prevButton = document.getElementById('prev-btn');
        const nextButton = document.getElementById('next-btn');
        const firstButton = document.getElementById('first-btn'); // ★追加
        const lastButton = document.getElementById('last-btn'); // ★追加
        const filterButton = document.getElementById('apply-filter-btn');
        const resetButton = document.getElementById('reset-filter-btn');
        const lineSelect = document.getElementById('line-select');
        searchButton?.addEventListener('click', () => this.applySearch());
        searchInput?.addEventListener('keypress', (event) => {
            if (event.key === 'Enter')
                this.applySearch();
        });
        prefectureSelect?.addEventListener('change', (event) => {
            this.selectedPrefecture = event.target.value || null;
            this.currentPage = 1;
            this.loadStations();
        });
        sortSelect?.addEventListener('change', (event) => {
            const value = event.target.value;
            this.sortOrder = value;
            this.currentPage = 1;
            this.loadStations();
        });
        prevButton?.addEventListener('click', () => {
            if (this.currentPage > 1) {
                this.currentPage -= 1;
                this.loadStations();
            }
        });
        nextButton?.addEventListener('click', () => {
            // 次のページへ（総ページ数計算はloadStations後のtotalCountに依存しますが、簡易的なチェックとしてlastResultCountも使用可能）
            // updatePaginationで制御されているため、ここではシンプルに加算
            this.currentPage += 1;
            this.loadStations();
        });
        // ★追加: 最初へボタンの処理
        firstButton?.addEventListener('click', () => {
            this.currentPage = 1;
            this.loadStations();
        });
        // ★追加: 最後へボタンの処理
        lastButton?.addEventListener('click', () => {
            const totalPages = Math.ceil(this.totalCount / this.pageSize);
            this.currentPage = totalPages > 0 ? totalPages : 1;
            this.loadStations();
        });
        filterButton?.addEventListener('click', () => {
            this.currentPage = 1;
            this.loadStations();
        });
        resetButton?.addEventListener('click', () => {
            this.resetFilters();
        });
        lineSelect?.addEventListener('change', () => {
            this.currentPage = 1;
            this.loadStations();
        });
    }
    applySearch() {
        const searchInput = document.getElementById('search-input');
        this.keyword = searchInput?.value.trim() || '';
        this.currentPage = 1;
        this.loadStations();
    }
    resetFilters() {
        // 都道府県をリセット
        const prefectureSelect = document.getElementById('prefecture-select');
        if (prefectureSelect) {
            prefectureSelect.value = '';
            this.selectedPrefecture = null;
        }
        // すべてのチェックボックスをリセット
        const checkboxes = document.querySelectorAll('.filter-checkbox');
        checkboxes.forEach((checkbox) => {
            checkbox.checked = false;
        });
        this.selectedFilters = [];
        // 検索キーワードをリセット
        const searchInput = document.getElementById('search-input');
        if (searchInput) {
            searchInput.value = '';
            this.keyword = '';
        }
        // ソートをリセット
        const sortSelect = document.getElementById('sort-select');
        if (sortSelect) {
            sortSelect.value = 'none';
            this.sortOrder = 'none';
        }
        const lineSelect = document.getElementById('line-select');
        if (lineSelect) {
            lineSelect.value = '';
        }
        // ページをリセットして再読み込み
        this.currentPage = 1;
        this.loadStations();
    }
    collectFilters() {
        const checkboxes = document.querySelectorAll('.filter-checkbox:checked');
        const filters = [];
        checkboxes.forEach((checkbox) => {
            const metricKey = checkbox.dataset.metricKey;
            if (metricKey) {
                filters.push(metricKey);
            }
        });
        return filters;
    }
    /**
     * プロフィールの優先機能を読み込んで自動的に適用
     */
    async applyPreferredFeatures() {
        const authState = getClientAuthState();
        if (!authState.isLoggedIn || !authState.userId) {
            // ログインしていない場合は何もしない
            return;
        }
        try {
            const { body: data } = await getApi('/auth/profile');
            if (data.success && data.data && data.data.preferred_features && data.data.preferred_features.length > 0) {
                // 優先機能をメトリックキーに変換
                const metricKeys = [];
                data.data.preferred_features.forEach((feature) => {
                    metricKeys.push(...metricKeysForPreferredFeature(feature, this.currentMode));
                });
                // 重複を除去
                const uniqueMetricKeys = [...new Set(metricKeys)];
                // 現在のモードで利用可能なメトリックのみをフィルタリング
                const availableMetricKeys = uniqueMetricKeys.filter(key => this.currentMetrics.some(metric => metric.key === key));
                if (availableMetricKeys.length > 0) {
                    // チェックボックスを自動的にチェック
                    availableMetricKeys.forEach(metricKey => {
                        const checkbox = document.querySelector(`input.filter-checkbox[data-metric-key="${metricKey}"]`);
                        if (checkbox) {
                            checkbox.checked = true;
                        }
                    });
                    // 絞り込み条件として適用
                    this.selectedFilters = availableMetricKeys;
                    // アクティブフィルターを表示
                    this.updateActiveFilters();
                }
            }
        }
        catch (error) {
            console.error('Failed to load preferred features:', error);
            // エラーが発生しても処理を続行
        }
    }
    /**
     * お気に入り駅IDを取得
     */
    async loadFavoriteStations() {
        const authState = getClientAuthState();
        if (!authState.isLoggedIn || !authState.userId) {
            // ログインしていない場合は空配列を設定
            this.favoriteStationIds = [];
            return;
        }
        try {
            const { body: data } = await getApi('/auth/profile');
            if (data.success && data.data && data.data.favorite_stations && Array.isArray(data.data.favorite_stations)) {
                // お気に入り駅IDを保存
                this.favoriteStationIds = data.data.favorite_stations.map(id => parseInt(String(id))).filter(id => !isNaN(id) && id > 0);
            }
            else {
                this.favoriteStationIds = [];
            }
        }
        catch (error) {
            console.error('Failed to load favorite stations:', error);
            // エラーが発生した場合は空配列を設定
            this.favoriteStationIds = [];
        }
    }
    async loadPrefectures() {
        const response = await this.fetchApi('/stations/prefectures');
        if (response.success && response.data) {
            const select = document.getElementById('prefecture-select');
            if (!select)
                return;
            select.innerHTML = '<option value="">都道府県</option>';
            response.data.forEach((item) => {
                const option = document.createElement('option');
                option.value = item.prefecture;
                option.textContent = `${item.prefecture} (${item.count}駅)`;
                select.appendChild(option);
            });
        }
    }
    async fetchApi(endpoint) {
        const result = await getApi(endpoint);
        return result.body;
    }
    async loadStations() {
        const loadingIndicator = document.getElementById('loading');
        const stationsContainer = document.getElementById('stations-list');
        if (loadingIndicator)
            loadingIndicator.style.display = 'block';
        if (stationsContainer)
            stationsContainer.innerHTML = '';
        // チェックボックスからフィルターを収集（既に設定されているフィルターとマージ）
        const collectedFilters = this.collectFilters();
        // 既存のフィルターとマージ（重複を除去）
        const allFilters = [...new Set([...this.selectedFilters, ...collectedFilters])];
        this.selectedFilters = allFilters;
        const params = new URLSearchParams({
            limit: this.pageSize.toString(),
            offset: ((this.currentPage - 1) * this.pageSize).toString(),
            sort: this.sortOrder,
        });
        if (this.selectedPrefecture)
            params.append('prefecture', this.selectedPrefecture);
        if (this.keyword)
            params.append('keyword', this.keyword);
        if (this.selectedFilters.length > 0) {
            params.append('filters', JSON.stringify(this.selectedFilters));
        }
        if (this.favoriteStationIds.length > 0) {
            params.append('favorite_station_ids', JSON.stringify(this.favoriteStationIds));
        }
        const lineSelect = document.getElementById('line-select');
        if (lineSelect && lineSelect.value) {
            params.append('line_name', lineSelect.value);
        }
        const apiPath = this.currentMode === 'hearing' ? '/hearing/stations' : this.currentMode === 'vision' ? '/vision/stations' : '/body/stations';
        const response = await this.fetchApi(`${apiPath}?${params.toString()}`);
        if (loadingIndicator)
            loadingIndicator.style.display = 'none';
        if (response.success && response.data) {
            this.totalCount = response.total_count ?? response.data.length;
            this.renderStationCards(response.data);
            this.updatePagination();
            this.updateActiveFilters();
        }
        else if (stationsContainer) {
            stationsContainer.innerHTML = `<p class="error">データの取得に失敗しました: ${response.error}</p>`;
        }
    }
    updateActiveFilters() {
        const container = document.getElementById('active-filters');
        const group = document.getElementById('active-filters-group');
        if (!container || !group)
            return;
        container.innerHTML = '';
        const hasFilters = this.selectedPrefecture || this.selectedFilters.length > 0 || this.keyword;
        if (!hasFilters) {
            group.style.display = 'none';
            return;
        }
        group.style.display = 'block';
        // 都道府県セクション
        if (this.selectedPrefecture) {
            const section = document.createElement('div');
            section.className = 'filter-section';
            section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">📍</span>
          <span class="filter-section-title">都道府県</span>
        </div>
        <div class="filter-chips">
          <div class="active-filter-chip filter-chip-prefecture">
            <span>${this.escapeHtml(this.selectedPrefecture)}</span>
            <button class="filter-remove-btn" data-type="prefecture" aria-label="削除">×</button>
          </div>
        </div>
      `;
            section.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
                const select = document.getElementById('prefecture-select');
                if (select) {
                    select.value = '';
                    this.selectedPrefecture = null;
                    this.currentPage = 1;
                    this.loadStations();
                }
            });
            container.appendChild(section);
        }
        // 設備フィルタセクション
        if (this.selectedFilters.length > 0) {
            const section = document.createElement('div');
            section.className = 'filter-section';
            section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">🔧</span>
          <span class="filter-section-title">設備条件 <span class="filter-count">(${this.selectedFilters.length}件)</span></span>
        </div>
        <div class="filter-chips">
        </div>
      `;
            const chipsContainer = section.querySelector('.filter-chips');
            this.selectedFilters.forEach((filterKey) => {
                const metric = this.currentMetrics.find(m => m.key === filterKey);
                if (!metric)
                    return;
                const chip = document.createElement('div');
                chip.className = 'active-filter-chip filter-chip-equipment';
                chip.innerHTML = `
          <span>${this.escapeHtml(metric.label)}</span>
          <button class="filter-remove-btn" data-type="filter" data-key="${filterKey}" aria-label="削除">×</button>
        `;
                chip.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
                    const checkbox = document.querySelector(`#filter-${filterKey}`);
                    if (checkbox) {
                        checkbox.checked = false;
                        this.currentPage = 1;
                        this.loadStations();
                    }
                });
                chipsContainer?.appendChild(chip);
            });
            container.appendChild(section);
        }
        // キーワード検索セクション
        if (this.keyword) {
            const section = document.createElement('div');
            section.className = 'filter-section';
            section.innerHTML = `
        <div class="filter-section-header">
          <span class="filter-icon">🔍</span>
          <span class="filter-section-title">検索キーワード</span>
        </div>
        <div class="filter-chips">
          <div class="active-filter-chip filter-chip-keyword">
            <span>"${this.escapeHtml(this.keyword)}"</span>
            <button class="filter-remove-btn" data-type="keyword" aria-label="削除">×</button>
          </div>
        </div>
      `;
            section.querySelector('.filter-remove-btn')?.addEventListener('click', () => {
                const input = document.getElementById('search-input');
                if (input) {
                    input.value = '';
                    this.keyword = '';
                    this.currentPage = 1;
                    this.loadStations();
                }
            });
            container.appendChild(section);
        }
    }
    renderStationCards(stations) {
        const container = document.getElementById('stations-list');
        if (!container)
            return;
        if (stations.length === 0) {
            container.innerHTML = '<p class="no-data">条件に一致する駅が見つかりませんでした。</p>';
            return;
        }
        container.innerHTML = '';
        stations.forEach((station) => {
            const isFavorite = this.favoriteStationIds.includes(station.station_id);
            const card = document.createElement('div');
            card.className = 'station-card';
            if (isFavorite) {
                card.classList.add('station-card--favorite');
            }
            card.innerHTML = `
        <div class="station-card__header">
          <span class="station-card__name">
            ${isFavorite ? '<span class="favorite-icon">★</span>' : ''}
            ${this.escapeHtml(station.station_name)}
          </span>
          <span class="station-card__score">${station.score.label}</span>
        </div>
        <div class="station-card__meta">
          <span>${this.escapeHtml(station.prefecture)} ${this.escapeHtml(station.city || '')}</span>
          <span>${this.escapeHtml(station.operator)}</span>
        </div>
        <div class="station-card__progress">
          <div class="station-card__progress-bar" style="width:${station.score.percentage}%"></div>
        </div>
        <div class="station-card__footer">詳細を見る</div>
      `;
            card.addEventListener('click', () => this.navigateToDetail(station.station_id));
            container.appendChild(card);
        });
    }
    updatePagination() {
        const pageInfo = document.getElementById('page-info');
        const prevButton = document.getElementById('prev-btn');
        const nextButton = document.getElementById('next-btn');
        const firstButton = document.getElementById('first-btn'); // ★追加
        const lastButton = document.getElementById('last-btn'); // ★追加
        // ★追加: 総ページ数の計算
        const totalPages = Math.ceil(this.totalCount / this.pageSize);
        if (pageInfo)
            pageInfo.textContent = `ページ ${this.currentPage} / ${totalPages || 1}`;
        const isFirstPage = this.currentPage === 1;
        const isLastPage = this.currentPage >= totalPages || totalPages === 0;
        if (prevButton)
            prevButton.disabled = isFirstPage;
        if (firstButton)
            firstButton.disabled = isFirstPage; // ★追加
        if (nextButton)
            nextButton.disabled = isLastPage;
        if (lastButton)
            lastButton.disabled = isLastPage; // ★追加
    }
    navigateToDetail(stationId) {
        const url = new URL('/detail', window.location.origin);
        url.searchParams.set('stationId', stationId.toString());
        url.searchParams.set('mode', this.currentMode);
        window.location.href = url.toString();
    }
    escapeHtml(text) {
        if (!text)
            return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    async fetchLines() {
        const lineSelect = document.getElementById('line-select');
        if (!lineSelect)
            return;
        try {
            const { body: json } = await getApi('/lines');
            if (json.success && json.data) {
                lineSelect.innerHTML = '<option value="">指定なし</option>';
                json.data.forEach((line) => {
                    const option = document.createElement('option');
                    option.value = line;
                    option.textContent = line;
                    lineSelect.appendChild(option);
                });
            }
        }
        catch (error) {
            console.error('Failed to fetch lines:', error);
        }
    }
}
document.addEventListener('DOMContentLoaded', () => {
    new StationApp();
});
//# sourceMappingURL=index.js.map