# 光 MBQC におけるフィードフォワード制約の定量評価
## OneAdapt コンパイル出力に基づく古典制御 Budget 解析

**坪井 星汰**  
東京大学 大学院情報理工学系研究科  
2026-04-15

---

## 概要

光量子コンピュータは、光子を媒体とする量子ビットが室温で動作し長距離通信と親和性が高いことから、フォールトトレラント量子計算の有力な実装候補として注目されている。測定型量子計算（MBQC）では、クラスター状態上の量子ビットを順次測定し、その結果に応じて後続測定の基底を古典的に決定する「フィードフォワード（FF）」が逐次実行の核心を担う。光子は delay line 内で有限時間しか保持できないため、FF に要する古典処理はすべて光子寿命 τ_ph（現状マイクロ秒オーダー）以内に完了しなければならない。

この制約を定量的に評価するには、コンパイル後の回路がどれだけの「FF 直列処理」を要求するかを測定する指標が必要である。しかし既存の MBQC コンパイラ（OneAdapt、OnePerc 等）は空間マッピングに起因する光子保持時間や測定遅延をレイヤ数で出力するにとどまり、「古典制御装置に何ナノ秒を要求しているか」を直接計算する評価基盤は存在しない。

本研究はこのギャップを埋めることを目的とし、MBQC コンパイラ OneAdapt の出力から FF 依存グラフを抽出して**最長依存深さ D_ff** を新規指標として定義した。さらに D_ff を光子寿命と照合することで古典制御 budget を定量化する枠組みを構築し、QAOA・QFT・VQE の 3 アルゴリズムについて H=4〜12、Q=16〜100 の規模スイープ（計 85 ケース）を実施した。

実験から得られた主な知見は以下のとおりである。(1) D_ff は論理量子ビット数 Q に対してほぼ線形にスケールし、その係数はアルゴリズムに強く依存する（VQE ≈ 1、QAOA ≈ 2.2、QFT ≈ 5.0）。(2) ハードウェアグリッドサイズ H を増やしても D_ff は変化せず、FF 依存制約はチップの物理的拡大では解決できない。(3) signal_shift 最適化は QAOA と VQE の D_ff を 97〜99% 削減し、現行参照コントローラ（OPX: 250 ns、XCOM: 185 ns）での実現可能性を 0/11 から 8/11 に改善する。(4) 支配的ボトルネックはアルゴリズムと規模によって異なり、dependency 制約・hold 制約・measurement delay 制約の三者を同時に評価することが不可欠である。

---

## 1. はじめに

### 1.1 光量子コンピュータと MBQC

近年、光量子コンピューティングの実験的進展が著しい。2025 年、Xanadu は Aurora システムで 86.4 億モードのクラスター状態生成を実証し [Madsen+, Nature 2025]、PsiQuantum は 99.72% の fusion fidelity を報告した [PsiQuantum, Nature 2025]。しかし「クラスター状態を大規模に生成できる」こととそれを「計算として活用できる」こととは別問題である。

MBQC（Measurement-Based Quantum Computation）では、あらかじめ準備したグラフ状態（クラスター状態）の量子ビットを 1 つずつ測定し、その結果に応じて後続測定の基底を適応的に変える。この**フィードフォワード**（FF）の操作が計算の実行を担う。FF はゲート型量子計算における量子ゲート適用に相当し、これなしには MBQC は成立しない。

光 MBQC では、光子が delay line という物理的な保持機構に蓄えられる間に古典処理が完了しなければならない。光子の delay line 内での寿命 τ_ph は現状でおよそ 1 マイクロ秒オーダーであり、この時間制約が光 MBQC における最大の実装上のボトルネックとなっている。

### 1.2 問題の所在

FF の依存関係は有向グラフ（FF 依存グラフ）で表現できる。ノードは各測定操作を、有向エッジは「ノード A の測定結果がノード B の基底決定に必要」という依存関係を表す。このグラフの最長パスは、古典処理装置が避けようのない「逐次処理の最小段数」を意味する。この段数が多ければ多いほど、1 段あたりの処理に許容される時間は短くなる。

