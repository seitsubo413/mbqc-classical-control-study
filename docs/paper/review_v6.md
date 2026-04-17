# Referee Report (Round 6): "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)
**Round:** Sixth review of revised draft (v6). Target: determine whether the paper reaches 9.0/10.

---

## 1. Overview

This round addresses two primary questions: (1) whether the Round-5 remaining items — specifically Figures 6 and 7 (previously placeholders) and the [DelfosseTillich2017] citation error — have been resolved in draft v6; and (2) whether the paper, read fresh, achieves the 9.0/10 overall score target.

---

## 2. Verification of Round-5 Remaining Items

### Item R5-1 — Figures 6 and 7: generate from placeholders

**Status: FULLY RESOLVED.**

Both figures are now generated image files (`figures/fig6_sensitivity.png` and `figures/fig7_scaling.png`) and are embedded with `![Figure 6]` and `![Figure 7]` markup in Section V-E. The bracketed placeholder specification text from v5 has been replaced by the standard figure reference + caption pattern used throughout the paper. This was the single highest-priority production task identified in Round 5.

**Figure 6 assessment.** The 4-panel heatmap (2×2: ff\_rate\_matched / ASAP × L\_ff / L\_meas) is immediately readable and makes its point with striking force. The all-green top row (F* = 4 uniformly) versus the predominantly dark-red bottom row (F* = 8 for most ASAP conditions) is visually unambiguous. The color legend at the bottom correctly maps green = F*=4 (W/2, optimal), orange = F*=7 (note: the legend says "F*=5–6" for yellow-green and "F*=7" for orange, while the actual data in the bottom row shows 6 for QAOA at L_ff=4–5 and 8 everywhere else — the displayed values 6 and 8 are consistent with the data in Section V-C, but the legend bucket labels need minor correction: the orange cells displaying "6" fall in the "F*=5–6" bucket per the legend scale, yet are rendered in the orange color which the legend labels "F*=7." This is a minor legend-data color inconsistency, detailed in Section 3 below). The axis labels (FF latency L_ff, Measurement latency L_meas, Algorithm, Algorithm+H) are clear. The figure title adequately summarizes the central claim. This figure contributes substantially to the paper's clarity score.

**Figure 7 assessment.** The 2×2 layout (QAOA / VQE × H=10 / H=12) shows stall rate as a function of FF width F for both ASAP (gray dashed) and ff\_rate\_matched (orange/blue solid), with the raw+ASAP baseline shown as a horizontal green dashed line and the F*=W/2=4 threshold marked by a vertical dotted line. The figure is small and somewhat dense at the rendered resolution — the legend in the top-left panel is partially clipped, and the y-axis labels on the H=12 panels (right column) are very compressed. However, the key message is legible: ff\_rate\_matched lines hug zero stall across all F values, while ASAP lines drop steeply from ~40–50% at F=2 to near-zero only at F=4. The convergence of ASAP and ff\_rate\_matched at F=4 is visible. A larger rendering or wider figure bounding box would improve this figure, but it is publication-adequate as-is.

### Item R5-2 — [DelfosseTillich2017] citation error

**Status: FULLY RESOLVED.**

The reference list in draft v6 now reads:

> [DelfosseNickerson2021] N. Delfosse and N. H. Nickerson, "Almost-linear time decoding algorithm for topological codes," *Quantum*, vol. 5, p. 595, 2021. arXiv:1709.06218.

And the in-text citation in Section VII-C reads "union-find decoders [DelfosseNickerson2021]." Both the reference key and the cited paper now correctly identify the Delfosse–Nickerson union-find decoder. The Round-5 bibliographic imprecision is corrected.

### Item R5-3 — Credit return arrow visibility in Figure 3 (low-priority polish)

**Status: PARTIALLY ADDRESSED / ACCEPTABLE.**

Inspecting Figure 3 directly: the credit return arrow ("credit return (on completion)") remains visually thinner than the "issue node (consume 1 credit)" forward arrow. However, the label is clearly readable and the return path is visually distinct from the forward path. For a conference or journal figure this is publication-quality. The Round-5 suggestion to use a heavier arrowhead or green color was marked as aesthetic polish; the current figure is acceptable.

### Item R5-4 — Figure title lines embedded in images

**Status: NOT RESOLVED.**

Both Figure 1 and Figure 3 retain title text embedded directly in the image ("Figure 1. MBQC Classical Control Pipeline (3-Stage Model)" in Figure 1, and "Figure 3. Credit-based flow control (ff\_rate\_matched, left) vs. greedy ASAP (right)..." at the bottom of Figure 3). Per standard journal style, figure numbers and captions should appear in the document text below the `\includegraphics`, not be baked into the image itself. This remains unaddressed from Round 5. It is a production formatting issue, not a scientific correctness issue, and does not affect readability for review purposes. It will need correction before camera-ready submission.

### Item R5-5 — QFT artifact description detail (lowest priority)

**Status: NOT RESOLVED / ACCEPTABLE.**

