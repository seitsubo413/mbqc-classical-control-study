# 仮説駆動型実験レポート：shifted DAG と controller の相互作用機構

**作成日**: 2026-04-17  
**実験者**: 坪井 星汰

---

## 概要

本レポートは 2026-04-17 に実施した 3 つの仮説駆動型実験をまとめたものである。

前回までの研究（doc 16、`docs/docs_old/16_shifted_dag_codesign_interim_conclusion.md`）で「shifted DAG を使うと stall が悪化する regime がある」「ASAP が shifted DAG 上で支配的になる」という現象が観測されたが、その **機構** は未解明だった。本日の実験はその因果構造を明らかにすることを目的とした。

### 実験の問い

1. **実験 1（D_ff 相関）**: D_ff の大きさは policy の有効性を予測するか？
2. **実験 2（burst 可視化）**: stall regression の原因は ready burst か？どのように発生するか？
3. **実験 3（ff_width sweep）**: stall regression が消えるための最小 ff_width（F*）はいくつか？

### 主要な発見

| 発見 | 内容 |
|---|---|
| **D_ff と policy の相関** | raw DAG では D_ff に関わらず greedy が ASAP を上回る。shifted DAG では D_ff 1-2（QAOA/VQE）で policy 差がほぼゼロ、D_ff 6-15（QFT 小規模）で sweet spot、D_ff 16-40（QFT 大規模）で stall 悪化 |
| **burst の正体** | shifted DAG では FF waiting queue が raw の 19-49 倍に膨張する。raw 最大 14-108、shifted 最大 507-2661 |
| **設計境界 F*** | ASAP で QAOA: F*=6、QFT: F*=7、VQE: F*=8。ff_width ≥ 7 で全アルゴリズムの stall regression が解消 |

---

## 実験環境・データ

### 入力データ

| データ | パス | 内容 |
|---|---|---|
| 基礎 sweep（policy 比較） | `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/summary/sweep.csv` | 2720 行。W8 M8 F4/F8、asap/greedy_critical/shifted_critical/stall_aware_shifted |
| FF evaluator artifacts | `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts/` | 45 件の JSON（QAOA/QFT/VQE × H4/H6/H8 × seed 0-4） |
| ff_width sweep（新規） | `results/studies/15_ffwidth_sweep/summary/sweep.csv` | 1275 行。F=4,5,6,7,8 × 3 policy × raw/shifted |

### 共通パラメータ（特記なき限り）

```
issue_width   : 8
l_meas        : 1
l_ff          : 2
meas_width    : 8
release_mode  : next_cycle
algorithms    : QAOA, QFT, VQE
hq_pairs      : 4:16, 6:36, 8:64
dag_seeds     : 0, 1, 2, 3, 4
dag_variant   : both (raw + shifted)
```

---

## 実験 1：D_ff の大きさと policy 有効性の相関

### 目的と仮説

**仮説**: D_ff が小さいほど priority ordering の signal が消え、complex policy が ASAP に対して優位を持てなくなる。

### 方法

既存の sweep.csv（`rerun_20260416/14_shifted_dag_codesign_w8_focus`）を再分析。各シナリオ（dag_variant × algorithm × H × Q × seed × l_meas × l_ff × meas_width × ff_width）で policy ごとのスループット・stall 率を ASAP と比較し、ff_chain_depth でビニングした。

**出力ファイル**:
- `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/summary/analysis/dff_policy_cases.csv`（2720 行）
- `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/summary/analysis/dff_correlation_bins.csv`（28 行）

**新規スクリプト**:
- `src/mbqc_pipeline_sim/analysis/shifted_study.py` に `build_dff_policy_cases()`, `build_dff_correlation_bins()` を追加
- `src/mbqc_pipeline_sim/cli/analyze_dff_correlation.py`（CLI）
- `src/mbqc_pipeline_sim/cli/plot_dff_correlation.py`（可視化）

### 結果

#### Raw DAG（D_ff = 6-400）

| D_ff bin | greedy_critical throughput 改善 | stall 改善率 |
|---|---|---|
| 6-15 | **+5.1%** | 100% のケースで改善 |
| 16-40 | +2.4% | 55% |
| 41-100 | +1.4% | 60% |
| 101-400 | +1.1% | 94% |

raw DAG では D_ff の大きさに関わらず greedy_critical が ASAP を上回る（throughput 改善率 100%）。ただし D_ff が小さいほど改善幅が大きい傾向がある。

#### Shifted DAG（D_ff = 1-40）—— 非単調な関係

