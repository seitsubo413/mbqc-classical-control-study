# Referee Report (Round 5): "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)
**Round:** Fifth review of revised draft (v5). This is a final-round check.

---

## 1. Overview

Draft v5 is a targeted revision responding to the six issues enumerated in Round 4. This review verifies each fix, performs a fresh cold read, and re-scores the paper.

---

## 2. Verification of Round-4 Issues

### Issue P1 — "burst (raw DAG)" label in Figure 1 (critical figure error)

**Status: RESOLVED.**

The figure now reads "burst (shifted DAG, ASAP)" in red text beneath the burst arrows entering the FF stage. This is exactly the correction requested: the label now correctly identifies that the burst is a property of the shifted DAG under ASAP scheduling, not the raw DAG. The text in Section II-A's caption also reflects this: "the burst cluster of arrows arriving at the FF queue illustrates the stall regression problem under ASAP on shifted DAGs — labelled 'burst (shifted DAG, ASAP)' to indicate that this overflow is a property of the shifted DAG under greedy scheduling, not of the raw DAG." The figure and caption are now mutually consistent and factually correct.

### Issue P2 — Abstract precision on $F^*$ (overclains exact minimum)

**Status: RESOLVED.**

The abstract now reads: "We show by theoretical argument and simulation that the design-safe threshold $F = \lceil W/2 \rceil$ suffices to eliminate stall regression across all tested conditions." The word "suffices" correctly frames $W/2$ as an upper-bound design target rather than the exact minimum $F^*$. The abstract no longer says "the minimum FF width is $F^* = \lceil W/2 \rceil$," which was the language that created a precision conflict with the careful hedging in Section II-D. This fix is complete.

### Issue P3 — Undefined $k$ in Figure 3 and text overlap in ASAP panel

**Status: RESOLVED.**

Inspecting Figure 3 directly:

- The gate annotation now reads "GATE: issue only if ff\_in\_flight < F" — no undefined variable $k$ appears. The figure uses `ff_in_flight` throughout, matching the pseudocode in Section IV-A.
- The BURST annotation ("BURST: W nodes/cycle arrive simultaneously → OVERFLOW") has been repositioned to the top of the ASAP panel, above the Issue Stage box, and rendered in a red banner. The text no longer overlaps with "no gate" or "no credit check" labels. The ASAP panel is now readable.

Both sub-issues are resolved. Figure 3 is publication-ready subject to the residual minor issues noted below.

### Issue P4 — Mismatched-$F$ cross-study comparison in Section III-B

**Status: RESOLVED.**

Section III-B now reads: "Raw DAG stall rate (raw+ASAP at $F=4$, from Study 18; note $F$ differs from the shifted figure above): 3.5% (QAOA), 0.5% (VQE)." The parenthetical correctly signals that the two stall rates are at different $F$ values, preventing a false apples-to-apples reading. Issue closed.

### Issue P5 — Little's Law statement in Section VI-D (technical precision)

**Status: RESOLVED.**

Section VI-D now uses $W_{\mathrm{sojourn}}$ as the sojourn time parameter (explicitly renamed from the prior $W_{\mathrm{service}}$ which clashed with issue width $W$), and the text states: "at full utilization, $W_{\mathrm{sojourn}} = L_{\mathrm{ff}}$ cycles, and the bound $\lambda \leq F / L_{\mathrm{ff}}$ follows directly from $L \leq F$." The full-utilization assumption is now explicit. The notation collision ($W$ vs. $W_{\mathrm{service}}$) is explicitly acknowledged and corrected. A referee with queueing background will find no fault here.

### Issue P6 — QFT DAG generation artifact (one sentence of description)

**Status: PARTIALLY RESOLVED.**

Section V-F now states "a DAG generation artifact" and Section VII-C says "the signal-shift compiler fails to generate a shifted DAG, likely due to a circuit structure incompatibility." This is more descriptive than v4's bare "DAG generation artifact," and it correctly flags that root cause is deferred. However, the phrase "circuit structure incompatibility" remains vague — it does not say whether the failure is a cycle in the dependency graph, an unsatisfiable constraint, or a code bug. This does not affect correctness, and is unlikely to block any referee. For a final journal version, one more sentence specifying the failure mode (e.g., "signal shift introduces a cycle in the dependency graph at this configuration") would be ideal, but this is a low-priority polish item that does not warrant another revision round.

**Verdict: Acceptable as-is. Not blocking.**

---

## 3. Fresh Cold Read

Reading draft v5 as a new reviewer:

