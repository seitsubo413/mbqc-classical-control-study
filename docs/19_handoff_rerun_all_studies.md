# 引き継ぎ: 全スタディ再実行手順

作成日: 2026-04-16  
対象ブランチ: `feat/merge`（コミット `19b46c9`）

---

## 背景

スケジューラのアーキテクチャを統一した（`codesign/w8-regime-aware-study` をマージ）。
これに伴い、旧コードで生成した実験結果はすべて**新コードで再実行して上書きする**。

---

## 1. 変更してはいけないもの

### スケジューラのアルゴリズムロジック

`research/mbqc_pipeline_sim/src/mbqc_pipeline_sim/core/scheduler.py` の各クラスの `select()` 内部ロジック。
以下のポリシーが確定版。**今後の比較はすべてこのコードが基準になる。**

| ポリシー | クラス | 備考 |
|---|---|---|
| `asap` | `ASAPScheduler` | topo_level → node_id でソート |
| `greedy_critical` | `GreedyCriticalScheduler` | -remaining_depth → node_id |
| `shifted_critical` | `ShiftedCriticalScheduler` | -depth, +topo_level, -adjacency_len, node_id |
| `stall_aware_shifted` | `StallAwareShiftedScheduler` | FF bottleneck時のみ unlock_count優先 |
| `stall_aware_shifted_refined` | `RefinedStallAwareShiftedScheduler` | pressure比例でissue_limit絞る |
| `regime_switch` | `RegimeSwitchScheduler` | 動的に3ポリシー切り替え（ff_waiting_count基準） |
| `regime_switch_refined` | `RefinedRegimeSwitchScheduler` | pressure scoreで切り替え閾値を調整 |

### スケジューラのAPI契約

```python
# SchedulerContext の4フィールド（変更禁止）
remaining_indegree: dict[int, int]
ff_waiting_count: int
ff_in_flight_count: int
meas_in_flight_count: int

# select() シグネチャ（変更禁止）
def select(self, ready: Sequence[int], limit: int, context: SchedulerContext | None) -> list[int]
```

### スイープパラメータ（再実行時の統一基準）

過去の全スタディで共通していたパラメータ。再実行時もこれで統一すること。

```
--algorithms QAOA,QFT,VQE
--hq-pairs 4:16,6:36,8:64
--dag-seeds 0,1,2,3,4
--release-modes next_cycle
--dag-variant both
```

---

## 2. 変更してよいもの

- `docs/` 以下のドキュメント
- `analysis/shifted_study.py` の集計・可視化ロジック（スケジューラ本体に触れない範囲）
- `tests/` のテストデータや期待値（ただしテストが通ることを必ず確認）
- `scripts/` の PowerShell スクリプト（パス・Python パスは環境に合わせて変更可）
- `results/` 以下のCSV/JSONアーティファクト（再実行で上書きされる）

---

## 3. この後の実行内容（デスクトップで）

### 前提

```powershell
# ブランチを取得
git fetch origin
git checkout feat/merge
git pull origin feat/merge
```

### セットアップ確認

```powershell
cd research\mbqc_pipeline_sim
python -m pytest --ignore=tests/test_plot.py -q
# → 31 passed であることを確認してから実行に進む
```

### Study 1: `13_shifted_dag_dynamic` の再実行

```powershell
$StudyArtifacts = "<リポジトリルート>\research\mbqc_ff_evaluator\results\studies\13_shifted_dag_dynamic\common_coupled_subset\artifacts"
$OutputDir = "<リポジトリルート>\research\mbqc_pipeline_sim\results\studies\13_shifted_dag_dynamic\raw_vs_shifted_next_cycle_width_matched\summary"

python -m mbqc_pipeline_sim.cli.sweep `
  --artifacts-dir $StudyArtifacts `
  --output "$OutputDir\sweep.csv" `
  --issue-widths 4,8 `
  --l-meas-values 1,2 `
  --l-ff-values 1,2 `
  --policies asap,greedy_critical `
  --release-modes next_cycle `
  --meas-widths 4,8 `
  --ff-widths 4,8 `
  --dag-variant both `
  --algorithms QAOA,QFT,VQE `
  --hq-pairs 4:16,6:36,8:64 `
  --dag-seeds 0,1,2,3,4