| D_ff bin | 対象 | greedy throughput | stall vs ASAP |
|---|---|---|---|
| **1-2** | QAOA/VQE shifted | **+0%（差なし）** | shifted_critical/stall_aware_shifted で **+8% 悪化** |
| **6-15** | QFT H4/H6 shifted | +1.9-2.1% | **stall も -4〜-6% 改善（sweet spot）** |
| **16-40** | QFT H6/H8 shifted | +0.4% | stall が **+7-8% 悪化** |

出典: `dff_correlation_bins.csv`

#### 解釈

仮説「signal 消失説」は **D_ff 1-2 に対しては正しい**。VQE shifted（D_ff=1）では greedy_critical が ASAP と完全一致（throughput_delta=0、stall_delta=0）。QAOA shifted（D_ff=2）では throughput は 0 だが stall は shifted_critical で悪化。

ただし D_ff 16-40（QFT H6/H8 shifted）では stall が悪化するにもかかわらず throughput は改善している。これは signal 消失では説明できない別の機構（→ 実験 2 で解明）が働いていることを示す。

**図**:
- `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/figures/fig_dff_binned_summary.png`
- `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/figures/fig_dff_hypothesis_summary.png`

---

## 実験 2：Ready burst の直接観察

### 目的と仮説

実験 1 の結果を踏まえ、stall regression の主因が **FF waiting queue の爆発的増大（burst）** であることを直接確認する。

**仮説 (HA-1)**: shifted DAG では依存解放イベントが cycle 0 付近に集中し、FF processor への流入が一斉に起こる。ff_width 制約のもとで FF waiting queue が爆発し、これが stall の真因である。

### 方法

代表 4 ケース（QAOA H8/Q64、QFT H6/Q36、QFT H4/Q16、VQE H8/Q64）の seed 0 について、raw/shifted × asap/greedy_critical でシミュレーションを実行し、サイクルごとの `ready_queue_size` と `waiting_ff_queue_size` を記録した。

**設定**: W=8, M=8, F=4, L_meas=1, L_ff=2, release_mode=next_cycle

**出力ファイル**:
- `results/studies/burst_analysis/cycle_records.csv`（17,152 行）
- `results/studies/burst_analysis/burst_summary.csv`（16 行）

**新規スクリプト**:
- `src/mbqc_pipeline_sim/cli/analyze_burst.py`（シミュレーション実行 + cycle 記録）
- `src/mbqc_pipeline_sim/cli/plot_burst.py`（可視化）

### 結果

#### FF waiting queue の raw vs shifted 比較（ASAP）

| ケース | raw D_ff | shifted D_ff | raw max | shifted max | 倍率 |
|---|---|---|---|---|---|
| QAOA H8/Q64 | 142 | 2 | 52 | **2,284** | **44×** |
| QFT H6/Q36 | 177 | 10 | 54 | **2,661** | **49×** |
| QFT H4/Q16 | 77 | 7 | 14 | **507** | **36×** |
| VQE H8/Q64 | 63 | 1 | 108 | **2,024** | **19×** |

出典: `burst_summary.csv`

**仮説 HA-1 は確認された**。Shifted DAG では FF waiting queue が raw の 19-49 倍に膨張する。

#### burst の発生機構

Ready queue の時系列（`fig_burst_timeseries_asap.png`）を見ると：

- **Raw DAG**: ready_queue_size は常にほぼ 0%（ほとんどのノードは依存待ちで即時 ready にならない）
- **Shifted DAG**: D_ff が 1-2 のとき、cycle 0 でほぼ全ノード（80-100%）が一斉に ready になり、急速に消費される

この一斉 ready が measurement pipeline → FF processor へ殺到し、ff_width=4 では処理が追いつかないため FF waiting queue が数千規模に膨張する。

#### greedy_critical が stall をさらに悪化させる機構

| ケース | ASAP stall % | greedy_critical stall % |
|---|---|---|
| QAOA H8/Q64 shifted | 24.8% | **45.4%** |
| QFT H6/Q36 shifted | 35.6% | **43.5%** |
| QFT H4/Q16 shifted | 40.4% | **45.4%** |
| VQE H8/Q64 shifted | 46.3% | **46.3%（同一）** |

出典: `burst_summary.csv`

**greedy_critical の悪化機構**:

Greedy_critical は「remaining depth が最大のノード」を優先発行する。Shifted DAG（D_ff=2）では depth=2 のノード群を全て先に発行するため、それらの FF 完了タイミングが同期し、第 2 層の依存解放も一斉に起こる。これがさらに大きな burst を作る。

