# Referee Report: "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)

---

## 1. Summary

This paper identifies and formalizes a phenomenon the authors call "stall regression" — a paradoxical throughput degradation that occurs when signal shift compilation is applied to MBQC programs without compensatory changes to the classical control scheduling policy. The root cause is that signal shift collapses feedforward (FF) chain depth from O(100–300) to O(1–2), converting a temporally spread workload into a bursty one that overflows the FF unit's in-flight capacity under greedy (ASAP) scheduling. The paper proposes **ff\_rate\_matched**, a credit-based issue throttle that gates node issue on FF slot availability, analogous to credit-based flow control in NoC router design. The central theoretical result is that the minimum FF width for zero stall regression under ff\_rate\_matched is F* = W/2, derived from a Little's Law flow balance argument, whereas ASAP requires F* = W. This claim is validated through a four-axis experimental campaign (Studies 17–20) covering F/W ratios, FF latency, measurement latency, and circuit scale. The experimental evidence is comprehensive and the practical implication — halving FF hardware requirements — is clearly articulated.

---

## 2. Strengths

- **Clear problem identification.** The stall regression phenomenon is precisely defined, intuitively motivated, and empirically characterized. The contrast between raw and shifted DAG stall rates (e.g., 49% vs. 0.5% for VQE at F=2) is striking and effectively conveys the severity of the problem.

- **Principled mechanism design.** The credit-based flow control analogy is apt and well-executed. The connection to NoC literature (Dally & Towles) and the O(1) implementation sketch (a single counter and comparator) make the proposal immediately actionable for hardware designers.

- **Comprehensive experimental validation.** The four-axis sweep (Study 17–20) covering 4,120 simulation runs is genuinely thorough for a systems paper. Sweeping F/W, L_ff, L_meas, and circuit scale independently, and showing invariance of F* = W/2 across all axes, is exactly the right validation strategy.

- **Perfect large-scale result.** The 1,080/1,080 exact cycle match in Study 20 is a strong empirical anchor. Achieving zero throughput cost while eliminating stall regression simultaneously strengthens the contribution considerably.

- **Good cross-disciplinary grounding.** The connections to RAW hazard prevention, Little's Law, and Rate Monotonic Scheduling are informative without being strained. The paper correctly situates itself in both the quantum computing and computer architecture literatures.

- **Honest treatment of limitations.** Section VII-C names several gaps (QFT large-scale coverage, probabilistic latency, fault-tolerant extension) clearly and specifically. This builds credibility.

---

## 3. Weaknesses / Major Concerns

### 3.1 The core theorem (Theorem 1) is stated informally and the proof is incomplete

This is the most significant concern. The paper claims a formal theorem (Section IV-B, Theorem 1) but provides only an informal flow balance argument, not a proof. Several gaps undermine the claim:

- The Little's Law argument requires a stable queue (arrival rate = departure rate at steady state). The paper does not establish that the credit-gated system actually operates in steady state for finite, DAG-structured workloads. MBQC programs are finite, not infinite streams, so "steady state" needs qualification — particularly for programs where the DAG has a bursty prefix and a tail.

- The derivation concludes F >= W/2 is sufficient for L_ff = 1, and then states "for L_ff > 1, the constraint relaxes further … but W/2 remains sufficient." This is asserted, not proved. The intuitive argument in the paragraph that follows is plausible but does not constitute a formal bound.

- Theorem 1 uses the asymptotic quantifier "as N -> infinity" to make the stall rate bound vanish, but the experiments are at finite N (Q up to 100). The gap between the asymptotic theorem and the finite-N experimental results deserves explicit treatment: what is the residual stall rate at finite N, and how does it scale?

- The theorem statement says stall regression is "zero" asymptotically, but Table V-E shows residual stall of ~0.05–0.15% even for ff\_rate\_matched at F=4, W=8. The paper needs to explain whether this is consistent with the theorem or represents a regime where the bound has not yet been reached.

The paper would be significantly stronger with either (a) a rigorous proof of Theorem 1 as stated, or (b) honest demotion of the statement to a "conjecture supported by extensive simulation" with the informal argument retained as intuition.

### 3.2 Simulator fidelity and model validity are not established

The entire experimental contribution rests on `mbqc_pipeline_sim`, a custom cycle-accurate simulator, but the paper provides almost no information about it. Key questions left unanswered:

