# 引き継ぎ資料：次フェーズの研究方針

**作成日**: 2026-04-17  
**作成者**: Claude Sonnet 4.6（坪井との共同研究セッションにて）  
**前提**: doc 20（`docs/20_hypothesis_driven_study_report.md`）の内容を踏まえた上で読むこと

---

## 現時点での研究の到達点

```
仮説 → 実験 → 理論 の一サイクルが完結した。

[問題発見]  shifted DAG で stall が悪化する謎の現象 (doc 16)
    ↓
[機構解明]  ready burst → FF queue 爆発 → issue stall (実験 1-3)
    ↓
[解法導出]  ff_rate_matched: 到達レート ≤ 処理レート を構造的に保証 (実験 A)
    ↓
[理論証明]  F*(ff_rate_matched) = ff_width_min が任意パラメータで成立 (実験 B)
```

**確立された設計指針**：
- Compiler が signal shift を使うなら、Scheduler は ff_rate_matched を採用せよ
- これにより ff_width ≥ 4（issue_width の半分）で stall regression ゼロが保証される
- ASAP では ff_width = issue_width（= W = 8）が必要だったが、ff_rate_matched で 4 まで下げられる

---

## 次フェーズの研究候補と優先順位

### 優先度 S：すぐにやるべき

---

#### 候補 1: ff_rate_matched の throughput コスト精密測定

**問い**：スロットリングによって総実行サイクルは増えるか？どの条件で増えるか？

**背景**：  
実験 A の結果では throughput gain（raw→shifted）の中央値が ASAP と ff_rate_matched でほぼ同値だった。しかし「中央値が同じ」は「常に同じ」ではない。特に：

- D_ff_shifted が 1（VQE）の場合、FF が律速になるため issued ノードが詰まる可能性がある
- スロットリングで発行を抑えると、FF の空きが生まれる前に次のノードが待つ、という別種の stall が発生し得る

**実験設計**：

```
sweep パラメータ:
  - policies: asap, ff_rate_matched
  - dag_variant: shifted のみ（raw は不要）
  - ff_widths: 2, 3, 4 (← ff_rate_matched が真に活きる低 ff_width 領域)
  - issue_widths: 4, 8, 16 (← W との比率 F/W を変化させる)
  - meas_widths: = issue_width
  - algorithms: QAOA, QFT, VQE
  - hq_pairs: 4:16, 6:36, 8:64
  - dag_seeds: 0-4

新規メトリクス（simulator 拡張が必要かも）:
  - issue_utilization: 実際に発行された / 上限 W の比率（スロットリングの効き具合）
  - ff_queue_mean/max: FF waiting queue の平均・最大値（burst が抑えられているか）
  - effective_throughput: total_nodes / total_cycles（絶対値での throughput 比較）
```

**仮説**：
- `F/W ≥ 0.5` では throughput コストはほぼゼロ（スロットリングが rarely 発動）
- `F/W < 0.5` では ff_rate_matched の throughput が ASAP を下回り始める
- クロスオーバー点 `(F/W)*` が存在し、それが実用設計の下限になる

**推定規模**: sweep 約 1,500 行、1-2 時間

---

#### 候補 2: L_ff（FF 処理レイテンシ）感度分析

**問い**：L_ff を変えると ff_rate_matched のトリガー条件はどう変わるか？F* は変化するか？

**背景**：  
現在の全実験は L_ff = 2 固定。しかし実際の量子ハードウェアでは FF 処理（ancient light cone 計算 + 古典ビット操作）のレイテンシは実装依存で 1〜5 サイクル程度が現実的。

ff_rate_matched のトリガーは `ff_in_flight_count ≥ ff_width`。
- `ff_in_flight` = FF パイプライン中のノード数 = 最大 `ff_width × L_ff` ノード
- L_ff が大きいと、同じ ff_width でもパイプライン容量が増える → burst の影響が変わる

**実験設計**：

```
sweep パラメータ:
  - policies: asap, ff_rate_matched
  - dag_variant: raw, shifted
  - ff_widths: 4, 6, 8
  - l_ff_values: 1, 2, 3, 4, 5
  - l_meas_values: 1（固定）
  - algorithms: QAOA, VQE（D_ff が極端なケースに絞る）
  - hq_pairs: 8:64（大規模）
  - dag_seeds: 0-4
```

