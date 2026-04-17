# Independent Reviewer Report

**Paper:** ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation

**Reviewer expertise:** Quantum computing architectures and compilation; classical computer architecture (CPU pipelines, memory systems, NoC); systems evaluation methodology.

**Review date:** 2026-04-17

---

## 1. Summary

This paper addresses a previously uncharacterized problem in Measurement-Based Quantum Computing (MBQC) classical control: **stall regression** caused by applying signal shift compilation without a commensurate scheduling policy. Signal shift reduces feedforward chain depth D_ff from O(100) to O(1), which collapses the natural staggering of FF-ready nodes and causes massive burst arrivals that overwhelm the finite-width FF processor, paradoxically increasing total execution time compared to the unoptimized baseline. The paper's core contribution is **ff_rate_matched**, a credit-based issue policy (one counter, one comparator) that gates node issue on the in-flight FF count, preventing overflow by construction. The key claimed result is that setting F = ceil(W/2) — half the issue width — is sufficient to eliminate stall regression, yielding a 50% reduction in FF hardware requirements while incurring zero throughput penalty. This claim is supported by a flow-balance argument invoking Little's Law and validated across four experimental axes (F/W sensitivity, L_ff sensitivity, L_meas sensitivity, circuit-scale scaling) over 4,120 simulation runs on QAOA and VQE circuits up to Q=100 qubits. The practical importance is clear: as MBQC classical control becomes an architectural bottleneck at scale, a simple, provably bounded scheduling policy with well-characterized hardware requirements is directly actionable by system designers.

---

## 2. Strengths

- **Well-motivated problem.** The stall regression phenomenon is non-obvious and counter-intuitive: a compilation optimization that is universally praised for reducing FF depth turns out to create a bursty scheduling pathology when paired with the naive ASAP policy. Naming and systematically characterizing this effect is a genuine contribution.

- **Elegant solution.** ff_rate_matched is minimal and correct: one counter, one comparator, O(1) per cycle. The design requires no DAG knowledge, no look-ahead, and no tuning. The analogy to credit-based NoC flow control is apt and illuminating.

- **Comprehensive experimental validation.** Four independent axes of sensitivity analysis (F/W ratio, L_ff, L_meas, circuit scale), 4,120 simulation runs, three circuit families, multiple qubit counts and random seeds. The methodology is systematic and the coverage is strong.

- **Honest calibration of empirical scope.** The paper explicitly labels the F* = W/2 claim a "Design Principle confirmed by simulation" rather than a theorem, acknowledges limitations (QFT coverage gap, D_ff <= 2 scope, probabilistic FF not modeled), and notes where the raw-DAG baseline sweep is incomplete at F < 4. This is uncommon intellectual honesty in a systems paper and strengthens credibility.

- **Well-executed four-way comparison (Table V-C).** Comparing all four combinations of {raw, shifted} x {ASAP, ff_rate_matched} at identical hardware parameters is the right controlled experiment. Showing that shifted+ff_rate_matched achieves both lower stall and lower total cycle count than raw+ASAP makes the end-to-end case compellingly.

- **Clear cross-disciplinary framing.** The connections to NoC credit-based flow control, RAW hazard prevention, Tomasulo's algorithm, Little's Law, and RMS theory are useful and mostly appropriate. The paper is careful to label analogies as analogies rather than formal reductions.

- **Good simulator validation.** The single-chain and fully-parallel canonical test cases, and the explicit correctness conditions checked before use, give confidence in the simulator.

- **Simulator pseudocode is provided.** The 6-line credit-gate loop is fully specified and unambiguous, enabling reproduction.

---

## 3. Weaknesses and Concerns

### Major Concerns

**M1. The "design-safe threshold" F* = W/2 is only weakly justified — the raw-DAG sweep stops at F = 4.**

Section II-D explicitly acknowledges that F*(ff_rate_matched) <= 2 cannot be excluded because raw+ASAP stall data at F < 4 was never collected. The definition of F* requires comparing shifted+ff_rm stall to raw+ASAP stall at the *same* F. If raw+ASAP stall at F=2 is, say, 0.02%, then shifted+ff_rm at 0.05% would violate the criterion and F*=2 would not hold. The paper sidesteps this by fixing F=4 as the conservative reporting point, but this is a gap in the experimental design, not a conservative choice. A reviewer cannot validate whether F* = W/2 is the minimal hardware target without that baseline. **Recommendation:** Either extend the raw-DAG sweep to F in {2, 3} or explicitly state and justify why the F=4 design point is the practical target (e.g., hardware granularity, not fundamental minimality). The current phrasing "design-safe threshold" may mislead readers into thinking F=4 is tight when it may not be.

