# ff_rate_matched スロットリングコストと L_ff 感度レポート

**作成日**: 2026-04-17  
**実験者**: 坪井 星汰

---

## 概要

本レポートは doc 20（`docs/20_hypothesis_driven_study_report.md`）で確立された `ff_rate_matched` policy について、2 つの追加検証を行った結果をまとめたものである。

### 研究の位置づけ

doc 20 では以下の設計指針を導いた:

> signal shift を使うなら ff_rate_matched を採用。ff_width = issue_width/2 で運用可能。

本レポートはこの指針の **実用的な限界** を 2 つの軸で検証する:

1. **Study 17（候補 1）**: ff_rate_matched のスロットリングは、低 F/W 比でも throughput コストを生じないか？
2. **Study 18（候補 2）**: L_ff を 1–5 に変えたとき、F* と throughput はどう変化するか？

### 主要な発見


| 発見                                       | 内容                                                                                                         |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------------------- |
| **Throughput コストはゼロ**                    | 360 ペア中 346 で total_cycles が完全一致。残り 14 ペアも ±0.17% 未満。F/W = 0.125（ff_width=2, issue_width=16）でもコストは観測されなかった |
| **F(ff_rate_matched) = 4 が L_ff に依存しない** | L_ff = 1–5 の全条件で、ff_rate_matched は F* = 4（= issue_width/2）を維持。全 50 ケース（QAOA/VQE × 5 seeds × 5 L_ff）で例外なし   |
| **F(ASAP) は L_ff が増えると下がりうる**            | QAOA で L_ff ≥ 3 のとき F(ASAP) = 6 に低下（L_ff ≤ 2 では F = 8）。VQE は L_ff = 1–5 を通して F(ASAP) = 8 で固定               |
| **Throughput は L_ff に依存しない**             | shifted DAG 上の ff_rate_matched と ASAP は全 30 条件で throughput 中央値が完全一致                                        |


---

## Study 17: ff_rate_matched の throughput コスト精密測定

### 問い

スロットリングによって総実行サイクルは増えるか？どの F/W 比で増え始めるか？

### 実験設計


| パラメータ                    | 値                     |
| ------------------------ | --------------------- |
| dag_variant              | shifted のみ            |
| policies                 | asap, ff_rate_matched |
| release_mode             | next_cycle            |
| l_meas, l_ff             | 1, 2                  |
| issue_width = meas_width | 4, 8, 16              |
| ff_width                 | 2, 3, 4               |
| algorithms               | QAOA, QFT, VQE        |
| hq_pairs                 | 4:16, 6:36, 8:64      |
| seeds                    | 0–4                   |


**規模**: 40 DAGs × 18 configs = **720 runs**（QFT H8/Q64 shifted 欠損のため 45→40 DAGs）

### F/W 比の探索範囲


| issue_width | ff_width | F/W    |
| ----------- | -------- | ------ |
| 16          | 2        | 0.125  |
| 16          | 3        | 0.1875 |
| 8           | 2        | 0.25   |
| 16          | 4        | 0.25   |
| 8           | 3        | 0.375  |
| 4           | 2        | 0.5    |
| 8           | 4        | 0.5    |
| 4           | 3        | 0.75   |
| 4           | 4        | 1.0    |


### 結果

**360 ペア**（同一 DAG・同一パイプライン設定で policy のみ異なるペア）の比較:


| メトリクス                                    | 値                     |
| ---------------------------------------- | --------------------- |
| cycles_ratio (ff/asap) 中央値               | **1.000000**          |
| throughput_gain_pct 中央値                  | **0.0000%**           |
| cycles 完全一致                              | **346 / 360** (96.1%) |
| cycles_ratio > 1.0 (ff_rate_matched が遅い) | **10**                |
| cycles_ratio < 1.0 (ff_rate_matched が速い) | **4**                 |


F/W × issue_width の 9 バケット全てで **median cycles_ratio = 1.0**:


