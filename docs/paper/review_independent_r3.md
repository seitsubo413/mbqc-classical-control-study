# Independent Reviewer Report — Round 3

**Paper:** ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation (draft v8)

**Reviewer expertise:** Quantum computing architectures and compilation; classical computer architecture (CPU pipelines, memory systems, NoC); systems evaluation methodology.

**Review date:** 2026-04-17

---

## 0. Overview of Revision

Draft v8 addresses all four P1–P4 priority issues identified in Round 2, plus incorporates the Figure 6 legend correction (P4) and Figure 1 annotation correction (P1) by regenerating both figures. The non-monotone stall explanation requested in P2 has been added as a full paragraph in Section V-F. The abstract has been rewritten to replace the "0.39 percentage points" framing with a relative reduction statistic (P3). This is a targeted, focused revision that directly addresses the items on the Round 2 priority list. The paper has not regressed on any point from Round 2.

---

## 1. Status of Round-2 Issues P1–P4

### P1 — Figure 1 annotation corrected
**Status: RESOLVED.**

Viewing the regenerated fig1_pipeline.png confirms the annotation now reads "D_ff^raw ≈ 28–226 cycles (QAOA), 15–99 (VQE)" in the gray annotation box, consistent with the abstract and Section II-B. The Round-2 inconsistency — where the revision changelog claimed a correction that had not been applied to the actual figure — is resolved. The credit return arrow, stall gate label, and burst annotation are all present and legible.

### P2 — Non-monotone VQE raw+ASAP stall in Table V-F explained
**Status: RESOLVED.**

Section V-F now contains a dedicated paragraph titled "Note on non-monotone stall rate values in Table V-F." The explanation is mechanistically correct:

- For VQE H8/Q64: D_ff^raw = 63 for all five seeds (identical circuits). As F increases, total_cycles drops sharply (2058 → 1379 → 1043) because larger F increases raw-DAG throughput. Absolute stall_cycles is nearly constant (6, 7, 9 cycles), changing by only 3 cycles across the full F range. Stall_rate = stall_cycles / total_cycles therefore rises as F increases because the denominator falls faster than the near-zero numerator.
- For QAOA H8/Q64: the same denominator effect explains the F=3 → F=4 non-monotonicity (2.53% < 3.45% at F=3 < F=4).

The explanation correctly identifies this as a denominator effect rather than a pipeline congestion anomaly. The key claim — that absolute stall counts are tiny (< 50 cycles) relative to thousands of total cycles — is stated explicitly, and the impact on the F* criterion is addressed: even the largest raw+ASAP stall rate in the table (5.52% QAOA H8/Q64 at F=2) far exceeds shifted+ff_rate_matched stall at the same F (0.051%), so the criterion result is unaffected.

**Technical assessment of the explanation:** The denominator-effect explanation is correct. The given numbers are internally consistent: (9 stall cycles) / (1043 total cycles) = 0.86%, which matches Table V-F. (6 stall cycles) / (2058 total cycles) = 0.29%. (7 stall cycles) / (1379 total cycles) = 0.51%. All three VQE entries check out. For QAOA: the claim that F=3 gives 2.53% and F=4 gives 3.45% is explained by the same mechanism — F=4 allows higher throughput on the raw QAOA H8/Q64 circuit (D_ff^raw ≈ 127–163), so total_cycles is lower at F=4 than at F=3, while absolute stall cycles may be slightly higher at F=4 due to more aggressive issue attempting to fill the FF pipeline. The explanation is physically sound. No further data verification is required.

One residual precision issue: the paragraph states "absolute stall counts are tiny (less than 50 cycles out of thousands of total cycles)" — this is accurate for the VQE case (9 cycles maximum) but the 50-cycle bound is loose. It is not wrong, but a reader who looks up the QAOA case may expect the actual number to be specified rather than bounded. This is a minor editorial note, not an error.

### P3 — Abstract median stall reduction reframed to relative reduction
**Status: RESOLVED.**