**M2. The theoretical justification for F* = W/2 is circular.**

Section IV-B states that "setting F = W/2 limits the credit-gated issue rate to W/2 nodes/cycle" and then observes empirically that throughput at F=W/2 matches F=W. The Little's Law argument (Section VI-D) is similarly empirically grounded: the bound F/L_ff >= lambda follows from L <= F, but the claim that lambda ≈ W/2 at steady state is asserted, not derived. The paper then says "the empirical evidence strongly supports the design principle," which reads as circular (the principle is derived from the same empirical runs it is said to support). This is acceptable for an empirically-grounded systems paper, but the paper intermittently uses the language of theorems ("Design Principle," "formal statement," Section IV-B header "Theoretical Analysis: Why F* = ceil(W/2)"). The gap between "theoretical argument" and "confirmed by simulation" should be made explicit at the beginning of Section IV-B rather than buried in the caveats at the end. As written, a reader could mistake the "Formal Statement" box for a proven theorem when it is an empirically confirmed design principle.

**M3. QFT is omitted from Studies 18–20 without adequate justification.**

The QFT gap is attributed to a "DAG generation artifact at H=8, Q=64 shifted." This is mentioned three times but never explained. What is the artifact? Does the signal-shift compiler fail to terminate, produce an incorrect DAG, or produce a DAG with D_ff > 2? Does QFT at H=8, Q=64 present a structurally different challenge that might invalidate the F* = W/2 principle for the QFT family? The paper's summary box explicitly qualifies the result to "QAOA and VQE," which is honest but weakens the generality of the contribution. If QFT represents a class of circuits with distinct burst structure (its regular FFT butterfly pattern is quite different from QAOA/VQE), omitting it from large-scale studies is a substantive coverage gap.

**M4. The model assumes every measurement generates exactly one FF operation (FF fraction = 1.0), which conflicts with hardware reality and inflates the practical case for ff_rate_matched.**

Section II-A acknowledges this is a conservative upper bound. Section IV-B then measures empirical FF fractions of 0.91–0.99 for the test circuits and uses this to justify the F = W/2 result. But if FF fraction were, say, 0.5 (half of nodes need correction), then the effective burst load B_eff ≈ 0.5 * N / D_ff, and ASAP might self-correct at F < W/2 for some circuits. The paper mentions this as a "future work" item (Section VII-C), but it is architecturally significant: a designer with circuits having FF fraction 0.5 who follows the W/2 guideline would over-provision. The paper should quantify how F* changes as a function of FF fraction, or at minimum provide tighter guidance.

**M5. The burst load approximation B ≈ N / D_ff is used throughout but not validated.**

This heuristic ignores DAG topology (width profile, node degree distribution, wavefront shape) entirely. Section III-A introduces it as "a heuristic measure; it ignores DAG structural details but captures the dominant effect." Section V-B (Figure 5) shows a strong positive correlation between B and F*(ASAP). However, no quantitative fit is provided and no bounds on the approximation error are given. For circuits where the DAG's parallelism is highly uneven (e.g., one very wide DAG level followed by narrow levels), B could be a poor predictor. The paper would be strengthened by showing a scatter plot of actual burst peak (measured from simulation) versus N/D_ff, or bounding the approximation error.

### Minor Concerns

**m1. Inconsistency in D_ff^raw figures.**

The abstract states D_ff^raw ≈ 100–300 cycles. Section II-B's experimental figures report D_ff^raw ≈ 63–139 for H=8, Q=64. Figure 1 caption repeats 100–300. The discrepancy is not explained. Is 100–300 from larger circuits not described elsewhere? If so, which? If not, the abstract is inaccurate.

**m2. The RMS (Rate Monotonic Scheduling) analogy is a poor fit and should be demoted or removed.**

