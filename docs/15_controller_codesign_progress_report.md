# Controller Co-Design Progress Report

## Scope

本レポートは、2026-04-16 に実施した `shifted DAG` 向け controller co-design 作業の進捗をまとめる。

主な目的は以下の 3 点だった。

1. scheduler 実装を、今後 policy を増やしても破綻しにくい構造へ整理する
2. `W8_M8_F4` で観測された stall regression を直接狙う shifted-aware policy を実装する
3. その policy を実データで比較し、co-design が研究テーマとして成立するかを確認する

## Code Work

### 1. Scheduler Architecture Refactor

既存 simulator に policy ごとの条件分岐を増やす方針は取らず、scheduler layer を型付きで分離した。

追加・更新した主要ファイル:

- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/scheduler_models.py`
  - `ReadyNodeView`
  - `SchedulerContext`
  - `SchedulerDecision`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/ports/scheduler_policy.py`
  - `SchedulerPolicyPort`
  - `SchedulerFactory`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler_features.py`
  - runtime state から scheduler 入力を構築する pure helper
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler_registry.py`
  - policy factory registry
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py`
  - context/decision ベースへ移行
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/simulator.py`
  - scheduler への依存を context 構築に限定
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/enums.py`
  - policy enum を拡張

この変更により、

- simulator は cycle progression のみ担当
- feature builder は runtime feature 構築のみ担当
- scheduler policy は node selection のみ担当

という責務分離が成立した。

### 2. New Policies

#### `shifted_critical`

`remaining_depth` を主軸に、tie-break で `unlock_count` を使う shifted-aware heuristic を追加した。

狙い:

- shifted DAG 上で critical path を優先しつつ
- unlock 効果の高い node を先に出す

#### `stall_aware_shifted`

`ff_width` が律速になり backpressure が見えているときに、

- issue 数を `ff_width` まで抑える
- `unlock_count` の小さい node を優先する

方針の policy を追加した。

狙い:

- `W8_M8_F4` で見えていた stall regression を直接抑える

#### `regime_switch`

rule-based に以下を切り替える policy を追加した。

- fully provisioned regime: `asap`
- ff bottleneck かつ backpressure active: `stall_aware_shifted`
- それ以外: `shifted_critical`

これは学習ベースではなく、まず regime-aware dispatch が機能するかを見るための最小実装である。

## Tests

追加した主な検証:

- `shifted_critical` が `unlock_count` を tie-break に使うこと
- `stall_aware_shifted` が pressure 下で issue cap をかけること
- `stall_aware_shifted` が low-unlock node を優先すること
- `regime_switch` が
  - fully provisioned で `asap`
  - mixed regime で `shifted_critical`
  - ff backpressure 下で `stall_aware_shifted`
  に落ちること
- registry 経由で各 policy を生成できること

実行したテスト:

- `research/mbqc_pipeline_sim/tests/test_scheduler.py`
- `research/mbqc_pipeline_sim/tests/test_simulator.py`
- `research/mbqc_pipeline_sim/tests/test_sweep.py`

最終結果:

- `25 passed in 117.49s`

## Experiments

### 1. Shifted Policy Comparison (`W8` Focus)

出力先:

- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/shifted_policy_comparison_w8_focus/`

条件:

- `issue_width=8`
- `meas_width=8`
- `ff_width=4,8`
- `l_meas=1,2`
- `l_ff=1,2`
- `release_mode=next_cycle`
- `dag_variant=both`
- `algorithm=QAOA,QFT,VQE`
- `seed=0..4`
- `H:Q = 4:16, 6:36, 8:64`
- policy:
  - `asap`
  - `greedy_critical`
  - `shifted_critical`
  - `stall_aware_shifted`

実行結果:

- 総 runs: `2720`
- 実時間: `2553.4s`
- paired comparison 行数: `256`

主要結果 (`ff_width=4`, throughput gain / stall reduction の中央値):

| Algorithm | ASAP | GreedyCritical | ShiftedCritical | StallAwareShifted |
|-----------|------|----------------|-----------------|-------------------|
| QAOA | `9.92% / -222.45%` | `7.58% / -635.73%` | `7.58% / -607.80%` | `11.04% / 73.63%` |
| QFT  | `9.36% / -754.39%` | `9.00% / -711.88%` | `8.84% / -720.56%` | `8.41% / 59.38%` |
| VQE  | `4.89% / -1554.98%` | `3.36% / -3461.21%` | `3.36% / -3461.21%` | `0.65% / 41.37%` |