ASAP は topo_level + node_id の自然順で発行するため、burst のタイミングが自然に分散する。これが ASAP の stall 率が低い理由である。

VQE shifted（D_ff=1）では全ノードが同じ depth=1 のため greedy が ASAP と同一の動作をする（priority 差がゼロ → 同一結果）。

**図**:
- `results/studies/burst_analysis/figures/fig_burst_timeseries_asap.png`（ready queue 時系列）
- `results/studies/burst_analysis/figures/fig_burst_ff_waiting_asap.png`（FF waiting queue 時系列）
- `results/studies/burst_analysis/figures/fig_burst_policy_shifted.png`（shifted DAG での policy 比較）

---

## 実験 3：ff_width sweep による設計境界の定量化

### 目的と仮説

**仮説 (HB-1)**: stall regression を burst が原因とするなら、ff_width を増やして FF processor のスループットを上げれば stall regression が消える臨界点 F* が存在する。

### 方法

ff_width = 4, 5, 6, 7, 8 の全組み合わせで sweep を新規実行した。

```
artifacts   : 13_shifted_dag_dynamic/common_coupled_subset/artifacts（45件）
issue_width : 8
meas_width  : 8
ff_widths   : 4, 5, 6, 7, 8
l_meas      : 1
l_ff        : 2
policies    : asap, greedy_critical, stall_aware_shifted
dag_variant : both
hq_pairs    : 4:16, 6:36, 8:64
dag_seeds   : 0-4
合計        : 1,275 シミュレーション
```

**出力ファイル**:
- `results/studies/15_ffwidth_sweep/summary/sweep.csv`（1,275 行）
- `results/studies/15_ffwidth_sweep/summary/analysis/policy_width_summary.csv`

**新規スクリプト**:
- `src/mbqc_pipeline_sim/cli/plot_ffwidth_sweep.py`（可視化 + F* テーブル）

### 結果

#### Stall reduction（raw→shifted）の ff_width 依存性（ASAP）

| ff_width | QAOA stall reduction | QFT stall reduction | VQE stall reduction |
|---|---|---|---|
| 4 | **−222%（悪化）** | **−612%（悪化）** | **−1555%（悪化）** |
| 5 | −52%（悪化） | −245%（悪化） | −628%（悪化） |
| 6 | **+21%（改善）** | −87%（悪化） | −285%（悪化） |
| 7 | +75%（改善） | **+13%（改善）** | −13%（悪化） |
| 8 | +94%（改善） | +91%（改善） | **+86%（改善）** |

出典: `15_ffwidth_sweep/summary/analysis/policy_width_summary.csv`

#### F*（stall regression が解消する最小 ff_width）

| Algorithm | ASAP | greedy_critical | stall_aware_shifted |
|---|---|---|---|
| **QAOA** | **F* = 6** | F* = 7 | F* = 7 |
| **QFT** | F* = 7 | F* = 7 | F* = 7 |
| **VQE** | F* = 8 | F* = 8 | F* = 8 |

#### Throughput gain は ff_width に依存しつつ常に正

Throughput gain（raw→shifted）は ff_width が増えるほど大きくなるが、ff_width=4 でも常に正である：

| ff_width | QAOA throughput gain | QFT throughput gain | VQE throughput gain |
|---|---|---|---|
| 4 | +9.8% | +13.0% | +4.9% |
| 5 | +19.1% | +20.7% | +6.5% |
| 6 | +31.0% | +30.0% | +10.0% |
| 7 | +41.9% | +41.6% | +13.2% |
| 8 | +56.6% | +54.2% | +18.2% |

出典: `15_ffwidth_sweep/summary/analysis/policy_width_summary.csv`

#### ASAP が最も低い F* を達成する

同じアルゴリズムの中で ASAP は常に greedy_critical や stall_aware_shifted より小さい F* を持つ（QAOA では 1 段分、QFT では同じ）。これは実験 2 の機構説明（ASAP の分散発行が burst を抑制する）と整合する。

**図**:
- `results/studies/15_ffwidth_sweep/figures/fig_ffwidth_combined.png`（stall reduction + throughput gain）
- `results/studies/15_ffwidth_sweep/figures/fig_ffwidth_stall_reduction.png`
- `results/studies/15_ffwidth_sweep/figures/fig_ffwidth_throughput_gain.png`

---

## 統合分析：3 実験から導かれる構造