Section IV-C presents the RMS analogy as "intuition only" and explicitly caveats that it is not a formal proof. But the analogy is structurally incorrect: RMS applies to n periodic independent tasks sharing a uniprocessor, while the FF pipeline processes a DAG-constrained stream of aperiodic events through a parallel-slot unit. The utilization bound 0.5 <= ln(2) ≈ 0.693 is presented as if it corroborates the W/2 threshold, but this is coincidental: RMS utilization and FF width fraction are not the same quantity. Section VI-D repeats this analogy. The analogy adds no insight and risks confusing a reader familiar with RMS theory.

**m3. The paper claims "zero throughput penalty" but 14/360 pairs in Study 17 show non-zero deviations (up to ±0.17%).**

These are attributed to tie-breaking artifacts in QFT circuits. The "zero" claim in the abstract and summary box is therefore slightly overstated. "Negligible throughput penalty (< 0.2% in all cases, zero for non-QFT)" would be more precise. The paper does explain this clearly in Section V-B, but the mismatch with the abstract is an editorial issue.

**m4. Figure numbering and figure paths are inconsistent.**

Figures 2, 4, and 5 reference paths inside the research subdirectory (../../research/mbqc_pipeline_sim/...), while Figures 1, 3, 6, and 7 reference the paper's figures/ directory. The paper mixes production figures and scratch study artifacts. Figures 4 and 5 (from Study 16, H=4–8) are used in Section V-E which discusses Study 20 (H=10, H=12), with a parenthetical noting Study 20 is "consistent with" Study 16. These should be replaced with Study 20 figures or explicitly placed in a separate section.

**m5. "cycles_ratio" is the stated throughput metric, but its definition (shifted+ff_rm / ASAP) is never explicitly provided in the text.**

The metric appears in tables and text without a formal definition. A one-line definition should be added to Section V-A where metrics are listed.

**m6. The paper title contains two compound technical terms ("ff_rate_matched" and "signal shift compilation") without disambiguation for readers unfamiliar with the MBQC literature.**

A subtitle or opening sentence orienting non-MBQC readers would improve accessibility for a systems/architecture audience.

**m7. The worked example in Section II-D (F* = W/2, not F* = 2) is convoluted.**

The paragraph "Why not F* = 2?" introduces F=2 data from Study 20 but then retreats because raw+ASAP data at F=2 is unavailable. This could confuse readers. The section would be cleaner if it directly stated the limitation upfront: "The dataset minimum for the raw-DAG sweep is F=4; we therefore define the design-safe threshold as F=4=W/2 for the scope of this paper."

**m8. Table II-D (worked example) shows only F=4 with one circuit.**

A table showing F* across all seeds for the worked example circuit would make this more convincing. The single-seed, single-F presentation is sparse.

---

## 4. Figure Evaluation

### Figure 1 (fig1_pipeline.png) — MBQC Classical Control Pipeline

**Clarity:** Good. The three-stage layout is clean, with the credit-return arrow and stall gate clearly labeled. The "burst (shifted DAG, ASAP)" annotation at the FF queue is effective.

**Correctness:** There is a minor annotation issue: Figure 1 shows D_ff^raw ≈ 100–300 cycles (consistent with the abstract) but Section II-B reports D_ff^raw ≈ 63–139 for the actual experimental circuits. This discrepancy is not reconciled. If the figure represents a qualitative range across all circuits (including those not in the experiments), this should be stated. Otherwise, one of the values is wrong.

**Contribution:** Central to the paper's narrative. The figure immediately establishes the pipeline model and makes the stall regression mechanism visually intuitive. The dual annotations (credit return vs. dependency resolved) appropriately distinguish ff_rate_matched from ASAP feedback.

**Recommendation:** Reconcile the D_ff^raw range with the experimental values in Section II-B.

---

### Figure 3 (fig3_credit_mechanism.png) — Credit-Based Flow Control vs. ASAP

**Clarity:** Excellent. The left/right comparison with color coding (blue = healthy, red = overflow) is immediately interpretable. The OVERFLOW banner on the right panel drives the message home. The gate symbol and "issue only if ff_in_flight < F" label are crisp.

**Correctness:** The figure shows F=4 slots on the left panel with slots labeled 1, 2, 3, 4. This is consistent with the F=4=W/2 example used throughout the paper.

**Contribution:** This is the best figure in the paper. It encapsulates the entire mechanism in one glance and would be the figure a practitioner would reproduce in a talk.

