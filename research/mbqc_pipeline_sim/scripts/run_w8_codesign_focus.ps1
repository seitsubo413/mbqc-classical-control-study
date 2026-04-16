$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
$Python = "C:\Users\tsuboi\AppData\Local\Programs\Python\Python313\python.exe"

$FfEvalSrc = Join-Path $RepoRoot "research\mbqc_ff_evaluator\src"
$PipelineSrc = Join-Path $RepoRoot "research\mbqc_pipeline_sim\src"
$VendorDeps = Join-Path $RepoRoot "research\_vendor\pydeps"

$StudyArtifacts = Join-Path $RepoRoot "research\mbqc_ff_evaluator\results\studies\13_shifted_dag_dynamic\common_coupled_subset\artifacts"
$OutputRoot = Join-Path $RepoRoot "research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign_w8_focus"
$SummaryDir = Join-Path $OutputRoot "summary"
$AnalysisDir = Join-Path $SummaryDir "analysis"

New-Item -ItemType Directory -Force -Path $SummaryDir | Out-Null
New-Item -ItemType Directory -Force -Path $AnalysisDir | Out-Null

$env:PYTHONPATH = $PipelineSrc
& $Python -m mbqc_pipeline_sim.cli.sweep `
  --artifacts-dir $StudyArtifacts `
  --output (Join-Path $SummaryDir "sweep.csv") `
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

& $Python -m mbqc_pipeline_sim.cli.aggregate `
  --input (Join-Path $SummaryDir "sweep.csv") `
  --output (Join-Path $SummaryDir "aggregated.csv") `
  --comparison-output (Join-Path $SummaryDir "comparison.csv")

& $Python -m mbqc_pipeline_sim.cli.analyze_shifted_study `
  --input (Join-Path $SummaryDir "sweep.csv") `
  --output-dir $AnalysisDir

Write-Host "Focused W8 co-design study completed."
Write-Host "Summary dir: $SummaryDir"
