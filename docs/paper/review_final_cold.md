# Reviewer Report — Cold Independent Review

**Paper:** "ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Reviewer:** Senior researcher, quantum computing architectures / classical computer architecture / systems performance evaluation

**Review date:** 2026-04-17

**Prior context:** None. This is a completely independent, first-reading review.

---

## 1. Summary

This paper identifies and characterizes **stall regression** — a paradoxical throughput degradation that occurs when signal shift compilation is applied to MBQC programs without a matching change in scheduling policy. Signal shift compresses feedforward (FF) chain depth from tens-to-hundreds of cycles down to one or two cycles, causing formerly staggered nodes to become ready simultaneously, overflowing the FF processor queue, and actually increasing total execution cycle count relative to the unoptimized baseline. The authors propose **ff_rate_matched**, a credit-based flow control policy that throttles node issue whenever the number of in-flight FF operations reaches the configured FF width F, exactly analogous to credit-based flow control in network-on-chip (NoC) router design. The central empirical claim is a design principle: F = ceil(W/2) FF slots suffice to eliminate stall regression with zero throughput penalty across all tested conditions, halving the FF hardware cost relative to ASAP scheduling. The claim is validated across five studies (4,360 simulation runs total) spanning F/W ratios, FF and measurement latencies, and circuit scales up to H=12, Q=100 for QAOA and VQE. The problem is timely and practically important as MBQC classical control is increasingly recognized as a first-class architectural bottleneck at scale. The cross-disciplinary framing — importing NoC credit-based flow control into the quantum control domain — is intellectually compelling and the paper is technically careful about distinguishing empirical findings from formal theorems.

---

## 2. Strengths (Detailed)