- How was the simulator validated against any ground truth? A comparison to even a simple analytical model or a known reference case would help.
- What are the simulator's assumptions about measurement contention, FF unit microarchitecture, and ready-queue management that might not hold in a physical system?
- Are there resource limits on the measurement stage (meas_width)? The model description mentions "meas_width" as a parameter, but the studies apparently do not vary it — is it set to infinity? If so, this is an important idealizing assumption.
- The description of the issue stage says "up to W nodes per cycle" — is the ready-queue lookup O(1) or O(Q)? This matters for feasibility of the hardware claim.

The claim that ff\_rate\_matched enables a "50% reduction in FF hardware area" (Section VII-A) requires more than a cycle count argument. The hardware claim should be qualified with a clear statement of which model assumptions the area reduction depends on.

### 3.3 The comparison baseline is too narrow

The paper compares ff\_rate\_matched only against ASAP scheduling on the shifted DAG. This leaves important questions unanswered:

- What does the raw DAG baseline achieve in terms of total cycle count (not just stall rate)? The paper states that ASAP on the shifted DAG can be worse than the raw DAG at low F — but are there conditions where the shifted DAG with ff\_rate\_matched is better, worse, or equal to the raw DAG with ASAP? A table or figure showing all four combinations (raw/shifted x ASAP/ff_rm) would clarify the end-to-end value of the proposed co-design.

- Are there other natural scheduling policies that could address stall regression without the credit gate? For example, a token-bucket rate limiter, a simple issue-rate throttle based on recent history, or a static round-robin issue policy? The paper positions ff\_rate\_matched as the natural solution but does not demonstrate that simpler alternatives fail.

- The claim that ASAP requires F* = W has strong dependence on circuit type: QAOA has F*(ASAP) = 6–8, not always W=8. This variability in ASAP's F* across algorithms (6 for QAOA, 7 for QFT, 8 for VQE in Figure 4) is acknowledged but not fully explained. Does ff\_rate\_matched's F* = W/2 hold when W is varied widely (e.g., W=32)?

### 3.4 Physical realism of the pipeline model

The pipeline model abstracts MBQC classical control to three idealized stages. Several realistic complicating factors are not addressed and could materially affect the F* = W/2 result:

- **Probabilistic measurement outcomes.** In real MBQC, not all measurements trigger FF corrections; the fraction that do is outcome-dependent. The model appears to assume all measurements generate FF work. If the fraction is less than 1, F* < W/2 might be achievable. The paper should state this assumption explicitly and discuss its impact.

- **Concurrent syndrome decoding (fault-tolerant case).** Section VII-C mentions fault-tolerant extension as future work, but a real MBQC system near-term likely runs surface code syndrome decoding alongside FF correction. This co-runner would compete for classical resources in ways the current model ignores.

- **Non-Clifford measurement angles.** Signal shift absorbs Pauli (Clifford) byproducts, but non-Clifford corrections require different treatment. The scope of the paper (circuits where signal shift applies fully) should be stated explicitly upfront, not deferred to limitations.

### 3.5 Figure referencing inconsistency

Several figures are referenced in the text but appear to be placeholders (Figures 1, 3, 6, 7 contain only bracketed text descriptions). Figures 4 and 5 reference paths under `studies/16_ff_rate_matched`, while Study 20 is described as a separate experiment. It is unclear whether Figures 4 and 5 were generated from Study 16 (a predecessor study not described in the paper) or Study 20 data. This inconsistency raises questions about whether the described studies are the same as those that generated the figures.

---

## 4. Minor Issues

- **Reference mismatches.** Several references have mismatched citation keys and actual publication details:
  - `[DanosKashefi2007]` cites a 2006 paper (Physical Review A, vol. 74, 2006) but the key implies 2007.
  - `[O'BrienBrowne2017]` points to a 2019 New Journal of Physics paper on quantum phase estimation — this appears to be an incorrect match for the cited work on fault-tolerant MBQC classical control overhead. The citation should be replaced with a more relevant fault-tolerant MBQC paper (e.g., Raussendorf, Harrington & Goyal 2006/2007, or Fowler et al. 2009).
  - `[BenjaminBrowne2005]` maps to a 2006 Journal of Physics: Condensed Matter paper on fullerene-based quantum computing — this is tangentially related at best and does not support the claim that it identified "classical control pipeline as a primary architectural concern."
  - `[MoravanouKent2023]` maps to Morvan et al.'s Nature 2024 paper on random circuit sampling phase transitions, which has essentially no connection to MBQC classical control architecture. This citation seems misplaced.

