# 現状スコア仕様

## 目的

この文書は、Phase 1 時点の実装に基づくスコア計算仕様を固定する。

対象実装は `backend/api_server.py` の以下である。

- `BODY_METRIC_DEFINITIONS`
- `HEARING_METRIC_DEFINITIONS`
- `VISION_METRIC_DEFINITIONS`
- `evaluate_metric`
- `compute_score`
- `build_station_response`
- `get_stations_with_score`
- `get_station_detail_with_score`

## 基本仕様

スコアは、評価項目ごとの達成有無を数え上げる単純な達成数方式である。

```text
met_items = 達成した評価項目数
total_items = 評価項目総数
percentage = met_items / total_items * 100
label = "{met_items}/{total_items}点"
```

重み付け計算は現状実装されていない。

## 評価項目タイプ

### `flag`

フラグ型。値を文字列化して前後空白を除去し、`"1"` と一致する場合のみ達成とする。

```text
met = str(value).strip() == "1"
processed_value = "○" if met else "×"
ratio = 1.0 if met else 0.0
```

`2`、`3`、`None`、空文字は未達成である。

### `ratio`

割合型。評価定義が持つ `numerator` と `denominator` から割合を計算する。

```text
calculated_ratio = numerator / denominator
met = calculated_ratio >= required
```

分母が 0 以下、または必要なキーがない場合は未達成である。

レスポンスの表示値は以下の形式になる。

```text
"{numerator}/{denominator} ({percentage:.1f}%)"
```

### `number`

数値型。数値化した値が `required` 以上の場合に達成とする。

```text
numeric_value = float(value) if value is not None else 0.0
met = numeric_value >= required
ratio = min(numeric_value / required, 1.0)
```

数値化できない値は 0 として扱う。

## 身体障害向けスコア

現状実装では 12 項目で評価する。

| Key | Label | Type | Required | Source |
| --- | --- | --- | --- | --- |
| `step_response_status` | 段差への対応 | `flag` | 1 | `stations.step_response_status` |
| `has_guidance_system` | 案内設備の設置の有無 | `flag` | 1 | `stations.has_guidance_system` |
| `has_accessible_restroom` | 障害者対応型便所の設置の有無 | `flag` | 1 | `stations.has_accessible_restroom` |
| `has_accessible_gate` | 障害者対応型改札口の設置の有無 | `flag` | 1 | `stations.has_accessible_gate` |
| `has_fall_prevention` | 転落防止のための設備の設置の有無 | `flag` | 1 | `stations.has_fall_prevention` |
| `platform_ratio` | 段差が解消されているプラットホームの割合 | `ratio` | 0.8 | `num_step_free_platforms / num_platforms` |
| `elevator_ratio` | 移動等円滑化基準に適合しているエレベーターの割合 | `ratio` | 0.8 | `num_compliant_elevators / num_elevators` |
| `escalator_ratio` | 移動等円滑化基準に適合しているエスカレーターの割合 | `ratio` | 0.8 | `num_compliant_escalators / num_escalators` |
| `num_other_lifts` | その他の昇降機の設置基数 | `number` | 2 | `stations.num_other_lifts` |
| `num_slopes` | 傾斜路の設置箇所数 | `number` | 2 | `stations.num_slopes` |
| `num_compliant_slopes` | 移動等円滑化基準に適合している傾斜路の設置箇所数 | `number` | 2 | `stations.num_compliant_slopes` |
| `num_wheelchair_accessible_platforms` | 車いす使用者の円滑な乗降が可能なプラットホームの数 | `number` | 6 | `stations.num_wheelchair_accessible_platforms` |

## 聴覚障害向けスコア

現状実装では 4 項目で評価する。

| Key | Label | Type | Required | Source |
| --- | --- | --- | --- | --- |
| `has_guidance_system` | 案内設備の設置の有無 | `flag` | 1 | `stations.has_guidance_system` |
| `has_accessible_restroom` | 障害者対応型便所の設置の有無 | `flag` | 1 | `stations.has_accessible_restroom` |
| `has_accessible_gate` | 障害者対応型改札口の設置の有無 | `flag` | 1 | `stations.has_accessible_gate` |
| `has_fall_prevention` | 転落防止のための設備の設置の有無 | `flag` | 1 | `stations.has_fall_prevention` |

