# MBQC パイプラインサイクル精度シミュレータ — 実験レポート

## 1. 概要

本レポートは、MBQC 制御パイプラインのサイクル精度シミュレータを用いた設計空間探索の結果をまとめたものである。
FF evaluator（[report 10](10_ff_evaluator_report.md)）が「コンパイラ出力の静的特性（D_ff, L_hold, L_meas）」を定量化したのに対し、本シミュレータは「マイクロアーキテクチャ構成がスループットとストール率に与える影響」を動的にモデル化する。

### 1.1 目的

FF evaluator では以下の問いに答えられなかった：

1. D_ff が大きい DAG でも、**並列測定**で FF 待ちを隠蔽できるのか？
2. **発行幅 W** を増やすとスループットの改善はどこで頭打ちになるか？
3. **スケジューリングポリシー**（in-order vs OoO）で実効性能はどれだけ変わるか？
4. 既存コントローラ仕様で、どの構成なら実行可能か？

### 1.2 手法

FF evaluator が生成した 85 件の依存 DAG（QAOA/QFT/VQE, H=4-10, Q=16-100）に対して、以下のパラメータを全組み合わせ（240 構成 × 85 DAG = **20,400 シミュレーション**）でスイープした。データセットの大半は seeds 0-4 だが、QAOA H=6,Q=36 には pilot として seeds 5-9 も含まれる。
加えて、common coupled subset に対する保守 sweep として `next_cycle + finite ff_width` を **10,800 runs**、`finite meas_width` を **1,440 runs** 実行した。

| パラメータ | 探索値 |
|---|---|
| 発行幅 W | 1, 2, 4, 8, 16 |
| 測定レイテンシ L_meas | 1, 2, 3 cycles |
| FF 計算レイテンシ L_ff | 1, 2, 3, 5 cycles |
| スケジューリングポリシー | ASAP, Layer, GreedyCritical, Random |

シミュレータは XQ-simulator と同じ **2相ロックステップ**（transfer→update→tick）アーキテクチャを採用し、以下の抽象パイプラインをモデル化した：

```
Ready Queue → [Issue: W nodes/cyc] → [Measurement: L_meas cyc] → [FF Processor: L_ff cyc] → Done
     ↑                                                                                        │
     └──────────────── dependency resolution (FF 結果による依存解放) ──────────────────────────┘
```

本レポートの主要図と主要表は、**比較条件を揃えた common coupled subset**  
`(H,Q) = (4,16), (6,36), (8,64)` × seeds `0-4` を用いる。これにより、アルゴリズム間比較で H/Q の混在を避ける。

また、ここで報告する sweep は以下の **baseline model** に基づく：

- FF 完了で依存が解けたノードは **same-cycle release** される
- Measurement 段と FF 段の **stage width は unlimited**
- 段間バッファは **容量無限**

したがって、本章の主要結果は「楽観的ベースライン」であり、有限 FF 幅・有限測定幅・next-cycle release を入れた保守モデルとは分けて読む必要がある。保守モデルの確認は 2.6 節と 2.7 節で別途行う。

## 2. 主要結果

### 2.1 発見 1: baseline model では FF ストールは小さい

最も重要な発見は、**common coupled subset の baseline model では**、OneAdapt が生成する依存 DAG は D_ff に比べて十分な横幅を持ち、中央値ベースでは FF ストールが小さいことである。

**基本構成（W=1, L_meas=1, L_ff=1, ASAP）でのストール率：**

| アルゴリズム | ストール率（中央値） | スループット（中央値） |
|---|---|---|
| QAOA | 0.12% | 0.998 nodes/cyc |
| QFT | 0.03% | 1.000 nodes/cyc |
| VQE | 0.08% | 0.998 nodes/cyc |

W=1（毎サイクル 1 測定しか発行できない最も保守的な構成）でも、中央値ではストール率は 0.13% 未満である。これは D_ff = 34-317 であっても、各トポロジカルレベルに独立ノードが十分残るケースが多いことを示す。