```

### Study 2: `14_shifted_dag_codesign` 系（旧コードの4スタディ）の再実行

以下の4スタディをすべて同じパラメータベースで再実行する。

**共通パラメータ:**
```
--issue-widths 8
--l-meas-values 1,2
--l-ff-values 1,2
--meas-widths 8
--ff-widths 4,8
--release-modes next_cycle
--dag-variant both
--algorithms QAOA,QFT,VQE
--hq-pairs 4:16,6:36,8:64
--dag-seeds 0,1,2,3,4
```

**各スタディの `--policies` だけ変える:**

| スタディ名 | `--policies` |
|---|---|
| `shifted_policy_comparison_w8_focus` | `asap,greedy_critical,shifted_critical,stall_aware_shifted` |
| `stall_aware_refined_w8_focus` | `asap,greedy_critical,shifted_critical,stall_aware_shifted,stall_aware_shifted_refined` |
| `regime_switch_w8_focus` | `asap,greedy_critical,shifted_critical,stall_aware_shifted,regime_switch` |
| `regime_switch_refined_w8_focus` | `asap,greedy_critical,shifted_critical,stall_aware_shifted,regime_switch,regime_switch_refined` |

各スタディで sweep → aggregate → analyze の3ステップ:

```powershell
# 例: regime_switch_refined_w8_focus
$StudyRoot = "<リポジトリルート>\research\mbqc_pipeline_sim\results\studies\14_shifted_dag_codesign\regime_switch_refined_w8_focus"
$SummaryDir = "$StudyRoot\summary"
$AnalysisDir = "$SummaryDir\analysis"
New-Item -ItemType Directory -Force -Path $AnalysisDir | Out-Null

python -m mbqc_pipeline_sim.cli.sweep `
  --artifacts-dir $StudyArtifacts `
  --output "$SummaryDir\sweep.csv" `
  --issue-widths 8 `
  --l-meas-values 1,2 `
  --l-ff-values 1,2 `
  --policies asap,greedy_critical,shifted_critical,stall_aware_shifted,regime_switch,regime_switch_refined `
  --release-modes next_cycle `
  --meas-widths 8 `
  --ff-widths 4,8 `
  --dag-variant both `
  --algorithms QAOA,QFT,VQE `
  --hq-pairs 4:16,6:36,8:64 `
  --dag-seeds 0,1,2,3,4

python -m mbqc_pipeline_sim.cli.aggregate `
  --input "$SummaryDir\sweep.csv" `
  --output "$SummaryDir\aggregated.csv" `
  --comparison-output "$SummaryDir\comparison.csv"

python -m mbqc_pipeline_sim.cli.analyze_shifted_study `
  --input "$SummaryDir\sweep.csv" `
  --output-dir $AnalysisDir
```

### Study 3: `14_shifted_dag_codesign_w8_focus` の再実行

既存のスクリプトがある:

```powershell
.\scripts\run_w8_codesign_focus.ps1
```

> ⚠️ スクリプト内の `$Python` パスをデスクトップ環境に合わせて変更すること。

---

## 4. 実行順序の推奨

```
1. git pull で最新コードを取得
2. uv sync または pip install -e . で依存解決
3. pytest で31テスト通過を確認
4. Study 1 (13_*) を実行（軽量: 2ポリシーのみ）
5. Study 2 の shifted_policy_comparison → stall_aware_refined → regime_switch → regime_switch_refined の順で実行
6. Study 3 (14_codesign_w8_focus) を実行（これが最重要・報告用）
7. 各スタディの analysis/ CSVを確認
8. 報告資料を作成
```

---

## 5. トラブルシューティング

**`ModuleNotFoundError: mbqc_pipeline_sim`**
→ `PYTHONPATH` に `research\mbqc_pipeline_sim\src` を追加するか、`pip install -e .` で editable install する。

**`PYTHONPATH` に `mbqc_ff_evaluator` も必要な場合**
→ artifact_loader がff_evaluatorの出力JSONを読む。`research\mbqc_ff_evaluator\src` も `PYTHONPATH` に追加。

**スイープが遅い**
→ `--hq-pairs 4:16` だけで試して動作確認してから全サイズに拡張する。

**`ValueError: Unknown policy: xxx`**
→ `--policies` に指定したポリシー名がタイポしていないか確認。使えるポリシー:
`asap`, `layer`, `greedy_critical`, `shifted_critical`, `stall_aware_shifted`, `stall_aware_shifted_refined`, `regime_switch`, `regime_switch_refined`, `random`
