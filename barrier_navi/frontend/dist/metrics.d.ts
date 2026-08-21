export type DisabilityMode = 'body' | 'hearing' | 'vision';
export type MetricType = 'flag' | 'number' | 'ratio';
export interface MetricDefinition {
    key: string;
    label: string;
    required: number;
    type: MetricType;
}
export declare const BODY_METRICS: MetricDefinition[];
export declare const HEARING_METRICS: MetricDefinition[];
export declare const VISION_METRICS: MetricDefinition[];
export declare const METRICS_BY_MODE: Record<DisabilityMode, MetricDefinition[]>;
export type PreferredFeature = 'エレベーター' | 'エスカレーター' | '障害者対応型改札口' | '障害者対応型便所' | '案内設備' | '転落防止設備' | '段差解消' | '車いす対応プラットフォーム';
export declare const PREFERRED_FEATURE_TO_METRIC_KEY: Record<PreferredFeature, Record<DisabilityMode, string[]>>;
export declare function metricKeysForPreferredFeature(feature: string, mode: DisabilityMode): string[];
//# sourceMappingURL=metrics.d.ts.map