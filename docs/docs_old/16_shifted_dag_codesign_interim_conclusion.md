# Shifted-DAG Co-Design Interim Conclusion

## Scope

このメモは `2026-04-16` 時点の focused study
`research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/`
の interim conclusion をまとめる。

主対象は次の 2 regime。

- problematic regime: `W8_M8_F4`
- fully provisioned reference: `W8_M8_F8`

比較 policy:

- `asap`
- `greedy_critical`
- `shifted_critical`
- `stall_aware_shifted`

## Dataset Status

paired raw/shifted set は 45 raw artifact 中 40 seed で成立。

出典:

- `summary/analysis/exclusion_summary.csv`

欠損は全部 `QFT_H8/Q64`。

- paired 不能: `QFT_H8_Q64_seed0..4`
- 他の `(algorithm, H, Q)` は 5/5 seed 完備

したがって mainline の co-design conclusion は

- `QAOA`: H4/H6/H8
- `QFT`: H4/H6
- `VQE`: H4/H6/H8

を用いて述べるのが安全。

## 1. W8_M8_F4 should be the main battlefield

`W8_M8_F4` では throughput gain は残るが stall regression が強く、
co-design の話が最も立つ。

出典:

- `summary/analysis/policy_width_summary.csv`
- `summary/analysis/stall_regression_summary.csv`

代表値:

- QAOA + `asap`
  - throughput gain median: `9.844558%`
  - stall reduction median: `-222.447444%`
- QFT + `asap`
  - throughput gain median: `9.229333%`
  - stall reduction median: `-727.362378%`
- VQE + `asap`
  - throughput gain median: `4.892963%`
  - stall reduction median: `-1554.983041%`

解釈:

- shifted DAG は static depth を減らして throughput を押し上げる
- しかし `F=4` の FF bottleneck 下では ready burst が強くなり、
  stall metric は悪化しやすい
- したがって `W8_M8_F4` は
  compiler optimization と controller policy の interaction を見る主戦場に向く

## 2. Policy roles are regime-dependent

### Fully provisioned: W8_M8_F8

`W8_M8_F8` では shifted により大きい gain が出るが、
policy 差はかなり薄い。

出典:

- `summary/analysis/policy_width_summary.csv`
- `summary/analysis/policy_vs_asap_summary.csv`

観測:

- QAOA
  - `asap`: throughput gain `56.585383%`
  - non-`asap`: `50.2439%`
- QFT
  - `asap`: `39.187145%`
  - non-`asap`: `37.243113%`
- VQE
  - `asap`: `18.181809%`
  - `greedy_critical` / shifted-aware: `0%`

解釈:

- fully provisioned 側では scheduler redesign の寄与は小さい
- 特に VQE では `asap` が最も自然な baseline で、
  refined policy を入れても universal improvement にはならない

### FF bottleneck: W8_M8_F4

`W8_M8_F4` では全 policy が stall regression を完全には消せないが、
`stall_aware_shifted` は少なくとも regression の悪化幅を最も抑える側に寄る。

出典:

- `summary/analysis/policy_width_summary.csv`
- `summary/analysis/stall_regression_summary.csv`

代表値:

- QAOA
  - `asap`: stall reduction `-222.447444%`
  - `stall_aware_shifted`: `-651.839449%`
  - この系では `asap` 優位
- QFT
  - `asap`: `-727.362378%`
  - `stall_aware_shifted`: `-707.364775%`
  - 他の refined policy より悪化幅が最小
- VQE
  - `asap`: `-1554.983041%`
  - `stall_aware_shifted`: `-1458.842293%`
  - `greedy_critical` / `shifted_critical` より明確に良い

解釈:

- `stall_aware_shifted` は universal winner ではない
- ただし FF bottleneck regime では
  refined policy の中では最も筋が良い候補
- とくに `QFT` と `VQE` の `W8_M8_F4` では
  stall worsening を抑える方向に効いている

## 3. Universal winner is the wrong target

この study から一番自然に出るメッセージは
「全 regime で勝つ 1 policy」ではなく
「shifted DAG の効果は controller regime に依存する」。

この主張を支える事実:

- `W8_M8_F8` では compiler-side gain が主で policy 差は薄い
- `W8_M8_F4` では shifted burst により stall regression が立つ
- refined policy は一部 regime で効くが、全部に勝つわけではない
- VQE fully provisioned 側では `asap` が素直に強い

したがって main message は次が良い。

- shifted DAG の dynamic effect は controller regime dependent
- FF bottleneck では shifted-aware / stall-aware controller が必要
- compiler と controller は individually optimal ではなく co-design で見るべき

## 4. Raw vs shifted baseline story is already sufficient

raw vs shifted の baseline 自体は既に十分強い。

出典:

- `summary/analysis/algorithm_hq_summary.csv`

代表例:

- QAOA H4/Q16: throughput gain `109.523815%`, stall reduction `75.658395%`
- QAOA H8/Q64: throughput gain `4.33819%`, stall reduction `-154.701178%`
- VQE H8/Q64: throughput gain `0.876325%`, stall reduction `-1271.28323%`

解釈:

- shifted が効く regime と効きにくい regime がはっきり分かれる
- `stall regression` は主に大きめ・飽和寄り・FF narrow の regime で出る
- これだけで
  raw baseline,
  problematic regime,
  shifted-aware policy の必要性,
  limitation
  まで書ける

## 5. Limitation

現時点の main limitation は `QFT_H8/Q64` shifted artifact が再現できていないこと。

出典:

- `summary/analysis/exclusion_summary.csv`

扱い:

- `QFT_H8/Q64` は main aggregate から除外された paired-missing case として記述
- これは weakness というより
  large-instance failure / availability limit として別節に回せる

## Recommended Paper Framing

現時点では次の framing が最も自然。

1. baseline raw vs shifted を示す
2. `W8_M8_F4` を problematic co-design regime として固定する
3. `asap` と `stall_aware_shifted` の役割差を示す
4. universal winner 探索ではなく regime-aware design を主張する
5. `QFT_H8/Q64` を未解決 large-instance limitation として残す

## Supporting Output Paths

主要に見る CSV:

- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/comparison.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/policy_width_summary.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/stall_regression_summary.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/policy_vs_asap_summary.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/policy_variant_summary.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/algorithm_hq_summary.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign_w8_focus/summary/analysis/exclusion_summary.csv`
