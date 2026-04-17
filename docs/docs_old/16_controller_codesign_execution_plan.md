# Controller Co-Design Execution Plan

## Positioning

本書は、`docs/docs_old/14_shifted_dag_controller_codesign_plan.md` の研究方針を、
実装・実験・評価の順序まで落とした実行計画書である。

これは固定仕様書ではない。co-design の性質上、

- policy 実装の途中で仮説が変わる
- 特定 algorithm だけ例外的な挙動が見える
- sweep 結果に応じて priority が変わる

ことを前提とする。

したがって本書の役割は、

- 何を先にやるか
- どこで成功/失敗を判定するか
- どこで方針変更してよいか

を明示することにある。

## Goal

最終的な主張は次の形を目指す。

1. shifted DAG の dynamic benefit は controller policy に強く依存する
2. raw DAG 向け baseline policy は shifted DAG に対して必ずしも最適ではない
3. ff bottleneck regime では shifted-aware controller policy が必要である
4. compiler optimization と controller scheduling は分離ではなく co-design すべきである

## Current Starting Point

現時点で既に揃っているもの:

- raw vs shifted dynamic study
  - `docs/docs_old/13_shifted_dag_dynamic_report.md`
- co-design 方針書
  - `docs/docs_old/14_shifted_dag_controller_codesign_plan.md`
- 今日までの進捗レポート
  - `docs/docs_old/15_controller_codesign_progress_report.md`
- scheduler architecture baseline
  - typed context
  - registry
  - policy port
  - regime/signal helper
- 実装済み policy
  - `asap`
  - `greedy_critical`
  - `shifted_critical`
  - `stall_aware_shifted`
  - `regime_switch`
- 既存 study outputs
  - `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/shifted_policy_comparison_w8_focus/`
  - `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/regime_switch_w8_focus/`

今の理解としては、

- `W8_M8_F4` の stall regression は controller 側でかなり抑えられる
- ただし `VQE` では conservative policy が throughput gain を削りやすい
- よって次の焦点は「stall を下げつつ throughput gain を殺しすぎない policy」にある

## Research Questions For The Next Phase

### RQ1

`stall_aware_shifted` の pressure 制御を滑らかにすると、`VQE` の過剰防御を抑えられるか。

### RQ2

`regime_switch` を width-based dispatcher から pressure-aware dispatcher に進化させると、
`W8_M8_F4` と `W8_M8_F8` を 1 policy で扱えるか。

### RQ3

cycle-local な pressure signal だけで十分か。
それとも ready-set 構造や unlock pattern を使う必要があるか。

### RQ4

algorithm 固有の条件分岐を入れずに、一般的な scheduler signal だけで有効 policy を作れるか。

## Design Principles

今後の実装は以下を崩さない。

### 1. Policy Logic Isolated

- simulator 本体に policy-specific な分岐を入れない
- scheduler は `SchedulerContext -> SchedulerDecision` を守る

### 2. Pure Signal Analysis

- regime 判定や pressure 判定は pure helper に閉じ込める
- heuristic の根拠を CSV / test で直接検証できるようにする

### 3. Typed Data First

- `dict[str, object]` ベースの feature 受け渡しはしない
- dataclass / Enum / Protocol を優先する

### 4. Small Experimental Surface

- まずは `W=8` study slice で比較する
- 有望 policy が見えたら full comparison へ広げる

### 5. Research Traceability

- 新 policy を入れたら
  - test
  - focused sweep
  - aggregated comparison
  - short progress note
  を必ず残す

### 6. Reproducibility Before Replacement

- 既存 policy 実装が明確に下位互換だと示せない限り、上書き置換しない
- 進化版 heuristic は別 policy 名で追加する
- 既存 result namespace と policy 名の対応を壊さない

## Execution Strategy

## Phase A. Stabilize The Current Scheduler Layer

### Objective

agile に作った scheduler 群を、今後さらに policy を足しても壊れにくい状態にする。

### Tasks

1. `scheduler_signals.py` を中心に signal 判定を集約する
2. policy class から閾値判定の重複を外す
3. test を policy 単体 / signal 単体の両方で持つ

### Exit Criteria

- regime 判定が policy から独立している
- signal helper 単体をテストできる
- new policy を増やすときに simulator に触らなくてよい

### Current Status

- ほぼ完了

## Phase B. Improve Pressure-Aware Policy

### Objective

`stall_aware_shifted` と `regime_switch` を、二値 backpressure 対応から連続的 pressure 対応へ進める。

### Tasks

1. `ff_pressure_score` の定義を調整する
   - `waiting_ff_count / ff_width`
   - `in_flight_meas_count / ff_width`
   - `ff_slots_available`
2. `stall_aware_shifted` の issue cap を pressure 強度で滑らかに変える
3. `regime_switch` の閾値を tune する
4. ready-set の `unlock_count` だけでなく `remaining_depth` との trade-off を再調整する

