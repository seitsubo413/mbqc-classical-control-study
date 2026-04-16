# Shifted DAG Dynamic Study Handoff

## Goal

`signal_shift` による static な dependency-depth 改善が、dynamic な throughput / stall / utilization にもつながるかを検証する。

主な問い:

- raw DAG と shifted DAG で dynamic performance はどれだけ違うか
- 差は QAOA / QFT / VQE でどう異なるか
- static depth 改善率と dynamic throughput 改善率は対応するか
- static は改善しても dynamic gain が限定的なケースがあるか

## Controlled Experiment Slice

- workload:
  - algorithm = `QAOA`, `QFT`, `VQE`
  - `(H, Q) = (4,16), (6,36), (8,64)`
  - `seed = 0..4`
- controller conditions:
  - `release_mode = next_cycle`
  - `policy = asap, greedy_critical`
  - `issue_width = 4, 8`
  - `meas_width = W`
  - `ff_width = W`
  - `l_meas = 1, 2`
  - `l_ff = 1, 2`

## Implemented Support

- FF evaluator artifact schema now supports `shifted_dependency_graph`
- existing raw JSON remains readable; shifted payload is optional
- `mbqc_ff_evaluator.cli.prepare_shifted_dag_study` creates namespaced study directories and copies the baseline subset
- `mbqc_ff_evaluator.cli.backfill_shifted_graph` can annotate existing artifacts
- pipeline sim supports `--dag-variant raw|shifted|both`
- aggregate supports `--comparison-output` for paired raw-vs-shifted summaries
- plotting supports:
  - `fig9_shifted_throughput_comparison`
  - `fig10_shifted_stall_comparison`
  - `fig11_depth_reduction_vs_throughput_gain`

## Recommended Execution Order

1. Backfill shifted DAG payloads into the existing artifact set
2. Run the controlled `next_cycle` width-matched sweep with `--dag-variant both`
3. Aggregate into both `aggregated.csv` and `shifted_comparison.csv`
4. Generate comparison figures
5. Write results into `docs/13_shifted_dag_dynamic_report.md`

## Commands

### 1. Prepare namespaced study directories

```bash
source .venv-ffeval310/bin/activate
export PYTHONPATH="$PWD/research/mbqc_ff_evaluator/src:$PWD/research/mbqc_pipeline_sim/src:$PYTHONPATH"

python -m mbqc_ff_evaluator.cli.prepare_shifted_dag_study
```

Prepared directories:

- FF evaluator:
  - `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/`
- Pipeline simulator:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/`

### 2. Backfill shifted DAG payloads

```bash
python -m mbqc_ff_evaluator.cli.backfill_shifted_graph \
  --raw-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --algorithms QAOA QFT VQE \
  --hardware-sizes 4 6 8 \
  --logical-qubits 16 36 64 \
  --seeds 0 1 2 3 4
```

### 3. Run the dynamic comparison sweep

```bash
python -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --dag-variant both \
  --release-modes next_cycle \
  --policies asap,greedy_critical \
  --issue-widths 4,8 \
  --meas-widths 4,8 \
  --ff-widths 4,8 \
  --l-meas-values 1,2 \
  --l-ff-values 1,2 \
  --algorithms QAOA,QFT,VQE \
  --dag-seeds 0,1,2,3,4 \
  --hq-pairs 4:16,6:36,8:64
```

### 4. Aggregate and build paired comparison CSV

```bash
python -m mbqc_pipeline_sim.cli.aggregate \
  --input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/aggregated.csv \
  --comparison-output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv
```

### 5. Generate figures

```bash
python -m mbqc_pipeline_sim.cli.plot \
  --input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --comparison-input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv \
  --outdir research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures
```

## Expected Primary Outputs

- `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts/*.json`
  - with `shifted_dependency_graph`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/aggregated.csv`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures/fig9_shifted_throughput_comparison.png`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures/fig10_shifted_stall_comparison.png`
- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures/fig11_depth_reduction_vs_throughput_gain.png`

## Notes

- `signal_shift` の有無以外の条件を変えないこと
- QFT で dynamic gain が限定的でも、その結果は重要
- full re-collection は高コストなので、まずは backfill を優先する
- 実シミュレーション実行前には所要時間の見積もりを共有する