**Recommendation:** Add the ASAP stall rate range (39–49%) as a label on the right panel to make the quantitative impact immediately visible. Currently stall rate 40–49% appears only in text labels at top-left of the right panel, which is easy to miss in print.

---

### Figure 6 (fig6_sensitivity.png) — Sensitivity Heatmap

**Clarity:** Very good. The 2x2 grid (ff_rm vs. ASAP, L_ff vs. L_meas) with discrete color scale (green/orange/red) immediately communicates the invariance of ff_rm vs. the fragility of ASAP. The use of bold numbers inside cells is effective.

**Correctness:** One issue: the legend color for F*=5–6 is labeled in the figure as a yellow-green, but the actual cell at QAOA, L_ff=4 and L_ff=5 (bottom-left) appears orange, while the legend says orange = F*=7. This label-color mapping should be verified. The paper text states F*(ASAP, QAOA) drops from 8 to 6 at L_ff >= 4 (Table in Section V-C), which should map to yellow-green (5–6), but the cell appears orange. This may be a rendering artifact or a legend inconsistency.

**Contribution:** Central to the Sections V-C and V-D arguments. The uniform-green top row is the most visually compelling summary of the paper's empirical claim.

**Recommendation:** Verify and correct the color scale mapping. Add a note in the caption explaining why QAOA H6 / L_meas=4 (bottom-right) is green (partial exception) vs. all other ASAP cells being red or orange.

---

### Figure 7 (fig7_scaling.png) — Stall Rate vs. FF Width (H=10, H=12, Study 20)

**Clarity:** Moderate. The 2x2 panel layout (QAOA/VQE x H=10/H=12) is logical, but the individual curves for Q=36/64/100 are rendered in slightly different shades that are difficult to distinguish in low-contrast print. The logarithmic/linear scale choice is not stated in the axis labels.

**Correctness:** The figure correctly shows ff_rm maintaining near-zero stall across F in {2, 3, 4} while ASAP shows monotone decrease converging at F=4. The raw+ASAP baseline (green dashed) as a horizontal reference line is the right comparison point. The vertical dotted line at F=4=W/2 is an effective annotation.

**Contribution:** This is the "scaling" evidence figure and provides the crucial confirmation that the F*=W/2 result is not an artifact of small circuits. The H=12 panels add important coverage.

**Recommendation:** (1) Increase line width or marker differentiation for Q=36/64/100 curves. (2) Add axis units (Stall Rate [%]) explicitly. (3) The H=12, Q=64 panels are sparser than the H=10 panels — note in caption whether the Q=100 point is absent for H=12 due to circuit size limitation or the DAG generation issue.

---

## 5. Section-by-Section Comments

### Abstract

- "Burst arrivals of ready nodes overwhelm the FF processor, causing issue stalls that are *worse* than the unoptimized baseline" — good framing, but "worse" here means "higher stall rate" not necessarily "worse total cycles." The abstract should be explicit that stall regression is a cycle-count regression, not just a stall-rate regression, since the paper's main metric is cycles_ratio.
- "halving the required FF hardware compared to ASAP scheduling" — this appears twice in the abstract (once in the body and once in a standalone sentence starting "Notably"). Remove the redundancy.
- The abstract states "1,080 paired comparisons at large scale" but the paper also reports 360 pairs in Study 17 and 1,440 total. Clarify which number belongs in the abstract or use the larger figure.
- D_ff ≈ 100–300 in the abstract vs. D_ff ≈ 63–139 in the experiments — reconcile (see major concern m1 above).

### Section I (Introduction)

- The NoC credit analogy is introduced twice in consecutive paragraphs (paragraph 3 and the contributions list). Consolidate.
- "This is precisely the mechanism of credit-based flow control" — the language is strong but the analogy is not yet introduced. Consider deferring the analogy to Section IV where it can be explained properly, or providing a brief forward reference.
- Contribution 3 says "derived from a flow conservation argument analogous to Little's Law." As noted in M2 above, "derived" overstates the result; "motivated by" or "consistent with" is more accurate.

### Section II (MBQC Pipeline Model)