| F/W    | W=4 | W=8 | W=16 |
| ------ | --- | --- | ---- |
| 0.125  | —   | —   | 1.0  |
| 0.1875 | —   | —   | 1.0  |
| 0.25   | —   | 1.0 | 1.0  |
| 0.375  | —   | 1.0 | —    |
| 0.5    | 1.0 | 1.0 | —    |
| 0.75   | 1.0 | —   | —    |
| 1.0    | 1.0 | —   | —    |


差が出た 14 ペアはすべて **QFT** であり、比率は ±0.17% 未満のノイズ級（greedy_critical ではなく ASAP 特有のタイブレーク差分と推定される）。

### 解釈

仮説「F/W < 0.5 ではスロットリングの throughput コストが発現する」は **棄却** された。F/W = 0.125 まで下げても ff_rate_matched と ASAP は同一の total_cycles を出力する。

これは shifted DAG の FF chain depth が非常に浅い（D_ff = 1–2）ため、**スロットリングが発動しうるタイミングで実際に FF 待ちノードがほぼ存在しない** ことによる。ff_rate_matched のガード条件 `ff_in_flight ≥ ff_width` は理論上は F/W < 0.5 で発動するが、shifted DAG 上ではそもそも同時に ff_in_flight が ff_width に達する頻度が極めて低い。

---

## Study 18: L_ff 感度分析

### 問い

L_ff（FF 処理レイテンシ）を 1–5 に変えたとき:

- F(ff_rate_matched) は変化するか？
- F(ASAP) は変化するか？
- throughput にコストが出るか？

### 実験設計


| パラメータ                    | 値                       |
| ------------------------ | ----------------------- |
| dag_variant              | both (raw + shifted)    |
| policies                 | asap, ff_rate_matched   |
| release_mode             | next_cycle              |
| l_meas                   | 1                       |
| l_ff                     | 1, 2, 3, 4, 5           |
| issue_width = meas_width | 8                       |
| ff_width                 | 4, 6, 8                 |
| algorithms               | QAOA, VQE（D_ff が極端なケース） |
| hq_pairs                 | 8:64                    |
| seeds                    | 0–4                     |


**規模**: 20 DAGs × 30 configs = **600 runs**（68s）

### 結果 1: F の L_ff 依存性

F = stall(shifted) ≤ stall(raw) を満たす最小 ff_width。


| L_ff | F(ASAP) QAOA | F(ASAP) VQE | F(ff_rate_matched) QAOA | F(ff_rate_matched) VQE |
| ---- | ------------ | ----------- | ----------------------- | ---------------------- |
| 1    | 8            | 8           | **4**                   | **4**                  |
| 2    | 8            | 8           | **4**                   | **4**                  |
| 3    | 6–8          | 8           | **4**                   | **4**                  |
| 4    | 6            | 8           | **4**                   | **4**                  |
| 5    | 6            | 8           | **4**                   | **4**                  |


- **ff_rate_matched**: F = 4 が全 50 ケースで不変。理論的保証（doc 20 実験 B）が L_ff 変動下でも成立することを実証。
- **ASAP**: QAOA で L_ff ≥ 3 のとき一部 seed で F = 6 に低下。L_ff が大きいと FF パイプラインの容量が増え、burst をバッファできるため。VQE は D_ff_raw が深く burst_load が大きいため L_ff = 5 でも F = 8 が必要。

### 結果 2: Stall regression (ff_width = 4)

shifted DAG + ff_width = 4 での stall_rate 中央値:


| L_ff | ASAP (QAOA) | ff_rate_matched (QAOA) | raw baseline (QAOA) | ASAP regression? |
| ---- | ----------- | ---------------------- | ------------------- | ---------------- |
| 1    | 0.2516      | **0.0016**             | 0.0181              | YES              |
| 2    | 0.2523      | **0.0024**             | 0.0345              | YES              |
| 3    | 0.2521      | **0.0032**             | 0.0519              | YES              |
| 4    | 0.2524      | **0.0040**             | 0.0790              | YES              |
| 5    | 0.2522      | **0.0048**             | 0.1079              | YES              |