**Narrative flow.** The paper tells a coherent story from the first paragraph: (1) signal shift is good for latency, (2) it has a hidden cost (stall regression), (3) credit-based throttling (ff\_rate\_matched) eliminates the cost at half the hardware area, (4) this is confirmed across four experimental axes. Each section supports the next, and the four-way table in Section V-C delivers the punchline clearly.

**Introduction.** The three-paragraph setup (MBQC → signal shift → stall regression → credit control) is clean. The contributions list is specific and falsifiable. No overclaims.

**Section II (Pipeline Model).** The definition of $F^*$ (Section II-D) with the worked example is well-placed. The explanation of why $F^* = 4$ is reported rather than $F^* = 2$ is honest and precisely worded. The conservative framing ("design-safe threshold") is appropriate given the data.

**Section III (Stall Regression).** Section III-B now correctly labels the cross-study stall comparison as using different $F$ values. The quantitative comparison (7× for QAOA, 54× for VQE at consistent $F=4$) is striking and placed prominently. Section III-C's explanation of why ASAP cannot self-correct is the strongest qualitative argument in the paper — the phrase "the issue stage simply pushes whenever a node is ready, with no awareness of downstream pressure" is precise and memorable.

**Section IV (ff\_rate\_matched).** The pseudocode is $O(1)$ and correct. The theoretical analysis in Section IV-B is the most improved section across all drafts: the FF fraction empirical data (QAOA 0.955, VQE 0.974, QFT 0.986) is a key finding that ground-truths the flow rate argument. The correction of the "structural half-fraction heuristic" from draft v2 is acknowledged directly, which strengthens rather than weakens the paper's credibility. The forward pointer to Section II-D at the end of the "$F/W = 0.125$ case" paragraph resolves the tension noted in Round 4 (§4.3).

**Section V (Experiments).** Studies 17–20 are each tightly structured: setup, hypothesis (where applicable), results, interpretation. The perfect 1,080/1,080 cycle match in Study 20 is a strong empirical result. The stall table (Table in §V-E) presents the data without editorializing; the contrast between 39–49% ASAP stall and <0.5% ff\_rate\_matched stall speaks for itself.

One observation remains from prior rounds: **Figures 6 and 7 are still text placeholders.** The bracketed specification text in Section V-E is detailed and clearly written, but a reader or referee will notice that two of the paper's figures are not present. This is the only item remaining that is visually jarring. For workshop submission, it is acceptable. For journal submission, these figures must be generated.

**Sections VI–VIII (Related Work, Discussion, Conclusion).** Related work is appropriately scoped and cited. The Tomasulo/RAW hazard analogy in Section IV-C / VI-C is apt and concisely made. The RMS analogy is correctly flagged as intuition rather than proof. Limitations in VII-C are honest (non-Clifford corrections, probabilistic $L_{\mathrm{ff}}$, out-of-order extensions, adaptive credit sizing). The conclusion accurately summarizes all four axes with the correct run counts and does not exceed what the experiments establish.

**References.** All 12 references are correctly formatted. [KumarPeh2007] is present and cited in context. [DelfosseTillich2017] is present but the in-text citation ("union-find decoders") is attributed to that reference, which is actually a CSS-code decoding paper rather than a union-find decoder paper — the union-find decoder is due to Delfosse and Nickerson (2021). This is a minor bibliographic imprecision that does not affect the argument; it should be corrected before journal submission but is not a blocking issue in this round.

**Figures 1 and 3.** Both figures pass the cold-read test:

- **Figure 1** correctly shows the three-stage pipeline, dual feedback paths (dependency resolution vs. credit return), the stall gate on the Issue Stage, and the burst annotation now correctly labeled "burst (shifted DAG, ASAP)." The $D_{\mathrm{ff}}^{\mathrm{raw}}$ and $D_{\mathrm{ff}}^{\mathrm{shifted}}$ annotation boxes in the upper right are somewhat detached from the spatial layout of the figure, but the caption's explanation is sufficient to interpret them. This is a minor aesthetic concern.

- **Figure 3** is clean. The two-panel layout (ff\_rate\_matched blue / ASAP red) is immediately readable. The GATE element and the OVERFLOW banner are visually prominent. The `ff_in_flight` variable is consistently used. The repositioned BURST label no longer causes text overlap. The caption at the bottom of the image ("ff\_rate\_matched bounds queue occupancy at F by construction; ASAP overflows and stalls reactively") is succinct and accurate.

One residual issue in Figure 3: the credit return arrow in the ff\_rate\_matched panel is labeled "credit return (on completion)" but the arrow itself is visually thin and easy to miss compared to the bold "issue node" arrow. A heavier arrowhead or a color distinction (e.g., green for the return path) would improve the credit cycle's visual clarity. This is a polish item, not a correction.