- **Equation (1) / steady-state derivation.** The inequality $F \geq W \cdot L_{\mathrm{ff}} / (L_{\mathrm{ff}} + 1)$ in Section IV-B appears without clear derivation — the preceding narrative does not follow cleanly into this expression. A one-sentence justification of how this fraction arises from the Little's Law substitution would help.

- **"F* = W/2 universally" is overstated.** The paper uses "universally" to mean "across all tested conditions" but the theorem statement requires N -> infinity. The experimental domain is finite. The word "universally" should be qualified (e.g., "across all tested configurations" or "asymptotically in N").

- **Study 17 discrepant pairs.** The 14 discrepant pairs in Study 17 (Section V-B) are all attributed to "tie-breaking differences." This dismissal is not fully justified — cycles_ratio deviations of up to 0.17%, even if small, deserve a brief mechanistic explanation. Are these deterministically reproducible across seeds?

- **Table formatting in Section V-E.** The stall rate table has an inconsistency: at F=4 (W=8), ASAP and ff\_rate\_matched both show ~0.07–0.08% stall. The table caption and surrounding text describe this as "convergence at F*," but it is not obvious why ASAP at F=4=W/2 would converge to the same low stall as ff\_rate\_matched. If the burst load at these scales does not actually exceed F=4, then ASAP does not stall regardless — in which case the stall regression problem does not require ff\_rate\_matched at these scales. This should be explicitly clarified.

- **Rate Monotonic Scheduling analogy (Section IV-C).** The analogy between the F/W >= 0.5 utilization bound and Liu-Layland's ln(2) schedulability bound is loose. RMS applies to periodic independent tasks on a uniprocessor; the MBQC FF pipeline is a pipelined single-resource system with DAG-constrained arrival. The analogy adds color but proves nothing — it should be presented as intuition only, not as a corroborating theoretical result.

- **Grammar / style.** A few minor issues: "stall is reactive, not preventive" (Section III-C) — "preventive" should be "proactive" or "predictive." The sentence "the burst damage is done" is informal for a technical paper. Section V-A says circuits are generated "for three quantum algorithms" (QAOA, QFT, VQE) but Study 18 and Study 19 omit QFT — this selective coverage should be flagged consistently in each study's setup paragraph, not only in the limitations section.

- **Missing figure for the stall regression visualization.** Figure 2 references a PNG at a specific local path (`results/studies/rerun_20260416/...`). This embedded file path will not render in a submitted paper and should be replaced with a self-contained figure. The path also reveals internal study numbering that may not match the paper's narrative (Study 14 vs. Study 17–20).

---

## 5. Section-by-Section Feedback

### Abstract

The abstract is well-written and accurately summarizes the contribution. The claim "we prove that the minimum FF width … is F* = W/2" is too strong given that Section IV-B provides an informal argument rather than a formal proof. Replace "prove" with "derive" or "establish by theoretical argument and simulation."

The abstract states "1,080 paired comparisons at large scale" and later the paper gives a total of "4,120 simulation runs" (and "1,440 paired comparisons" in the Conclusion). These numbers are inconsistent between the abstract and the conclusion — reconcile them.

### Section I (Introduction)

The introduction is effective. The contribution list at the end of Section I is clear and appropriately scoped. However, contribution 1 ("formal characterization of stall regression … including a quantitative model linking D_ff compression to burst load B = N / D_ff") overstates the formalism. The burst load formula B ≈ N / D_ff is a heuristic approximation, not a formal model — it ignores DAG structure entirely. A formal model would account for the distribution of DAG node depths and their co-arrival statistics. Qualify this as an "approximate characterization" rather than a "formal" one, or provide the missing formalism.

### Section II (MBQC Pipeline Model)

The pipeline model is clearly described. Two issues deserve attention:

1. The model silently assumes that every measurement generates exactly one FF operation. This may not hold for all MBQC programs (some measurements may be adaptive but require no correction; others may require multi-qubit corrections). State this assumption explicitly.

