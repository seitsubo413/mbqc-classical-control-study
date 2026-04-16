# Shifted-DAG-Aware Controller Co-Design Plan

## Positioning

本計画は、`docs/13_shifted_dag_dynamic_report.md` で得た結果を次の研究段階へ進めるための方針書である。

現時点で確認できていること:

- `signal_shift` は static depth を大きく削減する
- その dynamic gain は algorithm / width / latency / policy / raw stall / saturation に依存する
- `issue_width=4` では width 条件が実質 inactive なケースが多い
- `issue_width=8` では width 条件が dynamic gain に効き始める
- `W8_M8_F4` では throughput が改善しても stall だけ悪化する条件がある

この結果から、次の主テーマは **compiler optimization と controller policy を別々に最適化するのではなく、shifted DAG を前提に co-design すること** に置く。

## Main Research Theme

**Shifted-DAG-aware controller co-design**

### Core Question

`signal_shift` 済み DAG に対して、既存の `ASAP` / `GreedyCritical` をそのまま使うのが最適なのか。それとも shifted DAG の構造変化に合わせて controller-side の scheduling / width usage / release policy を再設計する必要があるのか。

### Target Message

- compiler optimization の効果は controller regime に依存する
- shifted DAG に最適な controller policy は raw DAG 向け policy と一致しない
- compiler と controller は分離最適化ではなく co-design すべきである

## Supporting Themes

主テーマを成立させるために、以下の副テーマを最小限で並行して扱う。

### 1. Dynamic Gain Predictor

目的:

- shifted DAG が効く条件を事前に予測できるようにする

現在使える特徴:

- `raw_stall_bucket`
- `raw_saturation_bucket`
- `policy`
- `latency_profile`
- `width_profile`

役割:

- 新しい shifted-aware policy が「どの regime に効くか」を説明する基盤
- 実験条件を無差別に増やさず、狙うべき regime を選ぶための指針

### 2. Regime Map

目的:

- dynamic gain が大きい領域と小さい領域を整理する

現時点の重要な観察:

- `issue_width=4` では width 条件が inactive
- `issue_width=8` では `meas_width` / `ff_width` の影響が顕在化
- high stall / non-saturated regime で gain が大きい
- saturated regime では static improvement が dynamic gain に乗りにくい

役割:

- co-design の評価軸を明確にする
- 新 policy の有効範囲を可視化する

### 3. QFT H8/Q64 Failure Analysis

目的:

- shifted payload が欠損する large-instance failure の原因を切り分ける

役割:

- co-design の前提条件ではない
- ただし最終的な研究の適用限界を示すうえで重要

扱い:

- 主テーマの後方支援タスクとして進める
- 初期フェーズでは深入りしない

## Research Questions

### RQ1

shifted DAG に対して、既存 policy (`ASAP`, `GreedyCritical`) の優劣は raw DAG の場合と同じか。

### RQ2

shifted DAG の dynamic gain は、どの regime で最も強く、どの regime では頭打ちになるか。

### RQ3

raw stall / saturation / width imbalance を考慮した shifted-aware scheduling heuristic は、既存 policy を上回るか。

### RQ4

stall regression (`W8_M8_F4` など) は scheduling choice によって軽減できるか。

## Current Evidence To Build On

利用可能な既存 output:

- dynamic comparison:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/comparison.csv`
- seed-level paired effects:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/summary/analysis/paired_seed_effects.csv`
- regime summaries:
  - `algorithm_summary.csv`
  - `algorithm_hq_summary.csv`
  - `policy_latency_summary.csv`
  - `policy_saturation_summary.csv`
  - `policy_width_summary.csv`
  - `policy_stall_summary.csv`
- special analyses:
  - `width_equivalence_summary.csv`
  - `stall_regression_summary.csv`
  - `gain_predictor_summary.csv`

今すぐ使える強い事実:

- `issue_width=4` は全 algorithm / 全 policy で width inactive
- `issue_width=8` では width condition が active
- stall regression は主に `W8_M8_F4` に集中
- saturated regime では `GreedyCritical` の zero-gain が増えやすい

## Research Strategy

### Phase 1. Baseline Clarification

目的:

- raw/shifted 差だけでなく、policy/regime 差を整理して baseline を固める

やること:

1. `gain_predictor_summary.csv` を使って gain-rich regime / gain-poor regime を定義する
2. `width_equivalence_summary.csv` を使って width-sensitive regime を切る
3. `stall_regression_summary.csv` を使って problematic regime を切る

完了条件:

- controller redesign の標的 regime が明示される
- “どこで改善余地があるか” が数値で整理される

### Phase 2. Shifted-Aware Heuristic Design

目的:

- shifted DAG 向けの新 heuristic を 1-2 個作る

最初の候補:

1. **ShiftedCritical**
   - shifted DAG の remaining depth を優先
   - raw criticality ではなく shifted topology を基準に priority を付与

2. **StallAwareShifted**
   - `ff_width` が詰まりやすい条件で ff 依存の密集を避ける priority を導入
   - `W8_M8_F4` の stall regression 対策を主眼に置く

3. **RegimeSwitch**
   - width / backpressure regime に応じて `asap`, `shifted_critical`, `stall_aware_shifted` を切り替える
   - まずは学習器ではなくルールベースで始める

完了条件:

- 既存 policy と比較可能な新 policy が実装される
- CLI で policy として選択できる

### Phase 3. Controlled Comparison

目的:

- new policy vs existing policy を shifted DAG で比較する

基本比較:

- DAG variant:
  - raw
  - shifted
