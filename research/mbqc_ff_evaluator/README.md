# MBQC FF Evaluator

MBQC フィードフォワード依存グラフの評価・バジェット計算を行う研究用サブプロジェクト。

## 依存パッケージ

- **`mbqc_graph_compiler`**: JCZ 回路 → グラフ状態 → FF 依存グラフのコンパイル（同リポジトリ内の `research/mbqc_graph_compiler/`）
- `networkx`, `numpy`, `matplotlib`

## セットアップ

```bash
cd /Users/seitsubo/Project/mbqc-classical-control-study
python3.10 -m venv .venv-ffeval310
source .venv-ffeval310/bin/activate
pip install -e research/mbqc_graph_compiler
pip install -e research/mbqc_ff_evaluator[dev]
```

`graphix` を使う場合は追加:

```bash
pip install graphix
```

## ディレクトリ構成

```text
research/mbqc_ff_evaluator/
  src/mbqc_ff_evaluator/
    domain/          # immutable model, Enum, domain error
    ports/           # Protocol による interface
    services/        # use case / pure logic
    adapters/        # mbqc_graph_compiler / graphix / JSON / CSV
    cli/             # smoke, sweep, aggregate, plot, outlier analysis ...
    visualization/   # 図生成
  tests/
  results/
    raw/             # 回路ごとの JSON アーティファクト
    summary/         # 集約 CSV
```

## 主な CLI

```bash
# 1ケースだけ実行（smoke test）
python -m mbqc_ff_evaluator.cli.smoke --algorithm QAOA --hardware-size 4 --logical-qubits 16 --seed 0

# raw JSON を集約して CSV にする
python -m mbqc_ff_evaluator.cli.aggregate

# publication figure を生成
python -m mbqc_ff_evaluator.cli.plot --selection-mode coupled_only --tau-ph-us 1.0

# shifted DAG payload を既存アーティファクトに追記
python -m mbqc_ff_evaluator.cli.backfill_shifted_graph \
  --raw-dir research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --algorithms QAOA QFT VQE \
  --hardware-sizes 4 6 8 \
  --logical-qubits 16 36 64 \
  --seeds 0 1 2 3 4

# measurement delay の outlier 解析
python -m mbqc_ff_evaluator.cli.analyze_measurement_delay

# simple controller model で feasibility を評価
python -m mbqc_ff_evaluator.cli.evaluate_controller_models --selection-mode coupled_only --tau-ph-us 1.0
```

## 設計方針

- `dataclass(frozen=True)` を基本とする
- string literal より `Enum` を優先する
- 外部依存は `Protocol` 越しに使う
- core logic は pure function を優先する
- CLI は orchestration のみに限定する
