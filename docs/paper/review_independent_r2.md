# Independent Reviewer Report — Round 2

**Paper:** ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation (draft v7)

**Reviewer expertise:** Quantum computing architectures and compilation; classical computer architecture (CPU pipelines, memory systems, NoC); systems evaluation methodology.

**Review date:** 2026-04-17

---

## 0. Overview of Revision

Draft v7 addresses all five major concerns (M1–M5) from Round 1, plus three factual corrections (FC-A through FC-C) identified by an automated verifier after Round 1. The response is substantive: 240 new simulation runs were added (Study 21), the abstract was significantly rewritten, Section IV-B was retitled and restructured, and the QFT omission is now explained mechanistically. Two previously reported numbers (stall rates attributed to wrong W, and an "below 0.5%" overclaim) were corrected. This is a thorough revision and the paper is substantially improved.

---

## 1. Status of Round-1 Major Concerns

### M1 — Raw-DAG sweep at F < 4
**Status: RESOLVED.**

Study 21 extends the raw-DAG sweep to F ∈ {2, 3} with 240 new simulation runs (W=8, L_meas=1, L_ff=2, QAOA and VQE, H ∈ {4,6,8,10}). The key results are correctly reported: raw+ASAP stall at F=2 is 5.52% (QAOA H8/Q64) and 0.29% (VQE H8/Q64), both above shifted+ff_rate_matched stall at the same F (0.051% and 0.060% respectively). The F* criterion is satisfied at F=2 in the cross-study comparison.

One residual caveat is honestly acknowledged: the Study 21 raw baseline uses H=8/Q=64 circuits while the shifted baseline comes from Study 20 at H=10/Q=100. This cross-scale mismatch means the F*≤2 result is not from a matched-circuit experiment. The paper states this clearly and recommends F=W/2 as the conservative design point pending same-circuit F*=2 confirmation. This is scientifically correct handling.

Section II-D now includes a full F=2, 3, 4 table with clear criterion columns. The worked example is now convincing; the Round-1 criticism (single-seed, single-F) has been addressed.

### M2 — Circular theoretical justification for F* = W/2
**Status: RESOLVED.**

Section IV-B is retitled "Design Principle and Empirical Validation of F* = ceil(W/2)" and opens with an explicit statement that a complete formal proof remains open. The paragraph labels the result "a Design Principle confirmed by simulation." The "Formal Statement" box is now titled "Design Principle (empirically confirmed, Study 21 raw baseline included)." The Little's Law argument is correctly qualified as a "consistency argument, not a derivation" in both Section IV-B and Section VI-D. The Round-1 concern that the paper was presenting an empirical observation as a theorem has been fully resolved.

### M3 — QFT omission unexplained
**Status: RESOLVED.**