**仮説**：
- L_ff が増えると FF パイプラインのバッファが増え、burst を一時的に吸収できる
- → ASAP の F* が小さくなる（L_ff=5 ならば F*=4 に近づく可能性）
- ff_rate_matched の F* は L_ff に依存しない（理論的保証は L_ff に無関係）
- ただし L_ff が大きいと issue_utilization が低下し得る（別種のコスト）

**推定規模**: sweep 約 600 行、30 分

---

### 優先度 A：近いうちにやりたい

---

#### 候補 3: 大規模回路（H=10/12, Q=100+）でのスケーリング検証

**問い**：burst_load = N / D_ff がさらに大きい回路でも F*(ff_rate_matched) = 4 が保証されるか？

**背景**：  
実験 B で導いた burst_load と F*(ASAP) の相関グラフは H=4/6/8 の範囲。
大規模になると：
- QAOA: N ∝ H²Q ≈ H²×H² → N が急増、D_ff_shifted = 2 固定 → burst_load が爆発的に増える
- F*(ASAP) は上界 W=8 に張り付く可能性が高い（既に H=8 で F*=7-8）
- ff_rate_matched の保証が維持されるか、throughput コストが出てくるかが本質的な問い

**前提条件**：
- まず H=10 以上のアーティファクト（JSON）を mbqc_ff_evaluator で生成する必要がある
- `research/mbqc_ff_evaluator/` 側の実験が必要（pipeline_sim ではなく evaluator 側）
- 時間がかかるため、先に候補 1・2 を終わらせてから着手推奨

**推定規模**: アーティファクト生成に数時間 + sweep/analyze で 1-2 時間

---

#### 候補 4: L_meas > 1 の挙動分析

**問い**：測定レイテンシが長くなると burst の発生タイミングはどう変わるか？

**背景**：  
現在 L_meas = 1（測定を 1 サイクルで完了）は最楽観的な仮定。実際の量子測定は：
- 光子検出: 数サイクル（L_meas = 2-4 が現実的）
- 測定後の古典処理: さらに数サイクル加算されることも

L_meas が増えると：
- 測定中のノード数が増える（`meas_pipe.occupancy` が増加）
- FF への到達レートが smoothing される（burst が時間的に分散する）
- 逆に言えば、L_meas が大きいと burst が自然に分散し、ff_rate_matched の必要性が下がるかもしれない

**実験設計**：

```
sweep パラメータ:
  - policies: asap, ff_rate_matched
  - dag_variant: shifted のみ
  - ff_widths: 4, 8
  - l_meas_values: 1, 2, 3, 4
  - l_ff_values: 2（固定）
  - algorithms: QAOA, VQE（burst が最大のケース）
  - hq_pairs: 6:36, 8:64
  - dag_seeds: 0-4
```

**仮説**：
- L_meas が増えるほど burst が分散 → ASAP の F* が下がる
- ある L_meas 閾値を超えると ASAP でも F*=4 になる（ff_rate_matched と同等）
- その閾値が「ハードウェア設計の余裕」を示す指標になる

**推定規模**: sweep 約 400 行、30 分

---

### 優先度 B：中長期的な課題

---

#### 候補 5: F*(ASAP) の精密予測モデル

**問い**：burst_load 単変数では説明しきれない F*(ASAP) の残余誤差を raw_stall_rate で説明できるか？

**背景**：  
実験 B で `F*(ASAP) ≈ ⌈W × (1 − 1/log₂(B+1))⌉` という参照式を示したが、精度は低い。
特に QFT H6/Q36（burst_load=375 なのに F*=8）が外れ値として目立つ。

これは raw_stall_rate（ベースラインの stall）が影響しているためで、raw_stall が低いほど F* が高くなる傾向がある（stall regression の「判定基準」が厳しくなるため）。

**提案**：
- 2 変数モデル: `F*(ASAP) = f(burst_load, raw_stall_rate)`
- 線形回帰または意思決定木で fit する
- 目標: 全 40 ケースで ±1 以内の誤差

---

#### 候補 6: QFT H8/Q64 shifted 未対応問題の解決

**問い**：なぜ QFT H8/Q64 の shifted アーティファクトが存在しないのか？