- policy:
  - `asap`
  - `greedy_critical`
  - `shifted_critical` (新規)
  - `stall_aware_shifted` (候補)

優先 regime:

- `issue_width=8`
- `meas_width=8`
- `ff_width=4,8`
- `l_meas=1,2`
- `l_ff=1,2`

理由:

- width sensitivity が現れるのが `W=8`
- stall regression が観測されるのが主に `W8_M8_F4`

完了条件:

- shifted-aware policy が既存 policy を上回る条件を示せる
- 逆に上回らない条件も説明できる

### Phase 4. Failure / Limit Analysis

目的:

- QFT large-instance とその他 failure mode を整理する

やること:

1. `QFT H8/Q64` shifted payload 欠損の再現
2. graph size / density / edge pattern の比較
3. minimum reproducible failure の抽出

位置づけ:

- mainline 実験の blocker ではない
- 論文や発表で “適用限界” を述べるための補助分析

## Concrete Implementation Tasks

## Scheduler Architecture Baseline

co-design 実装は、既存 simulator に policy-specific な条件分岐を増やす形では進めない。
その代わり、scheduler layer を以下の責務で分離する。

### Design Principles

- **Single Responsibility**
  - simulator は cycle progression のみ担当する
  - feature builder は runtime state から scheduler input を構築する
  - scheduler policy は node selection のみ担当する
- **Open/Closed**
  - policy 追加時に simulator 本体の条件分岐を増やさない
  - registry に factory を登録するだけで拡張できるようにする
- **Dependency Inversion**
  - simulator は具体 scheduler 実装ではなく policy port に依存する
- **Typed Context**
  - policy 間の入出力は `dict` ではなく dataclass と Protocol で表現する

### Current Scheduler Architecture

基盤として以下の型とレイヤを導入済み:

- `domain/scheduler_models.py`
  - `ReadyNodeView`
  - `SchedulerContext`
  - `SchedulerDecision`
- `ports/scheduler_policy.py`
  - `SchedulerPolicyPort`
  - `SchedulerFactory`
- `core/scheduler_features.py`
  - ready set と runtime state から `SchedulerContext` を組み立てる pure helper
- `core/scheduler_registry.py`
  - `SchedulingPolicy -> factory` の registry
- `core/scheduler.py`
  - 既存 policy (`ASAP`, `Layer`, `GreedyCritical`, `Random`) の実装
- `core/simulator.py`
  - scheduler へ `SchedulerContext` を渡し、`SchedulerDecision` を受け取る orchestrator

### Extension Rule

新 policy は以下を守る:

1. `SchedulerPolicyPort` を満たす
2. `SchedulerContext` だけを入力にする
3. `SchedulerDecision` だけを返す
4. simulator の cycle logic や queue mutation に直接触れない

### Next Step On This Architecture

この基盤の上に、次に以下を実装する:

- `shifted_critical`
- `stall_aware_shifted`
- 必要なら `regime_switch`

これらはすべて、既存 registry に追加するだけで CLI / sweep から選択できる形に保つ。

### Simulator / Scheduler

対象:

- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/enums.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/cli/run.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/cli/sweep.py`

やること:

1. `SchedulingPolicy` に shifted-aware policy を追加
2. shifted DAG の topo / remaining depth を直接使う priority 実装を追加
3. width imbalance を考慮する stall-aware heuristic を追加

### Analysis

対象:

- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/analysis/shifted_study.py`

やること:

1. new policy 向け summary を同じ分析 pipeline に統合
2. regime-based comparison を再利用可能に保つ
3. predictor を rule export できる形に整える

### Testing

対象:

- `research/mbqc_pipeline_sim/tests/`

やること:

1. policy 単体テスト
2. synthetic DAG での heuristic behavior test
3. shifted/raw 両方での regression test

## Experiment Priorities

### High Priority

1. `issue_width=8` の shifted-aware policy 比較
2. `W8_M8_F4` stall regression の改善確認
3. high-stall / active regime での throughput gain 上積み

### Medium Priority

1. saturated regime で zero-gain をどこまで崩せるか
2. `ASAP` と `GreedyCritical` の regime-dependent switching

### Low Priority

1. `issue_width=4` の追加探索
2. exhaustive parameter expansion

理由:

- `issue_width=4` は width inactive なので、co-design の主戦場ではない

## Expected Deliverables

### Short-Term

- shifted-aware scheduling policy 1 本
- controlled comparison CSV / figure
- `W8_M8_F4` regression の説明

### Medium-Term

- shifted-aware scheduling policy 2 本目
- regime-switch policy の rule table
- regime map の更新版

### Long-Term

- compiler-controller co-design の一貫した研究ストーリー
- failure / limit analysis を含めた完成版報告

## Recommended Execution Order

1. `gain_predictor_summary.csv` と `stall_regression_summary.csv` から target regime を固定する
2. `shifted_critical` を最初の新 policy として実装する
3. `issue_width=8` slice だけで小さく sweep する
4. `W8_M8_F4` に効くかを最優先で見る
5. その後に `regime_switch` または `stall_aware_shifted` を試す
6. 最後に `QFT H8/Q64` failure analysis を掘る

## Decision

次回以降の主研究テーマは **Shifted-DAG-aware controller co-design** とする。

ただし、以下を副テーマとして維持する:

- dynamic gain predictor
- regime map
- QFT H8/Q64 failure analysis

優先順位は以下:

1. shifted-aware policy の設計と比較
2. gain-rich / gain-poor regime の整理
3. stall regression の抑制
4. large-instance failure の解析
