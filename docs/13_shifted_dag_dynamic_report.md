# Shifted DAG Dynamic Study Report

## Research Question

`signal_shift` による static dependency-depth 改善が、dynamic throughput / stall / utilization まで改善するかを評価する。

## Experimental Setup

### Output Namespace

- FF evaluator artifacts:
  - `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts/`
- Pipeline simulator outputs:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/`

### Workloads

- algorithms: `QAOA`, `QFT`, `VQE`
- common coupled subset: `(H, Q) = (4,16), (6,36), (8,64)`
  - QFT H8/Q64 は `shifted_dependency_graph` が存在しないため paired comparison から除外
- seeds: `0..4`

### Controller Conditions

- `release_mode = next_cycle`
- `policy = asap, greedy_critical`
- `issue_width = 4, 8`
- `meas_width = W` (4, 8)
- `ff_width = W` (4, 8)
- `l_meas = 1, 2`
- `l_ff = 1, 2`

### Sweep Summary

- 総 runs: **5440**
- 実時間: **~894 s**
- 集約後の paired comparison 条件数: **512**
  - QAOA: 192, QFT: 128, VQE: 192

## Metrics

- `throughput_median` — 条件内 seed 中央値のスループット (nodes/cycle)
- `stall_rate_median` — 条件内 seed 中央値のストール率
- `utilization_median` — 条件内 seed 中央値の utilization
- `depth_reduction_pct` — shifted DAG の ff_chain_depth 削減率 (%)
- `throughput_gain_pct` — shifted DAG による throughput 改善率 (%)
- `stall_reduction_pct` — shifted DAG による stall rate 削減率 (%)

## Main Findings

### 1. Raw vs Shifted Throughput

Shifted DAG は全アルゴリズムで throughput を改善するか同等を維持し、悪化ケースは観測されなかった。

| Algorithm | Depth Reduction (中央値) | Throughput Gain (中央値) | Throughput Gain (最大) |
|-----------|-------------------------|-------------------------|----------------------|
| QAOA      | 97.37%                  | 9.92%                   | 279.28%              |
| QFT       | 90.65%                  | 10.60%                  | 146.54%              |
| VQE       | 97.14%                  | 1.46%                   | 112.82%              |

Hardware size 別にみると、小規模回路ほど dynamic gain が大きい:

| Algorithm | H4/Q16 (中央値) | H6/Q36 (中央値) | H8/Q64 (中央値) |
|-----------|-----------------|-----------------|-----------------|
| QAOA      | 72.09%          | 5.77%           | 1.49%           |
| QFT       | 22.61%          | 4.25%           | (除外)          |
| VQE       | 16.93%          | 2.45%           | 0.78%           |

### 2. Raw vs Shifted Stall Rate

Stall rate は大半の条件で改善した (正方向の削減)。stall が正しく削減されたケースの中央値:

| Algorithm | Stall 削減率 (中央値, 正のみ) | Stall 悪化ケース数 |
|-----------|-----------------------------|--------------------|
| QAOA      | 89.23%                      | 32 / 192           |
| QFT       | 93.21%                      | 16 / 128           |
| VQE       | 62.63%                      | 25 / 192           |

Stall 悪化ケースは `issue_width=8, meas_width=8` かつ `ff_width=4` の条件に集中しており、wide issue + narrow ff_width の組み合わせで shifted DAG のスケジューリングが meas/ff 競合を起こす edge case と考えられる。

### 3. Static Depth Reduction vs Dynamic Gain

Static depth reduction と dynamic throughput gain の間には **非線形な対応** が見られた。

- depth reduction が 90% を超えてもthroughput gain が 2% 未満のケースが多数存在する (特に H8/Q64 と greedy_critical の組み合わせ)
- これは raw DAG の時点でパイプラインが飽和 (throughput ≈ 4.0, stall_rate ≈ 0) に近いため、static improvement の余地があっても dynamic に反映されない
- 逆に raw 時点で stall_rate > 0.1 の条件では gain が顕著に発現する

**Latency 別の影響** は特に大きい:

| Latency     | QAOA (中央値) | QFT (中央値) | VQE (中央値) |
|-------------|--------------|-------------|-------------|
| l=1,1 (低)  | 3.95%        | 8.71%       | 0.78%       |
| l=2,2 (高)  | 19.48%       | 28.78%      | 7.01%       |

高レイテンシ環境 (l_meas=2, l_ff=2) では raw DAG のストールが深刻なため、shifted DAG の恩恵が 3–9× に増幅される。

## Figures

- `fig9_shifted_throughput_comparison` — raw vs shifted の throughput 比較 (アルゴリズム×HQ 別)
- `fig10_shifted_stall_comparison` — raw vs shifted の stall rate 比較
- `fig11_depth_reduction_vs_throughput_gain` — static depth reduction vs dynamic throughput gain の散布図

図の格納先: `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures/`

## Interpretation

### Algorithm-wise trends

**QAOA**: 全 HQ サイズで throughput gain を示す。H4/Q16 では中央値 72% と最も大きい。raw DAG の ff_chain_depth が 34 (H4) → 76 (H6) → 142 (H8) と増加し、shifted 後は全て 2 に圧縮される。ただし H8/Q64 では raw 時点でパイプラインが飽和に近く、dynamic gain は 1.5% 程度に留まる。

**QFT**: depth_reduction は 90.4–90.9% で QAOA/VQE (93–98%) より低いが、throughput gain の中央値は 10.6% で 3 アルゴリズム中最大。QFT は raw DAG 時点の stall_rate が中程度 (過飽和でも過小でもない) で、shifted DAG の改善がそのまま throughput に反映される sweet spot にある。H8/Q64 は shifted_dependency_graph が生成できないため今回は除外。

**VQE**: depth_reduction は 97.1% (中央値) と高いが、throughput gain 中央値は 1.46% で最も鈍い。VQE の raw DAG は ff_chain_depth が 15 (H4) → 35 (H6) → 63 (H8) と QAOA の半分以下であり、raw 時点の stall が少なく改善余地が限定的。さらに greedy_critical policy では raw でも shifted でも同一スケジュールが生成される条件が多く (zero-gain = 73/192 条件)、特に H6/Q36 と H8/Q64 で顕著。

### Pipeline width の効果

Wide pipeline (issue_width=8, meas_width=8, ff_width=8) では throughput gain が大幅に拡大する:

| Algorithm | Wide (中央値) | Narrow (中央値) |
|-----------|--------------|----------------|
| QAOA      | 53.10%       | 5.47%          |
| QFT       | 39.34%       | 7.78%          |
| VQE       | 9.83%        | 1.07%          |

wide pipeline は throughput の上限が高いため、dependency depth の短縮が直接的に issue rate 向上に寄与する。narrow pipeline では issue_width がボトルネックとなり、DAG 改善の恩恵が頭打ちになる。

### Cases with strong static but weak dynamic improvement

以下の条件で「static depth reduction > 97% だが throughput gain ≈ 0%」が観測された:

1. **VQE H6/Q36 + greedy_critical**: raw DAG の ff_chain_depth=35, shifted=1 (depth_reduction=97.1%) だが、raw 時点で throughput ≈ 3.95–3.98 (飽和近傍) のため dynamic gain が 0%
2. **VQE H8/Q64 + 全 policy**: raw ff_chain_depth=63, shifted=1 だが raw 時点で throughput ≈ 3.98–3.99 のため gain ≈ 0–2%
3. **QAOA H8/Q64 + greedy_critical + issue_width=4**: 同様にパイプライン飽和

共通パターン: **raw throughput > 3.9 (saturation region)** かつ **issue_width ≤ Q/H** の条件ではどれだけ depth を削減しても dynamic gain は発現しない。

## Takeaways

1. **Shifted DAG は全条件で throughput を改善または維持する** — 悪化ケースは 0 件。安全に適用できる最適化。
2. **Dynamic gain は static depth reduction と非線形に対応する** — パイプライン飽和度が最大の制約因子。raw 時点で stall_rate > 0.1 の条件でのみ顕著な改善が見込める。
3. **高レイテンシ環境で恩恵が増幅される** — l_meas=2, l_ff=2 では gain が 3–9× に拡大。実デバイスでの FF レイテンシが大きい場合に signal_shift の価値が高い。
4. **Wide pipeline ほど gain が大きい** — issue_width=8 + meas/ff_width=8 では QAOA/QFT で中央値 39–53% の改善。
5. **VQE は static 改善に対して dynamic gain が最も鈍い** — 元々の ff_chain_depth が浅く、raw 時点でパイプラインが飽和に近いため。
6. **QFT H8/Q64 は今後の課題** — shifted_dependency_graph を生成できなかった。signal_shift アルゴリズムの QFT 大規模インスタンスへの対応が必要。
