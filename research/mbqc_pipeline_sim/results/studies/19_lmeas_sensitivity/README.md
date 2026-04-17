# Study 19: L_meas sensitivity analysis (ASAP vs ff_rate_matched)

候補4（`docs/worklog/20260417_handoff_next_experiments.md`）: 測定レイテンシ L_meas を 1–4 に変化させたときの F* と stall / throughput への影響を見る。

## 設定

- `dag_variant`: both (raw + shifted)
- `policies`: asap, ff_rate_matched
- `release_mode`: next_cycle
- `l_meas` ∈ {1, 2, 3, 4}, `l_ff = 2`（固定）
- `issue_width = meas_width = 8`
- `ff_width` ∈ {4, 8}
- algorithms: QAOA, VQE
- hq_pairs: 6:36, 8:64
- seeds: 0–4

## 成果物

- `summary/sweep.csv` — 320 行（shifted のみ）
- `summary/sweep_raw.csv` — 320 行（raw のみ）
- `summary/sweep_all.csv` — 640 行（結合）

## 主要結果

- F\*(ff_rate_matched) = 4: 全 40 ケースで L_meas に依存しない
- F\*(ASAP): QAOA H6 で L_meas=4 のとき一部 seed で 4 に低下（3/5 seeds）。それ以外は全て 8
- Throughput: shifted 上で ASAP と ff_rate_matched が完全一致（全条件）

## 再現

```bash
cd research/mbqc_pipeline_sim
ART=../mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts

# shifted
PYTHONPATH=src ../../.venv-ffeval310/bin/python3 -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir "$ART" --output results/studies/19_lmeas_sensitivity/summary/sweep.csv \
  --issue-widths 8 --l-meas-values 1,2,3,4 --l-ff-values 2 \
  --policies asap,ff_rate_matched --release-modes next_cycle \
  --meas-widths 8 --ff-widths 4,8 --dag-variant shifted \
  --algorithms QAOA,VQE --hq-pairs 6:36,8:64 --dag-seeds 0,1,2,3,4

# raw
PYTHONPATH=src ../../.venv-ffeval310/bin/python3 -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir "$ART" --output results/studies/19_lmeas_sensitivity/summary/sweep_raw.csv \
  --issue-widths 8 --l-meas-values 1,2,3,4 --l-ff-values 2 \
  --policies asap,ff_rate_matched --release-modes next_cycle \
  --meas-widths 8 --ff-widths 4,8 --dag-variant raw \
  --algorithms QAOA,VQE --hq-pairs 6:36,8:64 --dag-seeds 0,1,2,3,4
```
