# MBQC Pipeline Simulator

FF evaluator が生成した DAG artifact を入力に、MBQC 古典制御パイプラインの設計空間を探索する研究用サブプロジェクトです。

コードやスキーマを変える前に: [`docs/project_change_policy.md`](../../docs/project_change_policy.md)（既存シミュレーション結果との互換を優先する方針）

## Inputs and Outputs

- 入力: `../mbqc_ff_evaluator/results/raw/*.json`
- 出力: `results/summary/*.csv`, `results/figures/*`

`research/mbqc_ff_evaluator/` が依存グラフを定量化し、このシミュレータがその DAG を使って
issue width・FF latency・scheduling policy などの影響を評価します。

## Setup

```bash
cd /Users/seitsubo/Project/mbqc-classical-control-study
source .venv-ffeval/bin/activate
pip install -e ./research/mbqc_pipeline_sim[dev]
```

editable install を使わない場合は `PYTHONPATH` に `research/mbqc_pipeline_sim/src` を追加します。

## Common Commands

```bash
# 単一 artifact を実行
python -m mbqc_pipeline_sim.cli.run \
  research/mbqc_ff_evaluator/results/raw/QAOA_H4_Q16_seed0.json

# 全 artifact に対して sweep
python -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir research/mbqc_ff_evaluator/results/raw \
  --output research/mbqc_pipeline_sim/results/summary/sweep.csv

# seed 集約と図生成
python -m mbqc_pipeline_sim.cli.aggregate
python -m mbqc_pipeline_sim.cli.plot
```

raw / shifted の両方を同時に比較したい場合:

```bash
python -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --dag-variant both

python -m mbqc_pipeline_sim.cli.aggregate \
  --input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/aggregated.csv \
  --comparison-output research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv

python -m mbqc_pipeline_sim.cli.plot \
  --input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/sweep.csv \
  --comparison-input research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv \
  --outdir research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/figures
```