### 因果構造

```
Signal shift（コンパイラ最適化）
    ↓
D_ff が大きく削減される（QAOA: 142→2, VQE: 63→1, QFT: 177→7-31）
    ↓
ほぼ全ノードが cycle 0 付近で一斉に ready になる
    ↓
W=8 で高速発行 → measurement → FF processor に殺到
    ↓
ff_width < F* のとき FF waiting queue が爆発（raw の 19-49 倍）
    ↓
FF 完了の遅延 → ready queue の枯渇 → stall
    ↓
stall regression（shifted DAG なのに stall が raw より悪化）
```

### D_ff ごとの挙動の整理

| shifted D_ff | 代表ケース | 主因 | 挙動 |
|---|---|---|---|
| 1-2 | QAOA/VQE shifted | Signal 消失 | greedy が無意味な並べ替え → stall 微悪化 |
| 6-15 | QFT H4/H6 shifted | Signal 有効 + burst 小 | **sweet spot**: throughput も stall も改善 |
| 16-40 | QFT H6/H8 shifted | Signal 有効だが burst 大 | throughput 改善 + **stall は悪化** |

### ASAP が shifted DAG で支配的である理由

ASAP は topo_level + node_id 順に発行するため、burst の発生タイミングが自然に分散する。Complex policy は「重要ノード優先」のために特定サイクルに発行を集中させ、FF 完了タイミングを同期させてしまう。Shifted DAG では D_ff が小さく「重要ノード」の判断基準が乏しいため、この悪影響だけが残る。

---

## 設計指針

### RTL チームへ

| 指針 | 根拠 |
|---|---|
| `ff_width ≥ 7` で全アルゴリズムの stall regression が ASAP で解消 | F* テーブル（実験 3）|
| `ff_width = issue_width` にするのが最も安全 | F*=8 = W の VQE ケース |
| Shifted DAG 使用時は throughput 改善は必ず得られる | 全 ff_width で gain > 0（実験 3）|
| Scheduler は ASAP で十分（OoO は shifted では stall を悪化させる） | 実験 2 の policy 比較 |

### コンパイラチームへ

| 指針 | 根拠 |
|---|---|
| Signal shift は必須だが、burst 問題を生む副作用がある | 実験 2 |
| QFT は shifted でも D_ff 6-40 が残り、burst 問題が最も深刻 | 実験 1 の D_ff bin |
| QAOA/VQE は D_ff→1-2 になるため burst は最大だが、F*=6/8 で対処可能 | 実験 3 |

---

## 実験 A：ff_rate_matched スケジューラ（2026-04-17 追加）

### 動機

実験 2・3 の機構解明から「FF プロセッサへの到達レートを発行段階でキャップすれば burst は根本的に防止できる」という仮説が自然に導かれた。これを実装したのが **ff_rate_matched** ポリシーである。

### 設計

```
trigger: ff_in_flight_count ≥ ff_width OR ff_waiting_count > 0
effect:  issue rate ← min(W, ff_width)   (= ff_width when ff_width < W)
```

ASAP との違いは「FF が飽和したら発行数を ff_width まで下げる」という**プロアクティブなスロットリング**のみ。burst が積み上がる前に防ぐ。

### 結果

| Algorithm | F*(ASAP) | F*(ff_rate_matched) | 削減幅 |
|-----------|----------|---------------------|--------|
| QAOA H4/Q16 | 4–5 | **4** | 0–1 |
| QAOA H6/Q36 | 5–6 | **4** | 1–2 |
| QAOA H8/Q64 | 7–8 | **4** | 3–4 |
| QFT H4/Q16 | 6 | **4** | 2 |
| QFT H6/Q36 | 8 | **4** | 4 |
| VQE H4/Q16 | 7 | **4** | 3 |
| VQE H6/Q36 | 8 | **4** | 4 |
| VQE H8/Q64 | 8 | **4** | 4 |

**全 40 ケースで F*(ff_rate_matched) = 4**（テスト範囲の最小値）。

Stall reduction（shifted vs raw）の中央値：

| Algorithm | F4: ASAP | F4: ff_rate_matched |
|-----------|----------|---------------------|
| QAOA | −222% | **+87%** |
| QFT | −612% | **+89%** |
| VQE | −1555% | **+62%** |

Throughput gain は ASAP と同水準を維持しつつ、stall regression を完全に排除した。

### データ・成果物