Section VII-C still reads "the signal-shift compiler fails to generate a shifted DAG, likely due to a circuit structure incompatibility." No additional mechanistic detail has been added. As noted in Round 5, this is the lowest-priority item and does not warrant another revision round.

---

## 3. Fresh Cold Read of Draft v6

Reading the paper as if for the first time, without reference to prior rounds:

### 3.1 Abstract

The abstract is precise, well-scoped, and makes quantitative claims that are substantiated by the paper body: "1,080 paired comparisons," "stall rate from 39–49% to below 0.5%," "four independent axes." The phrase "We show by theoretical argument and simulation that the design-safe threshold $F = \lceil W/2 \rceil$ suffices" correctly flags this as a sufficient-condition result rather than a sharp minimum. One redundancy: "Analogous to credit-based flow control in network-on-chip (NoC) and memory systems" appears twice in the abstract — once as a standalone sentence immediately after the preceding sentence already draws the NoC analogy. The duplicate sentence ("Analogous to credit-based flow control in network-on-chip (NoC) and memory systems, ff\_rate\_matched structurally prevents queue overflow...") should be merged with or replace the prior sentence to avoid the repetition. This is a minor prose issue.

### 3.2 Introduction

Clean and well-paced. The progression from MBQC → signal shift → stall regression → credit control is logical. The contributions list is specific and falsifiable, and each contribution is delivered in the paper body. No overclaims.

### 3.3 Section II: Pipeline Model

The 3-stage model is clearly defined. The $F^*$ definition (Section II-D) with the worked example is well-constructed. The conservative framing ("design-safe threshold" rather than "exact minimum") is honest and appropriate. The assumption that every measurement generates one FF operation is clearly stated as an upper bound.

### 3.4 Section III: Stall Regression

The stall regression mechanism is explained at the right level of detail. The parenthetical in Section III-B ("raw+ASAP at $F=4$, from Study 18; note $F$ differs from the shifted figure above") correctly prevents a false comparison. The four-way table in Section V-C is the paper's most important empirical result and is referenced from this section appropriately.

### 3.5 Section IV: ff\_rate\_matched

The pseudocode is correct and $O(1)$. The empirical FF fraction data (QAOA 0.955, VQE 0.974, QFT 0.986) ground-truths the flow rate argument and is one of the paper's stronger supporting measurements. The acknowledgment that the "structural half-fraction heuristic" from v2 was incorrect, and the explicit correction, strengthens rather than weakens credibility.

The theoretical argument in Section IV-B does not constitute a formal proof of $F^* = W/2$, and the paper explicitly labels it "Design Principle (empirically confirmed)" rather than a theorem — this is the appropriate epistemological framing. A knowledgeable reader can verify that the mechanical bound `ff_in_flight ≤ F` holds by construction, while the zero-regression claim is an empirical finding.

### 3.6 Section V: Experiments

The four-study structure is coherent. Each study's setup, hypothesis (where applicable), and results are clearly delineated.

**Figures 6 and 7** now contribute meaningfully to this section where they were previously absent. Figure 6's heatmap is the single most visually compelling figure in the paper — it delivers the latency-invariance result in one glance. Figure 7 provides the large-scale stall curve evidence that was previously accessible only through the Table V-E numbers.

**Minor issue in Figure 6 legend:** The color scale legend reads "F*=4 (W/2, optimal)" for green, "F*=5–6" for a light yellow-green (which does not appear in the heatmap cells), and "F*=7" for orange. The two ASAP cells that show value "6" (QAOA, L_ff=4 and L_ff=5 in the bottom-left panel) are rendered in orange, but the legend maps orange to "F*=7." The "6" cells should be the yellow-green color mapped to "F*=5–6" in the legend, not orange. This is a color-assignment mismatch between the plotted data and the legend. It does not affect the paper's core message (all top-row cells are green = F*=4; all bottom-row cells are yellow-green or worse), but a referee with color-detail attention will flag it. This should be corrected.

**Figure 7 resolution and legend clipping:** The figure is rendered at a resolution where the legend text in the top-left panel (QAOA, H=10) is partially cropped. At print resolution this will be illegible. The figure needs a higher DPI export or a larger figure size. This is a production issue but will affect readability in print.

### 3.7 Sections VI–VIII: Related Work, Discussion, Conclusion

Related work is appropriately scoped. The Tomasulo and RMS analogies are correctly flagged as intuition. Limitations (non-Clifford circuits, probabilistic latency, QFT gap, out-of-order extensions) are honestly disclosed. The conclusion accurately summarizes all four axes with correct run counts and does not exceed what the experiments establish.

### 3.8 References

All 13 references are now correctly identified and formatted. The [DelfosseNickerson2021] fix is complete.

---

## 4. Scores

