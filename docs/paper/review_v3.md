# Referee Report (Round 3): "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)
**Round:** Third review of revised draft (v3)

---

## 1. Overview of Revision

This revision addresses the two highest-priority blocking issues from Round 2 in one coordinated move: the writer measured the FF fraction for all circuits in the test set and discovered that it is ~95–99%, not ~50%. The "structural half-fraction" claim that was Round 2's central unresolved issue was simply wrong, and the writer corrects it honestly. The four-way comparison table — missing through two prior rounds — is now present in Section V-C. Several citation-level fixes (DanosKashefi key, $W_{\mathrm{service}}$ notation, Figure 4/5 provenance) are also addressed.

The net effect is a draft that is substantially more honest and internally consistent than v2. The high FF fraction finding complicates the $F^* = W/2$ explanation but the revised explanation in Section IV-B is materially better than its predecessor. A small number of issues remain — one at moderate priority and two at minor priority — before this paper reaches a clean acceptance threshold.

---

## 2. Status of Round-2 Blocking Issues

### Blocking Issue 1 — Structural half-fraction claim unsubstantiated

**Status: Resolved. The empirical correction is honest and the revised argument is materially better.**

The writer measured FF fraction across all 100 test instances and reports the result directly in Section IV-B:

> "QAOA (H=4–12, Q=16–100, 50 instances): FF fraction = 0.955 ± 0.025 (mean ± std), range 0.906–0.984 [...] In all cases the FF fraction is close to 1.0, not 0.5."

This is the honest and scientifically correct response to Round 2's demand: measure it and report it. The writer also explicitly acknowledges the prior error:

> "The 'structural half-fraction' heuristic stated in draft v2 was incorrect: it confused the pipeline's effective FF arrival rate with the fraction of nodes carrying FF edges."

This self-correction is commendable. The Round 2 concern is fully resolved at the level of factual accuracy.

However, the resolution raises a new question that the revised text only partially answers (see Section 4 below): if FF fraction is ~0.95–0.99, the constraint `ff_in_flight ≤ F = W/2` limits effective throughput to approximately $W/2$ nodes/cycle, not $W$ nodes/cycle. The paper now acknowledges this explicitly:

> "Since virtually all (≥90%) of issued nodes generate FF work, the long-run issue throughput under ff\_rate\_matched is approximately F nodes per cycle, not W nodes per cycle."

And confirms it empirically:

> "At W=8, F=4, L_ff=2, the simulator achieves throughput of approximately 3.99 nodes/cycle — consistent with F = 4 being the binding bottleneck, not the issue width W=8."

The revised argument — that both ASAP and ff\_rate\_matched achieve the same total cycle count because both are throttled to ~F nodes/cycle by different mechanisms (reactive stall vs. proactive credit gate) — is correct and well-stated. This is a materially better explanation than anything in v1 or v2.

**Residual concern (non-blocking, moderate):** The new explanation raises an implicit question about why $F^* = W/2$ is the threshold rather than some other value. The paper asserts this is the empirical finding — which is supported — but does not explain *why W/2 specifically* emerges as the boundary. With FF fraction ~0.95–0.99, one might naively expect $F^* \approx 0.95W$ to $0.99W$, not $W/2$. The text in Section IV-B attempts to explain this via the shifted DAG's structural parallelism:

> "The shifted DAG exposes enough parallel nodes to keep the credit-gated pipeline busy at F nodes/cycle, and the DAG does not have sufficient depth-parallelism to sustain a rate higher than F for the tested configurations."

This is a plausible account, but it is circular in a subtle way: it says $F^* = W/2$ works because the DAG's parallelism admits issue at rate $F = W/2$, but does not explain why $W/2$ rather than, say, $W/3$ or $W/4$ is the minimum. The $F/W = 0.125$ case in Section IV-B adds to this puzzle:

> "At extreme credit tightness (F=2, W=16, F/W=0.125), the credit gate fires whenever more than 2 nodes are in-flight. Despite this aggressive throttling, Study 17 finds cycles\_ratio = 1.000 in all cases."