ただし、これは **中央値の傾向** であって、全ケースでストールが無視できるという意味ではない。小規模 QAOA などには 10% 超の stall case もあり、以下の結論は「baseline model の中央値傾向」として読むべきである。

### 2.2 発見 2: W を増やすとスループットは伸びるが、QAOA は早く飽和する

**ASAP, L_meas=1, L_ff=1 でのスループット：**

| W | QAOA | QFT | VQE |
|---|---|---|---|
| 1 | 0.998 | 1.000 | 0.998 |
| 2 | 1.988 | 1.996 | 1.991 |
| 4 | 3.933 | 3.958 | 3.939 |
| 8 | 7.183 | 7.631 | 7.579 |
| 16 | 10.025 | 13.358 | 13.224 |

W=8 までは 3 アルゴリズムとも概ね良好に伸びるが、W=16 では差が顕著になる。特に common coupled subset では、QAOA の利用率が **62.7%** まで低下する一方、QFT/VQE は **83.5% / 82.7%** を維持する。

したがって、W 拡張の効果はアルゴリズム依存である。QAOA は W=8 付近から収穫逓減が強く、QFT/VQE はより広い issue 幅を有効利用できる。

### 2.3 発見 3: GreedyCritical（OoO）は stall を大きく下げるが throughput 改善は小さい

**W=4, L_meas=1, L_ff=2 でのポリシー比較：**

| ポリシー | QAOA スループット | QAOA ストール率 | QFT スループット | QFT ストール率 |
|---|---|---|---|---|
| ASAP | 3.815 | 2.49% | 3.897 | 1.29% |
| Layer | 3.592 | 2.58% | 3.759 | 1.53% |
| **GreedyCritical** | **3.966** | **0.49%** | **3.950** | **0.25%** |
| Random | 3.828 | 2.09% | 3.888 | 1.28% |

GreedyCritical（残りクリティカルパスが最も長いノードを優先する OoO ポリシー）は、ASAP に対してストール率を **およそ 1/5〜1/3** に削減する。ただし throughput 自体の改善は数 % 程度に留まる。

**Layer は最も性能が低い**。同一トポロジカルレベルのノードしか発行しないため、レベル末尾で発行幅を埋められないサイクルが増える。

### 2.4 発見 4: 深いパイプラインでは初めて stall が支配的になる

**最悪条件（W=16, L_meas=3, L_ff=5, ASAP）：**

| アルゴリズム | スループット | ストール率 | 利用率 |
|---|---|---|---|
| QAOA | 2.607 | 72.4% | 16.3% |
| QFT | 4.456 | 63.4% | 27.9% |
| VQE | 4.423 | 60.1% | 27.6% |

W=16 と大きな発行幅を想定しても、パイプラインレイテンシが長い（L_meas+L_ff = 8 cycles）場合、stall rate は 60-70% に達する。つまり、W を増やすだけでは深いパイプラインを打ち消せない。

**設計含意**: issue 幅の拡大を有効に使うには、L_meas + L_ff を短く保つ必要がある。W=4 は有望な開始点だが、ここではまだ「最適値」とまでは主張しない。

### 2.5 発見 5: アルゴリズム間の DAG トポロジ差

以下は baseline sweep の定性的まとめである：

| 特性 | QAOA | QFT | VQE |
|---|---|---|---|
| DAG の形状 | 「狭く深い」 | 「中間的」 | 「広いがケース依存」 |
| W=16 利用率（common subset） | 62.7% | 83.5% | 82.7% |
| W のスケーラビリティ | W=8 付近から逓減 | W=16 まで有効 | W=16 まで概ね有効 |
| ストール感度（L_ff） | 中 | 中 | 中 |

QAOA は W 拡張に対して最も早く飽和する。QFT/VQE はより広い DAG 幅を持ち、広い issue 幅の恩恵を受けやすい。

### 2.6 保守モデルでの sanity check: `next_cycle` と有限 `ff_width`

