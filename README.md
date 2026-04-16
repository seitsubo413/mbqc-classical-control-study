# MBQC Classical-Control Study


## Directory Layout

- `research/`: 研究用サブプロジェクトと vendored dependency 方針
- `research/mbqc_ff_evaluator/`: FF 依存深さと時間 budget を評価するツール
- `research/mbqc_pipeline_sim/`: FF evaluator artifact を入力に使うサイクル精度パイプラインシミュレータ
- `OneAdapt_AE 2/`: 再現性確保のために同梱した OneAdapt スナップショット
- `docs/`: 研究報告書と進捗レポート

## Component Relationship

1. `OneAdapt_AE 2/` が MBQC 依存グラフ生成の基盤コードを提供する
2. `research/mbqc_ff_evaluator/` がその出力を解析し、`results/raw/*.json` などの artifact を生成する
3. `research/mbqc_pipeline_sim/` が FF evaluator artifact を読み込み、設計空間探索の sweep・集約・図生成を行う

## Quick Start

```bash
cd /Users/seitsubo/Project/mbqc-classical-control-study
python3.10 -m venv .venv-ffeval
source .venv-ffeval/bin/activate
pip install -U pip
pip install -r "OneAdapt_AE 2/requirement.txt"
pip install -e ./research/mbqc_ff_evaluator[dev]
pip install -e ./research/mbqc_pipeline_sim[dev]
pip install pandas
```

`graphix` を使う段階で必要なら追加します。

```bash
pip install graphix
```

実行時の典型設定:

```bash
export MPLBACKEND=Agg
export PYTHONPATH="$PWD/OneAdapt_AE 2:$PWD/research/mbqc_ff_evaluator/src:$PWD/research/mbqc_pipeline_sim/src:$PYTHONPATH"
mkdir -p "OneAdapt_AE 2/layers"
```

## Shifted DAG Workflow

shifted DAG dynamic study は baseline の `results/raw` や `results/summary` を直接更新せず、study namespace を切って進めます。

最初に study layout を作成し、common coupled subset だけをそこへコピーします。

```bash
source .venv-ffeval310/bin/activate
python -m mbqc_ff_evaluator.cli.prepare_shifted_dag_study
```

既定の study path:

- FF evaluator:
  - `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/`
- Pipeline simulator:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/`

既存 raw artifact に shifted DAG payload を追加したい場合は、`map_route` を含むフル再収集ではなく backfill を使えます。

```bash
source .venv-ffeval310/bin/activate
python -m mbqc_ff_evaluator.cli.backfill_shifted_graph \
  --raw-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --algorithms QAOA QFT VQE \
  --hardware-sizes 4 6 8 \
  --logical-qubits 16 36 64 \
  --seeds 0 1 2 3 4
```

pipeline sim では `--dag-variant raw|shifted|both` を指定できます。

```bash
python -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --dag-variant both
```

## Git Policy

- `XQsim` 側の `origin` は変更しない
- 新しい GitHub remote はこのリポジトリにだけ追加する
- `OneAdapt_AE 2/` は再現用スナップショットとして扱い、更新時は理由と影響範囲をコミットに残す