The mechanistic explanation is now present and specific: inspection of QFT_H8_Q64_seed*.json artifacts reveals D_ff^shifted = 27–31 for all five seeds. The structural reason (QFT's Fourier butterfly dependency pattern involves long chains of angle-dependent non-Clifford corrections that resist the Pauli rewriting rule) is stated in Sections II-B, V-B, V-C, V-D, V-E, and VII-C. This is much more satisfying than the previous "DAG generation artifact" language. The limitation is now correctly framed as a scope boundary on signal shift applicability, not a simulation bug.

### M4 — D_ff^raw discrepancy (100–300 vs. 63–139)
**Status: RESOLVED.**

The abstract and Figure 1 previously stated 100–300 cycles, which conflicted with the experimental text. The draft now correctly reports 28–226 (QAOA) and 15–99 (VQE) throughout, aligned with Section II-B values. However, Figure 1 still displays "D_ff^raw ≈ 100–300 cycles" — the figure has NOT been regenerated with the corrected range. See Section 4 below.

### M5 — End-to-end result missing from Abstract
**Status: RESOLVED.**

The abstract now explicitly states the primary practical finding: "signal-shift compilation combined with ff_rate_matched reduces total execution cycles below the raw-DAG ASAP baseline, delivering end-to-end throughput improvement with no additional FF hardware cost." The four-way comparison result from Table V-C (1,248 vs. 1,284 QAOA cycles; 1,027 vs. 1,043 VQE cycles) is highlighted in Section V-C as a key result.

---

## 2. Factual Corrections Assessment

### FC-A — W= label error in Section III-B
The correction is applied correctly. Section III-B now presents both W=4 values (39.7%, 49.0%) and W=8 values (56.4%, 73.5%) with correct W= labels. The numbers are internally consistent with the Study 20 table in Section V-E. No anomaly detected.

### FC-B — "below 0.5%" overclaim in Abstract
This is an important correction and has been applied properly. The revised abstract reports the full range (0.049% to 5.62% for ff_rm stall, 0.07% to 85.71% for ASAP stall) with median and maximum reduction figures. The previous cherry-picked "39–49% to below 0.5%" claim is gone.

One concern: the abstract now reports "median stall reduction is 0.39 percentage points, with a maximum reduction of 0.86 percentage points." This sounds unimpressive as an absolute difference (0.39 pp). The more informative statistic — relative reduction (ASAP median 39.17% vs. ff_rm median 0.24%, a ~99% relative reduction) — is present in the text of the abstract but should be made more prominent or placed before the absolute pp figures.

### FC-C — Table V-E W column and QAOA H12/Q64 F=2 value
The W column has been added. The QAOA H12/Q64 F=2 value is now 38.8% (corrected from 39.3%). The table and surrounding text are now consistent.

---

## 3. Number Verification

The following key numbers were checked for internal consistency:

**Study 20 Table (Section V-E):**
- QAOA H10/Q100, W=4, F=2: ASAP 39.7%, ff_rm 0.05%. F=3: ASAP 19.2%, ff_rm 0.05%. F=4: ASAP 0.07%, ff_rm 0.07%. The convergence at F=4 (both policies near-zero) is consistent with the claim that F=W/2 is the threshold. No anomaly.
- VQE H10/Q100, W=4, F=2: 49.0% / 0.06%. F=3: 23.9% / 0.09%. F=4: 0.08% / 0.08%. Consistent. No anomaly.

**Study 21 Table (Section V-F):**
- QAOA H8/Q64: F=2: 5.52%. F=3: 2.53%. F=4: 3.45%. Note that F=3 stall (2.53%) < F=4 stall (3.45%) for QAOA. This is a non-monotone ordering that is suspicious. Stall rate is expected to decrease or stay flat as F increases (more slots → less overflow). A local increase from F=3 to F=4 could indicate a measurement artifact, a tie-breaking anomaly in a specific seed, or a genuine non-monotone dependency in the DAG. The paper does not address this. **This is a new flag that was not present in Round 1.**

- VQE H8/Q64: F=2: 0.29%. F=3: 0.51%. F=4: 0.86%. This is monotone-increasing as F increases, which is the opposite of the expected direction. Higher F should give ASAP more room to operate without overflow, reducing stall. A monotone increase in stall with F is physically unexpected for raw+ASAP. This is potentially a data integrity issue. If these numbers are correct, there should be an explanation; if they are artifacts, they should be flagged. **This is a new flag.**

**Four-way comparison (Section V-C, Table):**
- Raw+ASAP QAOA stall 3.45%; shifted+ASAP 25.23%; raw+ff_rm 1.87%; shifted+ff_rm 0.24%. These are internally consistent: raw DAG has low stall (well-behaved workload), shifted ASAP has high stall (burst pathology), ff_rm on shifted recovers to near-raw levels. The magnitude ratios (7× for QAOA, 54× for VQE) are correctly stated. No anomaly.
- Cycle counts: QAOA shifted+ff_rm 1,248 vs. raw+ASAP 1,284. Difference: 36 cycles (~2.8% improvement). This is a modest improvement but the direction is the claimed end-to-end result. VQE: 1,027 vs. 1,043, difference 16 cycles (~1.5%). These magnitudes are plausible. No anomaly.

**Abstract median stall reduction:**
The abstract states "median stall reduction is 0.39 percentage points, with a maximum reduction of 0.86 percentage points." The supporting text (FC-B header) says "ff_rm stall: 0.049% to 5.62% (median 0.24%), ASAP stall: 0.07% to 85.71% (median 39.17%), Median stall reduction (ASAP – ff_rm): 0.39 pp, max 0.86 pp." If median ASAP is 39.17% and median ff_rm is 0.24%, the median reduction is 38.93 pp, not 0.39 pp. The 0.39 pp figure must come from computing the per-pair difference (ASAP_i – ff_rm_i) and taking the median, which is a different statistic — it reflects the median over all pairs including small-scale circuits where ASAP stall is also near zero. This is a statistically valid but potentially misleading presentation: a reader unfamiliar with the per-pair vs. aggregate distinction will read "median reduction 0.39 pp" as a weak result when the dramatic cases (39.7% → 0.05%) are buried in the range. **This presentation choice should be clarified or the aggregate median should be added.**

---

## 4. Fresh Section-by-Section Assessment

### Abstract
**Now strong.** The rewrite addresses M5 (end-to-end result), FC-B (overclaim), and M4 (D_ff range). The reporting of both absolute range and median is honest. The specific W= scoping for the 39.7%/49.0% figures is correct. The "median stall reduction 0.39 pp" presentation concern noted above is a clarity issue, not a factual error. One remaining editorial issue: the abstract is now dense and slightly long, with several numerical ranges that are hard to parse in one reading. The core message (credit gate + W/2 = same throughput, half the hardware, no regression) is present but takes effort to extract.

### Section I (Introduction)
Good. The NoC analogy duplication issue from Round 1 (noted in m6) has not been addressed — the analogy appears in consecutive paragraphs (paragraph 3 and the contributions list). Minor. The contributions list is well-organized and accurate: "Design Principle confirmed by simulation" is correctly labeled.

### Section II (MBQC Pipeline Model)
Section II-A: The model assumption caveat ("every measurement generates exactly one FF operation") and its conservatism are now explicitly stated. Section II-B: The signal shift scope, non-Clifford limitation, and QFT exclusion are explained. The D_ff^raw ranges are correct and consistent with experiments. Section II-D: The F* definition and worked example are now convincing (full F=2,3,4 table). The "conservative design point" framing is honest.

Round-1 question Q3 (how signal shift applies to QAOA/VQE non-Clifford circuits) is not explicitly answered in the text. Section II-B says "the scope of this paper is circuits where signal shift reduces D_ff to 1–2" without explaining how non-Clifford parametrized rotations in QAOA/VQE are handled. This remains an open explanatory gap for readers outside the MBQC community.

### Section III (The Stall Regression Problem)
Section III-B is now correctly scoped with W= labels. The comparative figures at W=4 and W=8 are consistent. The F=3 data for ASAP (19.2% QAOA, 23.9% VQE at W=4) correctly shows stall regression persists at F=3 for the shifted DAG. The non-monotone/inverse behavior of VQE raw+ASAP stall (Table V-F, increasing with F) is not discussed here. Section III-C is unchanged and good.

### Section IV (ff_rate_matched)
Section IV-A pseudocode: The `available_credits = F - ff_in_flight` line no longer has the `max(0, ...)` noted in Round 1 (m4 from Round-1 minor concerns). This is correct — the invariant `ff_in_flight <= F` is maintained by construction so the clamp is unnecessary. Good.

Section IV-B: The retitle and restructure are effective. The FF fraction data (0.955, 0.974, 0.986) is clearly relevant and the design principle is honestly labeled. The "Intuition for the F/W = 0.125 case" paragraph is useful and new.

Section IV-C: The RMS analogy (m2 from Round 1 minor concerns) has been **removed** from this section. Good. However, the text still contains a reference in Section VI-D (Little's Law section): checking... the RMS analogy does not appear in Section VI-D in v7. The [LiuLayland1973] reference remains in the bibliography but is not cited in the main text. The RMS concern is resolved.

### Section V (Experimental Evaluation)
Section V-A: The canonical validation cases are now numerically reported ("expected 500 cycles, measured 500; expected 200 cycles, measured 200"). This directly addresses Round-1 concern (V-A subsection). Good. cycles_ratio is now formally defined in this section (addressing minor concern m5).

Section V-B (Study 17): The tie-breaking explanation for QFT discrepancies is now connected to QFT's structural properties. The 346/360 exact matches + 14 discrepant QFT pairs is clearly reported.

Section V-C (Study 18): The four-way comparison table is preserved and prominent. The cycle counts are clearly stated as the end-to-end result. The footnote on F*=4 meaning "F*≤4 within the swept range" is an honest qualification that was missing in v6.

Section V-D (Study 19): Round-1 concern about the undemonstrated causal claim ("raw-DAG baseline stall rate increases with L_meas because the longer measurement pipeline itself increases congestion") — this claim is still asserted without a supporting table or plot. It is a secondary point and the paper is not wrong for it, but a supporting table of raw+ASAP stall vs. L_meas would strengthen the argument.

Section V-E (Study 20): Perfect 1080/1080 exact cycle match result is correctly emphasized. The ASAP stall numbers at W=8 (Section III-B cross-reference, 56.4% and 73.5%) are consistent with the W=4 numbers in Table V-E.

Section V-F (Study 21): Clearly reported with a full table of raw+ASAP stall at F=2, 3, 4. The cross-study F* determination table is well-structured. The honest acknowledgment of the scale mismatch limitation is appropriate.

Section V-G (Summary box): The quantitative summary is accurate and the QFT caveat is properly included.

### Section VI (Related Work)
The Little's Law sojourn time clarification (the key correction requested in Round 1, Section VI-D) has been applied: "Under ff_rate_matched, no overflow queue forms (by construction), so W_sojourn = L_ff exactly, making the Little's Law bound tight." This is a substantive improvement.

The notation collision fix (W_sojourn replacing W_service) is applied consistently. The Kumar et al. comparison note (NoC traffic stochastic vs. DAG-structured) is now explicitly stated. These were Round-1 recommendations and have been implemented.

Round-1 requests for broader related work citations (Litinski 2019, Bombin et al., MBQC simulation frameworks) remain unaddressed. This is acceptable for a systems paper targeting architecture audiences, but the fault-tolerant MBQC citation gap persists.

### Section VII (Discussion)
Section VII-A now includes the explicit caveat that the area reduction claim applies to parallel-slot FF implementations and that hardware designers should validate the assumption. This was a Round-1 recommendation and has been implemented.

Section VII-C now includes the Round-1 requested note on the out-of-order extension condition ("possible only if there exist non-FF-dependent nodes in the ready queue at the time credits are blocked"). Good.

### Section VIII (Conclusion)
The conclusion is accurate and well-organized. The five-axis summary bullet list is a useful overview. The QFT caveat in the final paragraphs is correctly placed.

---

## 5. Figure Evaluation

### Figure 1 (fig1_pipeline.png)
**Residual issue (from M4, partially unresolved).** The figure still displays "D_ff^raw ≈ 100–300 cycles" in the annotation box. The paper text (abstract and Section II-B) now correctly states 28–226 cycles (QAOA) and 15–99 cycles (VQE). The figure annotation has not been updated to match. This is an inconsistency between the figure and the corrected text. It is minor in isolation but notable given that FC-A of the revision changelog explicitly says "Abstract and Figure 1 previously stated '100–300 cycles' which was inaccurate... Corrected to: QAOA H=4-12 range 28-226..." — the correction was noted but apparently not applied to the figure itself.

The credit return arrow and stall gate remain clearly labeled. The "burst (shifted DAG, ASAP)" annotation is effective. Core figure quality is good.

### Figure 3 (fig3_credit_mechanism.png)
**Excellent and unchanged.** The "Stall rate ~ 40-49%" label is now visible in the ASAP right panel (annotated on the "Queue overflows" text). The Round-1 suggestion to add the stall rate to the right panel has been implemented. This is the best figure in the paper.

### Figure 6 (fig6_sensitivity.png)
**Significantly improved.** The figure has been regenerated with Study 21 results incorporated. The color scheme now uses a discrete legend with "F*=2 (confirmed minimum)" (dark green), "F*=3" (medium green), "F*=4 (W/2 design point)" (light green), "F*=5-6" (yellow), "F*=7" (orange), "F*=8 (=W, worst)" (red). All ff_rate_matched cells show F*=4 in light green — consistent with the paper's claim that F*≤4 within Studies 18/19 swept range.

Round-1 concern about the color mapping inconsistency (orange vs. yellow-green for F*=6 in QAOA, L_ff=4,5 bottom row): in the regenerated figure, these cells are clearly orange with the value "6" displayed, and the legend maps orange to "F*=7." This remains inconsistent: the paper text (Section V-C Table) states QAOA drops to F*=6 at L_ff≥4, but the legend assigns orange to F*=7 and the cells display "6." Either the legend should include a distinct color for F*=6, or the orange cells should be relabeled. The "F*=5-6" yellow band in the legend does not appear to match any cell in the rendered figure. **This color-label mismatch persists from Round 1.**

The QAOA H6 / L_meas=4 partial exception (bottom-right of ASAP L_meas panel) is not labeled or explained in the figure caption, as suggested in Round 1. Still missing.

### Figure 7 (fig7_scaling.png)
**Now covers W=8 correctly.** The figure title states "Study 20, W=8" which is the correct configuration for large-scale stall rate characterization. The four panels (QAOA H10, QAOA H12/Q64, VQE H10, VQE H12/Q64) are organized logically. The green dashed horizontal line for raw+ASAP baseline (from Study 21) is present. The vertical dotted line at F=4 marking the W/2 design point is clear.

Residual issue from Round 1: line width and marker differentiation for Q=36/64/100 curves in the H=10 panels are still difficult to distinguish in the image. The curves are rendered in different shades of blue/orange but the differences are subtle. The H=12 Q=100 absence (only Q=64 shown) is now explained in the caption ("Q=100 is absent for H=12 due to circuit scale constraints in the test set"). Good.

The stall rate axis units are shown as "[%]" in the axis label in this version. Good.

---

## 6. Remaining Issues (Priority Order)

### P1 (Moderate): Figure 1 annotation not updated — D_ff^raw still shows 100–300
The revision changelog (FC-A) explicitly states that Figure 1's "100–300 cycles" was inaccurate and was "Corrected." The correction appears in the text but not in the figure. The figure still displays the old value. This should be corrected to show the experimentally verified range: "D_ff^raw ≈ 28–226 (QAOA), 15–99 (VQE)." Until corrected, there is an explicit inconsistency between the claimed fix and the actual figure content.

### P2 (Moderate): Non-monotone VQE raw+ASAP stall in Study 21 requires explanation
Table V-F shows VQE H8/Q64 raw+ASAP stall: F=2: 0.29%, F=3: 0.51%, F=4: 0.86%. Stall rate increasing with FF width is physically counterintuitive (more slots = more overflow capacity = less stall). This also applies, more mildly, to QAOA H8/Q64: F=3 stall (2.53%) < F=4 stall (3.45%) — another local non-monotone ordering. No explanation is provided. Possible explanations include: (a) different tie-breaking at different F values leading to different scheduling sequences; (b) the stall rate metric being sensitive to boundary effects at small circuit size; (c) a simulator bug. The paper should state whether this non-monotone behavior is expected and why, or flag it as a known anomaly.

### P3 (Minor): Abstract median stall reduction framing is misleading
The abstract reports "median stall reduction is 0.39 percentage points, with a maximum reduction of 0.86 percentage points." As noted in Section 3 above, this is the median of per-pair absolute differences, not the difference of medians. A reader will interpret this as "ff_rm typically saves only 0.39 percentage points of stall rate," which undersells the contribution dramatically. The dramatic cases (e.g., ASAP 39.7% → ff_rm 0.05%) are present in the abstract but in a different part of the sentence. Adding the relative reduction (e.g., "99% relative stall reduction in large-scale circuits") alongside the per-pair median would prevent this misreading.

### P4 (Minor): Figure 6 color-label mismatch persists for F*=6 ASAP cells
The ASAP L_ff heatmap shows "6" in orange cells at L_ff=4,5 for QAOA. The legend maps orange to "F*=7" and has a separate "F*=5-6" yellow entry that does not appear in any visible cell. The figure legend should be corrected to map orange (or a distinct color) to F*=6 values. This was flagged in Round 1 and remains unresolved.

### P5 (Minor): Non-Clifford scope of signal shift for QAOA/VQE not explained
Round-1 Q3 asked how signal shift applies to QAOA/VQE circuits with non-Clifford parameterized rotations. The paper still states "the scope of this paper is circuits where signal shift reduces D_ff to 1–2" without explaining the mechanism. A one-sentence clarification in Section II-B (e.g., whether the simulated QAOA/VQE circuit graphs represent a Clifford-only dependency structure or whether non-Clifford corrections are separately tracked) would close this gap for architecture-audience readers.

### P6 (Editorial): Introduction NoC analogy duplication persists
The NoC credit analogy appears in both paragraph 3 ("This is precisely the mechanism of credit-based flow control") and the contributions list ("Drawing on analogies to credit-based flow control"). Paragraph 3 sets the context and the contributions list builds on it — this is slightly redundant. One of the two occurrences could be trimmed or the forward reference could be moved to Section IV.

---

## 7. Scores (Round 2)

| Criterion | Round 1 | Round 2 | Change | Justification |
|---|---|---|---|---|
| Novelty / originality | 7 | **7.5** | +0.5 | Study 21 F*≤2 result sharpens the novelty; cross-study comparison is a genuine contribution even if not same-circuit. |
| Technical depth / correctness | 6 | **8.0** | +2.0 | FC-B and FC-A corrections are significant improvements. Study 21 fills the primary experimental gap. The non-monotone VQE stall anomaly (P2) prevents a higher score. |
| Clarity | 7 | **7.5** | +0.5 | Abstract rewrite and four-way comparison elevation improve clarity. The median stall framing (P3) and figure annotation mismatch (P1) are residual issues. |
| Experimental rigor / reproducibility | 7 | **8.5** | +1.5 | 240 new runs, honest cross-study caveat, W= labels corrected, canonical validation numerically reported. The non-monotone anomaly (P2) is a minor but noted concern. |
| **Overall** | **6.5** | **8.0** | **+1.5** | The paper has crossed from "major revision" territory into "minor revision" territory. The five major concerns are addressed, the factual corrections are applied, and the experimental coverage is now convincing. Remaining issues are resolvable without new experiments. |

---

## 8. Recommendation

**Minor Revision.**

The paper is substantially improved and the five major concerns from Round 1 are addressed. The core contribution is sound: ff_rate_matched is a clean, correct, and practically relevant policy; the F*≤W/2 design principle is empirically confirmed across a comprehensive parameter sweep; and the factual corrections (FC-A through FC-C) have removed previously reported errors.

The remaining issues (P1–P6) are fixable without new experiments:

- P1 requires regenerating Figure 1 with the corrected D_ff^raw annotation.
- P2 requires a one-paragraph explanation of the non-monotone VQE stall in Table V-F.
- P3 requires adding a relative reduction figure alongside the per-pair median in the abstract.
- P4 requires correcting the Figure 6 legend color mapping.
- P5 requires one sentence in Section II-B.
- P6 is an optional editorial polish.

None of P1–P6 challenge the paper's central claims or require new simulation runs.

**Overall score: 8.0. TARGET NOT YET REACHED (threshold 9.0).**

---

## 9. Summary for Authors

Round 1 identified five major weaknesses. Round 2 finds all five addressed. The paper is now honest, well-calibrated, and scientifically rigorous within its stated scope. The key remaining work is:

1. Fix the Figure 1 annotation (P1) — a single-line edit to the figure source.
2. Explain the non-monotone VQE stall values in Table V-F (P2) — a paragraph in Section V-F.
3. Add relative stall reduction statistics to the abstract (P3) — a sentence edit.
4. Fix Figure 6 legend color mapping for F*=6 (P4) — a figure source fix.

Items P5 and P6 are recommended but lower priority.

After addressing P1–P4, the paper would warrant an overall score of approximately 8.5–9.0. The sub-9.0 score in Round 2 reflects primarily P2 (an unexplained numerical anomaly that could indicate a data integrity issue) and the inherent limitation that the F*≤2 result is cross-study rather than same-circuit.

---

*End of Round 2 review.*