解釈:

- `stall_aware_shifted` は `W8_M8_F4` の stall regression を確実に反転した
- QAOA と QFT では throughput gain をおおむね維持しながら stall を改善できた
- VQE では stall は改善するが、元々小さい throughput gain をかなり削る

### 2. Regime Switch Comparison (`W8` Focus)

出力先:

- `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/regime_switch_w8_focus/`

条件:

- 上記と同じ
- 追加 policy:
  - `regime_switch`

実行結果:

- 総 runs: `3400`
- 実時間: `3126.4s`
- paired comparison 行数: `320`

主要結果:

- `ff_width=4` では `regime_switch` は `stall_aware_shifted` と同値
- `ff_width=8` では `regime_switch` は `asap` と同値

代表値:

| Regime | Algorithm | RegimeSwitch Throughput Gain | RegimeSwitch Stall Reduction |
|--------|-----------|------------------------------|------------------------------|
| `W8_M8_F4` | QAOA | `11.04%` | `73.63%` |
| `W8_M8_F4` | QFT  | `8.41%` | `59.38%` |
| `W8_M8_F4` | VQE  | `0.65%` | `41.37%` |
| `W8_M8_F8` | QAOA | `56.27%` | `94.55%` |
| `W8_M8_F8` | QFT  | `39.34%` | `90.97%` |
| `W8_M8_F8` | VQE  | `18.18%` | `85.23%` |

解釈:

- 今回の `regime_switch` は新しい中間挙動を作るというより
  - `F4` では `stall_aware_shifted`
  - `F8` では `asap`
  の良い方を幅 regime で拾う dispatcher として動いた
- したがって、設計としては正しく機能したが、policy 自体の新規性はまだ弱い

## What Was Clarified Today

今日の作業で、以下がかなり明確になった。

1. co-design 実装を進めるための scheduler architecture は成立した
2. `W8_M8_F4` の stall regression は policy 側でかなり抑えられる
3. ただし algorithm ごとの trade-off がある
   - QAOA/QFT では `stall_aware_shifted` が有望
   - VQE では守りすぎると throughput gain を潰しやすい
4. regime-aware policy は有効だが、今の `regime_switch` はまだ単純すぎる

## Open Issues

1. `VQE` で stall を下げつつ throughput gain を守る policy がまだ無い
2. `regime_switch` は width-based dispatch までは成功したが、pressure 強度や ready-set 特徴をまだ使っていない
3. `QFT H8/Q64` は shifted artifact が欠損しており、co-design 実験でも継続して除外されている

## Recommended Next Steps

1. `stall_aware_shifted` の pressure 判定を連続量にする
   - `waiting_ff_count`
   - `ff_slots_available`
   - `in_flight_meas_count / ff_width`
2. `regime_switch` に中間 regime を追加する
   - 常時 `stall_aware` に落とすのではなく、pressure が閾値を超えた cycle だけ抑制を強くする
3. `VQE` のような low-gain algorithm で conservative policy が過剰反応していないかを切り分ける
4. `QFT H8/Q64` 欠損の原因解析を別ラインで進める

## Related Outputs

- baseline dynamic study:
  - `research/mbqc_pipeline_sim/results/studies/13_shifted_dag_dynamic/raw_vs_shifted_next_cycle_width_matched/`
- first co-design comparison:
  - `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/shifted_policy_comparison_w8_focus/`
- regime-switch comparison:
  - `research/mbqc_pipeline_sim/results/studies/14_shifted_dag_codesign/regime_switch_w8_focus/`
- plan document:
  - `docs/14_shifted_dag_controller_codesign_plan.md`

## Bottom Line

今日の成果は、単なる方針検討ではなく、

- architecture refactor
- new policy implementation
- targeted co-design sweep
- regime-aware dispatch validation

まで一通り実施できた点にある。

研究メッセージとしては、

**shifted DAG の効果は controller policy でかなり変わり、特に `W8_M8_F4` のような ff bottleneck regime では policy co-design が本質的に重要**

というところまで、実装と数値の両方で踏み込めた。
