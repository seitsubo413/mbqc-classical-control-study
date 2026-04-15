# MBQC Pipeline Simulator

FF evaluator が生成した DAG artifact を入力に、MBQC 古典制御パイプラインの設計空間を探索する研究用サブプロジェクトです。

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