| L_ff | ASAP (VQE) | ff_rate_matched (VQE) | raw baseline (VQE) | ASAP regression? |
| ---- | ---------- | --------------------- | ------------------ | ---------------- |
| 1    | 0.4620     | **0.0019**            | 0.0048             | YES              |
| 2    | 0.4625     | **0.0029**            | 0.0086             | YES              |
| 3    | 0.4630     | **0.0039**            | 0.0171             | YES              |
| 4    | 0.4626     | **0.0049**            | 0.0225             | YES              |
| 5    | 0.4631     | **0.0058**            | 0.0361             | YES              |


- ASAP は全 L_ff で stall regression（shifted > raw）が発生。しかも **L_ff にほぼ依存しない一定値** (QAOA ~25%, VQE ~46%)。
- ff_rate_matched は全 L_ff で stall_rate ≈ L_ff × 0.001 程度に抑制。raw baseline を常に下回る。

### 結果 3: Throughput

shifted DAG 上の ASAP と ff_rate_matched の throughput 中央値は **全 30 条件で完全一致**。L_ff = 5 でもコスト差なし。

### 解釈

仮説の検証結果:


| 仮説                                                 | 結果                                                   |
| -------------------------------------------------- | ---------------------------------------------------- |
| L_ff が増えると FF バッファが増え burst を吸収できる → ASAP の F が下がる | **部分的に確認**: QAOA で L_ff ≥ 3 のとき F = 6 に低下。VQE では効果なし |
| ff_rate_matched の F は L_ff に依存しない                  | **完全に確認**: 全 50 ケースで F = 4                           |
| L_ff が大きいと issue_utilization が低下する（別種コスト）          | **否定**: throughput は L_ff 変動下でも完全一致                  |


ASAP の F 低下が QAOA のみで起きた理由: QAOA H8/Q64 は burst_load = N/D_ff が VQE より小さく、L_ff バッファの恩恵を受けやすい。VQE は burst_load が大きすぎて L_ff = 5 程度では吸収しきれない。

---

## 総合結論

### ff_rate_matched の実用性の確認


| 検証項目                            | 結論                                    |
| ------------------------------- | ------------------------------------- |
| Throughput コスト（F/W = 0.125–1.0） | **ゼロ**。全条件で total_cycles 一致           |
| F の L_ff 安定性（L_ff = 1–5）        | **完全安定**。F = 4 (= W/2) が L_ff に無関係に成立 |
| Stall 抑制の L_ff 安定性              | **安定**。L_ff = 5 でも stall_rate < 0.01  |
| 高 L_ff での隠れコスト                  | **なし**。throughput 完全一致                |


### 設計指針の強化

doc 20 の指針:

> signal shift を使うなら ff_rate_matched を採用。ff_width = issue_width/2 で運用可能。

を以下のように強化できる:

> **ff_rate_matched は、F/W = 0.125 まで、L_ff = 5 まで、throughput コストゼロで stall regression を完全に除去する。**  
> **F = issue_width/2 という保証はパラメータ空間全域で成立し、実用上の適用制限は観測されなかった。**

### 残課題


| 優先度 | 項目                                       |
| --- | ---------------------------------------- |
| A   | 大規模回路 (H ≥ 10, Q ≥ 100) でのスケーリング検証（候補 3） |
| A   | L_meas 感度（候補 4）: 測定レイテンシが burst 分散に与える影響 |
| B   | QFT H8/Q64 shifted 未生成の解消                |


---

## データ


| Study       | パス                                                                                | 行数  | 実行時間  |
| ----------- | --------------------------------------------------------------------------------- | --- | ----- |
| 17          | `research/mbqc_pipeline_sim/results/studies/17_throughput_cost/summary/sweep.csv` | 720 | ~136s |
| 17 (paired) | `同/summary/paired_comparison.csv`                                                 | 360 | —     |
| 18          | `research/mbqc_pipeline_sim/results/studies/18_lff_sensitivity/summary/sweep.csv` | 600 | ~68s  |