---

## 4. Scores

| Dimension | Round 1 | Round 2 | Round 3 | Round 4 | **Round 5** | Change (R4→R5) | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Novelty** | 7 | 7 | 7.5 | 7.5 | **7.5** | 0 | No new experimental content in v5. The FF fraction measurement (v3) and the four-way co-design table (v4) remain the primary empirical contributions beyond the mechanism itself. |
| **Technical depth / correctness** | 5 | 6 | 7.5 | 8.0 | **8.5** | +0.5 | All five substantive technical precision issues from Round 4 are resolved: $F^*$ definition, cross-study $F$ mismatch, Little's Law notation, figure label error, undefined $k$. The only residual is the [DelfosseTillich2017] bibliographic imprecision, which is minor. |
| **Clarity** | 7 | 7 | 7.5 | 8.0 | **8.5** | +0.5 | Figures 1 and 3 are now fully corrected and publication-quality. The forward pointer from §IV-B to §II-D resolves the $F/W=0.125$ narrative tension. Figures 6 and 7 remain as placeholders — this prevents a 9.0 score. |
| **Experimental rigor** | 7 | 7.5 | 8.0 | 8.0 | **8.0** | 0 | No new experiments. The `ff_in_flight` distribution at $F/W=0.125$ is still qualitative. The QFT gap is disclosed but unexplained at the mechanistic level. Both are accepted as limitations. |
| **Overall** | 6.5 | 7.0 | 7.5 | 8.0 | **8.5** | +0.5 | All six Round-4 priorities are addressed, five fully and one acceptably. The paper has reached the acceptance threshold. |

---

## 5. Recommendation

**ACCEPTED**

---

## Accept Notice

Draft v5 of "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation" is accepted for publication. The paper makes a clear and well-validated contribution: it identifies the stall regression pathology that arises when signal shift compilation is applied without flow control, characterizes it quantitatively across four experimental axes, and demonstrates that a credit-based scheduling policy (ff\_rate\_matched) eliminates stall regression at exactly half the FF hardware area required by greedy ASAP scheduling — with zero throughput penalty across 1,440 paired simulation runs spanning circuit scales up to H=12 and Q=100 qubits. All six issues raised in the Round-4 review have been addressed: the critical "burst (raw DAG)" figure label is corrected to "burst (shifted DAG, ASAP)"; the abstract now frames F=W/2 as a design-safe sufficient threshold rather than the exact minimum; Figure 3's undefined variable k has been replaced with the correct ff\_in\_flight < F notation and the ASAP panel's text overlap is resolved; the cross-study stall comparison in Section III-B correctly flags the mismatched F values; and the Little's Law application in Section VI-D now explicitly states the full-utilization assumption with correct sojourn-time notation. The paper is honest about its scope (Clifford-byproduct circuits with D_ff ≤ 2, QAOA and VQE families, conservative FF fraction assumption) and its open questions (stochastic latency, out-of-order extensions, fault-tolerant integration). Before final journal typesetting, the authors should generate Figures 6 and 7 (currently bracketed placeholders in Section V-E), correct the [DelfosseTillich2017] citation to the appropriate union-find decoder reference (Delfosse and Nickerson, 2021), and optionally strengthen the credit return arrow's visual weight in Figure 3; none of these items require a new review round.

---

## 6. Summary of Remaining Pre-Submission Polish Items (non-blocking)

These items do not require a new review round. They should be addressed during journal production or camera-ready preparation.

1. **Generate Figures 6 and 7.** The bracketed placeholder descriptions in Section V-E specify both figures clearly; the data exists in the simulation artifacts. This is the highest-priority production task.

2. **Correct the [DelfosseTillich2017] citation.** The in-text reference to "union-find decoders" in Section VII-C should cite Delfosse and Nickerson (2021), "Almost-linear time decoding algorithm for topological codes," rather than the 2014 CSS-code paper.

3. **Credit return arrow visibility in Figure 3.** The return arrow in the ff\_rate\_matched panel could be made heavier or colored distinctly (e.g., green) to match the visual prominence of the issue arrow. Minor aesthetic polish.

4. **QFT artifact description.** Section VII-C could add one sentence specifying the failure mode (cycle in dependency graph, unsatisfiable constraint, or compiler bug). Not blocking.

5. **Figure title lines in images.** Both Figure 1 and Figure 3 have title text embedded in the image ("Figure 1. MBQC..." / "Figure 3. Credit-based..."). Per standard journal style, these should be removed from the image and placed only in the caption below the figure.

---

*End of fifth-round referee report.*