baseline model の結論が楽観仮定に依存しすぎていないかを確認するため、common coupled subset に対して追加の保守 sweep を行った。追加した仮定は以下である。

- 依存解放は **next-cycle release**
- FF Processor の受理幅は **有限**（`ff_width ∈ {1,2,4,8}`）

結果は `results/summary/sweep_conservative_common.csv` と `aggregated_conservative_common.csv` に保存した。
対応する可視化として、**Figure 6** に `ff_width = W` のときの baseline / conservative の対応、**Figure 7** に `ff_width < W` の underprovisioning penalty を示す。

代表条件 `W=4, L_meas=1, L_ff=2, ASAP` では、

| アルゴリズム | baseline | next-cycle, `ff_width=∞` | next-cycle, `ff_width=2` |
|---|---|---|---|
| QAOA | 3.815 nodes/cyc, stall 2.49% | 3.608, 4.25% | 1.962, 7.52% |
| QFT | 3.897 nodes/cyc, stall 1.29% | 3.818, 2.76% | 1.978, 1.58% |
| VQE | 3.869 nodes/cyc, stall 1.19% | 3.801, 2.35% | 1.970, 0.91% |

ここから分かることは 2 つある。

1. **next-cycle release 単独の影響は中程度**であり、W=4 では throughput は 2-6% 程度しか落ちない。したがって、baseline の主要傾向は完全には崩れない。
2. **有限 `ff_width` の影響は大きい**。特に `ff_width < W` になると throughput は大きく落ちる。W=4 では `ff_width=2` でほぼ半減し、W=8 でも `ff_width=4` で同様の傾向が出る。

一方で、`ff_width = W` のときは `ff_width=∞` と同等の結果になった。これは、**無限 FF 幅は不要だが、FF Processor は少なくとも issue 幅に見合う受理能力を持つべき**ことを示している。

特に QAOA は `W=8, GreedyCritical` において next-cycle release の影響を強く受け、throughput が `6.96 → 5.24 nodes/cycle` に低下した。したがって、QAOA は FF wake-up timing に最も敏感なアルゴリズムである。

### 2.7 保守モデルでの追加確認: 有限 `meas_width` と backpressure 指標

さらに common coupled subset に対して、measurement 段の受理幅を有限化した保守 sweep を追加した。
結果は `results/summary/sweep_conservative_meas_common.csv` と
`aggregated_conservative_meas_common.csv` に保存し、**Figure 8** に `ff_width` と
`meas_width` の underprovisioning penalty を並べて示す。

代表条件 `next_cycle, L_meas=1, L_ff=2` では、

- `W=4, ASAP` の QAOA で `ff_width=1` は throughput 比 `0.444`、`meas_width=1` も `0.444`
- 同じ条件の QFT/VQE でも、`1/2 W` と `1/4 W` の throughput penalty は `ff_width` と `meas_width` でほぼ一致
- `W=8, GreedyCritical` でも QFT は `ff_width=4` で `0.826`、`meas_width=4` で `0.858`、VQE は `0.810` と `0.955` の範囲にあり、measurement 側 underprovisioning も無視できない

重要なのは、**throughput 低下の大きさに対して stall_rate の見え方が非対称**な点である。
たとえば `W=4, ASAP` の QAOA では `ff_width=1` と `meas_width=1` の throughput 比はいずれも `0.444` だが、
stall 率は `19.6%` と `0.93%` で大きく異なる。measurement 段の詰まりは ready queue の空転よりも
front-end backpressure として現れるため、**有限 stage width の評価では stall_rate 単独では不十分で、throughput を主指標に置く必要がある**。

## 3. 静的 FF budget との対照（FF evaluator からの参照）

本節は **pipeline simulator の動的結果ではない**。FF evaluator の静的指標 `D_ff(raw)` / `D_ff(shifted)` から計算した per-stage FF budget を、既存 controller 仕様と対照した参考情報である。

