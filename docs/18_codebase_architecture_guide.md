# Codebase Architecture Guide

## この資料の目的

本資料は、このリポジトリのコード全体について、

- どんなアーキテクチャで構成されているか
- どんなクラスとモジュールがあるか
- 何を設定できるか
- どう運用・再現・拡張するか

を説明するための技術ガイドである。

研究レポートではなく、**実装の地図**として読むことを想定している。

## 1. リポジトリ全体の構成

トップレベルの役割は以下の通り。

- [README.md](/Users/seitsubo/Project/mbqc-classical-control-study/README.md)
  - リポジトリ全体の入口
- [research/](/Users/seitsubo/Project/mbqc-classical-control-study/research)
  - 研究コード本体
- [OneAdapt_AE 2/](/Users/seitsubo/Project/mbqc-classical-control-study/OneAdapt_AE%202)
  - 再現性のために同梱した OneAdapt スナップショット
- [docs/](/Users/seitsubo/Project/mbqc-classical-control-study/docs)
  - 研究レポート、進捗、計画、catch-up 文書

研究コードは 2 つのサブプロジェクトに分かれている。

- [research/mbqc_ff_evaluator/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator)
  - OneAdapt 出力を解析し、FF 制約と budget を評価する
- [research/mbqc_pipeline_sim/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim)
  - FF evaluator artifact を入力にして、動的パイプライン性能をシミュレートする

## 2. システム全体のデータフロー

コード全体の関係は次の流れで理解すると分かりやすい。

```text
Quantum circuit / experiment config
  -> OneAdapt_AE 2
  -> mbqc_ff_evaluator
     -> raw JSON artifacts
     -> aggregated CSV / figures
  -> mbqc_pipeline_sim
     -> sweep.csv
     -> aggregated.csv / comparison.csv
     -> analysis CSV / figures
  -> docs
```

より具体的には、

1. `OneAdapt_AE 2/` が MBQC 依存グラフ生成の外部実装を提供する
2. `mbqc_ff_evaluator` がそれを呼び出して artifact JSON を生成する
3. `mbqc_pipeline_sim` が artifact JSON を読み、パイプライン動的性能を計算する
4. 結果を `results/` と `docs/` にまとめる

## 3. アーキテクチャ方針

両サブプロジェクトに共通して、次の方針で構成している。

- **domain**
  - 純粋な型、Enum、dataclass
- **ports**
  - Protocol ベースの抽象境界
- **adapters**
  - 外部入出力、外部ライブラリ、JSON/CSV、OneAdapt 依存
- **services / core**
  - 主処理ロジック
- **cli**
  - 実行入口
- **analysis**
  - sweep 後の数値分析

つまり、研究コードではあるが、

- 直接 `dict` を回しながら全てを処理する
- CLI の中に本処理を書く
- simulator と scheduler を密結合させる

といった作りは避けている。

## 4. `mbqc_ff_evaluator` の構成

### 4.1 役割

FF evaluator は、

- OneAdapt を呼ぶ
- FF dependency graph を抽出する
- `D_ff`, `L_hold`, `L_meas` を収集する
- budget 化する
- JSON / CSV / figure にまとめる

ためのサブプロジェクトである。

### 4.2 主要ディレクトリ

- [domain/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/domain)
- [ports/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/ports)
- [adapters/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/adapters)
- [services/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/services)
- [analysis/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/analysis)
- [cli/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/cli)

### 4.3 中心となる型

主要な型は [domain/models.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/domain/models.py) にある。

- `ExperimentConfig`
  - 1 実験ケースの入力
  - `algorithm`, `hardware_size`, `logical_qubits`, `seed`, `refresh`, `refresh_bound`
- `FFNode`, `FFEdge`
  - FF dependency graph のノード・エッジ表現
- `DependencyGraphSnapshot`
  - raw / shifted DAG のスナップショット
- `OnePercArtifact`
  - FF evaluator の最重要データモデル
  - 1 ケース分の収集結果を丸ごと保持する