| Dimension | R1 | R2 | R3 | R4 | R5 | **R6** | Change (R5→R6) | Notes |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| **Novelty** | 7 | 7 | 7.5 | 7.5 | 7.5 | **7.5** | 0 | No new experimental content in v6. Novelty score reflects the FF fraction measurement (v3), the four-way co-design table (v4), and the cross-disciplinary connection. Solid for a systems/architecture venue; not paradigm-shifting. |
| **Technical depth / correctness** | 5 | 6 | 7.5 | 8.0 | 8.5 | **8.5** | 0 | All prior precision issues resolved. Residual: Figure 6 color legend mismatch (orange vs. "F*=5–6" bucket) is minor. Citation fixed. No new technical issues introduced. |
| **Clarity** | 7 | 7 | 7.5 | 8.0 | 8.5 | **9.0** | +0.5 | Figures 6 and 7 are now generated and embedded, completing the visual argument. Figure 6 in particular is the paper's clearest single result: the all-green top row vs. predominantly red bottom row makes the central claim immediately legible. Figure 7 fills the large-scale stall curve gap. The abstract redundancy (duplicate NoC analogy sentence) and the Figure 7 legend clipping are minor deductions — they do not impair the overall clarity story but keep this from 9.5. |
| **Experimental rigor** | 7 | 7.5 | 8.0 | 8.0 | 8.0 | **8.5** | +0.5 | Figure 7 makes the Study 20 stall curves visually verifiable rather than table-only. The Q-scaling trend (Q=36, Q=64, Q=100) is now graphically evident. The residual `ff_in_flight` distribution omission at F/W=0.125 and the QFT gap remain, but both are disclosed and the overall validation is convincingly multi-axis. |
| **Overall** | 6.5 | 7.0 | 7.5 | 8.0 | 8.5 | **9.0** | +0.5 | The paper now presents its full empirical case visually. All blocking issues from prior rounds are resolved. Remaining items (Figure 6 legend color bucket, Figure 7 resolution, embedded figure title text, abstract redundancy) are production-level polish, none of which impairs the scientific contribution. |

---

## 5. TARGET REACHED

**Overall score: 9.0 / 10.**

---

## Accept Notice (Round 6)

Draft v6 of "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation" has reached the 9.0/10 target and is accepted for publication.

The paper makes a clear, well-validated, and practically actionable contribution: it identifies the stall regression pathology that arises when signal shift compilation is applied without flow control, characterizes it quantitatively across four independent experimental axes, and demonstrates that a credit-based scheduling policy (ff\_rate\_matched) eliminates stall regression at exactly half the FF hardware area required by greedy ASAP scheduling — with zero throughput penalty across 1,440 paired simulation runs spanning circuit scales up to H=12 and Q=100 qubits.

The addition of Figures 6 and 7 in v6 completes the visual argument that was carried by tables alone in v5. Figure 6's sensitivity heatmap is the paper's single most compelling figure: the uniform green top row (F*=4 for ff\_rate\_matched across all latency parameters and algorithm families) versus the predominantly red bottom row (F*=8 for ASAP in most conditions) communicates the central design principle in one glance. Figure 7 provides the large-scale stall curve evidence that makes the Study 20 results graphically verifiable.

All blocking issues from Rounds 1–5 have been resolved: the figure label error (burst annotation), the abstract overclaim on F*, the undefined variable in Figure 3, the cross-study mismatched-F comparison, the Little's Law notation collision, and the citation error are all corrected.

---

## 6. Remaining Pre-Submission Polish Items (non-blocking; for camera-ready)

These items do not require a new review round. They should be addressed during journal production or camera-ready preparation, in strict priority order:

1. **Fix Figure 6 legend color mapping.** The two ASAP cells displaying value "6" (QAOA, L_ff=4 and L_ff=5 in the bottom-left panel) are rendered in orange, but the legend maps orange to "F*=7." Those cells should use the yellow-green color mapped to "F*=5–6." This requires one code change in the heatmap generation script (the color boundary between the "5–6" and "7" buckets needs adjustment so that value=6 maps to yellow-green, not orange).

2. **Increase Figure 7 export resolution / figure size.** At current resolution, the legend text in the QAOA H=10 panel is partially cropped and will be illegible in print. Export at ≥300 DPI or increase the figure width parameter before camera-ready submission.

3. **Remove embedded title text from Figures 1 and 3.** Both image files contain baked-in title text ("Figure 1. MBQC Classical Control Pipeline (3-Stage Model)" and the two-line caption at the bottom of Figure 3). Per journal style, figure numbers and captions belong in the document text, not in the image file. Remove the title/caption text from both PNG files and rely solely on the markdown/LaTeX caption blocks.

4. **Remove duplicate NoC analogy sentence in Abstract.** The sentence "Analogous to credit-based flow control in network-on-chip (NoC) and memory systems, ff\_rate\_matched structurally prevents queue overflow while imposing zero throughput penalty." is redundant with the preceding sentence that already draws the NoC analogy. Merge or delete one of the two sentences.

5. **QFT artifact description.** Section VII-C could add one sentence specifying the failure mode (cycle in dependency graph, unsatisfiable constraint, or compiler bug). Lowest priority; not blocking.

---

*End of sixth-round referee report.*