If cycles\_ratio = 1.000 at F/W = 0.125, then $F^*$ might be as low as $W/8$ for some circuits — yet the paper identifies $F^* = W/2$ as the threshold. The threshold definition appears to be the smallest $F$ at which *stall regression* vanishes (shifted stall ≤ raw stall), not the smallest $F$ at which throughput equals ASAP. These are different criteria, and the paper conflates them in the Design Principle. For example, at F=2, W=8, cycles\_ratio = 1.000 (by Study 20's 100% match rate), so throughput is fine — yet the stall table shows ASAP at F=2 exhibits 39.8% stall while ff\_rate\_matched is 0.05%. Whether F=2 with ff\_rate\_matched counts as "zero stall regression" is ambiguous: the stall rate is 0.05% (below raw stall), so by definition it *does* meet the stall regression criterion. This means $F^* \leq 2$ for ff\_rate\_matched, contradicting the $F^* = 4 = W/2$ claim. The paper needs to reconcile this: is $F^*$ defined as the minimum F for zero stall regression (in which case Study 20 data suggest $F^* = 2$, not $F^* = 4$), or as the minimum F for which both stall regression and throughput cost are zero simultaneously (in which case the definition needs to be stated explicitly)?

**Required clarification (moderate priority):** Reconcile the $F^*$ definition with the Study 20 stall table, which shows ff\_rate\_matched achieving <0.5% stall at F=2 (below raw baseline), implying $F^*$ could be 2, not 4. Either redefine $F^*$ precisely or explain why F=4 is singled out as the threshold.

### Blocking Issue 2 — Four-way comparison table missing

**Status: Resolved. The table is present and does the required work.**

Section V-C now contains a four-row table comparing (raw, ASAP), (raw, ff\_rm), (shifted, ASAP), (shifted, ff\_rm) for QAOA H8/Q64 and VQE H8/Q64 at W=8, F=4, L_ff=2. The table reports stall rates and notes in the caption:

> "Note that total cycle counts for shifted ff\_rate\_matched (1,248 cycles for QAOA; 1,027 for VQE) are lower than for raw ASAP (1,284/1,043 respectively), confirming that the shifted + ff\_rate\_matched combination achieves strict throughput improvement over the unoptimized raw + ASAP baseline."

This is exactly what Round 2 required. The stall pattern — raw has low stall under both policies, shifted + ASAP causes regression, shifted + ff\_rm recovers — is unmistakably clear:

| DAG variant | Policy | QAOA stall | VQE stall |
|:-----------:|:------:|:----------:|:---------:|
| raw | ASAP | 3.45% | 0.86% |
| raw | ff\_rm | 1.87% | 0.77% |
| shifted | ASAP | **25.23%** | **46.25%** |
| shifted | ff\_rm | **0.24%** | **0.29%** |

The stall regression and recovery pattern is unambiguous. The cycle count comparison (shifted + ff\_rm < raw + ASAP) anchors the co-design claim. Round 2 blocking issue fully resolved.

---

## 3. Status of Round-2 Non-Blocking Issues

### Issue A — Little's Law $W_{\mathrm{service}}$ notation collision

**Status: Resolved.**

Section VI-D (now labeled Section VI-D in v3) uses $\mu$ for the service time parameter throughout, eliminating the collision with pipeline width $W$:

> "at steady state, mean queue length $L = \lambda \cdot \mu$, where $\lambda$ is the arrival rate (nodes/cycle entering the FF unit) and $\mu$ is the mean service time ($= L_{\mathrm{ff}}$ cycles)."

The note "In prior drafts, the service time parameter was incorrectly labeled $W_{\mathrm{service}}$, which collides with the pipeline issue width $W$. In this draft, the service time is denoted $\mu$ throughout" is helpful. Concern resolved.

### Issue B — [IyerKim2001] citation likely incorrect

**Status: Resolved. The citation has been removed and replaced.**

The [IyerKim2001] reference is absent from v3's references section. In its place, the paper now cites [KumarPeh2007], which is appropriately attributed to "Kumar, Peh, and Jha, 'Token flow control,' MICRO-40, 2007." The substitution is defensible: the MICRO-40 token flow control paper is a well-documented credit-based flow control reference. Concern resolved.

### Issue C — [DanosKashefi2006] key mismatch

**Status: Resolved.** The reference key is now [DanosKashefi2006] consistently throughout the paper. Concern resolved.

### Issue D — Figure 4 caption "universally across all three algorithms"

**Status: Resolved.** The Figure 4 caption now reads:

> "Data from Study 16 (H=4–8, QAOA/QFT/VQE). Study 20 (H=10/12) excludes QFT; its results are consistent with the H=4–8 trend and reported in Fig. 7. ASAP requires $F^* = 6$ (QAOA), 7 (QFT), or 8 (VQE). ff\_rate\_matched achieves $F^* = 4 = W/2$ for all three algorithms in Study 16, and for QAOA and VQE in Study 20."

This correctly attributes the QFT result to Study 16 and does not claim QFT coverage in Study 20. Concern resolved.

### Issue E — Grammar / informal register ("the burst damage is done")

**Status: Unresolved (minor).** Section III-C still contains the phrase "the stall is purely reactive: only after `ff_in_flight` has already reached F does ASAP pause — but by then, the burst has already been injected and the damage is done." The informal register ("the damage is done") persists. This is a trivial issue that does not affect scientific content.

---

## 4. Evaluation of the FF Fraction Finding and Its Explanatory Adequacy

### 4.1 Is the high FF fraction result itself credible?

Yes. The reported values (0.906–0.994 across all test instances) are consistent with the known structure of QAOA and VQE measurement patterns in MBQC: most qubits participate in entanglement operations that require Pauli byproduct corrections, and signal shift only redistributes these corrections — it does not eliminate them. A value near 1.0 for FF fraction is structurally plausible, and the writer provides per-algorithm statistics (mean ± std, range) for all 100 instances. The measurement methodology (analysis of the `ff_edges` fields in the per-circuit JSON artifacts) is traceable.

### 4.2 Does the high FF fraction change the explanation of why F* = W/2 works?

Yes, substantially — and the v3 explanation is largely adequate, though it leaves one gap.

**What the v3 explanation says:** With FF fraction ~0.95–0.99, almost every issued node generates FF work. The credit gate at F = W/2 therefore limits the sustained issue throughput to approximately F = W/2 nodes/cycle. ASAP at the same F also achieves ~F nodes/cycle throughput, but via reactive stalls (high stall rate). Since both policies achieve the same sustained throughput of ~F nodes/cycle, the total cycle counts are identical (cycles\_ratio = 1.000). The credit gate eliminates stall regression not by increasing throughput but by *smoothing* the delivery of that throughput.

**Why this is materially better than v2:** v2 claimed FF fraction ≤ 0.5, which implied that only half the issued nodes generate FF work, leaving the other half "free" to fill pipeline slack — a mechanism that was never explained clearly. v3's explanation is simpler and more honest: both policies are bottlenecked at the same rate (FF capacity F), and ff\_rate\_matched just prevents the overflow oscillation that causes ASAP's stall bursts.

**The remaining gap:** The explanation does not fully account for why F* = W/2 specifically. With FF fraction ~0.97 and the credit gate at F = W/2, the expected issue throughput is ~(W/2) nodes/cycle. With F = W/4 (e.g., F=2, W=8), the expected throughput would be ~(W/4) nodes/cycle — slower. Yet Study 17 reports cycles\_ratio = 1.000 at F/W = 0.125, which appears to contradict this. The reconciliation (offered in Section IV-B's intuition paragraph) is that $D_{\mathrm{ff}}^{\mathrm{shifted}} = 1$–$2$ makes the FF pipeline drain fast enough between bursts that even F=2 rarely triggers the credit gate in practice. This explanation is plausible but not quantitatively verified. The text states:

> "With F=2, the FF unit completes 2 operations per cycle, and the queue drains within L_ff cycles after each burst. Because D_ff_shifted = 1–2 means the next burst cannot arrive until the issue stage has processed more nodes and the DAG has advanced by at least one depth level, the FF queue is always drained before the next burst arrives."

This account is internally consistent but relies on a claim about burst inter-arrival time that is not directly measured. A brief empirical note on the distribution of `ff_in_flight` over time at F=2, W=8 would make this argument concrete. Without it, the reader is asked to accept an informal DAG-topology argument as the explanation for a quantitative result (cycles\_ratio = 1.000 at F/W = 0.125). This is a moderate gap, not a blocking one.

### 4.3 Is "Design Principle (empirically confirmed)" an adequate replacement for Theorem 1?

Yes. The replacement is appropriate and the language is precise:

> "We label this a 'Design Principle confirmed by simulation' rather than a theorem, following the reviewer's recommendation: the bound ff_in_flight ≤ F is guaranteed by the counter logic (a mechanical fact), while the zero-regression claim is an empirical finding that holds for our tested circuit families and may require re-examination for circuits outside this scope."

The separation of the mechanical guarantee (ff\_in\_flight ≤ F by construction) from the empirical claim (zero stall regression at F = W/2) is exactly what Round 2 requested. The scope restriction — QAOA and VQE with FF fraction ≥ 0.90, D_ff_shifted ∈ {1, 2} — is stated clearly both in the Design Principle box and in Section VII-C. This is honest and well-calibrated.

---

## 5. Overall Quality Assessment

### 5.1 Scores

| Dimension | Round 1 | Round 2 | **Round 3** | Change (R2→R3) | Notes |
|-----------|:-------:|:-------:|:-----------:|:--------------:|-------|
| **Novelty** | 7 | 7 | **7.5** | +0.5 | The high FF fraction finding and its implication for the $F^*$ explanation add a genuine empirical discovery on top of the mechanism contribution. The co-design framing is now complete. |
| **Technical depth / correctness** | 5 | 6 | **7.5** | +1.5 | The structural half-fraction error is corrected, the four-way comparison anchors the co-design claim, the Design Principle language is appropriately hedged, and the Little's Law notation is cleaned up. The $F^*$ definition ambiguity (see Section 2) prevents a higher score. |
| **Clarity** | 7 | 7 | **7.5** | +0.5 | Figures 1, 3, 6, 7 remain placeholders, which is the single largest remaining drag on this score. The four-way table in Section V-C is clear and well-annotated. The prose in Section IV-B is substantially improved. |
| **Experimental rigor** | 7 | 7.5 | **8.0** | +0.5 | The FF fraction measurement (100 instances, per-algorithm statistics) is rigorous and directly addresses Round 2's central demand. The four-axis validation is well-documented. QFT caveat consistently stated. |
| **Overall** | 6.5 | 7.0 | **7.5** | +0.5 | Meaningful progress. One moderate-priority issue ($F^*$ definition reconciliation) and two minor issues (figures, informal register) stand between the current draft and a clean acceptance score. |

### 5.2 What would push this to 8.5/10?

The paper needs three things to reach 8.5:

1. **(Moderate — required for score ≥ 8)** Reconcile the $F^*$ definition. The Design Principle states $F^* = W/2$, but Study 20's stall table shows ff\_rate\_matched achieves <0.5% stall (below raw baseline) at F=2 with W=8, which by the paper's own stall regression criterion implies $F^* = 2$, not $F^* = 4$. The paper must either (a) redefine $F^*$ as the minimum F for which ff\_rate\_matched's stall rate is below the raw-ASAP baseline AND below some absolute threshold (e.g., 1%), distinguishing the "threshold for practical stall elimination" from the "minimum for strict zero regression," or (b) show that F=2 does not satisfy the stall regression criterion when raw-DAG stall is taken as the proper baseline, and explain why F=4 is the correct threshold. The current text defines stall regression as "stall\_rate(shifted, ASAP) > stall\_rate(raw, ASAP)" and $F^*$ as the minimum F for which this inequality does not hold — but neither of these criteria uniquely selects F=4 for ff\_rate\_matched when F=2 already achieves 0.05% stall (which is well below the raw-ASAP 3.5%).

2. **(Minor — required for score ≥ 8)** Generate at least Figures 1 and 3. These are the two most important illustrative figures in the paper (pipeline architecture and credit mechanism contrast). A referee cannot evaluate the mechanism's clarity without seeing these. The placeholder text is detailed enough that the figures are imaginable, but unverifiable. The four-axis sensitivity figures (6 and 7) can remain as placeholders for a workshop submission but should be generated for final journal submission.

3. **(Minor — score boost to 8.5)** Add a brief empirical note on `ff_in_flight` distribution at F/W = 0.125 to ground the "burst inter-arrival" argument in Section VII-A and IV-B. A single histogram or time-series snippet showing that `ff_in_flight` returns to near-zero between bursts at F=2, W=16 would make the argument for why even F/W=0.125 imposes no throughput penalty quantitatively concrete rather than qualitatively plausible.

---

## 6. Remaining Issues Before Acceptance

### Must resolve (blocking):

1. **(High priority)** Reconcile the $F^*$ definition. If ff\_rate\_matched achieves <0.5% stall at F=2 (Study 20 stall table, QAOA H10 Q100, ff\_rm stall = 0.05%), and the raw-ASAP stall at the same configuration is 3.5%, then ff\_rate\_matched already satisfies "stall rate below raw baseline" at F=2. Why is $F^* = 4 = W/2$ claimed rather than $F^* = 2$? Either the $F^*$ definition excludes F=2 on some other ground (e.g., absolute stall threshold), or the claim "$F^* = W/2$" is imprecise. This needs a one-paragraph clarification, not new experiments.

### Should resolve (non-blocking, important for final submission):

2. Generate Figures 1 and 3 (pipeline diagram and credit mechanism contrast). These are the core illustrative figures for the mechanism.

3. Fix the informal register "the damage is done" in Section III-C.

4. Add an empirical note (even a brief inline observation) on the `ff_in_flight` distribution at F/W = 0.125 to support the burst inter-arrival argument in Sections IV-B and VII-A.

---

## 7. Updated Recommendation

**Accept with Minor Revision**

The paper has progressed from Major Revision (Round 1) → Minor Revision (Round 2) → Accept with Minor Revision (Round 3). The two blocking issues from Round 2 are resolved. The FF fraction finding is a genuine scientific discovery that strengthens the paper's empirical case. The Design Principle framing is honest, well-scoped, and appropriately hedged. The four-way comparison table provides the end-to-end co-design evidence that was missing through two prior rounds.

The one remaining substantive issue — the $F^*$ definition ambiguity — is a one-paragraph clarification, not a new experiment. The remaining minor issues (figures, informal register, ff\_in\_flight distribution) are editorial. The paper can be accepted following revision of the $F^*$ definition and generation of Figures 1 and 3.

---

## 8. Summary for Author Response

**On the FF fraction finding:** The discovery that FF fraction is ~0.95–0.99 (not ~0.5) is an important empirical contribution in its own right. Report it prominently — it validates the universal FF generation assumption and sharpens the hardware sizing guideline. The revised explanation of why F = W/2 suffices (both policies are FF-bottlenecked at rate F; ff\_rate\_matched eliminates the overflow oscillation) is correct and clear.

**On the $F^*$ definition:** Section 2 of this review identifies a specific inconsistency. Study 20's stall table shows ff\_rate\_matched achieving 0.05% stall at F=2 (below the raw-ASAP 3.5% baseline), which appears to satisfy the paper's own stall regression criterion. If F=2 already eliminates stall regression for ff\_rate\_matched, the claim "$F^* = 4 = W/2$" needs to be qualified. A clean fix: define $F^*$ explicitly as "the minimum F such that ff\_rate\_matched stall rate ≤ 1% AND ≤ raw-ASAP stall rate," and show that F=2 (with W=8) fails the 1% threshold for some circuit/seed combinations. Alternatively, if the 0.05% at F=2 is already below the threshold, then $F^*$ should be reported as ≤ 2 for ff\_rate\_matched, not = 4, and the W/2 claim would need to be revised downward. Either resolution is fine, but the current state leaves the claim imprecise.

**On figures:** For final submission, at minimum generate Figures 1 and 3. These are the mechanistic figures that a reader unfamiliar with credit-based flow control will need to follow the argument.

---

*End of third-round referee report.*