**τ_ph = 1 μs の場合の代表 budget：**

| ケース | D_ff(raw) budget | D_ff(shifted) budget | OPX (250ns) | XCOM (185ns) |
|---|---|---|---|---|
| QAOA (common subset) | 7.0–29.4 ns | 500 ns | OK | OK |
| QFT H=4,Q=16 | 13.0 ns | 125–142.9 ns | NG | NG |
| QFT H=8,Q=64 | 3.2 ns | 32.3–37.0 ns | NG | NG |
| VQE (common subset) | 10.1–66.7 ns | 1000 ns | OK | OK |

ここから言えるのは、`signal_shift` は **QAOA/VQE の静的 FF budget を大きく緩和する有望な最適化**だという点である。一方 QFT は、H=4 の shifted case でも `125–142.9 ns`、H=8 では `32–37 ns` に留まり、**OPX/XCOM ではなお不十分**である。

したがって、「shifted なら controller feasible」と言えるのは現時点では **QAOA/VQE の静的 budget 文脈** に限られる。shifted DAG 上の動的 throughput/stall は未シミュレーションである。

## 4. 統合的な設計指針

本シミュレータと FF evaluator の結果を統合すると、以下の設計指針が得られる：

### 4.1 signal_shift は高優先の静的最適化候補

signal_shift なしでは raw FF budget が数 ns〜数十 ns に留まり、既存 controller では厳しい。QAOA/VQE では signal_shift により budget が 500–1000 ns 級まで緩和されるため、**controller/co-compiler co-design の優先候補**と見なせる。

### 4.2 baseline model では issue 幅が支配的だが、これは楽観条件つき

short-latency 条件（L_meas=1, L_ff=1〜2）では、common subset の中央値ベースで FF stall は小さく、W 拡張の効果が大きい。ただしこれは same-cycle release・unlimited stage width を置いた **optimistic baseline** である。保守 sweep の結果、next-cycle release 単独の影響は中程度だが、`ff_width < W` は throughput を大きく落とすことが分かった。

### 4.3 推奨マイクロアーキテクチャ

| パラメータ | 推奨値 | 根拠 |
|---|---|---|
| W（発行幅） | 4 を開始点 | W=4 で既に高い throughput が得られる。最適値の主張にはコストモデルが必要 |
| L_meas | 1-2 | 深い測定レイテンシは stall を急増させる |
| L_ff | 1-2 | L_ff を短く保つほど W 拡張の効果が維持される |
| meas_width / ff_width | `W` 以上 | `ff_width < W` と `meas_width < W` はいずれも throughput を大きく落とす |
| Policy | ASAP または GreedyCritical | GreedyCritical は stall 改善に有効。実装コストを抑えるなら ASAP でも baseline 性能は悪くない |

### 4.4 アルゴリズム別の注意点

- **QAOA**: W 拡張に最も早く飽和する。signal_shift の静的効果は大きいが、shifted DAG の動的評価は未実施。
- **QFT**: raw/shifted のいずれでも static FF budget が厳しい。signal_shift だけでは controller feasibility に届かない。
- **VQE**: QAOA より広い issue 幅を活かしやすい。signal_shift の静的効果も大きい。

## 5. 手法の限界と今後の課題

### 5.1 現在のモデルの仮定

- **即時スケジューリング**: Ready Queue への追加とノード選択が 0 サイクルで完了する仮定。実際のハードウェアではスケジューラ自体にレイテンシがある。
- **same-cycle release**: FF 完了で解放された依存ノードを同一サイクルに issue 可能とする楽観仮定。
- **無限 stage width / 無限バッファ**: baseline model では MeasurementUnit と FFProcessor の受理幅・段間キュー容量に制限がない。保守 sweep で有限 `ff_width` / `meas_width` は部分的に確認したが、有限バッファは未導入である。
- **Raw DAG のみ**: signal_shift 後の DAG トポロジでのシミュレーションは未実施。shifted DAG の並列度プロファイルは今後の分析対象。
- **理想グラフ状態**: Fusion 失敗によるグラフ構造の変化は未モデル化。
- **stall_rate の意味**: 現在の stall は ready queue 空転に基づくため、measurement 側の backpressure を十分に表さない。有限 stage width の研究では throughput も必須指標である。

