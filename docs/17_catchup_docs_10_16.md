# Docs 10-16 Catch-up Guide

## この資料の目的

本資料は、`docs/10` から `docs/16` までに書かれている内容を、
「研究全体として今どこまで進んでいるか」という観点で一気に追えるように整理した catch-up 用資料である。

想定読者は、

- 途中経過を細かく追えていない自分
- 発表準備の前に全体像をつかみたい自分
- 他人にこの研究を説明する前に、自分の理解を揃えたい自分

である。

ここでは、各 doc の中身をそのまま要約するのではなく、

1. 研究の出発点
2. 何を作ったか
3. どんな問いを立てたか
4. 何が分かったか
5. 何が未解決か

の順に再構成する。

## まず 30 秒で全体像

この研究は、光 MBQC における古典制御の難しさを、

- **静的解析**
- **動的シミュレーション**
- **controller co-design**

の 3 段で調べている。

大きな流れはこうである。

1. `docs/10`
   - OneAdapt のコンパイル結果から、FF 依存深さ `D_ff` を新しく定義して評価した
2. `docs/11`
   - その依存 DAG を入力にして、パイプライン性能を動的にシミュレートした
3. `docs/12`
   - ここまでの成果を、研究としてどういう意味があるかという観点で整理した
4. `docs/13`
   - `signal_shift` により static 改善が dynamic 改善につながるかを raw vs shifted で直接比較した
5. `docs/14`
   - そこから「compiler optimization だけではなく controller も co-design すべき」という方針を立てた
6. `docs/15`
   - 実際に shifted-aware scheduler を実装し、focused な比較実験を回した
7. `docs/16`
   - 今後の co-design 実行計画を整理した

つまり、研究の流れは

**FF の静的な厳しさを測る**
→ **動的に見ると何が起こるかを調べる**
→ **shifted DAG を使うと状況がどう変わるかを見る**
→ **controller 側の設計まで踏み込む**

という段階を踏んで進んでいる。

## 各 doc の役割

### `docs/10_ff_evaluator_report.md`

役割:

- 研究の最初の柱
- OneAdapt コンパイル出力から古典制御制約をどう定量化するかを示した

この doc の本質:

- `D_ff` という新指標を導入した
- `D_ff` から `t_ff_crit = τ_ph / D_ff` を計算し、
  「古典制御装置に何 ns 必要か」を出せるようにした

重要な結果:

- `D_ff` は Q にほぼ線形にスケール
- 係数はアルゴリズム依存
  - VQE ≈ 1
  - QAOA ≈ 2.2
  - QFT ≈ 5
- ハードウェアサイズ `H` を増やしても `D_ff` は改善しない
- `signal_shift` は QAOA / VQE の `D_ff` を劇的に削減する
- QFT は `signal_shift` をかけても依然として厳しい

この段階で分かったこと:

- 光 MBQC の問題は、単に「光子を長く保持する」ことではなく、
  **古典制御の逐次依存が深い**ことにもある
- しかもその深さはアルゴリズム依存である

### `docs/11_pipeline_sim_report.md`

役割:

- 研究の第二の柱
- 静的な `D_ff` だけでは見えない動的性能を調べた

この doc の本質:

- 依存 DAG を入力にして、MBQC 制御パイプラインのサイクル精度シミュレータを作った
- 発行幅、測定レイテンシ、FF レイテンシ、スケジューリング policy を変えながら、
  throughput / stall / utilization を評価した

重要な結果:

- baseline model では stall は中央値では小さい
- issue 幅 `W` を増やすと throughput は伸びる
- ただし QAOA は早く飽和する
- `GreedyCritical` は stall をかなり下げるが throughput 改善は小さい
- 深いパイプラインでは初めて stall が支配的になる
- finite `ff_width` や `meas_width` を入れると、throughput が大きく落ちる

この段階で分かったこと:

- 静的に `D_ff` が大きくても、動的には並列性で隠蔽できる場合がある
- 逆に、幅やレイテンシの条件次第では一気に性能が悪化する

### `docs/12_research_progress_report.md`

役割:

- `10` と `11` の結果を研究ストーリーとして接続した中間整理

この doc の本質:

- FF evaluator と pipeline simulator を統合すると、
  光 MBQC の古典制御制約は
  - dependency
  - hold
  - measurement delay
  - pipeline width / scheduling
  の相互作用として理解すべきだと整理した

この doc を読む意味:

- 研究の初期フェーズで「何ができるようになったか」を把握できる
- 後続の `13-16` が何を拡張したのかを理解しやすくなる

### `docs/13_shifted_dag_dynamic_report.md`

役割:

- `signal_shift` の効果を static だけでなく dynamic まで持っていく

この doc の本質:

- raw DAG と shifted DAG を直接比較した
- 「static で改善したら dynamic でも改善するのか？」を検証した

対象:

- algorithm: `QAOA`, `QFT`, `VQE`
- common coupled subset:
  - `(H,Q) = (4,16), (6,36), (8,64)`
- seeds: `0..4`
- policy: `asap`, `greedy_critical`
- `issue_width = 4,8`
- `meas_width = W`
- `ff_width = W`
- `l_meas = 1,2`
- `l_ff = 1,2`

重要な結果:

- shifted DAG は throughput を悪化させなかった
- しかし gain は一様ではなかった
- `QAOA` と `QFT` は比較的 gain が大きい
- `VQE` は static 改善が大きくても dynamic gain は小さい
- `issue_width=8, meas_width=8, ff_width=4` に stall 悪化条件が集中した

この段階で分かったこと:

- **static improvement != dynamic improvement**
- 問題は shifted DAG 自体ではなく、
  それをどんな controller 条件で流すかにある