- `DependencyBudget`, `LayerBudget`, `ConservativeBudget`
  - budget 評価用の型
- `ArtifactRecord`
  - `artifact_path` と `artifact` をまとめた保存結果

このサブプロジェクトでは、基本的に **`OnePercArtifact` が中心オブジェクト** である。

### 4.4 ports

Protocol は次の責務に分かれている。

- `CompilerBackend`
  - 外部コンパイラを呼んで artifact を作る
- `ArtifactRepository`
  - artifact の保存・読み出し
- `CircuitFactory`
  - OneAdapt に渡す入力回路の生成
- `DepthReferenceBackend`
  - graphix など、比較用の外部 depth reference

これにより、

- OneAdapt 本体
- artifact 保存形式
- reference backend

を差し替え可能にしている。

### 4.5 adapters

代表的な adapter は以下。

- [oneadapt_backend.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/adapters/oneadapt_backend.py)
  - OneAdapt / OnePerc を呼ぶ最重要 adapter
  - `collect_artifact()` が `OnePercArtifact` を返す
  - raw と shifted の dependency snapshot もここで抽出する
- [oneadapt_circuit_factory.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/adapters/oneadapt_circuit_factory.py)
  - OneAdapt に渡す回路 payload を構築
- [json_repository.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/adapters/json_repository.py)
  - artifact を JSON として保存
- [csv_repository.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/adapters/csv_repository.py)
  - summary CSV の読み書き
- `graphix_reference.py`
  - 比較用の depth reference backend

### 4.6 services

代表的な service は以下。

- [collect_artifacts.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_ff_evaluator/src/mbqc_ff_evaluator/services/collect_artifacts.py)
  - `ArtifactCollectionService`
  - backend から収集し、必要なら reference を足して、repository へ保存
- `aggregate_results.py`
  - raw JSON artifact 群から summary を作る
- `compute_metrics.py`
  - `ff_chain_depth_raw`, `ff_chain_depth_shifted` などを計算

### 4.7 CLI 一覧

主要 CLI:

- `mbqc_ff_evaluator.cli.sweep`
  - OneAdapt を回して raw artifact を集める
- `mbqc_ff_evaluator.cli.aggregate`
  - raw JSON から CSV summary を生成
- `mbqc_ff_evaluator.cli.plot`
  - publication 用 figure を生成
- `mbqc_ff_evaluator.cli.backfill_shifted_graph`
  - 既存 raw artifact に shifted graph を後付け
- `mbqc_ff_evaluator.cli.prepare_shifted_dag_study`
  - shifted study 用 namespace を準備
- `mbqc_ff_evaluator.cli.evaluate_controller_models`
  - controller spec と budget を照合

### 4.8 出力物

FF evaluator の代表的な出力は次。

- `results/raw/*.json`
  - 1 ケース 1 artifact
- `results/summary/*.csv`
  - 集約結果
- `results/studies/...`
  - study 専用 namespace

## 5. `mbqc_pipeline_sim` の構成

### 5.1 役割

Pipeline simulator は、

- FF evaluator artifact を読み込む
- dependency DAG をサイクル精度で実行する
- throughput / stall / utilization を計算する
- policy / width / latency の design space を探索する

ためのサブプロジェクトである。

### 5.2 主要ディレクトリ

- [domain/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain)
- [ports/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/ports)
- [core/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core)
- [adapters/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/adapters)
- [analysis/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/analysis)
- [cli/](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/cli)

### 5.3 中心となる型

主要な型は [domain/models.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/models.py) にある。

- `PipelineConfig`
  - simulator 設定
  - `issue_width`, `l_meas`, `l_ff`, `meas_width`, `ff_width`, `release_mode`, `policy`, `seed`
- `MeasNode`, `MeasEdge`
  - simulator 用 DAG 表現
- `SimDAG`
  - 前処理済み DAG
  - adjacency, indegree, topo_level, remaining_depth などを持つ
- `CycleRecord`
  - 各 cycle の発行数、待ち行列、完了数
- `SimResult`
  - 1 ケース分の結果
  - throughput, stall_rate, utilization, cycle_records など

