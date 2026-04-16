# Shifted-DAG Co-Design Repro Runbook

## Purpose

`W8_M8_F4` を主戦場にした shifted-DAG-aware controller co-design の実装と実験を、
後から同じ条件で再実行できるようにするための runbook。

対象は次の 2 系統です。

- 実装再現: scheduler / simulator / analysis の変更
- 実験再現: shifted artifact backfill, focused sweep, aggregate, analysis

## Files Changed

今回の scheduler / analysis 実装は次のファイルに入っている。

- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/domain/enums.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/simulator.py`
- `research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/analysis/shifted_study.py`
- `research/mbqc_pipeline_sim/tests/test_scheduler.py`
- `research/mbqc_pipeline_sim/tests/test_shifted_study_analysis.py`

## Implemented Policies

追加した policy は次の 2 つ。

- `shifted_critical`
  - shifted DAG 上の `remaining_depth` を主優先に使う
  - tie-break は早い `topo_level` と大きい fanout
- `stall_aware_shifted`
  - `ff_width < issue_width` または `ff_width < meas_width` のときだけ
    FF bottleneck とみなす
  - その regime では「この cycle に打つと successor が ready になる node」を優先
  - それ以外では `shifted_critical` に fallback

## Runtime Interface Change

動的 priority を入れるために、scheduler 呼び出しに cycle context を追加している。

- `SchedulerContext.remaining_indegree`
- `SchedulerContext.ff_waiting_count`
- `SchedulerContext.ff_in_flight_count`
- `SchedulerContext.meas_in_flight_count`

`MbqcPipelineSimulator` が毎 cycle これを埋めて `scheduler.select(...)` に渡す。

## Analysis Outputs Added

`research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/analysis/shifted_study.py`
から次の CSV が新たに出る。

- `policy_variant_summary.csv`
  - dag variant ごとの throughput / stall / utilization の代表値
- `policy_win_summary.csv`
  - 同一 scenario 内で各 policy が throughput / stall で何回勝つか
- `policy_vs_asap_summary.csv`
  - `asap` を基準にした差分比較

既存の `policy_width_summary.csv`, `stall_regression_summary.csv`,
`paired_seed_effects.csv` と合わせると、次の主張を直接確認できる。

- `W8_M8_F4` では stall regression が集中する
- fully provisioned 側では `asap` が強い
- FF bottleneck 側では shifted-aware / stall-aware policy の余地がある

## Reproduction Environment

Windows PowerShell 前提。

使用 Python:

- `C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe`

研究コード import 用:

- `research/mbqc_ff_evaluator/src`
- `research/mbqc_pipeline_sim/src`

OneAdapt 依存の local vendor install 先:

- `research/_vendor/pydeps`

### Install local dependencies for shifted backfill

```powershell
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' -m pip install `
  --target research\_vendor\pydeps `
  pyzx==0.10.0 networkx==3.4.2 qiskit==1.4.2
```

## Artifact Preparation

### 1. Prepare namespaced study artifacts

```powershell
$env:PYTHONPATH='c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\mbqc_ff_evaluator\src'
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' `
  -m mbqc_ff_evaluator.cli.prepare_shifted_dag_study --force
```

出力先:

- `research/mbqc_ff_evaluator/results/studies/13_shifted_dag_dynamic/common_coupled_subset/artifacts`

### 2. Backfill shifted DAG payloads

```powershell
$env:PYTHONPATH='c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\_vendor\pydeps;c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\mbqc_ff_evaluator\src'
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' `
  -m mbqc_ff_evaluator.cli.backfill_shifted_graph `
  --raw-dir research\mbqc_ff_evaluator\results\studies\13_shifted_dag_dynamic\common_coupled_subset\artifacts `
  --algorithms QAOA QFT VQE `
  --hardware-sizes 4 6 8 `
  --logical-qubits 16 36 64 `
  --seeds 0 1 2 3 4
```

### 3. Progress check while backfill is running