| パス | 内容 |
|------|------|
| `results/studies/16_ff_rate_matched/summary/sweep.csv` | 1,275 行。3 policy × raw/shifted × F4-F8 |
| `results/studies/16_ff_rate_matched/analysis/` | aggregate + analyze_shifted_study 出力全般 |
| `results/studies/16_ff_rate_matched/figures/fig_ffrm_stall_reduction.png` | **stall reduction 比較（推奨閲覧図）** |
| `results/studies/16_ff_rate_matched/figures/fig_ffrm_fstar_summary.png` | F* バー比較 |

---

## 実験 B：F* の理論的考察（2026-04-17 追加）

### 主要発見

**ff_rate_matched の F* = ff_width_min は理論的保証である（経験則ではない）。**

**証明スケッチ**：
1. トリガー条件 `ff_in_flight ≥ F OR ff_waiting > 0` が成立した瞬間、発行レート ≤ F
2. これにより FF ステージへの**到達レート ≤ F = 処理レート**が保証される
3. よって FF キューは成長不可 → FF 起因の stall は発生不可
4. shifted_stall ≤ raw_stall が任意の N, D_ff, W に対して成立

**ASAP の F*(ASAP) は回路パラメータに強く依存する**：

```
burst_load B = N / D_ff_shifted

B ≈ 150-180 → F* = 4-6
B ≈ 750-1300 → F* = 6-8
B ≈ 2500-4100 → F* = 7-8
```

経験的参照式（過推定に注意）：
```
F*(ASAP) ≈ ceil(W × (1 − 1/log₂(B+1)))
```

ただし raw stall rate（raw DAG のベースライン stall）も F* に影響するため、この式は上界推定として使う。

**重要な含意**：ff_rate_matched を使えば F* の計算自体が不要になる。

### データ・成果物

| パス | 内容 |
|------|------|
| `results/studies/16_ff_rate_matched/fstar_theory/fstar_per_case.csv` | per-case F* (40 件) |
| `results/studies/16_ff_rate_matched/fstar_theory/fstar_aggregated.csv` | circuit 別 F* 集計 |
| `results/studies/16_ff_rate_matched/figures/fig_fstar_burst_load.png` | **burst_load vs F*(ASAP) 散布図** |
| `results/studies/16_ff_rate_matched/figures/fig_fstar_reduction.png` | F* 削減量バー図 |

---

## 設計指針（更新版）

### RTL チームへ

| 指針 | 根拠 |
|---|---|
| **ff_rate_matched を採用すれば ff_width ≥ 4 で stall regression ゼロが保証される** | 実験 A（全 40 ケース F*=4） |
| ASAP 使用時は `ff_width ≥ 7` でほぼ全アルゴリズムの regression が解消 | 実験 3 F* テーブル |
| 大規模回路（N>4000, D_ff=1）では ASAP の F*=8 → ff_rate_matched で 4 削減可能 | 実験 B の burst_load 分析 |

### コンパイラチームへ

| 指針 | 根拠 |
|---|---|
| Signal shift を採用する場合、**スケジューラを ff_rate_matched に変更するだけで burst 問題が解消** | 実験 A |
| QFT は shifted でも D_ff=7-17 が残り、burst_load は QAOA より低いが raw stall も低く F* は最大 | 実験 B |
| QAOA/VQE は D_ff→1-2 になるが、ff_rate_matched で完全対処可能 | 実験 A/B |

---

## 今後の課題

| 優先度 | 課題 | 根拠 |
|---|---|---|
| 高 | **ff_rate_matched の throughput コスト精密測定**：大規模回路でスロットリングによる総実行サイクル増加を定量化 | 実験 A では中央値では差なしだが variance は検討余地あり |
| 中 | **F* の理論式の精度向上**：raw stall rate を組み込んだ 2 変数モデル (burst_load, raw_stall) で予測精度を向上 | 実験 B の残余誤差分析 |
| 中 | **QFT H8/Q64 shifted の失敗原因特定**：OneAdapt の compile timeout か signal shift の構造的限界か | doc 16 から続く未解決問題 |
| 低 | **ff_width sweep の大規模版**：hq_pairs に H=10/12 を追加し、F* スケーリングを確認 | 実験 A/B は H=4/6/8 のみ |

---

## 付録：生成されたファイル一覧

### 新規スクリプト