### 5.4 scheduler 関連の型

scheduler layer は別の型を持つ。

- [domain/scheduler_models.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/scheduler_models.py)
  - `ReadyNodeView`
  - `SchedulerContext`
  - `SchedulerSignals`
  - `SchedulerDecision`
- [domain/enums.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/enums.py)
  - `SchedulingPolicy`
  - `SchedulerRegime`
  - `ReleaseMode`
  - `DagVariant`
  - `NodeState`

この層があることで、

- simulator 本体
- scheduler policy
- regime 判定

を分離している。

### 5.5 core

代表的な core モジュール:

- [simulator.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/simulator.py)
  - `MbqcPipelineSimulator`
  - メインループ本体
- [pipeline_stage.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/pipeline_stage.py)
  - `LatencyPipeline`
  - fixed-latency stage の抽象
- [scheduler.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py)
  - scheduler policy 群
- [scheduler_features.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler_features.py)
  - ready set から `SchedulerContext` を組み立てる
- [scheduler_signals.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler_signals.py)
  - pressure / regime の pure helper
- [scheduler_registry.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler_registry.py)
  - policy factory registry

### 5.6 simulator の処理順

`MbqcPipelineSimulator.run()` の 1 cycle は概ね次の順で動く。

1. FF 完了を処理して依存を解放
2. Measurement 完了を FF stage へ渡す
3. Ready Queue から scheduler が issue 対象を選ぶ
4. Measurement stage に enqueue
5. record を保存

この流れにより、`same_cycle` / `next_cycle` release や stage width 制約を表現する。

### 5.7 scheduler policy 群

現在の policy は [scheduler.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py) にある。

- `ASAPScheduler`
- `LayerScheduler`
- `GreedyCriticalScheduler`
- `ShiftedCriticalScheduler`
- `StallAwareShiftedScheduler`
- `RefinedStallAwareShiftedScheduler`
- `RegimeSwitchScheduler`
- `RefinedRegimeSwitchScheduler`
- `RandomScheduler`

方針の違い:

- `ASAP`
  - topo level 優先
- `GreedyCritical`
  - remaining depth 優先
- `ShiftedCritical`
  - remaining depth + unlock count
- `StallAwareShifted`
  - FF backpressure 時に issue を抑える
- refined 系
  - 旧実装を壊さずに version 分離して探索したもの

### 5.8 ports

- [ports/scheduler_policy.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/ports/scheduler_policy.py)
  - `SchedulerPolicyPort`
  - `SchedulerFactory`

重要なのは、simulator が具体 scheduler class に直接依存せず、
`Protocol` に依存している点である。

### 5.9 adapters

代表的 adapter:

- `artifact_loader.py`
  - FF evaluator JSON を `SimDAG` に変換
- `csv_writer.py`
  - `SimResult` を CSV に保存

### 5.10 analysis

中心は [analysis/shifted_study.py](/Users/seitsubo/Project/mbqc-classical-control-study/research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/analysis/shifted_study.py)。

ここでは、

- `SweepObservation`
- `PairedSeedEffect`
- `SummaryRow`
- `ShiftedStudyOutputs`

などの dataclass を使って、

- paired raw/shifted effects
- algorithm summary
- policy summary
- bottleneck summary
- stall regression summary

を作る。

### 5.11 CLI 一覧

主要 CLI:

- `mbqc_pipeline_sim.cli.run`
  - 単一 artifact の単発実行
- `mbqc_pipeline_sim.cli.sweep`
  - design-space sweep
- `mbqc_pipeline_sim.cli.aggregate`
  - median / IQR 集約
- `mbqc_pipeline_sim.cli.plot`
  - figure 生成
- `mbqc_pipeline_sim.cli.analyze_shifted_study`
  - shifted study 専用の数値分析

## 6. 何を設定できるか

### 6.1 FF evaluator 側

主な設定項目:

- `algorithm`
- `hardware_size`
- `logical_qubits`
- `seed`
- `refresh`
- `refresh_bound`

