# MBQC Classical Control Study

MBQC（測定ベース量子計算）における古典制御のスループットとコスト設計を研究するリポジトリ。

## 研究概要

Signal shift 最適化が引き起こす **stall regression** 現象を明らかにし、
credit-based な **ff_rate_matched** ポリシーによって解決できることを示した。

- signal shift により FF 依存の深さ D_ff が大幅に圧縮される
- その結果、多数のノードが短時間に ready になり FF 処理器に burst が集中する
- ff_width が小さい場合、shifted DAG + ASAP では raw DAG より stall が悪化する（stall regression）
- ff_rate_matched は FF in-flight 数に基づいて issue をスロットリングし、burst を防ぐ
- **F\*(ff_rate_matched) = W/2** が理論保証されており、throughput コストはゼロ

## リポジトリ構成

```
research/
  mbqc_graph_compiler/   # MBQC グラフ状態コンパイラ（JCZ モデル）
  mbqc_ff_evaluator/     # FF 依存グラフの評価・バジェット計算
  mbqc_pipeline_sim/     # パイプラインシミュレーション・スケジューラ比較
docs/
  paper/                 # 論文ドラフト（v9）
  20_hypothesis_driven_study_report.md
  21_throughput_cost_and_lff_sensitivity_report.md
OneAdapt_AE 2/           # 参照資産（グラフコンパイラの元実装）
```

## 環境セットアップ

### mbqc_ff_evaluator（Python 3.10 専用）

```bash
python3.10 -m venv .venv-ffeval310
source .venv-ffeval310/bin/activate
pip install -e research/mbqc_graph_compiler
pip install -e research/mbqc_ff_evaluator[dev]
```

### mbqc_pipeline_sim

```bash
cd research/mbqc_pipeline_sim
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 主要な実験結果

| Study | 内容 | 結論 |
|-------|------|------|
| Study 15–16 | ff_width sweep + ff_rate_matched 初実装 | F\*(ff_rate_matched) = 4 = W/2（全 40 ケース） |
| Study 17 | throughput コスト精密測定 | F/W = 0.125 まで cycles_ratio = 1.0 |
| Study 18 | L_ff 感度分析（L_ff = 1–5） | F\* = W/2 が L_ff に依存しない |
| Study 19 | L_meas 感度分析（L_meas = 1–4） | F\* = W/2 が L_meas に依存しない |
| Study 20 | 大規模回路（H=10/12, Q=100） | F\* = W/2 がスケールしても成立 |
| Study 21 | raw+ASAP ベースライン（F=1–3） | shifted+ff_rm は raw+ASAP より低 stall |
