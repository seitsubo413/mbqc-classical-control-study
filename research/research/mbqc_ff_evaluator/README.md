# MBQC FF Evaluator

研究用の独立サブプロジェクトです。`XQsim` 本体や `OneAdapt_AE 2` を汚さずに、
MBQC フィードフォワード制約評価の実験コードをここに集約します。

## 方針

- この repo の中で進める
- 既存実装 (`src/`, `OneAdapt_AE 2/`, `ls-pattern-compile/`) には直接混ぜない
- Python 環境はこの研究専用に分離する
- `OneAdapt_AE 2` は依存資産として参照し、基本はラッパー側で吸収する

## 推奨環境

XQsim root の `requirements.txt` は Python 3.9 系、`OneAdapt_AE 2/requirement.txt` は
別の `qiskit` 系列を要求しているため、環境は分ける。

この研究では root に専用 venv を置く:

```bash
cd /Users/seitsubo/Project/XQsim
python3.10 -m venv .venv-ffeval
source .venv-ffeval/bin/activate
pip install -U pip
pip install -r "OneAdapt_AE 2/requirement.txt"
pip install -e ./research/mbqc_ff_evaluator[dev]
pip install pandas
```

`graphix` を使う段階で必要なら追加:

```bash
pip install graphix
```

再現性固定:

```bash
pip freeze > research/mbqc_ff_evaluator/requirements-lock.txt
```

## 実行時の前提

```bash
export MPLBACKEND=Agg
export PYTHONPATH="$PWD/OneAdapt_AE 2:$PWD/research/mbqc_ff_evaluator/src:$PYTHONPATH"
mkdir -p "OneAdapt_AE 2/layers"
```

## ディレクトリ構成

```text
research/mbqc_ff_evaluator/
  src/mbqc_ff_evaluator/
    domain/
    ports/
    services/
    adapters/
    cli/
    visualization/
  tests/
  results/
    raw/
    summary/
```

## 役割

- `domain/`: immutable model, Enum, domain error
- `ports/`: `Protocol` による interface
- `services/`: use case / pure logic
- `adapters/`: OneAdapt / graphix / JSON / CSV
- `cli/`: smoke, sweep, aggregate, plot, graphix backfill, outlier analysis, controller evaluation
- `visualization/`: 図生成
- `tests/`: 数式・グラフ・smoke test
- `results/`: 生データと集約結果

## 設計方針

- `dataclass(frozen=True)` を基本とする
- string literal より `Enum` を優先する
- 外部依存は `Protocol` 越しに使う
- core logic は pure function を優先する
- CLI は orchestration のみに限定する

## 主な CLI

```bash
# 1ケースだけ実行
python -m mbqc_ff_evaluator.cli.smoke --algorithm QAOA --hardware-size 4 --logical-qubits 16 --seed 0

# raw JSON を集約して CSV にする
python -m mbqc_ff_evaluator.cli.aggregate

# publication figure を生成
python -m mbqc_ff_evaluator.cli.plot --selection-mode coupled_only --tau-ph-us 1.0

# 小規模ケースに graphix reference depth を書き戻す
python -m mbqc_ff_evaluator.cli.backfill_graphix_reference --algorithms QAOA QFT VQE --max-logical-qubits 16

# measurement delay の outlier 解析
python -m mbqc_ff_evaluator.cli.analyze_measurement_delay

# simple controller model で feasibility を評価
python -m mbqc_ff_evaluator.cli.evaluate_controller_models --selection-mode coupled_only --tau-ph-us 1.0
```