CLI では例えば次を指定できる。

- `--algorithms`
- `--hardware-sizes`
- `--logical-qubits`
- `--seeds`
- `--coupled`
- `--refresh-bound`
- `--oneadapt-root`

### 6.2 pipeline sim 側

主な設定は `PipelineConfig` に集約されている。

- `issue_width`
- `l_meas`
- `l_ff`
- `meas_width`
- `ff_width`
- `release_mode`
- `policy`
- `seed`

CLI ではさらに sweep 範囲やフィルタも指定する。

- `--dag-variant raw|shifted|both`
- `--algorithms`
- `--dag-seeds`
- `--hardware-sizes`
- `--logical-qubits`
- `--hq-pairs`

## 7. 典型的な運用フロー

### 7.1 baseline の FF evaluator

1. `mbqc_ff_evaluator.cli.sweep`
2. `mbqc_ff_evaluator.cli.aggregate`
3. `mbqc_ff_evaluator.cli.plot`

### 7.2 baseline の pipeline simulation

1. FF evaluator の raw artifact を用意
2. `mbqc_pipeline_sim.cli.sweep`
3. `mbqc_pipeline_sim.cli.aggregate`
4. `mbqc_pipeline_sim.cli.plot`

### 7.3 shifted study

1. `prepare_shifted_dag_study`
2. `backfill_shifted_graph`
3. `mbqc_pipeline_sim.cli.sweep --dag-variant both`
4. `aggregate`
5. `analyze_shifted_study`

### 7.4 co-design study

1. policy を追加
2. unit / simulator / sweep test
3. focused slice で `sweep`
4. `aggregate`
5. `analyze_shifted_study`
6. 結果を study namespace に保存

## 8. 結果の保存方針

結果は基本的に 2 系統ある。

- `results/raw`, `results/summary`
  - ベースライン
- `results/studies/...`
  - 研究テーマごとの独立 namespace

重要なのは、**新しい study を始めるときに既存結果を上書きしない**ことである。

とくに co-design では、

- `shifted_policy_comparison_w8_focus`
- `regime_switch_w8_focus`
- `regime_switch_refined_w8_focus`
- `stall_aware_refined_w8_focus`

のように namespace を切って保存している。

## 9. 再現性と versioning の考え方

この repo では、研究結果の再現性を守るため、

- 既存 policy が明確に下位互換でない限り上書きしない
- 改良版は別 policy 名で追加する
- result namespace と実装段階の対応を崩さない

という方針を取る。

例:

- `regime_switch`
  - 初期版を保持
- `regime_switch_refined`
  - 改良版を別名で追加
- `stall_aware_shifted`
  - 初期版を保持
- `stall_aware_shifted_refined`
  - pressure-dependent 版を別名で追加

## 10. このコードを読むときのおすすめ順

### FF evaluator を理解したいとき

1. `domain/models.py`
2. `adapters/oneadapt_backend.py`
3. `services/collect_artifacts.py`
4. `cli/sweep.py`
5. `cli/aggregate.py`

### pipeline sim を理解したいとき

1. `domain/models.py`
2. `core/simulator.py`
3. `core/pipeline_stage.py`
4. `core/scheduler.py`
5. `core/scheduler_signals.py`
6. `cli/sweep.py`
7. `analysis/shifted_study.py`

### scheduler co-design を理解したいとき

1. `domain/scheduler_models.py`
2. `ports/scheduler_policy.py`
3. `core/scheduler_features.py`
4. `core/scheduler_signals.py`
5. `core/scheduler.py`

## 11. 一言でまとめると

このコードベースは、

- **OneAdapt を外部依存とする static evaluator**
- **artifact 駆動の cycle-accurate pipeline simulator**
- **typed scheduler architecture を持つ co-design sandbox**

の 3 層でできている。

研究用途のコードではあるが、

- domain / adapter / core / cli を分離し
- dataclass / Enum / Protocol を中心に置き
- 結果を study namespace で version 管理する

ことで、再現性と拡張性を両立する構成にしている。