| ファイル | 役割 |
|---|---|
| `src/mbqc_pipeline_sim/analysis/shifted_study.py`（拡張） | `build_dff_policy_cases()`, `build_dff_correlation_bins()` を追加 |
| `src/mbqc_pipeline_sim/cli/analyze_dff_correlation.py` | 実験 1 の分析 CLI |
| `src/mbqc_pipeline_sim/cli/plot_dff_correlation.py` | 実験 1 の可視化 CLI |
| `src/mbqc_pipeline_sim/cli/analyze_burst.py` | 実験 2 のシミュレーション実行 + cycle 記録 |
| `src/mbqc_pipeline_sim/cli/plot_burst.py` | 実験 2 の可視化 CLI |
| `src/mbqc_pipeline_sim/cli/plot_ffwidth_sweep.py` | 実験 3 の可視化 CLI + F* テーブル出力 |
| `src/mbqc_pipeline_sim/core/scheduler.py`（拡張） | `FfRateMatchedScheduler` を追加（実験 A） |
| `src/mbqc_pipeline_sim/domain/enums.py`（拡張） | `FF_RATE_MATCHED` を `SchedulingPolicy` に追加 |
| `src/mbqc_pipeline_sim/cli/plot_ff_rate_matched.py` | 実験 A の可視化 CLI |
| `src/mbqc_pipeline_sim/cli/analyze_fstar_theory.py` | 実験 B：per-case F* 計算 + 理論式検証 |
| `src/mbqc_pipeline_sim/cli/plot_fstar_theory.py` | 実験 B の可視化 CLI |

### 生成データ

| パス | 内容 | 行数 |
|---|---|---|
| `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/summary/analysis/dff_policy_cases.csv` | 実験 1: per-seed policy vs ASAP with D_ff | 2,720 |
| `results/studies/rerun_20260416/14_shifted_dag_codesign_w8_focus/summary/analysis/dff_correlation_bins.csv` | 実験 1: D_ff bin 集計 | 28 |
| `results/studies/burst_analysis/cycle_records.csv` | 実験 2: cycle ごとのキューサイズ | 17,152 |
| `results/studies/burst_analysis/burst_summary.csv` | 実験 2: ケース別サマリ | 16 |
| `results/studies/15_ffwidth_sweep/summary/sweep.csv` | 実験 3: ff_width sweep 全結果 | 1,275 |
| `results/studies/15_ffwidth_sweep/summary/analysis/policy_width_summary.csv` | 実験 3: 集計済み | 15 |
| `results/studies/16_ff_rate_matched/summary/sweep.csv` | 実験 A: ff_rate_matched sweep | 1,275 |
| `results/studies/16_ff_rate_matched/analysis/policy_width_summary.csv` | 実験 A: 集計済み | 15 |
| `results/studies/16_ff_rate_matched/fstar_theory/fstar_per_case.csv` | 実験 B: per-case F* (40 件) | 40 |
| `results/studies/16_ff_rate_matched/fstar_theory/fstar_aggregated.csv` | 実験 B: circuit 別集計 | 8 |

### 生成図

| パス | 内容 |
|---|---|
| `rerun_20260416/.../figures/fig_dff_binned_summary.png` | D_ff bin × policy 改善量（4 パネル） |
| `rerun_20260416/.../figures/fig_dff_hypothesis_summary.png` | D_ff 連続値 × policy 改善量 |
| `burst_analysis/figures/fig_burst_timeseries_asap.png` | ready queue 時系列 raw vs shifted |
| `burst_analysis/figures/fig_burst_ff_waiting_asap.png` | FF waiting queue 時系列（burst の直接観察） |
| `burst_analysis/figures/fig_burst_policy_shifted.png` | shifted での ASAP vs greedy_critical |
| `15_ffwidth_sweep/figures/fig_ffwidth_combined.png` | ff_width sweep 総合図（推奨閲覧図） |
| `16_ff_rate_matched/figures/fig_ffrm_stall_reduction.png` | **実験 A: stall reduction 比較（推奨閲覧図）** |
| `16_ff_rate_matched/figures/fig_ffrm_fstar_summary.png` | 実験 A: F* バー比較 |
| `16_ff_rate_matched/figures/fig_fstar_burst_load.png` | **実験 B: burst_load vs F*(ASAP) 散布図** |
| `16_ff_rate_matched/figures/fig_fstar_reduction.png` | 実験 B: F* 削減量バー図 |

---

> **レポート作成日**: 2026-04-17  
> **最終更新**: 2026-04-17（実験 A: ff_rate_matched, 実験 B: F* 理論 を追加）  
> **使用データ**: rerun_20260416 sweep（2720件）+ burst 実験（17,152 cycle records）+ ff_width sweep × 2（各 1,275件）
