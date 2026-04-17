# Study 17: Throughput cost (ASAP vs ff_rate_matched, shifted DAG)

候補1（`docs/worklog/20260417_handoff_next_experiments.md`）: 低 `ff_width` 域で `ff_rate_matched` のスロットリングが総サイクル / throughput に与えるコストを見る。

## 設定

- `dag_variant`: shifted のみ
- `policies`: asap, ff_rate_matched
- `release_mode`: next_cycle
- `l_meas=1`, `l_ff=2`
- `issue_width = meas_width` ∈ {4, 8,16}（幅ごとに sweep を分割して結合）
- `ff_width` ∈ {2, 3, 4}
- algorithms: QAOA, QFT, VQE
- hq_pairs: 4:16, 6:36, 8:64
- seeds: 0–4

## 成果物

- `summary/sweep.csv` — 720 行 + ヘッダ（40 DAGs × 18 configs）。`partial_W*.csv` は再現用の分割出力。

## 注意

- QFT H8/Q64 は shifted graph 欠損のため 40 DAGs（45 件中 5 件除外）。既知どおり。

## 再現（リポジトリルートから）

`research/mbqc_pipeline_sim` で、`partial` を出してから `sweep.csv` を結合する。例:

```bash
cd research/mbqc_pipeline_sim
PY=../../.venv-ffeval310/bin/python3
ART=../mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts
OUTDIR=results/studies/17_throughput_cost/summary
for W in 4 8 16; do
  PYTHONPATH=src "$PY" -m mbqc_pipeline_sim.cli.sweep \
    --artifacts-dir "$ART" --output "$OUTDIR/partial_W${W}.csv" \
    --issue-widths "$W" --l-meas-values 1 --l-ff-values 2 \
    --policies asap,ff_rate_matched --release-modes next_cycle \
    --meas-widths "$W" --ff-widths 2,3,4 \
    --dag-variant shifted --algorithms QAOA,QFT,VQE \
    --hq-pairs 4:16,6:36,8:64 --dag-seeds 0,1,2,3,4
done
head -1 "$OUTDIR/partial_W4.csv" > "$OUTDIR/sweep.csv"
for W in 4 8 16; do tail -n +2 "$OUTDIR/partial_W${W}.csv" >> "$OUTDIR/sweep.csv"; done
```