### Expected Outcome

- `QAOA/QFT` の stall 改善を保つ
- `VQE` の throughput 劣化を少しでも戻す

### Exit Criteria

- `W8_M8_F4` で `stall_aware_shifted` 系 policy が baseline stall regression を反転できる
- そのうえで `VQE` の throughput gain が現状より改善する、または悪化理由を説明できる

## Phase C. Add One More General-Purpose Policy

### Objective

pressure-aware regime switch だけで足りない場合に備えて、もう 1 本だけ一般的な heuristic を試す。

### Candidate

`balanced_shifted`

意図:

- `remaining_depth`
- `unlock_count`
- `ff_pressure_score`

を同時に見る中庸 policy。

ポイント:

- algorithm 固有分岐は入れない
- scheduler signal だけで一般化を狙う

### Exit Criteria

- `balanced_shifted` が少なくとも 1 つの problematic regime で `regime_switch` を上回る
- もしくは「追加しても価値が薄い」と判断できるだけの証拠が揃う

## Phase D. Controlled Comparison

### Objective

有望 policy を、既存 baseline と同条件で比較して研究結果に落とす。

### Primary Comparison Set

- policy:
  - `asap`
  - `greedy_critical`
  - `shifted_critical`
  - `stall_aware_shifted`
  - `regime_switch`
  - 必要なら `balanced_shifted`
- DAG variant:
  - `raw`
  - `shifted`
- regime:
  - `issue_width=8`
  - `meas_width=8`
  - `ff_width=4,8`
  - `l_meas=1,2`
  - `l_ff=1,2`

### Secondary Comparison Set

必要なら後で追加する:

- `issue_width=4`
- broader width asymmetry
- release mode の差

### Exit Criteria

- shifted-aware policy がどの regime で優位か言える
- 同時に、効かない regime も整理できる

## Phase E. Analysis And Packaging

### Objective

結果を「実装ができた」ではなく「研究として説明できる」状態へ持っていく。

### Tasks

1. policy × regime summary を追加出力する
2. `stall_reduction` と `throughput_gain` の trade-off を algorithm 別に整理する
3. `regime_switch` が実際にどの regime を何回選んだかを集計する
4. short report を `docs/` に残す

### Exit Criteria

- why this policy worked / failed を signal ベースで説明できる
- 単なる best-number 比較で終わらない

## Concrete Next Steps

次にやることは以下の順を基本とする。

1. refined `regime_switch` を `W8` slice で再実行する
2. `VQE` の throughput 劣化がどこまで戻るか確認する
3. 必要なら `stall_aware_shifted` の issue cap を pressure-dependent に再設計する
4. その後で `balanced_shifted` を検討する

## Deliverables

次フェーズで最低限残したい成果物:

### Code

- refined scheduler signal layer
- improved pressure-aware policy
- tests

### Results

- focused sweep output
- aggregated comparison
- analysis CSV

### Docs

- progress report
- short experiment note
- 必要なら plan update

## Risks

### Risk 1. Overfitting To `W8_M8_F4`

stall regression を強く意識しすぎると、他 regime で gain を落とす危険がある。

対策:

- `F4` だけでなく `F8` も同時に比較する
- `regime_switch` による切替を必ず評価する

### Risk 2. Algorithm-Specific Hidden Tuning

`QAOA` 向けに効く heuristic が `VQE` を壊す可能性がある。

対策:

- algorithm 名ではなく runtime signal だけで policy を作る
- 失敗してもそのまま結果として残す

### Risk 3. Too Many Policies

policy を増やしすぎると、研究の軸がぼやける。

対策:

- 常に「主力 1-2 policy」に絞る
- 追加候補は 1 本ずつ評価する

### Risk 4. QFT H8/Q64 Missing Shifted Artifact

large QFT の比較が不完全なままになる。

対策:

- co-design mainline とは分離して扱う
- blocker にしない

## Decision Rules

今後の分岐は次で判断する。

1. refined `regime_switch` が `VQE` を改善した
   - そのまま主力 policy 候補にする
2. `VQE` が改善しないが `QAOA/QFT` では強い
   - `regime_switch` を ff-bottleneck specialist として位置づける
3. どの algorithm でも中途半端
   - `balanced_shifted` を追加検討する
4. 新 policy が既存 policy をほぼ上回れない
   - co-design の主張を「regime-aware policy selection」へ寄せる

## Bottom Line

次フェーズの中心は、**pressure-aware controller policy を一般的な signal だけで改善できるか** の検証である。

当面は、

- scheduler architecture を崩さず
- `W8` study slice に絞り
- `stall reduction` と `throughput gain` の両立

を狙って進める。

最初の優先実装は、**refined `regime_switch` の focused re-evaluation** である。