2. "Stall rate" is defined as "fraction of issue-stage cycles during which no node is issued despite a non-empty ready queue." This definition conflates credit-gate stalls (caused by FF saturation) with other potential stalls (empty measurement pipeline, meas_width limits). The paper should confirm that in all experiments the only source of stall is FF saturation.

The description of signal shift compilation is correct but brief. A one-paragraph summary of why signal shift achieves D_ff reduction — the key algebraic insight — would make the paper more self-contained for readers unfamiliar with measurement calculus.

### Section III (The Stall Regression Problem)

Section III is the strongest section of the paper. The mechanistic explanation is clear, the empirical characterization in Section III-B is compelling, and Section III-C correctly identifies why ASAP cannot self-correct.

One issue: the claim "ASAP's shifted-DAG stall rate is nearly independent of L_ff … varies by less than 0.1 percentage points" is stated but not shown directly in any figure or table within Section III. The supporting data comes from Study 18 (Section V-C), but a forward reference or a brief data snippet here would strengthen the argument.

### Section IV (ff_rate_matched)

The credit-based design principle is well-motivated and the pseudocode in Section IV-A is clear and correct.

Section IV-B has the problems noted in weakness 3.1. The flow balance argument needs to be tightened or the theorem claim needs to be demoted. The key missing step is: what prevents a finite DAG from producing a transient burst that temporarily exceeds F even when F = W/2? The credit gate prevents `ff_in_flight > F` by construction, but this means the issue stage must stall until a slot opens — which could still cause total cycle count regression if the burst is large enough. The paper needs to show that with F = W/2 and D_ff = 1, the credit gate stall duration is zero (or negligibly small) asymptotically.

The derivation in Section IV-B states "This is achievable when F >= W * L_ff / (L_ff + 1)" but then immediately uses this to derive F >= W/2 at L_ff = 1, and then asserts the W/2 bound is "sufficient" for L_ff > 1 without showing that the bound for L_ff > 1 is always <= W/2. In fact, for L_ff = 2: W * 2/3 ≈ 0.667W > 0.5W. This would mean F* > W/2 for L_ff = 2 under the formula as stated. Yet the experiments show F* = W/2 for all L_ff. There is a contradiction between the formula and the experimental result that the paper does not resolve. Either the formula is wrong, or the argument for why W/2 suffices for L_ff > 1 needs to be rewritten carefully.

Section IV-C (connection to classical architecture) is informative. The Tomasulo comparison is fair and the rate monotonic analogy, while loose, is flagged appropriately as intuition.

### Section V (Experimental Evaluation)

The experimental section is thorough and the results are clearly presented. Several issues:

- **Study 17 (Section V-B):** The observation that even at F/W = 0.125 (F=2, W=16), the median cycles_ratio = 1.000 is counterintuitive and the paper's explanation ("the credit gate condition is rarely triggered because the FF pipeline drains nearly as fast as it fills") needs to be backed up with data. At W=16, F=2, and L_ff = 1, the FF unit can process at most 2 nodes per cycle while 16 can be issued. If 16 nodes arrive simultaneously (D_ff = 1 burst), the credit gate fires immediately and stalls 14 of them. Yet the cycles_ratio is still 1.000? This would only be true if the DAG is never actually issuing 16 nodes simultaneously. The paper should show the distribution of per-cycle issue counts for a representative W=16, F=2 case to justify this claim.

- **Study 18 (Section V-C):** The table showing F*(ASAP) decreasing from 8 to 6 for QAOA at L_ff >= 3 is interesting but the explanation ("lower burst load for QAOA" vs VQE) is not quantified. What is the burst load B for QAOA vs VQE at H=8, Q=64? Providing B values for each circuit type would make the L_ff-dependent behavior more transparent.

- **Study 19 (Section V-D):** The hypothesis-driven structure (stating a hypothesis and then testing it) is commendable. The key finding — that increasing L_meas delays bursts uniformly but does not spread them — is important and correctly explained. However, the partial exception (QAOA H6 at L_meas = 4, F*(ASAP) drops for 3/5 seeds) deserves more attention. Is this artifact a seed-dependent DAG structure effect or a genuine regime? If 3/5 seeds show F*(ASAP) = 4, is this enough to conclude the effect is real?