- Section II-A: "every measurement generates exactly one FF operation" — this is stated as a model assumption but is also an upper bound. The phrase "conservative assumption" is used, but the paper goes on to derive F* = W/2 from this assumption. The conclusion (F* = W/2) is therefore conservative in the sense of over-provisioning, but the paper does not say so explicitly.
- Section II-B: Signal shift is described as applicable when "all corrections are Pauli (Clifford) byproducts." This is accurate for the standard one-way model, but QAOA and VQE circuits involve non-Clifford gates (parameterized rotations). The paper should clarify exactly how signal shift applies to these circuits. Do the simulated circuits have D_ff^shifted = 1-2 because the non-Clifford parts are handled separately, or is there a simplification in the circuit model used for the experiments?
- Section II-D (Definition of F*): The definition is careful and correct. However, the worked example immediately below is for a single seed of one circuit at one latency setting. The reader cannot tell from this example how representative it is.

### Section III (The Stall Regression Problem)

- Section III-B: "The stall regression magnitude exceeds 40 percentage points" — note that the comparison is between F=2 (shifted ASAP) and F=4 (raw+ASAP at a *different* F). This is mixing hardware configurations and is not a controlled comparison. It is informative but should be flagged as such in the text.
- Section III-C: "ASAP has no mechanism to sense FF saturation before it occurs" — this is accurate. The paragraph is good but could note that adding a saturation detector to ASAP (rather than a full credit gate) would be a weaker alternative; the credit gate is stronger because it prevents overflow, not just detects it.

### Section IV (ff_rate_matched)

- Section IV-A: The pseudocode is clean and correct. One issue: "available_credits = max(0, F - ff_in_flight)" — if ff_in_flight can exceed F (which should not happen with the credit gate), this is a clamp, which suggests the code handles an inconsistency case. If the invariant ff_in_flight <= F holds by construction, the max(0, ...) is unnecessary. Clarify which is the case.
- Section IV-B (header): "Theoretical Analysis: Why F* = ceil(W/2)" — as noted in M2, this is an empirically confirmed design principle, not a theoretical proof. Rename to "Empirical Characterization and Intuition for F* = ceil(W/2)."
- Section IV-B: The FF fraction measurements (0.955, 0.974, 0.986) are interesting and should be connected more explicitly to the D_ff^shifted = 1–2 assumption. Specifically: if FF fraction is ~0.96, do the remaining 4% of non-FF-generating nodes act as "bubble" cycles that help drain the FF queue between bursts? This could be why even F=2 works.
- Section IV-C: The Tomasulo analogy is good and apt. The RMS analogy should be removed or demoted to a footnote (see m2 above).

### Section V (Experimental Evaluation)

- Section V-A: The canonical validation (single chain + fully parallel) is good but should be reported with the numerical results (i.e., "For a chain of N=100 with L_meas=2, L_ff=3, expected 500 cycles, measured 500 cycles"). The current description is too vague to be checkable.
- Section V-B (Study 17): "The 14 discrepant pairs are all QFT circuits" — if QFT is later dropped from Studies 18–20, this raises the question of whether there is a structural reason that QFT produces tie-breaking anomalies. The paper does not connect these observations.
- Section V-C (Study 18): The four-way comparison table is excellent. The note that shifted+ff_rm cycle counts (1,248 for QAOA, 1,027 for VQE) are lower than raw+ASAP (1,284, 1,043) is a key result and should be in the abstract or at least in the introduction.
- Section V-D (Study 19): "the raw-DAG baseline stall rate increases with L_meas (because the longer measurement pipeline itself increases congestion)" — this causal claim is asserted but not demonstrated. It should be supported with a table or plot showing raw+ASAP stall vs. L_meas to confirm this mechanism.
- Section V-E (Study 20): "all 1,080 paired comparisons yield exact cycle matches" — this is the strongest result in the paper and should be stated as such, with emphasis on H=12, Q=100 as the maximum scale tested.
- The "summary box" in Section V-F is valuable but the claim "1,440 paired comparisons" does not match the "1,080" from Study 20 cited just above; the 360 from Study 17 plus 1,080 from Study 20 = 1,440. This arithmetic should be made explicit.

### Section VI (Related Work)

