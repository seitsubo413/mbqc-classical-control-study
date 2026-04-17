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
- `summary/paired_comparison.csv` — 上記を DAG×設定ごとに ASAP と ff_rate_matched を突き合わせた 360 行（`compute_paired_comparison.py` で生成）。
- `summary/study17_summary.txt` — ペア比較の集計サマリ（同スクリプトが上書き生成）。
- `compute_paired_comparison.py` — `paired_comparison.csv` と `study17_summary.txt` の再計算用。

## 結果（一次集計・本 sweep 時点）

- **360 ペア**について `total_cycles_ff / total_cycles_asap` の中央値は **1.0**（`throughput` も中央値で差なし）。
- **346 / 360** はサイクル数が **完全一致**。差が出たのは **14 ペアのみ**で、比率は **±0.17% 未満**の微差に留まる（主に QFT）。
- **F/W × issue_width** の各バケット（各 40 ペア）でも、サイクル比の中央値はすべて **1.0**。

→ 本パラメータ域（shifted・next_cycle・l_ff=2・ff_width∈{2,3,4}）では、**スロットリングによる「総実行サイクルの明確な増加」は観測されず**、仮説の「F/W が小さいほどコストが出る」も、この集計粒度では裏付けられなかった。

（待ち行列や issue 利用率などの **メトリクス拡張**で差が見えるかは別途。）

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

## ペア集計の再現

リポジトリルートから:

```bash
python3 research/mbqc_pipeline_sim/results/studies/17_throughput_cost/compute_paired_comparison.py
```