既存の MBQC コンパイラ研究を振り返ると、表 1 に示すように、いずれも FF 依存構造を物理時間へ変換する機能を持たない。OneQ [Zhang+, ISCA'23] は fusion が常に成功するという理想化を行い、OnePerc [Zhang+, ASPLOS'24] と OneAdapt [Zhang+, MICRO'25] は光子保持レイヤ数や測定遅延レイヤ数を出力するが、「1 レイヤを処理するのに何 ns かかるか」を評価する枠組みは提供しない。

**表 1：先行研究との差分**

| 研究 | FF 依存の扱い | 物理時間への変換 |
|------|-------------|---------------|
| OneQ [ISCA'23] | 無視（fusion 常に成功と仮定） | なし |
| OnePerc [ASPLOS'24] | L_meas をレイヤ数で出力 | なし |
| OneAdapt [MICRO'25] | L_hold, L_meas をレイヤ数で出力 | なし |
| arXiv:2109.04792 | FPGA 静的タイミング解析 | ハードウェア実測値 |
| **本研究** | D_ff（最長依存深さ）を抽出 | t_ff_crit として定量化 |

### 1.3 本研究の貢献

本研究の主要な貢献は 3 点である。

**貢献 1：FF 依存深さ指標 D_ff の定義と budget 写像**　OneAdapt の FF 依存グラフから最長依存鎖を抽出し、古典制御 budget（t_ff_crit = τ_ph ÷ D_ff）に写像するフレームワークを構築した。この枠組みにより、コンパイラの出力から直接「コントローラに何 ns を要求しているか」が計算できる。

**貢献 2：3 種制約の統一評価**　dependency serialization（D_ff）、hold 制約（L_hold）、measurement delay（L_meas）という性質の異なる 3 つの制約を同一スケールで評価し、支配項がアルゴリズムと規模に依存することを実証した。これにより「どの制約を優先的に改善すべきか」をアルゴリズムごとに特定できる。

**貢献 3：controller model との定量的照合**　OPX（Quantum Machines 社、250 ns）と XCOM（Fermilab、185 ns）という実在するコントローラの仕様を budget と照合し、signal_shift の有無が実現可能性の境界を左右することを定量的に示した。

---

## 2. 背景

### 2.1 MBQC のフィードフォワード

MBQC の実行は、グラフ状態上の量子ビットを適切な順序・基底で測定していくことで進む。基底の選択は通常 XY 平面内の角度で指定され、先行測定の結果（0 または 1 のビット）に応じて角度を補正する必要がある。この補正には 2 種類あり、**X 補正**は直接の隣接ノードに、**Z 補正**は 1 ステップ先のノードに伝播する。

FF 依存グラフでは、X 補正に由来するエッジを x-エッジ、Z 補正に由来するエッジを z-エッジと呼ぶ。グラフ全体が有向非巡回グラフ（DAG）であることが gflow の理論的条件として保証されており、最長パスが存在する。

### 2.2 OneAdapt の処理パイプライン

OneAdapt [MICRO'25] は OnePerc [ASPLOS'24] をベースにした光 MBQC 向けコンパイラである。入力回路を受け取り、以下のステップで処理を進める。

1. 量子回路をグラフ状態に変換する
2. FF 依存グラフ（dgraph）を `determine_dependency()` で生成する
3. グラフ状態の次数を削減し、2D ハードウェアグリッドへのマッピング・ルーティングを行う（`map_route()`）
4. 出力として `required_life_time`（光子保持要求レイヤ数）と `max_measure_delay`（最大測定遅延レイヤ数）を返す

本研究ではこのパイプラインに介入し、ステップ 2 で生成される dgraph を取得して D_ff を計算する。

### 2.3 signal_shift 最適化

`determine_dependency()` は z 補正の伝播規則に従って dgraph を構築するが、z-エッジの連鎖が深い依存パスを生む原因となる。`signal_shift()` はこれらの z-エッジを下流に繰り越すことで依存グラフを簡約化し、D_ff を大幅に削減できる。

OneAdapt の現行コードでは signal_shift はコメントアウトされており本番環境では未使用だが、依存グラフの構造を理解する上で重要な最適化である。本研究では signal_shift を適用した「shifted」グラフと適用しない「unshifted」グラフの両方について D_ff を計算し、比較する。

---

## 3. 評価指標と物理モデル

### 3.1 評価指標

本研究で定義・使用する指標を表 2 に整理する。

**表 2：評価指標の定義**

| 記号 | 定義 | 出所 |
|------|------|------|
| D_ff (raw) | FF 依存グラフの最長パス長（signal_shift なし） | 本研究（新規） |
| D_ff (shifted) | signal_shift 後の最長パス長 | 本研究（新規） |
| L_hold | 光子保持要求レイヤ数（required_life_time） | OneAdapt 既存 |
| L_meas | 最大測定遅延レイヤ数（max_measure_delay） | OneAdapt 既存 |
| t_ff_crit | τ_ph / D_ff（FF 1 段あたりの許容処理時間） | 本研究（新規） |
| t_hold_crit | τ_ph / L_hold | 本研究（新規） |
| t_meas_crit | τ_ph / L_meas | 本研究（新規） |

budget（t_\*_crit）は小さいほど制約が厳しい。D_ff と L_hold は異なる物理制約を捉えていることに注意されたい。**L_hold** は空間マッピングの混雑により光子が delay line で「待たされる」時間であり、ハードウェアサイズを増やすと改善する。一方 **D_ff** は古典処理が逐次的に完了しなければならない依存段数であり、アルゴリズムの回路構造で決まるためハードウェアサイズでは改善しない。

### 3.2 Dependency-Serial Budget Model

1 つの FF 依存グラフエッジが 1 段の処理コスト（unit-weight）に対応すると仮定する。この近似の根拠は 2 点ある。第一に、OneAdapt の dgraph はエッジごとのレイテンシ注釈を持たず、構造情報として得られるのは「依存の有無」のみである。第二に、x 補正と z 補正はいずれも古典 XOR 演算として対称的に実装されるため、処理コストに実質的な差はない。

古典制御装置が 1 FF 段あたり t_ff_ns で処理するとき、全 FF 処理時間は

```
T_FF = D_ff × t_ff_ns
```

であり、これが光子寿命 τ_ph_ns を超えてはならない。したがって許容される古典制御 budget は

```
t_ff_crit = τ_ph_ns / D_ff
```

である。このモデルは pipeline・並列処理を考慮しないため保守的な上界を与える。

### 3.3 実験設計

**アルゴリズムの選定**

3 つのアルゴリズムを選んだ。QAOA（Quantum Approximate Optimization Algorithm）は乱数により相互作用グラフが変化する確率的アルゴリズムであり、seed 依存の変動を観察できる。QFT（量子フーリエ変換）は全量子ビット間の制御回転ゲートを含む規則的・決定論的なアルゴリズムである。VQE（Variational Quantum Eigensolver）は量子化学向けの ansatz 回路を用いる決定論的アルゴリズムである。

**パラメータ空間**

| パラメータ | 設定値 |
|-----------|--------|
| H（グリッドサイズ） | 4, 6, 8, 10, 12 |
| Q（論理量子ビット数） | Coupled: Q = H²（16, 36, 64, 100）/ Sweep B: Q 固定・H 可変 |
| seed | 5〜10（QAOA）、5（QFT/VQE） |
| τ_ph | 0.5, 1.0, 5.0 μs（感度分析） |

3 種類のスイープを実施した。**Sweep A**（主実験）では Q = H²（coupled）として規模全体をスイープし、アルゴリズムごとの D_ff スケーリングを評価する。**Sweep B** では Q を固定して H のみを変えることで、ハードウェアサイズが D_ff と L_hold に与える効果を分離する。**Sweep C** では H を固定して Q のみを変え、問題規模の効果を純粋に評価する。

**再現性**：全実験で `random.seed` と `numpy.random.seed` を固定。結果は seed ごとの raw JSON で保存し、集計は中央値と IQR（四分位範囲）を用いる。

**停止条件**：1 ケースの実行時間中央値が 10 分超、または 2 連続の H で全 seed が timeout となった場合は打ち切る。QFT H=10（Q=100）はこの条件に抵触したため（推定 5〜10 時間/ケース）実施しなかった。

---

## 4. 実験結果

全 85 ケースが成功し、timeout は 0 件であった。以下に 7 つの知見を順に述べる。

### 4.1 D_ff の規模スケーリング

Coupled configurations（Q = H²）における D_ff の中央値を表 3 に示す。

**表 3：D_ff のスケーリング（中央値、raw）**

| Q | QAOA | QFT | VQE |
|---|------|-----|-----|
| 16 | 34（IQR: 29–36） | 77（±0） | 15（±0） |
| 36 | 75（IQR: 73–82） | 177（±0） | 35（±0） |
| 64 | 142（IQR: 133–156） | 317（±0） | 63（±0） |
| 100 | 217（IQR: 213–226） | —（停止条件） | 99（±0） |

3 アルゴリズム全てで D_ff は Q にほぼ線形にスケールする。スケーリング係数はアルゴリズムごとに大きく異なる。

- **VQE**（係数 ≈ 1）：VQE の ansatz 回路が MBQC グラフ状態に変換されると Q−1 個のゲートが逐次依存する線形チェーン構造になる。このため D_ff ≈ Q−1 という最もシンプルなスケーリングを示す。QFT や QAOA と比較して、光 MBQC への適合性が高い。

- **QAOA**（係数 ≈ 2.2）：乱数によって相互作用グラフが変わるため seed 間の変動（±15%）がある。しかし変動の中央値はほぼ線形の傾向を示す。

- **QFT**（係数 ≈ 5.0）：全量子ビット間の制御回転ゲートが高密度な全結合依存構造を生み、係数が最大となる。また seed による変動は全くなく完全に決定論的である。

この結果から、光 MBQC で FF レイテンシを議論する際、アルゴリズムを区別しない一般論は意味をなさないことがわかる。同じ Q=64 でも VQE (D_ff=63) と QFT (D_ff=317) では要求する古典処理の逐次段数が 5 倍以上異なる。

### 4.2 D_ff と L_hold の乖離

D_ff と L_hold は直感的には「回路が複雑なほど両者とも大きくなる」と思いがちだが、実際には独立した制約を測定している。図 1 は全実験ケースを D_ff（横軸）と L_hold（縦軸）の散布図として示したものである。

図 1 から明らかなように、両者の間に強い相関はない。QFT では D_ff が 317 に達する一方で L_hold は 40 前後に留まる。逆に QAOA の大規模ケースでは L_hold が相対的に大きくなることもある。

この乖離の原因は両者の物理的意味の違いにある。L_hold は「ハードウェアの空間的混雑」を反映しており、より大きなグリッドを使えば混雑が緩和されて改善する。D_ff は「アルゴリズムの回路構造に固有の直列依存性」を反映しており、グリッドサイズとは無関係である。次節ではこの点を実験的に確認する。

### 4.3 ハードウェアサイズ H は D_ff を改善しない

Sweep B の結果を表 4 に示す（QAOA Q=64、H=8/10/12）。

**表 4：Sweep B — H 可変・Q=64 固定（QAOA）**

| H | D_ff（中央値） | L_hold（中央値） |
|---|---|---|
| 8 | 142 | 40 |
| 10 | 142 | 34 |
| 12 | 142 | 31 |

D_ff は H を変えても完全に不変である。一方 L_hold は H=8→12 で 40→31（−22%）と改善する。

この結果は図として見ても明瞭である。`H` を横軸、`D_ff` と `L_hold` を縦軸に取ると、
`D_ff` は水平線、`L_hold` は右下がりとなる。すなわちハードウェア幅の増加は空間混雑に由来する hold 制約には効くが、
アルゴリズムの直列依存で決まる dependency 制約には効かない。

この結果は光量子コンピュータのシステム設計に対して重要な示唆を与える。チップ面積を拡大してグリッドを大きくすることは hold 制約の緩和には有効だが、FF 依存制約は改善しない。つまり FF 依存制約を解消するためには、ハードウェアの物理的拡張ではなく**コンパイラ側の最適化**（signal_shift 等）が必要である。

### 4.4 signal_shift による D_ff の劇的削減

signal_shift を適用した場合の D_ff の変化を表 5 に示す。

**表 5：signal_shift 前後の D_ff 比較**

| アルゴリズム・規模 | D_ff（raw） | D_ff（shifted） | 削減率 |
|---|---|---|---|
| QAOA（Q=16〜100、全ケース） | 28〜226 | **常に 2** | 97〜99% |
| QFT（H=8、Q=64） | 317 | 27〜31 | 90% |
| VQE（Q=16〜100、全ケース） | 15〜99 | **常に 1** | 93〜99% |

QAOA は Q=16〜100 の全ケースで shifted depth が 2 に収束し、VQE は 1 に収束する。この結果は驚くべきものである。signal_shift を適用するだけで、QAOA/VQE の FF 依存構造はほぼ完全に並列化可能になる。言い換えれば、D_ff=2 または 1 とは、全測定をほぼ 2 段（または 1 段）の古典処理で済ませられるということを意味する。

一方 QFT は削減率こそ 90% と高いが、Q=64 での shifted depth は 27〜31 に留まり、依然として厳しいレイテンシ要求が残る。QFT の構造的複雑さは signal_shift だけでは解消しきれない。

signal_shift が OneAdapt の現行コードでコメントアウトされていることを踏まえると、この最適化を実装として復活させることが QAOA/VQE における FF 実現可能性の鍵となる。

### 4.5 支配制約のアルゴリズム依存性

τ_ph = 1 μs のもとで 3 種類の budget を比較した結果を表 6 に示す。

**表 6：各アルゴリズムの budget 比較（τ_ph = 1 μs、coupled configurations）**

#### QAOA（Q=100）
| 制約 | budget（ns） | 備考 |
|------|------------|------|
| t_ff_crit（raw） | 4.6 | **支配的** |
| t_hold_crit | 19.2 | — |
| t_meas_crit | 19.6 | — |

#### QFT（Q=64）
| 制約 | budget（ns） | 備考 |
|------|------------|------|
| t_ff_crit（raw） | 3.2 | 厳しい |
| t_hold_crit | 25.6 | — |
| t_meas_crit | 0.37 | **支配的** |

#### VQE（Q=100）
| 制約 | budget（ns） | 備考 |
|------|------------|------|
| t_ff_crit（raw） | 10.1 | — |
| t_hold_crit | 23.3 | — |
| t_meas_crit | 1.08 | **支配的** |

各アルゴリズムで支配的なボトルネックが異なることが明確に示されている。QAOA は dependency 制約が支配的であり続ける（全 Q 範囲）。QFT は小規模では dependency が支配的だが、Q≥36 で measurement delay が 1 桁以上厳しくなり主要ボトルネックへと遷移する。VQE は Q=16 では hold 制約が最も厳しいが、Q≥36 になると measurement delay が支配的となる。

特に QFT Q=64 における t_meas_crit = 0.37 ns という値は極めて厳しい。τ_ph = 1 μs のもとで最大測定遅延が 2700 レイヤ超という意味であり、単純なコントローラ高速化では対処できないことを示している。

支配制約の遷移をまとめると以下のようになる。

| アルゴリズム | Q=16 | Q≥36 |
|------------|------|-------|
| QAOA | dependency | dependency |
| QFT | dependency | measurement delay |
| VQE | hold | measurement delay |

### 4.6 測定遅延外れ値の構造

L_meas（最大測定遅延レイヤ数）には定性的に異なる 2 種類の大きさが観測された。

**種別 A：Seed-sensitive instability**　特定の seed のみで L_meas が跳ね上がる。QAOA H=8 Q=64 seed=4 では L_meas = 1189（他の seed: 35〜40）、QFT H=4 Q=16 seed=0 では L_meas = 160（他: 26〜27）が該当する。これは `map_route()` の routing heuristic が特定の空間配置で局所解にはまり込む不安定性に起因すると考えられる。

**種別 B：Systematic-high regime**　全 seed が一様に高い L_meas を示す。QFT H=8 Q=64 では L_meas 中央値 2723（budget = 0.37 ns）、VQE H=10 Q=100 では中央値 928（budget = 1.08 ns）がこれに該当する。こちらはアルゴリズム構造そのものに起因する本質的な大きさであり、heuristic の改良では解消できない。

この切り分けは重要である。種別 A は routing 改善で緩和できる可能性があるが、種別 B の systematic-high は QFT/VQE の大規模実行における構造的な課題であり、別途の対策が必要となる。

### 4.7 コントローラモデルとの照合

τ_ph = 1 μs として coupled configurations 11 ケース（QAOA 3 点・QFT 2 点・VQE 3 点 + 感度確認用）に対するコントローラ成立判定を表 7 に示す。

**表 7：コントローラ feasibility（τ_ph = 1 μs）**

| コントローラモデル | レイテンシ | raw dependency | shifted dependency |
|-----------------|----------|---------------|------------------|
| OPX-like（Quantum Machines） | 250 ns | **0 / 11** | 8 / 11 |
| XCOM-like（Fermilab） | 185 ns | **0 / 11** | 8 / 11 |
| 1 GHz、5 サイクル | 5 ns | 9 / 11 | 11 / 11 |
| 2 GHz、5 サイクル | 2.5 ns | 10 / 11 | 11 / 11 |
| CMOS 10 ns ターゲット | 10 ns | 7 / 11 | 11 / 11 |

raw depth に対しては現行参照コントローラ（OPX / XCOM）は 11 ケース全てで不成立となる。しかし signal_shift 後では 11 ケース中 8 ケースで成立する。失敗する 3 ケースは QFT の大規模ケース（measurement delay が支配的な種別 B に分類される）であり、コントローラのレイテンシを下げるだけでは解決できない。

この結果から、signal_shift の実装は光 MBQC の物理的成立条件において必須の最適化であることが定量的に確認された。

### 4.8 独立コンパイラ baseline との比較

OneAdapt がどの程度の最適化をしているかを評価するため、小規模ケース（Q=16）について汎用 MBQC transpiler である graphix を使って同じ回路を独立コンパイルし、D_ff を比較した（表 8）。

**表 8：OneAdapt vs graphix baseline（Q=16）**

| アルゴリズム | D_ff（OneAdapt raw） | D_ff（OneAdapt shifted） | D_ff（graphix） |
|------------|---------------------|------------------------|----------------|
| QAOA | 34 | 2 | 189 |
| QFT | 77 | 7 | 615 |
| VQE | 15 | 1 | 90 |

OneAdapt の raw depth は graphix より 4.5〜8.0 倍浅い。これは OneAdapt の専用最適化が有効に機能していることを示す。さらに signal_shift を適用すると、差はさらに 1〜2 桁広がる。

ただし graphix は OneAdapt とは独立した経路で回路変換を行うため、理論的最適値との差を論じるには別途の検証が必要である。

---

## 5. 考察

### 5.1 アルゴリズム選択の重要性

D_ff のスケーリング係数（VQE ≈ 1、QAOA ≈ 2.2、QFT ≈ 5.0）は、各アルゴリズムが MBQC にどれほど自然に対応するかを定量的に示している。VQE の係数が最小なのは、量子化学の ansatz 回路が「各量子ビットへの操作がほぼ独立」という構造を持つためである。光 MBQC で最初に実用的な計算を行うアルゴリズムとして VQE が有望であることを示唆している。

QFT の係数 5.0 は顕著に大きく、これは QFT 回路の全量子ビット間結合がグラフ状態に変換されると極めて複雑な依存構造を生むためである。光 MBQC で QFT を実用化するには、signal_shift を超えた高度なコンパイラ最適化（gflow 再スケジューリング等）と、より長い光子寿命（τ_ph ≥ 5 μs）が必要と考えられる。

### 5.2 H 独立性が示す設計原則

H を増やすことは hold 制約には有効だが dependency 制約には無効という結果は、光量子コンピュータのスケールアップ戦略に直接の含意を持つ。大型チップの製造は FF レイテンシ問題を解決しない。制御プロセッサの古典処理速度（t_ff_ns）の改善、または signal_shift 相当の最適化をコンパイルパイプラインに組み込むことが根本的な解決策となる。

この観点では、本研究の評価枠組みは「どのコンパイラ最適化が FF 制約に効くか」を定量的に評価するベンチマークとして機能する。

### 5.3 signal_shift の意義

signal_shift は QAOA/VQE において D_ff を 2 または 1 まで削減する。D_ff=2 とは、全測定が最大 2 段の古典処理（ほぼ全て並列実行可能）で済むことを意味する。FF 逐次処理のボトルネックがほぼ消滅し、OPX/XCOM クラスのコントローラでも実現可能になる。

一方 QFT の場合、signal_shift を適用しても shifted depth が 27〜31 に留まり、根本的な解決には至らない。QFT の構造的課題は signal_shift の適用範囲を超えており、回路レベルの再設計が必要である。

signal_shift が OneAdapt の現行コードでコメントアウトされている理由は不明だが、本研究の結果は QAOA/VQE の実用化に向けてその実装を優先すべきことを強く示唆している。

### 5.4 三者制約の同時評価の必要性

本研究で最も重要な発見の一つは、どのボトルネックが支配的かがアルゴリズムと規模によって変わることである。dependency 制約だけ、または hold 制約だけを見ていても、制約の全体像は見えない。

QAOA は signal_shift により dependency 制約がほぼ消滅する一方、QFT/VQE の大規模ケースでは measurement delay が主要ボトルネックとなり signal_shift は無効である。このように支配制約の種類が変わることは、コンパイラ最適化の優先度が問題設定によって変わることを意味しており、アルゴリズム・規模ごとの統合評価が不可欠である。

### 5.5 本研究の限界

**抽象 budget model**：t_ff_crit は FF 段を直列処理した場合の上界 budget であり、パイプライン・並列処理を考慮した実際の要求は緩和される可能性がある。特に D_ff=2 の QAOA については、2 段の直列処理として解釈してよいかを手計算で検証することが望ましい。

**unit-weight 近似**：x 補正と z 補正に同一コストを仮定した。実装によっては両者の処理時間が異なる場合があり、重み付きモデルへの拡張が今後の課題である。

**fusion 失敗の非考慮**：実際の光量子チップでは fusion 成功率が ≈75%（補助光子 4 個使用時）であり、グラフ構造が確率的に変動する。本研究は固定グラフ評価に留まり、失敗時の依存グラフ変動は考慮していない。

**RTL レベルの未検証**：t_ff_crit が具体的なハードウェアで実現可能かは RTL 設計・タイミング解析によって初めて確認できる。本研究の budget はあくまで必要条件であり、充分条件ではない。

---

## 6. まとめと今後の課題

### 6.1 まとめ

本研究では、MBQC コンパイラ OneAdapt の FF 依存グラフから最長依存深さ D_ff を抽出し、光子寿命制約と照合する評価基盤を構築した。85 ケースのスイープ実験を通じて以下の 4 点を示した。

1. **D_ff は Q に線形スケールし、係数はアルゴリズム依存**（VQE ≈ 1、QAOA ≈ 2.2、QFT ≈ 5.0）。同じ規模でもアルゴリズムによって FF 制約の厳しさが 5 倍以上異なる。

2. **ハードウェアサイズ H は D_ff に無効**。H を増やすと hold 制約は緩和されるが、dependency 制約はアルゴリズムの回路構造で決まるためハードウェア拡大では改善しない。

3. **signal_shift は QAOA/VQE の実現可能性を左右する**。この最適化により D_ff が 2〜1 まで削減され、現行コントローラ（OPX/XCOM）で 11 ケース中 8 ケースが成立するようになる。

4. **支配制約はアルゴリズムと規模で遷移する**。QAOA は常に dependency 支配、QFT/VQE の大規模ケースは measurement delay 支配となり、三者を同時評価することが設計上不可欠である。

これらの結果は、光 MBQC 制御プロセッサの設計において D_ff の解析が hold 制約と同等以上に重要であることを示しており、本枠組みを XQsim の MBQC 拡張に組み込むことで RTL レベルの定量評価へと接続できる。

### 6.2 今後の課題

| 課題 | 内容 | 優先度 |
|------|------|--------|
| signal_shift 後 depth の理論検証 | QAOA/VQE の D_ff=2/1 が gflow 理論の最適性と整合するか確認 | 高 |
| measurement delay 高騰の根因解析 | routing heuristic の改良による systematic-high の解消可能性 | 高 |
| RTL 設計との接続 | XQsim を MBQC 向けに拡張し、t_ff_ns を RTL 計測値で置き換える | プロジェクト本体 |
| RHG 誤り訂正の統合 | デコーダ遅延を FF 段レイテンシに加算した評価 | 中 |
| 確率的 fusion への拡張 | fusion 失敗時の依存グラフ変動を Monte Carlo でモデル化 | 中 |

---

## 参考文献

[1] Bartolucci, S. et al. "Fusion-based quantum computation." *Nature Communications* 14, 912 (2023).

[2] Madsen, L. S. et al. "Scaling and networking a modular photonic quantum computer." *Nature* 637, 592–601 (2025).

[3] PsiQuantum Team. "A manufacturable platform for photonic quantum computing." *Nature* 638, 912–920 (2025).

[4] Zhang, Y. et al. "OneQ: A Compilation Framework for Photonic One-Way Quantum Computation." *Proc. ISCA* (2023).

[5] Zhang, Y. et al. "OnePerc: A Randomness-aware Compiler for Photonic Quantum Computing." *Proc. ASPLOS* (2024).

[6] Zhang, Y. et al. "OneAdapt: Adaptive Compilation for Resource-Constrained Photonic One-Way Quantum Computing." *Proc. MICRO* (2025). arXiv:2504.17116.

[7] Raussendorf, R., Harrington, J. & Goyal, K. "A fault-tolerant one-way quantum computer." *Ann. Phys.* 321, 2242–2270 (2006).

[8] Briegel, H. J. et al. "Measurement-based quantum computation." *Nature Physics* 5, 19–26 (2009).

[9] Browne, D. E. & Rudolph, T. "Resource-Efficient Linear Optical Quantum Computation." *Phys. Rev. Lett.* 95, 010501 (2005).

---

## 付録 A：実験再現手順

```bash
cd /Users/seitsubo/Project/XQsim
source .venv-ffeval/bin/activate
cd research/mbqc_ff_evaluator

# Sweep A 全実験
python -m pytest tests/test_sweep_main.py -m sweep_a -v -s

# 集約・図生成
python -m pytest tests/test_pipeline.py -v -s

# 外れ値解析
python -m mbqc_ff_evaluator.cli.analyze_measurement_delay

# controller model 評価
python -m mbqc_ff_evaluator.cli.evaluate_controller_models
```

生成物：`results/raw/`（85 JSON）、`results/summary/`（metrics.csv、budgets.csv、controller_budget_eval.csv、measurement_delay_group_summary.csv）、`results/figures/`（fig1〜fig7、appendix）

## 付録 B：用語集

| 用語 | 説明 |
|------|------|
| MBQC | Measurement-Based Quantum Computation（測定型量子計算）。グラフ状態上の測定と FF によって計算を実行する。 |
| フィードフォワード（FF） | 先行測定結果を後続測定基底の決定に反映する操作。MBQC の計算実行の核心。 |
| D_ff | FF 依存グラフの最長パス長。本研究が定義した新規指標。 |
| signal_shift | FF 依存グラフの z 補正エッジを下流に伝播・除去する最適化。OneAdapt では現在コメントアウト。 |
| t_ff_crit | τ_ph / D_ff。FF 1 段あたりに許容される古典処理時間（ns）。 |
| L_hold | 光子を何レイヤ分保持する必要があるか（OneAdapt 既存指標）。空間マッピングの混雑に起因。 |
| L_meas | 最大の測定遅延レイヤ数（OneAdapt 既存指標）。 |
| coupled configuration | Q = H²（論理量子ビット数とハードウェアグリッドサイズを連動させた設定）。 |
| gflow | MBQC の測定パターンに対して理論的に最適な実行順序を保証する数学的条件。 |
| OPX | Quantum Machines 社の量子制御プロセッサ。参照値 FF 遅延 < 250 ns。 |
| XCOM | Fermilab の量子制御システム。参照値 FF 遅延 < 185 ns。 |