### `docs/14_shifted_dag_controller_codesign_plan.md`

役割:

- `13` の結果を受けて、co-design を主テーマに据えた方針書

この doc の本質:

- compiler optimization の効果は controller regime に依存する
- shifted DAG に最適な controller policy は raw DAG 向け policy と同じとは限らない
- よって compiler と controller は分離ではなく co-design すべき

ここで立てた問い:

- shifted DAG に対して既存 policy は本当に最適か
- どの regime で dynamic gain が強く、どこで頭打ちになるか
- stall regression は scheduling choice で軽減できるか

この doc は、
「次は co-design に進むべきだ」という研究上の方向付けをした文書である。

### `docs/15_controller_codesign_progress_report.md`

役割:

- 実際に co-design 実装を進めた結果のレポート

この doc の本質:

- scheduler layer を型付きで再設計した
- `shifted_critical`
- `stall_aware_shifted`
- `regime_switch`

を実装し、focused な `W8` 実験を回した

使うべき主結果:

- `W8_M8_F4` では raw/shifted 比較で stall regression が見えた
- `stall_aware_shifted` はその regression を反転できた
- ただし algorithm ごとに trade-off があった
  - QAOA/QFT では有望
  - VQE では throughput gain を削りやすい

重要な結果ディレクトリ:

- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/shifted_policy_comparison_w8_focus/`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/regime_switch_w8_focus/`

この段階で分かったこと:

- controller 側の policy は本当に効く
- ただし universal winner はまだない

### `docs/16_controller_codesign_execution_plan.md`

役割:

- co-design の実装・実験・評価の順序を決めた実行計画書

この doc の本質:

- どこで成功/失敗を判定するか
- どこまでを focused sweep で見て、どこから full comparison に広げるか
- policy をどう増やすか
- 再現性をどう守るか

特に重要な点:

- 明確に下位互換と示せない限り既存 policy を上書きしない
- 改良版 heuristic は別 policy 名で追加する

このルールに基づいて、その後

- `regime_switch_refined`
- `stall_aware_shifted_refined`

のような version 分離を行っている。

## 研究の時系列

### フェーズ 1: 静的制約の可視化

対応 doc:

- `10`

やったこと:

- `D_ff` を定義
- budget 化
- `signal_shift` の static 効果を確認

得た主張:

- FF 制約はアルゴリズム依存
- `signal_shift` は静的にはかなり効く

### フェーズ 2: 動的性能の評価

対応 doc:

- `11`
- `12`

やったこと:

- cycle-accurate simulator を作成
- baseline / conservative な controller 条件をスイープ

得た主張:

- static 指標だけでは性能を言い切れない
- width / latency / policy が dynamic に効く

### フェーズ 3: raw vs shifted の直接比較

対応 doc:

- `13`

やったこと:

- shifted DAG を artifact として保存
- raw / shifted を同条件で比較

得た主張:

- shifted は基本的に throughput を悪化させない
- ただし gain は regime dependent
- stall regression が一部条件で起きる

### フェーズ 4: controller co-design

対応 doc:

- `14`
- `15`
- `16`

やったこと:

- shifted-aware scheduler を実装
- `W8_M8_F4` を主ターゲットに focused sweep
- `regime_switch` や refined variants を探索

得た主張:

- policy co-design は意味がある
- ただし 1 policy で全部勝つわけではない
- ff bottleneck regime での specialist policy という見方が有力

## 今この研究で「確立している」と言ってよいこと

この時点で比較的安心して主張できるのは以下である。

1. `D_ff` は有効な static 指標である
2. `signal_shift` は static dependency depth を大幅に削減する
3. その dynamic gain は一様ではなく、controller regime に依存する
4. `W8_M8_F4` は shifted DAG にとって problematic regime である
5. `stall_aware_shifted` 系 policy は、その regime の stall regression をかなり抑えられる

## まだ「探索中」だと思っておくべきこと

まだ確立していない、あるいは本編では補助扱いにすべきなのは以下である。

1. `regime_switch` が universal に強いか
2. refined variants が常に旧版より良いか
3. QFT H8/Q64 の欠損原因
4. 全 regime に共通する単一最強 policy の存在

つまり、今の主張は

**co-design は必要**

までは強く言えるが、

**これが最終解の policy である**

とはまだ言わない方がよい。

## 今見るべき結果と、今は見なくてよい結果

### 今見るべきもの

- `docs/10`
- `docs/11`
- `docs/13`
- `docs/15`
- `docs/16`

結果ファイルとしては:

- `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv`
- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/shifted_policy_comparison_w8_focus/summary/comparison.csv`
- 必要なら
  - `regime_switch_w8_focus`
  - `stall_aware_refined_w8_focus`

### 今は深追いしなくてよいもの

- exploratory な analysis CSV を全部読むこと
- `regime_switch_refined` の細かい差分
- `QFT H8/Q64` 欠損の技術詳細

## まず何から読めばよいか

時間別のおすすめ読順は以下。

### 15 分で追う

1. この資料
2. `docs/13`
3. `docs/15`

### 1 時間で追う

1. この資料
2. `docs/10`
3. `docs/11`
4. `docs/13`
5. `docs/15`

### 発表準備レベルで追う

1. この資料
2. `docs/10`
3. `docs/11`
4. `docs/13`
5. `docs/14`
6. `docs/15`
7. `docs/16`

## 最後に一言で言うと

`docs/10-16` の流れを一言でまとめると、

**光 MBQC の古典制御制約を、静的な FF 深さ評価から始めて、動的シミュレーションに拡張し、最終的に shifted DAG を前提にした controller co-design の問題として再定義した**

という研究である。

いま自分が把握すべき中心メッセージはこれで十分である。