## 視覚障害向けスコア

現状実装では 10 項目で評価する。

| Key | Label | Type | Required | Source |
| --- | --- | --- | --- | --- |
| `step_response_status` | 段差への対応 | `flag` | 1 | `stations.step_response_status` |
| `has_tactile_paving` | 視覚障害者誘導用ブロックの設置の有無 | `flag` | 1 | `stations.has_tactile_paving` |
| `has_guidance_system` | 案内設備の設置の有無 | `flag` | 1 | `stations.has_guidance_system` |
| `has_accessible_restroom` | 障害者対応型便所の設置の有無 | `flag` | 1 | `stations.has_accessible_restroom` |
| `has_accessible_gate` | 障害者対応型改札口の設置の有無 | `flag` | 1 | `stations.has_accessible_gate` |
| `has_fall_prevention` | 転落防止のための設備の設置の有無 | `flag` | 1 | `stations.has_fall_prevention` |
| `platform_ratio` | 段差が解消されているプラットホームの割合 | `ratio` | 0.8 | `num_step_free_platforms / num_platforms` |
| `num_compliant_elevators` | 移動等円滑化基準に適合しているエレベーターの設置基数 | `number` | 4 | `stations.num_compliant_elevators` |
| `num_compliant_escalators` | 移動等円滑化基準に適合しているエスカレーターの設置基数 | `number` | 4 | `stations.num_compliant_escalators` |
| `num_compliant_slopes` | 移動等円滑化基準に適合している傾斜路の設置箇所数 | `number` | 2 | `stations.num_compliant_slopes` |

注意:

既存 README や一部ドキュメントでは視覚障害向けを 9 項目としているが、実装上は 10 項目である。

## スコアレスポンス

### 一覧

`include_details=False` のため、`metrics` は返らない。

```json
{
  "station_id": 1,
  "station_name": "東京",
  "prefecture": "東京都",
  "city": "千代田区",
  "operator": "JR",
  "line_name": "山手線",
  "score": {
    "met_items": 8,
    "total_items": 12,
    "percentage": 66.7,
    "label": "8/12点"
  }
}
```

### 詳細

`include_details=True` のため、`metrics` が返る。

```json
{
  "key": "platform_ratio",
  "label": "段差が解消されているプラットホームの割合",
  "value": "4/5 (80.0%)",
  "raw_value": null,
  "ratio": 0.8,
  "met": true,
  "type": "ratio",
  "required": 0.8,
  "numerator": 4,
  "denominator": 5,
  "percentage": 80.0
}
```

## 絞り込み仕様

スコア付き一覧 API の `filters` は、評価項目キーの JSON 配列である。

例:

```text
/api/body/stations?filters=["has_accessible_gate","platform_ratio"]
```

項目タイプ別の条件:

| Type | 条件 |
| --- | --- |
| `flag` | DB カラムが `1` |
| `ratio` | 分母が 0 より大きく、分子 / 分母 が `required` 以上 |
| `number` | DB カラムが 0 より大きい |

注意:

数値型フィルタはスコア計算の `required` 以上ではなく、`> 0` で絞り込む。

## 並び替え仕様

スコア付き一覧 API の `sort` は以下を受け付ける。

| Value | Behavior |
| --- | --- |
| `none` | `station_name` 昇順 |
| `score-asc` | `score.percentage` 昇順 |
| `score-desc` | `score.percentage` 降順 |

## 現状仕様として固定すること

- 重み付けスコアは実装されていない。
- スコアは達成項目数の単純カウントである。
- フラグは `1` のみ達成である。
- `3` や `NULL` は未達成である。
- 割合型は分母が 0 の場合に未達成である。
- 一覧レスポンスは `metrics` を含まない。
- 詳細レスポンスは `metrics` を含む。
- 身体障害 12 項目、聴覚障害 4 項目、視覚障害 10 項目を現状実装として扱う。