**背景**：  
`13_shifted_dag_dynamic/common_coupled_subset/artifacts/` に `QFT_H8_Q64_seed*.json` はあるが、shifted DAG が含まれていない。sweep 時に `UserWarning: Skipping ... Shifted dependency graph is not available` が出ている。

mbqc_ff_evaluator 側で signal shift の計算が timeout したか、QFT H8 の回路構造が signal shift に対応していない可能性がある。これを解決すると QFT の大規模ケースが使えるようになる。

---

## 実験コマンド早見表

### 候補 1 を実施する場合

```bash
cd research/mbqc_pipeline_sim
PYTHONPATH=src .venv-ffeval310/bin/python3 -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir ../../research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --output results/studies/17_throughput_cost/summary/sweep.csv \
  --issue-widths 4,8,16 --l-meas-values 1 --l-ff-values 2 \
  --policies asap,ff_rate_matched \
  --release-modes next_cycle \
  --meas-widths 4,8,16 --ff-widths 2,3,4 \
  --dag-variant shifted \
  --algorithms QAOA,QFT,VQE \
  --hq-pairs 4:16,6:36,8:64 \
  --dag-seeds 0,1,2,3,4
```

### 候補 2 を実施する場合

```bash
PYTHONPATH=src .venv-ffeval310/bin/python3 -m mbqc_pipeline_sim.cli.sweep \
  --artifacts-dir ../../research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts \
  --output results/studies/18_lff_sensitivity/summary/sweep.csv \
  --issue-widths 8 --l-meas-values 1 --l-ff-values 1,2,3,4,5 \
  --policies asap,ff_rate_matched \
  --release-modes next_cycle \
  --meas-widths 8 --ff-widths 4,6,8 \
  --dag-variant both \
  --algorithms QAOA,VQE \
  --hq-pairs 8:64 \
  --dag-seeds 0,1,2,3,4
```

---

## ファイル・ディレクトリ構成（現状）

```
mbqc-classical-control-study/
├── docs/
│   ├── 20_hypothesis_driven_study_report.md   ← 本日の成果レポート（必読）
│   └── worklog/
│       └── 20260417_handoff_next_experiments.md  ← 本ファイル
│
└── research/mbqc_pipeline_sim/
    ├── src/mbqc_pipeline_sim/
    │   ├── core/scheduler.py                  ← FfRateMatchedScheduler 追加済み
    │   ├── domain/enums.py                    ← FF_RATE_MATCHED 追加済み
    │   ├── analysis/shifted_study.py          ← D_ff 相関分析関数 追加済み
    │   └── cli/
    │       ├── analyze_burst.py               ← 実験 2
    │       ├── analyze_dff_correlation.py     ← 実験 1
    │       ├── analyze_fstar_theory.py        ← 実験 B
    │       ├── plot_burst.py
    │       ├── plot_dff_correlation.py
    │       ├── plot_ff_rate_matched.py        ← 実験 A 可視化
    │       ├── plot_ffwidth_sweep.py          ← 実験 3 可視化
    │       └── plot_fstar_theory.py           ← 実験 B 可視化
    │
    └── results/studies/
        ├── rerun_20260416/                    ← canonical データセット
        ├── 15_ffwidth_sweep/                  ← 実験 3（F* テーブル）
        ├── 16_ff_rate_matched/                ← 実験 A/B（主要成果）
        ├── burst_analysis/                    ← 実験 2（burst 可視化）
        └── data_old/                          ← 旧データ（13/14）
```

---

## 重要な数値・結論の早引き表

| メトリクス | ASAP（shifted） | ff_rate_matched（shifted） |
|---|---|---|
| F*(QAOA H8/Q64) | 7–8 | **4** |
| F*(QFT H6/Q36) | 8 | **4** |
| F*(VQE H8/Q64) | 8 | **4** |
| Stall QFT F=4 | −612% (regression) | **+89%** |
| Throughput gain QFT F=4 | +13% | **+13%** |

**設計指針ワンライナー**：  
> signal shift を使うなら ff_rate_matched を採用。ff_width = issue_width/2 で運用可能。

---

> **次のセッションでやること**（優先順）: 候補 1 → 候補 2 → 候補 3  
> **仮想環境**: `.venv-ffeval310`（Python 3.10）  
> **作業ディレクトリ**: `research/mbqc_pipeline_sim/`
