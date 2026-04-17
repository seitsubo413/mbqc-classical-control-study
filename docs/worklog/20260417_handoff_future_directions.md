# 引き継ぎ資料：研究完了と今後の拡張方針

**作成日**: 2026-04-17  
**作成者**: Claude Sonnet 4.6（坪井との共同研究セッションにて）  
**前提**: doc 21（`docs/21_throughput_cost_and_lff_sensitivity_report.md`）まで読了していること

---

## 本日の到達点

Study 17〜20 を完結し、研究の主軸が出揃った。

```
[設計指針の確立 (doc 20)]
    ff_rate_matched + ff_width = W/2 で stall regression ゼロ

[4 軸の検証 (doc 21)]
    Study 17: throughput コスト = ゼロ（F/W = 0.125 まで）
    Study 18: F*(ff_rate_matched) は L_ff に依存しない
    Study 19: F*(ff_rate_matched) は L_meas に依存しない
    Study 20: F*(ff_rate_matched) は回路規模 H=10/12 に依存しない  ← 本日完了
```

**現在地のまとめ**：
- 提案手法（ff_rate_matched）の有効性が 4 つの独立した軸で検証された
- H=4〜12、Q=16〜100、L_ff=1〜5、L_meas=1〜4、F/W=0.125〜1.0 の全域で保証を確認
- 論文の主要主張として提示できる水準に達していると考える

---

## 未解決の小課題（polish 相当）

| 優先度 | 項目 | 内容 |
|--------|------|------|
| B | QFT H8/Q64 shifted 欠損 | 候補 6 参照。QFT 大規模が使えるようになると Study 17/20 のカバレッジが広がる |
| B | F*(ASAP) 精密予測モデル | 候補 5 参照。burst_load × raw_stall_rate の 2 変数モデル |

---

## 今後の拡張方針：CS・Computer Architecture 知識の接続

現研究は量子スケジューリングの文脈で独立して発展してきたが、古典的な CS・CompArch の概念と対応関係を明示することで、論文の位置づけと貢献が格段に明確になる。以下に接続できる箇所を整理する。

---

### 1. データハザードと発行制御（CPU パイプライン理論）

**対応関係**:
- MBQC の FF 依存 = CPU の RAW ハザード（Read After Write）
- issue_width = スーパースカラの発行幅
- ff_rate_matched のガード `ff_in_flight ≥ ff_width` = ハザード検出による発行ストール

**接続の意義**:  
CPU ではハザード検出に「スコアボード法」や「Tomasulo アルゴリズム」を使う。ff_rate_matched はこれらの「構造的ハザード回避」と同等の機能をより単純なカウンタで実現していると解釈できる。論文でこの対応を明示することで、CompArch コミュニティへのアピールになる。

**将来実験**:
- OoO（アウトオブオーダー）発行との比較。ready burst を先読みして FF 使用量を予測する投機的スケジューラとの性能差。

---

### 2. クレジットベースフロー制御（ネットワーク・メモリシステム）

**対応関係**:
- ff_rate_matched = クレジットベースフロー制御の送信側スロットリング
- ff_width = クレジット総数
- `ff_in_flight` = 未返却クレジット数
- FF 処理完了 = クレジット返却

**接続の意義**:  
ネットワーク・オン・チップ（NoC）やメモリコントローラで広く使われる手法と同一の設計原理。「MBQC の古典制御問題がネットワークフロー制御と同型である」という新しい視点を与えられる。  
関連文献: `Dally & Towles, "Principles and Practices of Interconnection Networks"` のクレジットベースフロー制御の章。

**将来実験**:
- 動的クレジット調整（ff_width を実行時に変える adaptive 版）の性能評価。
- burst 到達レートの計測に基づいてクレジット数を自動チューニングする手法。

---

### 3. Little's Law とスループット保証

**対応関係**:
- Little's Law: `L = λW`（L=在庫、λ=到達レート、W=滞在時間）
- ff_in_flight = L（FF パイプラインにいるノード数）
- ff_width = L の上限
- F*(ff_rate_matched) = W/2 の保証は `λ ≤ μ`（到達レート ≤ 処理レート）の構造的な保証

**接続の意義**:  
F*(ff_rate_matched) = W/2 の理論証明（実験 B）を Little's Law の枠組みで再解釈することで、「なぜ W/2 で十分なのか」の直感的な説明が得られる。  
D_ff = 1–2 のとき、FF パイプラインの平均滞在時間が短く、クレジット W/2 で十分な処理能力を確保できることを Little's Law で定式化できる。