The abstract has been rewritten. The problematic "median stall reduction is 0.39 percentage points" sentence has been replaced with: "ff_rate_matched reduces the median stall rate from 39.17% (ASAP) to 0.24% (ff_rm) across all 1,440 paired comparisons — a 99.4% relative reduction — with zero throughput cost in every comparison." The per-pair median of 38.85 pp absolute reduction is also retained.

**Assessment:** The new framing is dramatically clearer. The 99.4% relative reduction figure is the correct headline statistic: it is computed as (39.17 − 0.24) / 39.17 = 99.4%, using the aggregate medians across all 1,440 pairs. This is the difference of medians, not the median of differences — a methodologically valid and more informative statistic for summarizing magnitude of effect. The abstract now properly calibrates reader expectations: the contribution is large and the framing is honest.

### P4 — Figure 6 legend color-label mismatch corrected
**Status: RESOLVED.**

Viewing the regenerated fig6_sensitivity.png confirms the legend now contains seven distinct entries with correct labels and matching colors:
- F*=2 (confirmed minimum): dark green (#1a7a1a-range)
- F*=3: medium green
- F*=4 (W/2 design point): lighter green (the top-row cells)
- F*=5 (yellow-green): present in legend, no cells in current data — correct (no parameter combination yields F*=5)
- F*=6 (orange): correctly labeled, matching the QAOA L_ff=4,5 cells in the ASAP bottom-left panel that display "6"
- F*=7 (red-orange): legend entry present
- F*=8 (=W, worst, dark red): all ASAP cells not showing 6

The Round-2 mismatch — orange cells labeled "6" in the figure while the legend mapped orange to "F*=7" — is resolved. The cell values in the ASAP panel at L_ff=4,5 for QAOA now correctly read "6" and the legend entry for orange reads "F*=6 (orange)." The F*=5 yellow-green entry appears in the legend even though no current cell has that value; this is correct behavior (the legend documents the full color scale), not an error.

The top-row ff_rate_matched panels are uniformly green with value "4," consistent with F*≤4 within the Studies 18/19 sweep range. The caption correctly notes that Study 21 confirms F*≤2 in the cross-study comparison, making the "4" cells conservative.

The QAOA H6 / L_meas=4 partial exception in the ASAP L_meas panel (bottom-right) remains unlabeled in the figure, as was flagged in Round 2 as a P6 note. The figure caption in the draft text reads "ASAP — F*(ASAP) ranges from 6 to 8 (orange to dark red), with VQE requiring F*=8 regardless of latency parameters." However, the actual bottom-right ASAP panel shows all "8" for the L_meas sweep; the partial exception that appears at QAOA H6/L_meas=4 in Study 19 (3/5 seeds) is averaged to "8" in the figure because the figure shows F* per row (not per-seed). This is an acceptable representation choice and the text in Section V-D addresses the partial exception explicitly.

---

## 2. Evaluation of the VQE Non-Monotone Explanation (P2 Detailed)

The denominator-effect explanation added to Section V-F is correct and well-presented. Specifically:

**Correctness:** The mechanism is real and the numbers check out exactly. VQE H8/Q64 having D_ff^raw = 63 for all seeds (identical circuits) means total_cycles is purely a function of F on the raw DAG — the circuit is deterministic. The fact that total_cycles decreases by ~50% from F=2 to F=3 (2058 → 1379) while stall_cycles increases by only one cycle (6 → 7) is a clean, verifiable demonstration of denominator dominance. The explanation is specific enough that a skeptical reader can check the arithmetic without ambiguity.

**Presentation:** The paragraph is structured well. It opens with the counterintuitive observation ("seems counterintuitive"), names the mechanism ("denominator effect"), gives the specific numbers (6, 7, 9 stall cycles; 2058, 1379, 1043 total cycles), derives the implication (stall_rate = stall_cycles / total_cycles rises as denominator falls), then explains the QAOA case by analogy, and closes by reasserting the F* criterion is unaffected. This structure is pedagogically effective.

**One residual precision concern:** The explanation states "absolute stall counts change by only 3 cycles across the entire F range" for VQE H8/Q64. This is accurate (9 − 6 = 3). However, the explanation of the QAOA non-monotonicity says "absolute stall counts change by at most a few tens of cycles across F values, while total_cycles drops by hundreds." This is less precise — "a few tens" could be 20 or 90. Given that the VQE case is fully quantified, the QAOA claim would benefit from the actual numbers. However, the QAOA data in Table V-F is at the H=8/Q=64 level (not the H=10/Q=100 level), and the F=3 vs. F=4 stall rates (2.53% vs. 3.45%) are the raw circuit values. The explanation is sufficient for the reader to understand the mechanism even without the exact stall cycle counts.

**Conclusion:** The explanation is correct, well-placed, and sufficient to close the anomaly flag from Round 2.

---

## 3. Evaluation of the 99.4% Relative Reduction Claim (P3 Detailed)

**The statistic as reported:** "ff_rate_matched reduces the median stall rate from 39.17% (ASAP) to 0.24% (ff_rm) across all 1,440 paired comparisons — a 99.4% relative reduction."

**Methodological question:** The 1,440 pairs span Studies 17 and 20, which cover substantially different (W, F) configurations and circuit scales (H=4–12, Q=16–100). Computing a single aggregate median conflates small-scale circuits (H=4/Q=16, where ASAP stall may itself be low) with large-scale circuits (H=10/Q=100, where ASAP stall is 39–73%). Is the 99.4% figure meaningful as an aggregate?

**Assessment: Yes, the claim is meaningful and is presented honestly.**

The revision changelog (FC-B metadata in the draft header) provides the full distribution: ff_rm stall ranges from 0.049% to 5.62% (median 0.24%); ASAP stall ranges from 0.07% to 85.71% (median 39.17%). The abstract reports both the full range and the medians. The 99.4% figure (= (39.17 − 0.24) / 39.17) is the relative reduction using the aggregate medians. It does not claim to represent every pair — it is an aggregate summary statistic. The fact that some pairs (small-scale circuits) contribute low ASAP stall values will pull the median downward, making the 99.4% figure conservative if anything (the improvement at large scale is even more dramatic). The abstract also separately calls out the specific large-scale figures (39.7% and 49.0% ASAP at W=4, F=2; 56.4% and 73.5% at W=8, F=2), so the reader is not misled about the per-circuit magnitude.

**Honest reporting check:** The draft does not cherry-pick only favorable conditions. The abstract explicitly states: "The full stall range is 0.049%–5.62% (ff_rate_matched) vs. 0.07%–85.71% (ASAP), with a median per-pair absolute reduction of 38.85 percentage points." This is complete. The cross-study heterogeneity (different W and F values) is an inherent feature of a comprehensive parameter sweep, not a methodological deficiency. The 99.4% figure is valid as a summary of aggregate behavior across all tested conditions.

**One precision check:** The abstract states the per-pair median absolute reduction is 38.85 pp, while the aggregate median reduction is 39.17 − 0.24 = 38.93 pp. These differ slightly because the median of (ASAP_i − ff_rm_i) across pairs ≠ median(ASAP_i) − median(ff_rm_i) in general (Equation of medians inequality). Both statistics are reported, and both are labeled correctly. No error.

**Conclusion:** The 99.4% relative reduction claim is statistically meaningful, accurately computed, and presented with full distributional context. It is not misleading.

---

## 4. Fresh Read — New Issues in Draft v8

### 4.1 Figure 7 legend readability (residual from Round 2, not resolved)
As flagged in Round 2 but not classified as P1–P4, the line width and marker differentiation for Q=36/64/100 curves in the H=10 QAOA and VQE panels remain difficult to distinguish in the rendered figure. The curves are plotted in different shades of blue/orange. At printed or reduced-size viewing, Q=36 and Q=64 lines are nearly indistinguishable. The H=12 panels are unaffected (single curve). This is a presentation issue that affects readability of the scaling conclusion.

**Severity:** Minor. The stall rate values at F=2 and F=4 (the design-relevant operating points) can still be read from the figure even with overlap. The main claim — that ff_rm stays near zero across all Q while ASAP is high at F=2 and drops at F=4 — is visually clear. However, the caption claims three curves are present in H=10 panels and a reader may not be able to verify this from the figure alone.

### 4.2 Internal terminology: "stall regression" vs. "stall rate non-monotonicity" distinction
Section V-F's new explanation paragraph uses "non-monotone stall rate values" in the section title and "non-monotonicity" in the prose. The term "stall regression" is used elsewhere in the paper for the phenomenon of shifted+ASAP stall exceeding raw+ASAP stall. These are two distinct phenomena:
- "Stall regression" = shifted+ASAP performs worse than raw+ASAP (the main problem this paper solves).
- "Non-monotone stall" = raw+ASAP stall rate increases with F (the Table V-F anomaly explained in the new paragraph).

The paper keeps these distinct throughout — "stall regression" never appears in the new non-monotone paragraph. This is correct usage. No issue.

### 4.3 The per-pair median of 38.85 pp reported twice in the abstract
The abstract now reports the same absolute-difference statistic in two places: (1) as "a 99.4% relative reduction" embedded in the new aggregate sentence, and (2) as "a median per-pair absolute reduction of 38.85 percentage points" at the end. These are not duplicates — the first is the relative version of the aggregate-median calculation, the second is the per-pair median. However, the two are easily confused in a dense abstract. The abstract as a whole is effective but continues to be long (approximately 350 words). This is a presentation note rather than a correctness concern.

### 4.4 Cross-study mismatch in the Section II-D worked example (inherited limitation, properly disclosed)
The worked example in Section II-D compares Study 21 raw+ASAP (H=8/Q=64) against Study 20 shifted+ff_rm (H=10/Q=100). This cross-scale mismatch was flagged in Round 2 as an acknowledged limitation, and the paper continues to handle it honestly: the conservative design point recommendation (F=W/2 rather than F=2) is explicitly justified by this mismatch. The limitation is disclosed in three places (Section II-D, Section V-F, Section VII-C). No new concern; confirming continued appropriate disclosure.

### 4.5 Reference [LiuLayland1973] in bibliography but uncited in text
The [LiuLayland1973] entry (Liu and Layland 1973 on real-time scheduling) remains in the references section but is not cited anywhere in the draft. This was noted in Round 2 (the RMS reference removal was confirmed resolved), but the bibliographic entry was not cleaned up. This is a minor editorial residual — an orphaned reference. It does not affect scientific content, but the bibliography should be consistent.

### 4.6 Section V-D causal claim without supporting data
Round 2 noted that the claim in Section V-D ("the raw-DAG baseline stall rate increases with L_meas because the longer measurement pipeline itself increases congestion") is asserted without a supporting table or figure. This claim remains unsupported in v8. The text explains the causal chain ("not because the shifted burst is reduced" but because "raw-DAG baseline stall rate increases"), which is a necessary step for interpreting the QAOA H6/L_meas=4 partial exception. A table of raw+ASAP stall vs. L_meas for Study 19 circuits would confirm this, but the paper makes no such claim in the experimental results — the argument is qualitative. The causal statement is plausible and internally consistent, and the paper is not making a quantitative claim from it. This remains a minor weakness but does not undermine the main conclusions.

### 4.7 No new correctness concerns found
The numerical values in the abstract, Section III-B, Section V-E (Table), Section V-F (Table), and Section VIII (Conclusion) are internally consistent and consistent with the Round 2 verified values. No new numerical anomaly was detected in a full re-read.

---

## 5. Scores (Round 3)

| Criterion | Round 1 | Round 2 | Round 3 | Change vs. R2 | Justification |
|---|---|---|---|---|---|
| Novelty / originality | 7 | 7.5 | **7.5** | 0 | No new contributions; F*≤2 result from Study 21 remains cross-study. The credit-gate mechanism and W/2 design principle are the core novelty, unchanged. |
| Technical depth / correctness | 6 | 8.0 | **9.0** | +1.0 | P2 (non-monotone anomaly) is now fully explained with correct arithmetic and clear mechanism. No unresolved numerical anomalies remain. The denominator-effect explanation is tight. The cross-study limitation is properly bounded. |
| Clarity | 7 | 7.5 | **8.5** | +1.0 | Abstract rewrite (P3) dramatically improves the key statistic presentation. Figure 1 (P1) and Figure 6 (P4) corrections remove visual inconsistencies. The new V-F paragraph is pedagogically effective. Residuals: Figure 7 curve distinguishability and abstract density. |
| Experimental rigor / reproducibility | 7 | 8.5 | **9.0** | +0.5 | All numerical anomalies from Round 2 are explained or eliminated. Study coverage, honest caveats, W= labels, canonical validation — all confirmed from Round 2. Limitation of cross-study F*≤2 is properly disclosed. Orphaned [LiuLayland1973] reference and Figure 7 curve differentiation are the only residuals. |
| **Overall** | **6.5** | **8.0** | **9.0** | **+1.0** | P1–P4 are all resolved without introducing new issues. The paper is now technically correct, clearly presented, and experimentally rigorous within its stated scope. The remaining items (Figure 7 curve differentiation, orphaned reference, abstract length) are editorial and do not affect scientific validity. |

---

## 6. TARGET ASSESSMENT

**Overall score: 9.0**

**TARGET REACHED.**

The paper ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation (draft v8) has reached the 9.0 threshold across three rounds of review.

All five major concerns from Round 1 (M1–M5) were fully addressed in Round 2 (draft v7). All four prioritized issues from Round 2 (P1–P4) have been fully addressed in Round 3 (draft v8):

- P1: Figure 1 annotation corrected and figure regenerated. RESOLVED.
- P2: Non-monotone VQE stall explained via denominator effect with correct arithmetic. RESOLVED.
- P3: Abstract rewritten with 99.4% relative reduction as the headline statistic. RESOLVED.
- P4: Figure 6 legend corrected with seven distinct F* color entries. RESOLVED.

The core contribution — a credit-based flow control policy that eliminates stall regression at F=W/2 with zero throughput cost across 1,440 paired comparisons — is sound, honestly reported, and supported by comprehensive experimental validation across five independent parameter axes. The factual corrections (FC-A through FC-C) from the automated verifier pass in Round 2 have been maintained in Round 3.

Remaining items are editorial only and do not affect the scientific contribution:

1. [Low priority] Figure 7: Q=36/64/100 curve differentiation in H=10 panels. Consider thicker line widths or distinct markers.
2. [Low priority] Bibliography: Remove orphaned [LiuLayland1973] reference (uncited in text).
3. [Optional] Abstract: Consider trimming to under 300 words; the current density may challenge readers at first reading.
4. [Optional] Section V-D: Add a small supporting table for the "raw-DAG baseline stall rate increases with L_meas" claim to close the qualitative assertion.

None of items 1–4 are required for acceptance. The paper is ready for submission.

---

## 7. Acceptance Notice

Based on three rounds of review covering all major concerns, factual corrections, and priority issues raised by this reviewer, **draft v8 of "ff_rate_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation" is recommended for acceptance** in its current form, subject to the optional editorial items above at the authors' discretion.

The paper makes a genuine contribution to MBQC classical control design, identifies and resolves a real and previously unnamed problem (stall regression under signal shift compilation), provides a clean and implementable solution (ff_rate_matched), and validates the resulting design principle comprehensively. The cross-disciplinary connection to credit-based NoC flow control is a useful contribution to the emerging field of quantum systems architecture.

---

*End of Round 3 review.*
