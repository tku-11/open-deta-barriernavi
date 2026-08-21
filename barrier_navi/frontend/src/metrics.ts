export type DisabilityMode = 'body' | 'hearing' | 'vision';
export type MetricType = 'flag' | 'number' | 'ratio';

export interface MetricDefinition {
  key: string;
  label: string;
  required: number;
  type: MetricType;
}

export const BODY_METRICS: MetricDefinition[] = [
  { key: 'step_response_status', label: '段差への対応', required: 1, type: 'flag' },
  { key: 'has_guidance_system', label: '案内設備の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_restroom', label: '障害者対応型便所の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_gate', label: '障害者対応型改札口の設置の有無', required: 1, type: 'flag' },
  { key: 'has_fall_prevention', label: '転落防止のための設備の設置の有無', required: 1, type: 'flag' },
  { key: 'platform_ratio', label: '段差が解消されているプラットホームの割合', required: 0.8, type: 'ratio' },
  { key: 'elevator_ratio', label: '移動等円滑化基準に適合しているエレベーターの割合', required: 0.8, type: 'ratio' },
  { key: 'escalator_ratio', label: '移動等円滑化基準に適合しているエスカレーターの割合', required: 0.8, type: 'ratio' },
  { key: 'num_other_lifts', label: 'その他の昇降機の設置基数', required: 2, type: 'number' },
  { key: 'num_slopes', label: '傾斜路の設置箇所数', required: 2, type: 'number' },
  { key: 'num_compliant_slopes', label: '移動等円滑化基準に適合している傾斜路の設置箇所数', required: 2, type: 'number' },
  { key: 'num_wheelchair_accessible_platforms', label: '車いす使用者の円滑な乗降が可能なプラットホームの数', required: 6, type: 'number' },
];

export const HEARING_METRICS: MetricDefinition[] = [
  { key: 'has_guidance_system', label: '案内設備の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_restroom', label: '障害者対応型便所の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_gate', label: '障害者対応型改札口の設置の有無', required: 1, type: 'flag' },
  { key: 'has_fall_prevention', label: '転落防止のための設備の設置の有無', required: 1, type: 'flag' },
];

export const VISION_METRICS: MetricDefinition[] = [
  { key: 'step_response_status', label: '段差への対応', required: 1, type: 'flag' },
  { key: 'has_tactile_paving', label: '視覚障害者誘導用ブロックの設置の有無', required: 1, type: 'flag' },
  { key: 'has_guidance_system', label: '案内設備の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_restroom', label: '障害者対応型便所の設置の有無', required: 1, type: 'flag' },
  { key: 'has_accessible_gate', label: '障害者対応型改札口の設置の有無', required: 1, type: 'flag' },
  { key: 'has_fall_prevention', label: '転落防止のための設備の設置の有無', required: 1, type: 'flag' },
  { key: 'platform_ratio', label: '段差が解消されているプラットホームの割合', required: 0.8, type: 'ratio' },
  { key: 'num_compliant_elevators', label: '移動等円滑化基準に適合しているエレベーターの設置基数', required: 4, type: 'number' },
  { key: 'num_compliant_escalators', label: '移動等円滑化基準に適合しているエスカレーターの設置基数', required: 4, type: 'number' },
  { key: 'num_compliant_slopes', label: '移動等円滑化基準に適合している傾斜路の設置箇所数', required: 2, type: 'number' },
];

export const METRICS_BY_MODE: Record<DisabilityMode, MetricDefinition[]> = {
  body: BODY_METRICS,
  hearing: HEARING_METRICS,
  vision: VISION_METRICS,
};

export type PreferredFeature =
  | 'エレベーター'
  | 'エスカレーター'
  | '障害者対応型改札口'
  | '障害者対応型便所'
  | '案内設備'
  | '転落防止設備'
  | '段差解消'
  | '車いす対応プラットフォーム';

export const PREFERRED_FEATURE_TO_METRIC_KEY: Record<PreferredFeature, Record<DisabilityMode, string[]>> = {
  'エレベーター': {
    body: ['elevator_ratio'],
    hearing: [],
    vision: ['num_compliant_elevators'],
  },
  'エスカレーター': {
    body: ['escalator_ratio'],
    hearing: [],
    vision: ['num_compliant_escalators'],
  },
  '障害者対応型改札口': {
    body: ['has_accessible_gate'],
    hearing: ['has_accessible_gate'],
    vision: ['has_accessible_gate'],
  },
  '障害者対応型便所': {
    body: ['has_accessible_restroom'],
    hearing: ['has_accessible_restroom'],
    vision: ['has_accessible_restroom'],
  },
  '案内設備': {
    body: ['has_guidance_system'],
    hearing: ['has_guidance_system'],
    vision: ['has_guidance_system'],
  },
  '転落防止設備': {
    body: ['has_fall_prevention'],
    hearing: ['has_fall_prevention'],
    vision: ['has_fall_prevention'],
  },
  '段差解消': {
    body: ['step_response_status', 'platform_ratio'],
    hearing: [],
    vision: ['step_response_status', 'platform_ratio'],
  },
  '車いす対応プラットフォーム': {
    body: ['num_wheelchair_accessible_platforms'],
    hearing: [],
    vision: [],
  },
};

export function metricKeysForPreferredFeature(feature: string, mode: DisabilityMode): string[] {
  return PREFERRED_FEATURE_TO_METRIC_KEY[feature as PreferredFeature]?.[mode] ?? [];
}