### 5.2 今後の拡張

1. **shifted DAG の動的シミュレーション**: shifted edges を保存し、shifted DAG で throughput/stall を比較
2. **backpressure 指標の拡張**: `issue_blocked_rate` など、measurement 側詰まりを直接表す統計の導入
3. **バッファサイズ制約の導入**: 有限バッファモデルによるバックプレッシャの影響評価
4. **Fetch/Decode レイテンシの導入**: フロントエンド遅延が QAOA の感度にどう効くかを調べる
5. **RTL との突き合わせ**: Verilog チームの RTL 実装結果とサイクル数を比較検証

## 6. 実装詳細

### 6.1 プロジェクト構成

```
research/mbqc_pipeline_sim/
├── src/mbqc_pipeline_sim/
│   ├── domain/models.py      # PipelineConfig, SimDAG, SimResult, CycleRecord
│   ├── domain/errors.py      # InvalidArtifactError, SimulationDeadlockError
│   ├── core/
│   │   ├── simulator.py      # MbqcPipelineSimulator（メインループ）
│   │   ├── scheduler.py      # ASAP, Layer, GreedyCritical, Random
│   │   ├── pipeline_stage.py # LatencyPipeline（固定レイテンシ + stage width）
│   │   └── dag_analysis.py   # トポロジカルレベル、ILP 分析
│   ├── adapters/
│   │   ├── artifact_loader.py # FF evaluator JSON → SimDAG
│   │   └── csv_writer.py     # SimResult → CSV
│   └── cli/{run,sweep,aggregate,plot}.py
├── tests/ (18 tests, all passing)
└── results/
    ├── summary/sweep.csv                    (20,400 rows, optimistic baseline)
    ├── summary/aggregated.csv              (3,840 groups)
    ├── summary/sweep_conservative_common.csv
    ├── summary/aggregated_conservative_common.csv
    ├── summary/sweep_conservative_meas_common.csv
    ├── summary/aggregated_conservative_meas_common.csv
    └── figures/ (10 figure files, PNG + PDF)
```

### 6.2 XQ-simulator との対応

本シミュレータは XQ-simulator の設計パターンを踏襲している：
- **2相ロックステップ**: transfer（依存解決 + 配線）→ update（パイプライン進行）→ tick（サイクル更新）
- **LatencyPipeline**: XQ-simulator の `buffer.py`（valid/ready）に相当する固定レイテンシキュー
- **統計収集**: `unit_stat_sim` に相当する `CycleRecord` で毎サイクルの発行数・Ready Queue サイズ・in-flight 数を記録

## 7. まとめ

本シミュレータによって、以下が定量的に示された：

1. **baseline model の中央値では** OneAdapt 生成 DAG は高並列であり、FF 依存ストールは小さい
2. **baseline model では** W 拡張の効果が大きく、QAOA は QFT/VQE より早く飽和する
3. **GreedyCritical（OoO）は stall を 1/5〜1/3 に下げる** — ただし throughput 改善は小さい
4. **保守モデルでも主要傾向は残る** が、QAOA は next-cycle release に敏感である
5. **stage width は issue 幅に見合う受理能力が必要** — `ff_width < W` でも `meas_width < W` でも throughput が大きく落ちる
6. **signal_shift は QAOA/VQE の static FF budget を大幅に緩和するが、QFT にはなお不十分**

現時点で RTL チームへ渡せる最も堅いメッセージは、「W=4 は有望な開始点」「short-latency path を優先すべき」「`ff_width` と `meas_width` は issue 幅を下回らないように設計すべき」「QAOA と QFT/VQE では width sensitivity が異なる」である。
