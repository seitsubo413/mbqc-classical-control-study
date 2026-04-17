# Study 18: L_ff sensitivity analysis (ASAP vs ff_rate_matched)

候補2（`docs/worklog/20260417_handoff_next_experiments.md`）: FF 処理レイテンシ L_ff を 1–5 に変化させたときの F* と throughput への影響を見る。

## 設定

- `dag_variant`: both (raw + shifted)
- `policies`: asap, ff_rate_matched
- `release_mode`: next_cycle
- `l_meas=1`, `l_ff` ∈ {1, 2, 3, 4, 5}
- `issue_width = meas_width = 8`
- `ff_width` ∈ {4, 6, 8}
- algorithms: QAOA, VQE（D_ff が極端なケース）
- hq_pairs: 8:64（大規模）
- seeds: 0–4

## 成果物

- `summary/sweep.csv` — 600 行 + ヘッダ（20 DAGs × 30 configs）。

## 再現

```bash
cd research/mbqc_pipeline_sim
PYTHONPATH=src ../../.venv-ffeval310/bin/python3 -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir ../mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --output results/studies/18_lff_sensitivity/summary/sweep.csv \
  --issue-widths 8 --l-meas-values 1 --l-ff-values 1,2,3,4,5 \
  --policies asap,ff_rate_matched --release-modes next_cycle \
  --meas-widths 8 --ff-widths 4,6,8 \
  --dag-variant both --algorithms QAOA,VQE \
  --hq-pairs 8:64 --dag-seeds 0,1,2,3,4
```