```powershell
$files = Get-ChildItem research\mbqc_ff_evaluator\results\studies\13_shifted_dag_dynamic\common_coupled_subset\artifacts\*.json
$withShifted = 0
foreach ($f in $files) {
  $raw = Get-Content -Raw $f.FullName
  if ($raw -match '"shifted_dependency_graph"\s*:\s*\{') { $withShifted++ }
}
[pscustomobject]@{ total = $files.Count; with_shifted = $withShifted }
```

補足:

- 既に shifted payload がある artifact は skip される
- 中断後に再実行しても基本的には続きから進む

## Focused W8 Study

対象 study:

- issue width 固定: `W=8`
- measurement width: `M=8`
- FF width: `F=4,8`
- policy: `asap`, `greedy_critical`, `shifted_critical`, `stall_aware_shifted`
- release mode: `next_cycle`
- latencies: `l_meas=1,2`, `l_ff=1,2`

### Sweep

```powershell
$env:PYTHONPATH='c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\mbqc_pipeline_sim\src'
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' `
  -m mbqc_pipeline_sim.cli.sweep `
  --artifacts-dir research\mbqc_ff_evaluator\results\studies\13_shifted_dag_dynamic\common_coupled_subset\artifacts `
  --output research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\sweep.csv `
  --issue-widths 8 `
  --l-meas-values 1,2 `
  --l-ff-values 1,2 `
  --policies asap,greedy_critical,shifted_critical,stall_aware_shifted `
  --release-modes next_cycle `
  --meas-widths 8 `
  --ff-widths 4,8 `
  --dag-variant both `
  --algorithms QAOA,QFT,VQE `
  --hq-pairs 4:16,6:36,8:64 `
  --dag-seeds 0,1,2,3,4
```

### Aggregate

```powershell
$env:PYTHONPATH='c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\mbqc_pipeline_sim\src'
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' `
  -m mbqc_pipeline_sim.cli.aggregate `
  --input research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\sweep.csv `
  --output research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\aggregated.csv `
  --comparison-output research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\comparison.csv
```

### Shifted-study analysis

```powershell
$env:PYTHONPATH='c:\Users\tsuboi\Documents\mbqc-classical-control-study\research\mbqc_pipeline_sim\src'
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' `
  -m mbqc_pipeline_sim.cli.analyze_shifted_study `
  --input research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\sweep.csv `
  --output-dir research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus\summary\analysis
```

## Key Outputs To Inspect

`W8_M8_F4` を見るとき:

- `summary/analysis/policy_width_summary.csv`
- `summary/analysis/stall_regression_summary.csv`
- `summary/analysis/policy_vs_asap_summary.csv`
- `summary/analysis/policy_win_summary.csv`
- `summary/analysis/paired_seed_effects.csv`

`W8_M8_F8` を fully provisioned reference として見るとき:

- `summary/analysis/policy_width_summary.csv`
- `summary/analysis/policy_variant_summary.csv`
- `summary/analysis/policy_vs_asap_summary.csv`

## Expected Interpretation Template

最終的には次の軸でまとめる。

- baseline raw vs shifted:
  - shifted は static depth を大きく減らす
- problematic regime:
  - `W8_M8_F4` では throughput gain があっても stall regression が起こる
- policy roles:
  - `asap` は fully provisioned 側で強い
  - `stall_aware_shifted` は FF bottleneck 側の改善候補
  - refined policy は universal winner ではない
- conclusion:
  - universal winner を探すより regime-aware design が筋が良い

## Verification Notes

この環境では `pytest` が system Python に入っていなかったため、
現時点の quick verification は次の 2 つで行っている。

- `ast.parse(...)` による edited file の構文確認
- 手書きスモークで scheduler priority と analysis CSV 出力を確認

依存が整った Python 環境がある場合は追加で次を回す。

```powershell
& 'C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe' -m pytest `
  research\mbqc_pipeline_sim\tests\test_scheduler.py `
  research\mbqc_pipeline_sim\tests\test_shifted_study_analysis.py `
  research\mbqc_pipeline_sim\tests\test_simulator.py `
  research\mbqc_pipeline_sim\tests\test_sweep.py
```