**将来実験**:
- D_ff > 2 の回路（例：深い条件分岐を含む量子アルゴリズム）での F* の変化。
- `F*(ff_rate_matched) = max(W/2, ⌈D_ff⌉)` という一般化式の検証。

---

### 4. バックプレッシャー機構と非同期パイプライン

**対応関係**:
- ff_rate_matched = バックプレッシャー型フロー制御（受信側が詰まったら送信側を止める）
- issue stage ← FF queue のバックプレッシャー
- ASAP = バックプレッシャーなしのプッシュ型スケジューラ（burst が無制限に流れ込む）

**接続の意義**:  
非同期パイプライン設計（GALS: Globally Asynchronous Locally Synchronous）との接続。古典制御系が非同期で動作する将来の量子コンピュータアーキテクチャを想定すると、バックプレッシャー設計の重要性がより際立つ。

**将来実験**:
- FF 処理レイテンシが確率的（L_ff が固定でなく分布を持つ）場合のロバスト性評価。
- バックプレッシャーの伝播遅延が stall 特性に与える影響。

---

### 5. リアルタイムスケジューリング理論

**対応関係**:
- MBQC 実行 = リアルタイムタスクスケジューリング（締切り = FF 完了までに次のゲートを待てる時間）
- ff_rate_matched = EDF（Earliest Deadline First）的な優先度制御ではなく、レート制御型
- F* = スケジューリング可能性の境界（schedulability bound）

**接続の意義**:  
Liu & Layland (1973) の Rate Monotonic Scheduling と対応関係を整理することで、「ff_rate_matched が保証する実行可能性条件」を既存の実時間理論に位置づけられる。  
`F/W ≥ 0.5` という条件は、FF ユニットの利用率が 50% 以下に保たれることを意味し、これは RMS の利用率上限（`U ≤ ln 2 ≈ 0.693`）と類似した構造を持つ。

**将来実験**:
- FF タスクに優先度をつける（測定結果依存度が高いゲートを優先）スケジューリングとの比較。
- 複数の FF ユニット（ヘテロジニアス構成）を持つアーキテクチャへの拡張。

---

### 6. メモリレイテンシ隠蔽（プリフェッチ・投機実行）

**接続の意義**:  
L_ff が大きい（FF 処理が遅い）ケースは、CPU における高レイテンシメモリアクセスと同型。「FF 結果が返ってくる前に次のゲートを投機的に発行できるか」という問いは、投機実行やアウトオブオーダー実行の量子版になる。  
現在の実装は保守的（FF 結果が確定してから依存ゲートを発行）だが、将来の量子エラー訂正スキームでは投機的実行が議論されている。

**将来実験**:
- FF 結果の「楽観的事前推定」に基づく投機発行とロールバックコストの評価。
- Pauli フレーム追跡との組み合わせによる投機的フィードフォワード。

---

## 論文化に向けた推奨構成メモ

現時点の研究成果を論文にまとめるとすれば、以下の構成が考えられる：

```
1. Introduction
   - MBQC のフィードフォワード問題
   - 古典制御ボトルネックの重要性

2. Background
   - MBQC パイプラインモデル
   - signal shift と stall regression 問題（doc 16/20）
   - [CompArch との対応: データハザード・フロー制御]

3. ff_rate_matched の提案（doc 20 実験 A/B）
   - 設計原理（クレジットベースフロー制御として）
   - F* = W/2 の理論証明（Little's Law による再解釈）

4. 実験的検証（doc 21 Study 17–20）
   - Throughput コスト（4 軸で全てゼロ）
   - F* の安定性（L_ff, L_meas, H/Q スケール）

5. Discussion
   - ASAP の限界と設計指針
   - [CompArch 既存手法との比較]
   - 残課題（QFT H8/Q64, 投機的発行）

6. Conclusion
```

---

## ファイル構成（本日終了時点）

```
docs/
├── 20_hypothesis_driven_study_report.md     ← 主要理論（実験 A/B）
├── 21_throughput_cost_and_lff_sensitivity_report.md  ← 4 軸検証（本日更新）
└── worklog/
    ├── 20260417_handoff_next_experiments.md  ← 候補 1–6 の詳細
    └── 20260417_handoff_future_directions.md ← 本ファイル

research/mbqc_pipeline_sim/results/studies/
├── 17_throughput_cost/   sweep 720 runs
├── 18_lff_sensitivity/   sweep 600 runs
├── 19_lmeas_sensitivity/ sweep 640 runs
└── 20_large_scale_h10_h12/  sweep 2160 runs  ← 本日完了

research/mbqc_ff_evaluator/results/raw/
└── VQE_H10_Q36/Q64, VQE_H12_Q64  ← 本日生成
```