- Section VI-A: "we are not aware of a published treatment that specifically analyzes the stall regression consequence of signal shift in a pipeline execution context" — this is a strong claim that the problem is novel. It is plausible but the paper would benefit from a brief search justification (e.g., "We searched proceedings of [venues] and found no work...").
- Section VI-B: The Kumar et al. [KumarPeh2007] citation ("credit pool equal to half the link bandwidth is sufficient under typical traffic distributions") is a useful corroboration, but the paper should note the key difference: NoC traffic is typically independent and stochastic, while the MBQC FF arrivals are structurally determined by the DAG. The agreement at F/W = 0.5 may be coincidental.
- Section VI-D: The Little's Law application is stated but the sojourn time is implicitly set to L_ff. For a queued system, sojourn time >= L_ff (it includes waiting time). The bound lambda <= F / L_ff holds only at zero queuing delay (no waiting), which is the credit-gate's guaranteed condition (since ff_in_flight <= F means no overflow queue can form). The paper should state this explicitly: "Under ff_rate_matched, no overflow queue forms, so sojourn time = L_ff exactly, making the Little's Law bound tight."

### Section VII (Discussion)

- Section VII-A: "The area reduction claim assumes the pipeline model's assumptions hold" — this is a necessary caveat, but the paper could be more specific about what "FF processing slots" means in hardware: dedicated functional units? buffer entries? The area argument depends on which resource is being halved.
- Section VII-C: The out-of-order extension is promising. The paper should note that this is possible only if there exist non-FF-dependent nodes in the ready queue at the time credits are blocked — which is not guaranteed for all DAG structures.

### Section VIII (Conclusion)

- The conclusion is accurate and well-organized. The "More broadly..." paragraph connecting to classical architecture is appropriate and adds context.
- "As quantum processors scale and classical control becomes an increasingly dominant cost" — a citation or quantitative statement to support this claim would strengthen the motivation.

---

## 6. Questions for the Authors

**Q1. Raw-DAG sweep at F < 4.**
The design-safe threshold F* = W/2 = 4 is established by comparing shifted+ff_rm stall at F=4 to raw+ASAP stall at F=4. The paper explicitly acknowledges that raw+ASAP stall at F=2 and F=3 is unknown, and that F* might be lower. Did you perform any experiments with the raw DAG at F=2 or F=3, even informally? If so, what did you observe? If not, why was F=4 chosen as the sweep minimum for the raw-DAG studies?

