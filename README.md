# MBQC Classical-Control Study

光 MBQC における古典制御アーキテクチャ評価の研究成果を、`XQsim` 本体から切り離して管理するための独立リポジトリです。

このリポジトリでは、既存の `XQsim` remote は触らず、研究コード・再現用スナップショット・レポートだけを新しい git history で管理します。

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

## Git Policy

- `XQsim` 側の `origin` は変更しない
- 新しい GitHub remote はこのリポジトリにだけ追加する
- `OneAdapt_AE 2/` は再現用スナップショットとして扱い、更新時は理由と影響範囲をコミットに残す