**S1. Clear identification of a real, non-obvious problem.** The stall regression phenomenon — signal shift making things *worse* without a companion scheduling fix — is a genuine and non-obvious pitfall. The paper is the first (by the authors' claim, unchallenged by evidence in the reference list) to quantify this effect in a pipeline execution context. The four-way comparison table in Section V-C makes the problem and solution concrete: raw+ASAP stall of 3.45% (QAOA) jumps to shifted+ASAP stall of 25.23%, then collapses back to shifted+ff_rm stall of 0.24%. This presentation is immediately persuasive.

**S2. Technically sound cross-domain analogy.** The analogy to credit-based flow control in NoC routers (Dally and Towles 2004) is not merely rhetorical. The mapping is tight: FF slots correspond to receiver buffer space, issued nodes correspond to flits, and the credit counter is structurally identical. The paper correctly notes the key difference (MBQC FF arrivals are DAG-structurally determined, not stochastic), and the agreement at F/W = 0.5 with the NoC prior work (Kumar et al. 2007) is noted without overclaiming a deep structural equivalence. This level of intellectual honesty is appreciated.

**S3. Remarkably clean O(1) implementation.** The pseudocode in Section IV-A is unambiguous and complete. The counter-and-comparator approach requires no look-ahead, no DAG knowledge, and no tuning. The implementation overhead is genuinely minimal. This is a strong engineering contribution.

**S4. Rigorous experimental scope.** Five independent validation axes (F/W ratio, L_ff, L_meas, circuit scale, raw-DAG baseline extension) with 4,360 total simulation runs across QAOA and VQE is unusually thorough for a single paper. The decision to include Study 21 specifically to address the "what is F* at F=2?" question — identified as a gap — reflects strong scientific integrity. The simulator validation against two analytical canonical cases (single chain and fully parallel) is appropriate and correctly reported.

**S5. Honest treatment of empirical vs. formal claims.** The paper repeatedly and explicitly flags that the F = W/2 design principle is "empirically confirmed" rather than formally proven. The framing in Section IV-B ("While a complete formal proof remains open...") and the formal statement explicitly labeling it a Design Principle rather than a Theorem is the right level of epistemic rigor. The paper does not oversell.

**S6. End-to-end result stated clearly.** The four-way comparison confirms that shifted+ff_rm achieves *lower* total cycle count than raw+ASAP — this means signal shift + ff_rm is strictly better than the baseline on both metrics simultaneously. This is the strongest possible experimental outcome and is correctly foregrounded.

**S7. Thorough limitations section.** Section VII-C enumerates all major limitations: non-Clifford corrections, probabilistic FF latency, probabilistic measurement outcomes, QFT coverage gap, same-circuit F*=2 confirmation, out-of-order extension, adaptive credit sizing, and fault-tolerant integration. The QFT exclusion in particular is handled with unusual care: it is explained mechanistically (butterfly dependency chains resist Pauli rewriting at H=8, Q=64), disclosed prominently in the abstract and section headers, and flagged as future work. This is good practice.

---

## 3. Weaknesses and Concerns

### 3.1 Major Concerns (Would Affect Acceptance)

**M1. The F* cross-study comparison is methodologically weak and is under-disclosed at the claim level.**

The paper's primary hardware sizing claim is F = W/2. Study 21 is introduced to establish that F* may be as low as 2 (i.e., well below W/2). However, the cross-study F* determination in Table V-F compares:

- raw+ASAP stall from Study 21 (H=8, Q=64)
- shifted+ff_rm stall from Study 20 (H=10, Q=100)

These are *different circuits at different scales*. The paper acknowledges this in Section V-F and Section VII-C ("the cross-study comparison mixes circuit scales, and a definitive same-circuit F*=2 determination would require dedicated experiments"). However, this caveat is buried after the headline claim "F*(ff_rate_matched) ≤ 2" appears in the abstract and is repeated in the contributions list. A reader absorbing the abstract at face value would not understand that the F*≤2 claim rests on a cross-scale comparison. The cross-study caveat should be promoted to the abstract and the contributions list, or the F*≤2 claim should be qualified as "indicative" rather than "confirmed." The F=W/2 claim (based on same-study data) is well-supported; the F*≤2 upgrade is not.

**M2. The non-monotone stall rate in Table V-F is explained as a denominator effect, but the raw data provided raises a consistency concern.**

The paper explains that VQE H8/Q64 raw+ASAP stall increases with F (0.29% at F=2, 0.51% at F=3, 0.86% at F=4) because total_cycles drops while absolute stall_cycles stays near-constant. The mechanism is plausible. However, the paper also states: "VQE H8/Q64 has D_ff_raw = 63 for all five seeds (identical circuits). As F increases from 2 to 4, the FF processor can sustain a higher throughput, so total_cycles drops sharply: 2058 cycles at F=2, 1379 at F=3, 1043 at F=4." This claim that total_cycles drops sharply as F increases for the *raw* DAG at VQE H8/Q64 is itself non-trivial: if D_ff_raw=63 and the raw DAG is well-staggered, the FF unit should not be the bottleneck at F≥2, so why would total_cycles change by 49% from F=2 to F=4? The paper attributes this to the raw DAG operating near the FF capacity limit at F=2 for VQE, but no supporting data (e.g., raw+ASAP FF utilization figures) are provided. Without this supporting data, the denominator-effect explanation is incomplete. Similarly, the QAOA F=3 < F=4 non-monotonicity (2.53% < 3.45%) is explained only in the header comment of the draft, not in the main body text (Section V-F). The body text refers to it but the explanation for QAOA is thinner than for VQE.

**M3. The "zero throughput cost" claim in Study 17 has a critical exception that requires more prominent qualification.**

Section V-B reports "Pairs with exact cycle match: 346/360 (96.1%)" and "Pairs where ff_rate_matched is slower: 10." The text attributes the 14 discrepant pairs to tie-breaking differences in QFT circuits "with deviations below ±0.17%." However:

1. 10 pairs where ff_rate_matched is *slower* is not the same as "zero throughput cost." Even if the magnitude is small (±0.17%), the claim "zero throughput cost in every comparison" in the abstract is technically falsified by these 10 pairs.
2. The abstract states "zero throughput cost in every comparison" — this sentence applies to the 1,440 paired comparisons in Studies 17 and 20 combined. Study 20 achieves 1080/1080 exact matches, which is clean. But Study 17's 346/360 should not be silently upgraded to "zero throughout cost" without the QFT-specific qualification in the abstract.
3. The characterization of these as "tie-breaking differences" is plausible but unverified in the paper; the authors should demonstrate that the discrepant pairs are indeed QFT instances and report the distribution of cycles_ratio for these 14 pairs explicitly.

**M4. The flow-balance argument for F = W/2 is informal to the point of being circular.**

Section IV-B states: "The maximum sustained issue rate is limited by the credit budget: at most F nodes can be simultaneously in-flight in the FF pipeline. Since virtually all (≥90%) of issued nodes generate FF work, the long-run issue throughput under ff_rate_matched is approximately F nodes/cycle, not W nodes/cycle." This is correct but trivially follows from the construction — it does not explain *why* F = W/2 is sufficient rather than, say, F = W/3 or F = W/4. The argument then says "Why F = W/2 suffices... Empirically, the answer is yes." The Little's Law application in Section VI-D is used as a "consistency check," not a derivation. The paper correctly labels this a Design Principle rather than a theorem, but the flow-balance argument as presented provides essentially no analytical insight into *why* W/2 is the right boundary. The Section IV-B heading promises "Design Principle and Empirical Validation of F* = ceil(W/2)" but the analytical content does not deliver an argument for W/2 specifically — it could equally support W/3 or W/8. The disconnect between the section heading's promise and the analytical content is potentially misleading.

**M5. The model assumption of universal FF generation (every measurement generates one FF operation) is never experimentally validated for the specific circuits in the test set.**

Section II-A states: "The model assumes that every measurement generates exactly one FF operation." The paper provides FF *fraction* data (fraction of nodes with at least one outgoing FF edge): QAOA 0.955±0.025, VQE 0.974±0.018. But this is the fraction of nodes that *have* FF edges in the DAG, not the fraction of runtime measurements that actually trigger a correction (which depends on measurement outcomes). In MBQC, whether a Pauli correction is applied depends on whether the parity of prior measurement outcomes is 0 or 1. For a Clifford byproduct, the correction is always applied (the measurement basis is updated), so the FF fraction equals the edge fraction — but this conflation is never stated explicitly. If the model's "FF operation" means "update the measurement angle register regardless of correction value," then the fraction is indeed the edge fraction and the data supports the assumption. If it means "apply a non-trivial correction only when the parity triggers one," then the expected fraction is ~50% of the edge fraction. This ambiguity needs to be resolved explicitly, because it affects the actual FF unit load and consequently the interpretation of F* results.

### 3.2 Minor Concerns (Editorial/Polish)

**m1.** The abstract is too long at approximately 550 words. The detailed stall range statistics ("0.049%–5.62% (ff_rate_matched) vs. 0.07%–85.71% (ASAP)") are more appropriate for the results section. The abstract should be condensed to ~250 words.

**m2.** Section III-B presents stall rates for "W=8, F=2" and "W=4, F=2" but the table in Section V-E reports results at W=4 only. The text in III-B cites Study 20 for the W=8 values (56.4%, 73.5%) but Study 20's representative table in V-E uses W=4. A reader trying to reconcile III-B with V-E must trace this across multiple sections. A consolidated cross-W comparison table in V-E would improve clarity.

**m3.** The worked example in Section II-D mixes circuits from different studies and scales (QAOA H=8/Q=64 raw from Study 21 vs. H=10/Q=100 shifted from Study 20). The column header should explicitly flag "CROSS-STUDY" to prevent misreading.

**m4.** Figures 4 and 5 reference a "Study 16" that is not described anywhere in the main text or experimental section (which covers Studies 17–21). If Study 16 is a predecessor study, it needs at least one sentence of description, or these figures should be replaced by figures drawn from Studies 17–21.

**m5.** The Little's Law section (IV-C) uses W_sojourn for sojourn time, which avoids collision with issue width W. However, the notation W_sojourn itself is unusual; standard queueing theory uses T or S for sojourn time. A brief notation note would help readers familiar with queueing theory.

**m6.** The reference to [LiuLayland1973] appears in the reference list but is never cited in the main text. Remove or cite.

**m7.** The claim in Section IV-B that "throughput of approximately 3.99 nodes/cycle" at W=8, F=4 is presented as confirmation, but no figure or table directly displays throughput values; all tables show stall rate. Throughput data should be tabulated or at minimum the derivation (total_nodes / total_cycles) should be shown.

**m8.** The title uses an underscore identifier (ff_rate_matched) directly. Most top-tier systems/architecture venues would expect either a proper algorithmic name or a formatted label. Minor but worth considering for camera-ready.

---

## 4. Figure Evaluation

### Figure 1 (fig1_pipeline.png) — MBQC Classical Control Pipeline

**Clarity:** Good. The three-stage layout (Issue, Measurement, FF) is clean and immediately readable. The stall gate symbol (orange hexagon with X) at the issue stage and the "stall if ff_in_flight ≥ F" annotation are well-placed. The dual feedback arrows (dependency resolved, credit return) are distinct in color (blue solid vs. blue dashed).

**Correctness:** The D_ff^raw annotation (28–226 cycles QAOA, 15–99 VQE) is consistent with the corrected values in the abstract. The D_ff^shifted = 1–2 cycles annotation is correct. The "burst (shifted DAG, ASAP)" label with red arrows correctly illustrates the overflow problem.

**Visual quality:** Adequate for a conference paper. The color coding (blue = ff_rate_matched path, red = burst/overflow) is consistent with Figure 3. The stage boxes have sufficient whitespace.

**Contribution:** High. This figure anchors the entire paper and is referenced in the first paragraph of Section II. It successfully communicates both the architecture and the problem (burst at FF) and the solution (credit gate) in one diagram.

**Issue:** The figure caption in the paper body says "A solid forward path passes through all three stages. A dashed feedback arrow from the FF stage back to the issue stage represents dependency resolution." But in the actual figure, both feedback arrows appear as blue curves — it is not immediately clear which is the credit return (ff_rate_matched only) vs. the dependency resolution (both policies). A legend or more distinct visual differentiation would help.

---

### Figure 3 (fig3_credit_mechanism.png) — Credit Mechanism vs. ASAP

**Clarity:** Good. The side-by-side layout (ff_rate_matched left, ASAP right) is an effective contrast. The OVERFLOW banner in red on the right panel is visually striking and correctly represents the problem.

**Correctness:** The left panel shows F=4 slots with only 3 occupied (labeled 1, 2, 3) and slot 4 empty, which is consistent with the "stall rate ~0%" annotation. The gate symbol and "GATE: issue only if ff_in_flight < F" label are correct. The right panel shows the FF processor in red with the OVERFLOW label, which correctly represents the ASAP failure mode.

**Visual quality:** Good. The color contrast (blue for controlled state, red for overflow) is effective.

**Contribution:** Moderate-high. This figure is pedagogically useful for readers unfamiliar with credit-based flow control.

**Issue:** The right panel shows "Stall rate ~40–49%" but the paper's data shows W=4, large-scale ASAP stall ranging from 19% (F=3) to 73.5% (W=8). The "40–49%" is a selective slice. This minor inconsistency between the figure annotation and the broader result range could be misleading. Either use a more representative range or add a subscript "(example: W=4, F=2, H=10)."

---

### Figure 6 (fig6_sensitivity.png) — F* Sensitivity Heatmap

**Clarity:** High. The 2×2 panel layout (top row: ff_rm, bottom row: ASAP; left column: vs L_ff, right column: vs L_meas) is immediately interpretable. The color coding (solid green for F*=4, dark red for F*=8) makes the contrast between the two policies visually unambiguous.

**Correctness:** The top row is uniformly "4" (green), which is consistent with the paper's claim that F*(ff_rm) = 4 is invariant across latency parameters. The ASAP bottom row shows "8" uniformly except QAOA L_ff=4,5 which show "6" (orange). This is consistent with Table V-C text stating F*(ASAP) drops to 6 at large L_ff for QAOA only.

**Visual quality:** Good. The legend is clear. However, the figure title is verbose (three lines of title text) and the subtitle "Direct F*=2 confirmation: Study 20 shifted+ff_rm (F=2,3,4) vs Study 21 raw+ASAP" is not reflected in the heatmap panels themselves — the panels show F*=4, not F*=2. This creates a disconnect: the title says F*=2 is confirmed but the panels show green cells labeled "4." A reader expecting to see F*=2 in the top row will be confused. The F*=2 confirmation belongs in a separate subplot or the title should be revised.

**Contribution:** High. This is probably the most informative figure in the paper — it shows at a glance that ff_rm is insensitive to both L_ff and L_meas while ASAP is not. The invariance of the green top row is the central experimental finding.

---

### Figure 7 (fig7_scaling.png) — Stall Rate vs. FF Width (H=10, H=12)

**Clarity:** Moderate. The 2×2 panel layout (QAOA/VQE rows, H=10/H=12 columns) is logical. However, the figure is rendered at low resolution and the multiple line curves (Q=36, Q=64, Q=100 for H=10) are difficult to distinguish at the rendered size, especially when printed in grayscale. The legend entries ("ff_rm Q=36", "ff_rm Q=64", etc.) and dashed/solid line styles are hard to parse in the H=10 panels due to overlap near F=4.

**Correctness:** The qualitative pattern is correct: ff_rate_matched lines are near-zero stall for all F in {2,3,4}, while ASAP lines steeply drop from ~40–70% at F=2 to near-zero at F=4. The raw+ASAP baseline (green dashed horizontal) and the F*=W/2=4 vertical dotted line are correctly placed.

**Visual quality:** Below typical conference standard. The figure is too small for the amount of information it contains; curves overlap significantly in the left panels. The axis labels and tick values are difficult to read at the current rendering size. This figure needs to be either enlarged or split into separate panels for H=10 and H=12.

**Contribution:** High in principle — this is the scale validation that demonstrates H=12 results. But the poor rendering quality undermines its impact. A reader scanning figures would likely give this figure less attention than it deserves.

---

## 5. Section-by-Section Comments

### Abstract

The abstract at ~550 words is approximately twice the typical length for the target venues (ISCA: 150 words, IEEE Quantum Week: 200 words, QIP: structured abstract). The sentence "The full stall range is 0.049%–5.62% (ff_rate_matched) vs. 0.07%–85.71% (ASAP), with a median per-pair absolute reduction of 38.85 percentage points" contains three statistics that add precision without adding insight at the abstract level; these belong in the results section. The abstract should lead with the problem, the solution, and the two headline results: (1) F = W/2 suffices with zero throughput cost, (2) shifted+ff_rm beats raw+ASAP end-to-end.

The sentence "Study 21 further extends the raw-DAG sweep to F ∈ {2,3} (240 additional simulation runs), confirming that the criterion F*(ff_rate_matched) ≤ 2 is satisfied" overstates the strength of the cross-scale comparison. See Major Concern M1.

### Section I (Introduction)

The contributions list is well-structured. Contribution 4 ("4,360 simulation runs on QAOA, QFT, and VQE circuits from H=4 to H=12, Q=16 to Q=100") includes QFT in the headline count, but QFT is excluded from the primary shifted-DAG studies (18–20). The contribution should be qualified: "QAOA and VQE circuits across H=4–12; QFT included in Study 17 only."

The practical implication statement ("halving the FF hardware area while maintaining full throughput") is accurate but should note the "for QAOA and VQE with D_ff_shifted = 1–2" qualifier.

### Section II (MBQC Pipeline Model)

Section II-A's model assumption deserves a citation or derivation for the claim that "every measurement generates exactly one FF operation." See Major Concern M5.

The definition of F* in Section II-D is clean. However, the worked example mixes H=8/Q=64 raw (Study 21) with H=10/Q=100 shifted (Study 20) without flagging this in the table itself. Readers will not detect this without reading the surrounding text carefully. Add a "cross-study" marker to the table.

The claim "D_ff^shifted ≈ 1–2 (both algorithms)" for QAOA and VQE is the critical empirical anchor for the entire paper. The paper never shows a distribution of D_ff^shifted values across all 85+ circuit instances — only specific values for H=8/Q=64 seeds. A table or histogram of D_ff^shifted across the full circuit test set would strengthen this claim substantially.

### Section III (Stall Regression Problem)

Section III-A: The burst load formula B ≈ N/D_ff is presented as a "heuristic measure" that "ignores DAG structural details." However, the paper relies on this heuristic throughout to explain stall regression. A brief comment on when this heuristic can fail — e.g., when nodes are unevenly distributed across DAG levels — would improve the discussion.

Section III-B: The claim "ASAP stall rate on the shifted DAG is nearly independent of L_ff... vary by less than 0.1 percentage points" is a strong result that is stated briefly without a supporting table. This independence claim (ASAP stall is structural, not speed-limited) is central to the paper's argument and deserves its own display item.

### Section IV (ff_rate_matched)

The pseudocode in Section IV-A is correct but note a subtle ordering issue: the code decrements ff_in_flight by completions before incrementing by issue_count. This means completions and new issues within the same cycle are correctly handled (completion credits are available for reuse immediately). This FIFO vs. same-cycle credit recycling behavior should be noted explicitly; it matters for the formal correctness of the invariant ff_in_flight ≤ F.

Section IV-B's flow-balance argument has the circularity issue noted in Major Concern M4. The argument that "the long-run issue throughput under ff_rate_matched is approximately F nodes/cycle" follows mechanically from the construction but does not explain why F=W/2 and not F=W/3 is sufficient. The honest statement is: "We observe empirically that the DAG's own parallelism structure — not the FF width — is the throughput-limiting factor for shifted DAGs with D_ff=1–2, so any F that keeps the queue from overflowing on the critical burst is sufficient, and W/2 empirically achieves this."

### Section V (Experimental Evaluation)

Section V-A: The simulator validation is appropriate but minimal. Two canonical circuits are tested (single-chain and fully parallel). Neither of these tests the burst-load scenario that is central to the paper's concern. A third validation case — a deliberately bursty circuit where the burst load can be analytically computed — would increase confidence in the simulator's correctness in the regime of interest.

Section V-B (Study 17): The claim "Median cycles_ratio: 1.000000" is clean. The 14 discrepant pairs need stronger treatment — see Major Concern M3. The 6 decimal places reported for cycles_ratio (1.000000) are appropriate given that the claim is about exact equality, not approximate equality.

Section V-C (Study 18): The four-way policy comparison table is the most compelling single piece of evidence in the paper. It should be promoted to the paper's executive summary or abstract, not buried in Study 18. The total_cycles comparison (shifted+ff_rm at 1,248 cycles vs. raw+ASAP at 1,284 cycles for QAOA) is the end-to-end result that matters most for practitioners; consider making this a headline result.

Section V-D (Study 19): The finding that L_meas = 4 produces partial F* reduction for QAOA H6 (3/5 seeds) is interesting but the mechanism explanation — "the raw-DAG baseline stall rate increases with L_meas (because the longer measurement pipeline itself increases congestion)" — is counterintuitive and merits a more careful explanation. Why would longer measurement latency increase the raw-DAG stall rate? One expects longer latency to increase total_cycles, not necessarily the stall *rate*. This explanation is incomplete.

Section V-E (Study 20): The convergence of ASAP and ff_rm at F=4 (both near-zero stall) is clearly shown in Table V-E. The explanation — "when F = W/2, ASAP itself rarely triggers the overflow condition" — is correct but slightly circular (it amounts to saying F=W/2 is the threshold because ASAP is fine at F=W/2). The note at the bottom of V-E comparing Study 20 shifted at F=2 to Study 21 raw at F=2 is the key evidence for F*≤2 but the cross-study caveat is stated only as a parenthetical. See Major Concern M1.

Section V-F (Study 21): The non-monotone stall rate explanation is detailed and mechanically correct for the denominator effect. The claim "absolute stall counts are tiny (less than 50 cycles out of thousands of total cycles)" is well-substantiated. However, the implication that this is a *boundary effect* ("boundary effects at computation start and end") is asserted without evidence — the paper should show that the ~7 absolute stall cycles occur at the very beginning or end of execution, not in the middle of the steady state.

### Section VI (Related Work)

The related work is adequate. The NoC credit flow control connection (Dally & Towles 2004) is properly cited and appropriately scoped. The Tomasulo/superscalar connection (Section VI-C) is apt. 

One notable omission: there is no discussion of **prior work on MBQC scheduling at the classical control level** beyond the foundational theory papers (Raussendorf, Broadbent). The paper implicitly claims that no prior work analyzes the stall regression problem in pipeline execution context, but the related work section should do more to survey (and rule out) prior scheduling proposals for MBQC classical control. For example: work on MBQC compilation for specific hardware platforms (photonic, trapped-ion), or work on classical control latency analysis in topological quantum computing (which the paper touches on only through Fowler/Martinis 2012). The related work as written will invite reviewer pushback at venues with MBQC specialists.

### Section VII (Discussion)

Section VII-A's hardware implication ("50% reduction in FF hardware requirements") is the central practical claim and is well-stated. The caveat "the area reduction claim assumes the FF unit is implemented as parallel independent slots... less accurate for fully pipelined single-throughput FF units" is honest and appropriate.

The extreme-case analysis (W=16, F=2, F/W=0.125) in Section VII-A is one of the most interesting results — at 87.5% hardware reduction with zero throughput penalty — but receives only a paragraph. This deserves more prominence.

Section VII-C's limitations are comprehensive. The "probabilistic measurement outcomes" limitation (Sec. VII-C) is important and the paper handles it by noting that the conservative assumption of universal FF generation provides an upper bound on required F. This is correct.

### Section VIII (Conclusion)

The conclusion accurately summarizes the contributions. The bulleted list of validation axes is clear. The closing paragraph connecting classical architecture techniques (NoC, superscalar, queueing theory) to MBQC classical control is well-written and appropriately broad.

---

## 6. Questions for the Authors

**Q1.** The cross-study F* determination (Study 21 raw H=8/Q=64 vs. Study 20 shifted H=10/Q=100) is the evidence for F*≤2. The circuits are at different scales. Could the authors conduct even one experiment pairing raw+ASAP and shifted+ff_rm at F∈{2,3} on identical circuits (e.g., QAOA H=10, Q=100 or QAOA H=8, Q=64) to provide a same-circuit F*=2 data point? Without this, the F*≤2 claim is indicative at best.

**Q2.** The model assumes every measurement generates exactly one FF operation. In practice, does this mean: (a) every issued node triggers an update to the FF correction register regardless of the parity of measurement outcomes, or (b) every node that has a FF edge in the DAG generates a FF operation? If (b), then the ~4–6% of nodes without FF edges never generate FF work — does the simulator correctly model this, and does it affect the quantitative stall results?

**Q3.** The non-monotone raw+ASAP stall rate for VQE H8/Q64 (stall *increases* with F) is explained by total_cycles dropping faster than stall_cycles. But you state total_cycles = 2058, 1379, 1043 for F=2, 3, 4 respectively. For a raw DAG with D_ff_raw=63 and the circuit presumably not dominated by FF contention, why does increasing F from 2 to 4 reduce total_cycles by 49%? Is the raw VQE H8/Q64 circuit genuinely FF-bottlenecked at F=2, and if so, how does this reconcile with the claim that raw DAGs are "well-behaved" and produce low burst load?

**Q4.** Study 17 reports 10 pairs where ff_rate_matched is *slower* than ASAP. You attribute these to tie-breaking in QFT circuits. Can you confirm that all 10 slower pairs are QFT instances, and report the range of cycles_ratio (not just "below ±0.17%") for these 10 cases? The claim "zero throughput cost in every comparison" in the abstract appears inconsistent with 10 slower pairs.

**Q5.** The FF fraction measurement (Section IV-B) reports the fraction of nodes with at least one outgoing FF edge (0.955 for QAOA, 0.974 for VQE). The flow-balance argument uses this to justify "approximately F nodes/cycle long-run issue throughput." But FF fraction ≠ runtime correction probability. Have you verified that the simulator's FF traffic model corresponds to the "FF fraction" measurement or to a probabilistic correction model?

---

## 7. Scores (1–10)

| Criterion | Score | Rationale |
|-----------|-------|-----------|
| Novelty / originality | **7/10** | Clear first treatment of stall regression from signal shift in pipeline context; credit-gate solution is cross-domain import rather than novel invention, but the combination is original. |
| Technical correctness and depth | **6/10** | Mechanically sound, simulator correctly validated; but the flow-balance argument does not analytically justify W/2 specifically, the cross-scale F*≤2 comparison is methodologically weak, and the universal FF generation assumption is incompletely justified. |
| Clarity and presentation | **6/10** | Well-structured and readable, but abstract is too long, Study 16 reference in Figures 4/5 is unexplained, and Figure 7 has rendering quality issues. |
| Experimental rigor and reproducibility | **6/10** | Five-axis validation is thorough; simulator publicly scoped. However: cross-study F* comparison, 10 "slower" pairs in Study 17, denominator-effect explanation without boundary-event evidence, and absence of D_ff^shifted distribution across all circuits weaken rigor. |
| **Overall score** | **6/10** | A solid and practically important paper with a clear problem statement and clean solution; the experimental scope is impressive. The main weaknesses are the overclaimed F*≤2 result, the circular flow-balance argument, and incomplete justification of the universal FF generation assumption. With focused revisions these are addressable. |

---

## 8. Recommendation

**Major Revision**

The paper makes a genuine contribution: stall regression is a real problem, ff_rate_matched is an elegant O(1) solution, and the five-axis validation at 4,360 runs is thorough. The core F=W/2 design principle is well-supported for QAOA and VQE circuits within the tested parameter ranges.

However, the following issues require revision before acceptance:

1. **M1 (Cross-study F*≤2):** The F*≤2 claim in the abstract and contributions must be qualified as a cross-scale indication rather than a confirmed result. Alternatively, a same-circuit F*=2 experiment should be added.

2. **M3 (Zero throughput cost claim):** The abstract's "zero throughput cost in every comparison" claim must be qualified to acknowledge the 10 Study 17 pairs where ff_rate_matched is slower, or the QFT exclusion from the "zero cost" claim must be explicitly stated in the abstract.

3. **M4 (Flow-balance argument):** Section IV-B should be rewritten to clearly state what the flow-balance argument establishes (that the credit gate guarantees the queue is bounded — a mechanical fact) and what it does not establish (why W/2 and not W/3 or W/4 is sufficient). The claim that "the argument is grounded in two empirically verified properties" implies more analytical content than is present.

4. **M5 (FF generation assumption):** A clarifying paragraph in Section II-A should explicitly state what "FF operation" means at runtime (update measurement angle register on all nodes with FF edges, vs. conditional correction on parity). This is essential for reproducibility and for readers evaluating the quantitative stall results.

5. **m4 (Study 16):** Figures 4 and 5 should reference Studies 17–21, not Study 16 (which is not described in the paper), or Study 16 must be introduced.

These revisions do not require new experiments (except optionally for M1) and are primarily about correct scoping of claims, improved argument clarity, and figure quality. The paper would be suitable for acceptance after major revision if these concerns are addressed.

---

## 9. Comparison to Prior Work

The paper cites the foundational MBQC theory papers correctly and completely. The NoC credit-flow control analogy to Dally & Towles 2004 and Kumar et al. 2007 is well-developed. The Tomasulo/superscalar connection is noted appropriately.

The primary differentiator the paper claims — that it is the first to analyze stall regression from signal shift in a pipeline execution context — is plausible given the reference list, but the related work section does not provide a thorough enough survey of MBQC classical control scheduling literature to be confident. Specifically:

1. **MBQC hardware compilation papers** (e.g., for photonic cluster-state computers) have addressed classical control timing constraints; the paper should discuss whether these address the FF scheduling problem and, if not, why.

2. **Fault-tolerant MBQC classical control** papers (Fowler 2012 is cited but only briefly) likely contain implicit scheduling assumptions that interact with the stall regression problem; this connection deserves one paragraph.

3. The **token flow control** paper (Kumar et al. 2007) cited as corroborating evidence for F/W=0.5 is from 2007 NoC router design. The paper should note whether that result is for static or adaptive traffic, since MBQC FF arrivals are structurally determined rather than stochastic — the agreement may be coincidental rather than reflecting a shared mechanism.

The paper is differentiated from all cited prior work in that none of the prior work addresses the specific combination of: (a) signal shift compilation, (b) burst-load stall regression, (c) credit-based scheduling policy, and (d) the F=W/2 hardware sizing result. This differentiation is clearly established by the paper's narrative, though a more thorough literature survey would strengthen the case.

---

*End of review.*