**Q2. QFT DAG generation artifact.**
What exactly causes the DAG generation failure for QFT at H=8, Q=64 shifted? Is it a compiler bug, a structural property of QFT under signal shift (e.g., residual D_ff > 2 that the paper's model cannot handle), or a numerical issue? Does QFT at H=8, Q=64 *unshifted* present different burst structure than QAOA/VQE? Is there a reason to expect F* = W/2 might NOT hold for large-scale QFT?

**Q3. QAOA/VQE circuit model and signal shift scope.**
QAOA and VQE circuits involve parameterized single-qubit rotations (Rz gates) that are non-Clifford. Signal shift as described in [DanosKashefi2006] applies to Clifford byproducts. How exactly is signal shift applied to the QAOA/VQE circuits in your experiments? Are the non-Clifford corrections handled by a different mechanism, or do the simulated circuits represent a Clifford-only approximation? This directly affects whether the D_ff^shifted = 1–2 claim holds for general QAOA/VQE.

**Q4. Tie-breaking discrepancies in QFT circuits (Study 17).**
Fourteen out of 360 pairs in Study 17 show non-zero cycles_ratio deviations (up to ±0.17%), all in QFT circuits. Since QFT is also the circuit family with the DAG generation artifact in Studies 18–20, is there a structural reason QFT behaves differently under ff_rate_matched? Does ff_rate_matched interact with QFT's regular butterfly structure in a way that differs from QAOA/VQE?

**Q5. Hardware area claim validation.**
The paper claims a "50% reduction in FF hardware area." This depends on FF processing being implemented as parallel independent slots (each slot holding one in-flight FF operation). For what hardware targets is this model accurate? In a real MBQC classical control processor (e.g., FPGA, ASIC), would FF processing be implemented as a register file with W entries, and would halving W literally halve area? Or is the FF processor a pipelined unit where the relationship between F and area is more complex?

---

## 7. Scores

| Criterion | Score (1–10) | Justification |
|---|---|---|
| Novelty / originality | **7** | The stall regression phenomenon is novel and well-named. The credit-gate solution is elegant but conceptually simple (direct application of known NoC technique). The F* = W/2 design rule is the main quantitative novelty. |
| Technical correctness and depth | **6** | The simulation is thorough and the accounting is careful. However, the theoretical justification for F* = W/2 is empirical rather than analytical, the raw-DAG sweep is incomplete at F < 4, and the burst load approximation B ≈ N/D_ff is unvalidated quantitatively. |
| Clarity and presentation | **7** | Generally well-written with clear notation. Figure 3 is excellent. Weaknesses: inconsistent D_ff^raw figures between abstract and experiments, the "theoretical analysis" section header overstates the result, and the QFT anomalies are underexplained. |
| Experimental rigor and reproducibility | **7** | Four-axis sweep with 4,120 runs is impressive. Simulator pseudocode is provided. Canonical validation cases are described. Gaps: QFT large-scale missing, raw-DAG sweep missing at F < 4, canonical validation results not numerically reported, cycles_ratio undefined in Section V-A. |
| Overall score | **6.5** | A solid, honest systems paper with a clear practical contribution and well-executed experiments. The main weaknesses — incomplete theoretical grounding and the F < 4 raw-DAG gap — prevent a strong accept. With targeted revisions these could be addressed. |

---

## 8. Recommendation

**Major Revision**

The paper makes a useful contribution and the experimental work is extensive. However, several issues require substantive revision before publication:

1. The raw-DAG sweep must be extended to F=2 and F=3, or the paper must clearly reframe F* = W/2 as a conservative design point (not a tight minimum) and explain why F=4 is the practical design target.

2. Section IV-B must be retitled and restructured to avoid implying a proof where only simulation evidence exists. The Little's Law argument should be presented as motivation and consistency check, not derivation.

3. The QFT DAG generation issue must be explained and its implications for the generality of the F* = W/2 claim must be addressed.

4. The D_ff^raw discrepancy between the abstract/Figure 1 (100–300 cycles) and the experimental text (63–139 cycles) must be reconciled.

5. The four-way comparison result (shifted+ff_rm outperforms raw+ASAP in total cycles) is among the most important results and should be elevated to the abstract.

These revisions are substantial but not fundamental — the core contribution and experimental methodology are sound. The paper is unlikely to be fatally flawed but requires careful revision to accurately represent the scope and strength of its claims.

---

## 9. Comparison to Prior Work

The paper's positioning relative to prior work is generally adequate but has gaps.

**What is well-differentiated:**
- The specific problem of stall regression under signal shift + ASAP scheduling is not treated in prior MBQC compilation work ([DanosKashefi2006], [Broadbent2009]). These works analyze FF depth reduction as uniformly beneficial; the pipeline execution dynamics are not modeled.
- The ff_rate_matched policy and its F* = W/2 design rule are not present in the cited literature.
- The quantitative characterization of burst load B ≈ N/D_ff is new, even if not rigorously bounded.

**Where the positioning is weak:**
- The paper does not cite or discuss quantum circuit scheduling work beyond MBQC (e.g., superconducting qubit gate scheduling, trapped-ion instruction scheduling), where analogous pipeline bottleneck problems have been studied. These are different hardware models but the scheduling insight (credit gating) may have been applied before.
- The paper does not cite recent MBQC architecture papers (e.g., Nickerson and Rudolph 2014, Litinski 2019 on resource state geometry, or Bombin et al. on MBQC for fault-tolerant computation with topological codes) that discuss classical control latency constraints. The fault-tolerant setting mention in Section VII-C is too brief given that fault tolerance is the dominant motivation for large-scale MBQC.
- The Kumar et al. [KumarPeh2007] citation on NoC credit pools with F/W = 0.5 is useful and under-discussed. The paper should either develop this parallel more carefully (explaining precisely which traffic model applies and whether the circuit-structured DAG arrival stream satisfies the assumptions) or reduce it to a remark.
- There is no discussion of existing MBQC simulation frameworks or compilation toolchains (e.g., PySi2q, mbqcflow, or other open tools). If the simulation is entirely custom, this should be noted; if existing tools were used as a base, they should be cited.

Overall, the paper is credibly differentiated from the specific prior work it cites. The comparison would benefit from broader coverage of adjacent scheduling literature.

---

*End of review.*
