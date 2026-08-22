import { getApi } from './api.js';
import { metricKeysForPreferredFeature } from './metrics.js';
class DetailPage {
    constructor() {
        this.titleEl = null;
        this.scoreEl = null;
        this.metaEl = null;
        this.tableBodyEl = null;
        this.decisionSummaryEl = null;
        this.decisionSummaryTextEl = null;
        this.decisionSummaryListEl = null;
        // ★追加: 現在のモード
        this.currentMode = 'body';
        this.titleEl = document.getElementById('detail-title');
        this.scoreEl = document.getElementById('detail-score');
        this.metaEl = document.getElementById('detail-meta');
        this.tableBodyEl = document.getElementById('detail-table-body');
        this.decisionSummaryEl = document.getElementById('decision-summary');
        this.decisionSummaryTextEl = document.getElementById('decision-summary-text');
        this.decisionSummaryListEl = document.getElementById('decision-summary-list');
        // ★追加: モード判定
        const params = new URLSearchParams(window.location.search);
        const urlMode = params.get('mode');
        const bodyMode = document.body.dataset.mode;
        if (urlMode === 'hearing' || bodyMode === 'hearing') {
            this.currentMode = 'hearing';
        }
        else if (urlMode === 'vision' || bodyMode === 'vision') {
            this.currentMode = 'vision';
        }
        else {
            this.currentMode = 'body';
        }
        this.setupBackButton();
        this.load();
    }
    setupBackButton() {
        const backBtn = document.getElementById('back_btn');
        if (backBtn) {
            if (this.currentMode === 'hearing') {
                backBtn.href = '/hearing';
            }
            else if (this.currentMode === 'vision') {
                backBtn.href = '/vision';
            }
            else {
                backBtn.href = '/index';
            }
        }
    }
    async load() {
        this.updateStatus('駅の詳細情報を読み込んでいます。');
        const params = new URLSearchParams(window.location.search);
        const stationId = Number(params.get('stationId'));
        if (!stationId) {
            this.renderError('駅IDが指定されていません。');
            return;
        }
        // ★修正: モードに応じてAPIパスを切り替える
        const apiPath = this.currentMode === 'hearing' ? '/hearing/stations' : this.currentMode === 'vision' ? '/vision/stations' : '/body/stations';
        // 修正後:
        const response = await this.fetchApi(`${apiPath}/${stationId}`);
        if (response.success && response.data) {
            this.renderDetail(response.data);
            await this.renderDecisionSummary(response.data);
        }
        else {
            this.renderError(response.error || 'データを取得できませんでした。');
        }
    }
    async fetchApi(endpoint) {
        const result = await getApi(endpoint);
        return result.body;
    }
    updateStatus(message) {
        const status = document.getElementById('detail-status');
        if (status)
            status.textContent = message;
    }
    renderDetail(detail) {
        if (!this.titleEl || !this.scoreEl || !this.metaEl || !this.tableBodyEl)
            return;
        this.titleEl.textContent = detail.station_name;
        this.scoreEl.textContent = detail.score.label;
        const city = detail.city ? ` ${detail.city}` : '';
        this.metaEl.innerHTML = `
      <p>鉄道事業者: ${this.escape(detail.operator)}</p>
      <p>路線: ${this.escape(detail.line_name)}</p>
      <p>所在地: ${this.escape(detail.prefecture)}${this.escape(city)}</p>
    `;
        const rows = detail.metrics.map((metric) => {
            let valueDisplay = '';
            let requiredDisplay = '';
            if (metric.type === 'ratio') {
                // 割合型: 既にAPI側で「何分の何 (何%)」形式で処理されているので、そのまま表示
                valueDisplay = String(metric.value ?? '-');
                const requiredPercent = (metric.required !== undefined && metric.required !== null) ? (metric.required * 100) : 100;
                requiredDisplay = `${requiredPercent}%以上`;
            }
            else if (metric.type === 'number') {
                const rawValue = typeof metric.raw_value === 'number' ? metric.raw_value : (metric.value !== null && typeof metric.value === 'number' ? metric.value : 0);
                valueDisplay = `${rawValue}`;
                const required = (metric.required !== undefined && metric.required !== null) ? metric.required : '不明';
                requiredDisplay = `${required}以上`;
            }
            else {
                valueDisplay = String(metric.value ?? '-');
                requiredDisplay = '設置あり';
            }
            return `
        <tr class="${metric.met ? 'metric-met' : ''}">
                    <td data-label="項目">${this.escape(metric.label)}</td>
          <td class="metric-value" data-label="設置の有無と数">${this.escape(valueDisplay)}</td>
          <td class="metric-required" data-label="基準値">${this.escape(requiredDisplay)}</td>
          <td class="metric-status" data-label="判定">${metric.met ? '達成（基準を満たす）' : '未達（基準を満たしていない）'}</td>

        </tr>

      `;
        }).join('');
        this.tableBodyEl.innerHTML = rows;
        this.updateStatus(`${detail.station_name}の詳細情報を表示しました。${detail.metrics.length}項目を確認できます。`);
    }
    async renderDecisionSummary(detail) {
        if (!this.decisionSummaryEl || !this.decisionSummaryTextEl || !this.decisionSummaryListEl)
            return;
        const metMetrics = detail.metrics.filter((metric) => metric.met);
        const unmetMetrics = detail.metrics.filter((metric) => !metric.met);
        this.decisionSummaryTextEl.textContent = `${detail.score.label}。${detail.score.met_items} / ${detail.score.total_items}項目を達成し、達成率は${detail.score.percentage}%です。`;
        this.decisionSummaryListEl.replaceChildren();
        const addItem = (message, className) => {
            const item = document.createElement('li');
            if (className)
                item.className = className;
            item.textContent = message;
            this.decisionSummaryListEl?.appendChild(item);
        };
        addItem(`達成: ${metMetrics.length}項目`);
        if (unmetMetrics.length > 0) {
            addItem(`未達: ${unmetMetrics.length}項目（${unmetMetrics.slice(0, 3).map((metric) => metric.label).join('、')}）`, 'decision-summary-list__unmet');
        }
        else {
            addItem('未達項目はありません。');
        }
        try {
            const profile = await this.fetchApi('/auth/profile');
            const features = profile.success && profile.data && Array.isArray(profile.data.preferred_features)
                ? profile.data.preferred_features
                : [];
            const preferredMetricKeys = [...new Set(features.flatMap((feature) => metricKeysForPreferredFeature(feature, this.currentMode)))];
            if (features.length > 0 && preferredMetricKeys.length > 0) {
                const preferredMetrics = detail.metrics.filter((metric) => preferredMetricKeys.includes(metric.key));
                const preferredMetCount = preferredMetrics.filter((metric) => metric.met).length;
                addItem(`プロフィールの優先設備に対応する評価項目: ${preferredMetCount} / ${preferredMetrics.length}項目を達成`);
                const preferredUnmet = preferredMetrics.filter((metric) => !metric.met);
                if (preferredUnmet.length > 0) {
                    addItem(`優先設備で未達: ${preferredUnmet.map((metric) => metric.label).join('、')}`, 'decision-summary-list__unmet');
                }
            }
            else if (features.length > 0) {
                addItem('プロフィールの優先設備は、このカテゴリの評価項目には対応していません。');
            }
        }
        catch (error) {
            // ログインしていない場合やプロフィール取得に失敗した場合も詳細比較は利用可能にする。
            console.warn('Failed to load profile preferences for detail summary:', error);
        }
        this.decisionSummaryEl.hidden = false;
    }
    renderError(message) {
        if (this.tableBodyEl) {
            this.tableBodyEl.innerHTML = `<tr><td colspan="4" class="error" role="alert">${this.escape(message)}</td></tr>`;
            this.updateStatus(`駅詳細の取得に失敗しました。${message}`);
        }
    }
    escape(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}
document.addEventListener('DOMContentLoaded', () => new DetailPage());
//# sourceMappingURL=detail.js.map