- **Study 20 (Section V-E):** The 1,080/1,080 exact cycle match is a clean result, but the figure paths reference Study 16 (not Study 20). Either the figures should be regenerated from Study 20 data, or it should be clearly stated that Figure 4 and Figure 5 are from a predecessor study and the claim that Study 20 confirms these results should reference specific Study 20 figures.

- **QFT coverage gap** is correctly identified in Section VII-C but should also appear as a caveat in Section V's summary box (Section V-F). The bold summary statement there ("ff\_rate\_matched eliminates stall regression … for circuit scales up to H=12, Q=100") is currently unqualified and does not note the QFT coverage gap.

### Section VI (Related Work)

The related work is generally well-covered. The four subsections are appropriate. The citation issues identified in the minor issues section (O'BrienBrowne2017, BenjaminBrowne2005, MoravanouKent2023) significantly weaken this section — replacing them with accurate references to MBQC-relevant fault-tolerance and hardware papers is necessary.

One missing citation: there is a body of work on MBQC resource state scheduling and classical side-channel latency budgeting (e.g., Broadbent, Fitzsimons & Kashefi 2009 on blind quantum computation; Briegel et al.'s original cluster state papers) that could be cited to better situate the feedforward scheduling problem in the broader MBQC execution model.

### Section VII (Discussion)

Section VII is well-organized. The hardware implications (Section VII-A) are clear and the co-design principle (Section VII-B) is the right framing. The limitations list in Section VII-C is honest and appropriate.

One important limitation is not addressed: the paper's model assumes a single FF unit with uniform latency L_ff. A real MBQC control processor might have heterogeneous FF operations (e.g., single-qubit Pauli updates are fast; multi-qubit or non-Clifford corrections are slow). A credit model with a single uniform L_ff would mis-size F* if the actual latency distribution has high variance.

### Section VIII (Conclusion)

The conclusion is accurate but repeats the overstatement of the "zero throughput cost" guarantee. The total count of "1,440 paired comparisons" in the conclusion does not match "1,080 paired comparisons" in the abstract (the former may be combining Studies 17 and 20, but this should be explicit). Clarify the accounting.

---

## 6. Overall Recommendation

**Major Revision**

The paper addresses a real and important problem, proposes a clean and implementable solution, and provides an unusually thorough experimental validation. The cross-disciplinary framing (MBQC + NoC + CPU architecture) is genuinely insightful. However, the paper cannot be accepted in its current form for the following reasons, in order of priority:

1. Theorem 1 is not proved, and the informal argument contains a potential algebraic inconsistency (the F >= W * L_ff/(L_ff+1) formula implying F > W/2 for L_ff = 2, which contradicts both the theorem and the experiments). This must be resolved before the paper's central theoretical claim is credible.

2. The simulator is a black box. The experimental contribution depends entirely on an undescribed custom tool. At minimum, a concise description of the simulator's assumptions, a validation against a known case, and clarification of the meas_width parameter are required.

3. Several reference mismatches (O'BrienBrowne2017, BenjaminBrowne2005, MoravanouKent2023) are material errors that undermine the credibility of the related work section.

4. The figure referencing inconsistency (Figures 4 and 5 from Study 16; placeholder text for Figures 1, 3, 6, 7) must be resolved for the paper to be evaluable as submitted.

With these issues addressed — particularly the theoretical gap and the simulator description — this paper would be a strong contribution to a systems or architecture venue.

---

## 7. Scores (1–10)

| Dimension | Score | Rationale |
|-----------|-------|-----------|
| **Novelty** | 7 | The stall regression problem is well-identified and the credit-based solution is a natural but non-obvious application of NoC techniques to MBQC. The F* = W/2 result is a clean and memorable finding. |
| **Technical depth** | 5 | The theoretical argument has a significant gap (Theorem 1 is informal and may contain an inconsistency). The simulator is undescribed. These are not minor issues. |
| **Clarity** | 7 | Writing is generally clear and the narrative logic is good. The figure placeholder problem and the duplicate/inconsistent numbers hurt the presentation. |
| **Experimental rigor** | 7 | Four-axis sweep with 4,000+ runs is genuinely thorough. The Study 17/20 figure reference inconsistency and the QFT coverage gap reduce the score. |
| **Overall** | 6.5 | Strong problem + clean solution + broad experiments, but theoretical and presentation gaps must be resolved. Borderline for a top venue in current form; likely acceptable after major revision. |

---

*End of referee report.*
