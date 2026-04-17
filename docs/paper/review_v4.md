# Referee Report (Round 4): "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)
**Round:** Fourth review of revised draft (v4)

---

## 1. Overview of Revision

Draft v4 addresses the one blocking issue from Round 3 ($F^*$ definition ambiguity), generates Figures 1 and 3, and carries minor fixes forward from prior rounds. This review checks each Round-3 issue in full, evaluates the two new figures as visual artifacts, and performs a fresh read of the complete draft.

---

## 2. Status of Round-3 Issues

### Issue 1 (High priority — blocking) — $F^*$ definition ambiguity

**Status: Resolved. The fix is well-structured and logically consistent.**

Round 3 identified a specific inconsistency: the Study 20 stall table shows ff\_rate\_matched achieving 0.05% stall at $F=2$, $W=8$ — below the raw+ASAP baseline of ~3.45% — which by the paper's own criterion would imply $F^* \leq 2$, not $F^* = 4 = W/2$ as claimed. Draft v4 addresses this with a dedicated Definition II-D and a worked example that directly confronts the inconsistency.

**Definition II-D** (as printed):

> $F^*(\pi) = \min\{F : \text{stall\_rate}(\text{shifted},\, \pi,\, F) \leq \text{stall\_rate}(\text{raw},\, \text{ASAP},\, F)\}.$
> Here, the raw+ASAP baseline at the **same** FF width $F$ serves as the reference.

The accompanying worked example explains why $F^* = 4$ is reported rather than $F^* = 2$: the raw+ASAP stall at $F=2$ is simply not present in the dataset (raw DAG sweeps cover $F \geq 4$), so the criterion cannot be verified at $F=2$. The paper therefore conservatively reports $F^* \leq 4$ as the **design-safe threshold**, with a clear caveat:

> "Whether $F^* < 4$ is achievable depends on the unknown raw+ASAP baseline at $F=2$; conservatively, we report $F^* = 4 = W/2$ as the design-safe threshold."

This is logically sound. The paper does not claim $F^* = 4$ is tight — it claims $F^* \leq 4$ is verified and $F = W/2$ is a safe design target. A note at the bottom of Section V-E reinforces this reading:

> "Note that at $F=2$, the ff\_rate\_matched stall of 0.05% is well below the raw+ASAP baseline of ~3.45% [...] we conservatively report $F^* = 4 = W/2$ as the design-safe threshold."

The resolution is correct and the conservative framing is appropriate. The one residual imprecision is that the abstract still says "the minimum FF width for zero stall regression is $F^* = \lceil W/2 \rceil$" without qualifying that this is an upper bound on $F^*$ (the true minimum could be lower). This creates a mild tension with the careful hedging in Sections II-D and V-E. A single word — "at most $\lceil W/2 \rceil$" — would align the abstract with the body. This is a minor editorial issue, not a blocking one.

**Status: Resolved at scientific level. Minor editorial alignment of abstract language recommended.**

### Issue 2 (Non-blocking) — Generate Figures 1 and 3

**Status: Resolved. Both figures are generated and present in the PDF path.**

Figures 1 and 3 are evaluated in detail in Section 3 below.

### Issue 3 (Minor) — Informal register ("the damage is done")

**Status: Resolved.** Section III-C no longer contains "the damage is done." The phrase has been replaced with the more formal "the stall is purely reactive: only after `ff_in_flight` has already reached $F$ does ASAP pause — but by then, the burst has already been injected and the queue is full." This is publication-appropriate language. Issue closed.

### Issue 4 (Minor) — `ff_in_flight` distribution at $F/W = 0.125$

**Status: Partially addressed.** The draft adds a qualitative explanation in Section VII-A ("With $F=2$, the FF unit completes 2 operations per cycle, and the queue drains within $L_{\mathrm{ff}}$ cycles after each burst..."), but the empirical note on `ff_in_flight` distribution requested in Round 3 is not present. The argument remains qualitatively plausible but not quantitatively substantiated. This remains a minor gap for the final submission; it does not block acceptance.

---

## 3. Figure Evaluation

### Figure 1: MBQC Classical Control Pipeline (3-Stage Model)

**Does it communicate the pipeline model?** Yes, clearly. The three-stage left-to-right layout (Issue → Measurement → Feedforward) is immediately readable. The ready-queue input on the far left and the dual feedback arrows (dependency resolved in blue solid, credit return in blue dashed) correctly represent the two distinct paths from FF back to Issue. The stall gate (orange hexagon with an X) at the Issue Stage is visually prominent and labelled "stall if ff\_in\_flight ≥ F" — exactly the right annotation.

**What works well:**
- The $D_{\mathrm{ff}}^{\mathrm{raw}} \approx 100$–$300$ cycles annotation (gray box, top right) and $D_{\mathrm{ff}}^{\mathrm{shifted}} = 1$–$2$ cycles annotation (blue box) are both present and placed in a visually sensible location. The contrasting colors (gray vs. blue) correctly map to "raw" vs. "shifted" throughout the paper.
- The red burst arrows entering the FF queue from the Measurement Stage effectively illustrate the stall regression scenario. The label "burst (raw DAG)" is slightly confusing — the burst problem is a property of the *shifted* DAG under ASAP, not the raw DAG. See the defect note below.
- The credit return dashed arrow is labelled "credit return on FF completion (ff\_rate\_matched)" — this correctly shows that the credit path is policy-specific.

**Defects:**

1. **Label "burst (raw DAG)" is incorrect.** The red burst arrows represent the burst load that causes stall regression — but this happens on the *shifted* DAG under ASAP, not on the raw DAG. The label should read "burst (shifted DAG, ASAP)" or "burst on shifted DAG → stall regression." As written, a reader skimming the figure will incorrectly infer that the raw DAG produces bursts, which is the opposite of the paper's argument.

2. **The $D_{\mathrm{ff}}^{\mathrm{raw}}$ and $D_{\mathrm{ff}}^{\mathrm{shifted}}$ annotation boxes float in the upper right without a clear visual connection to the figure's spatial structure.** Their placement suggests they annotate the right portion of the diagram (the FF Stage), but the relevant contrast ($D_{\mathrm{ff}}$ compression due to signal shift) applies to the *entire pipeline's DAG input*, not specifically to the FF Stage. A short horizontal arrow or a bracket connecting these annotations to the figure's input DAG (or to a "signal shift" label) would clarify their meaning.

3. **The caption in the draft (Section II-A) is detailed and helpful, but the figure itself carries no figure number caption line.** The title at the top reads "Figure 1. MBQC Classical Control Pipeline (3-Stage Model)" which is fine for a standalone image, but in the paper body this is redundant with the caption. Standard journal practice omits the title from within the figure and relies on the caption below. For final submission, the figure title should be removed from the image and the caption placed below the figure per journal style.

**Publication quality assessment:** Near-publication quality. The "burst (raw DAG)" label error is the only substantive mistake; correcting it would make this figure acceptable for a top-venue submission. The annotation placement and figure title placement are minor style concerns.

### Figure 3: Credit-Based Flow Control (ff\_rate\_matched vs. ASAP)

**Does it communicate the credit mechanism?** Yes, effectively. The two-panel side-by-side layout (ff\_rate\_matched left, ASAP right) with contrasting color schemes (blue for ff\_rate\_matched, red for ASAP) immediately signals the comparison. The GATE element in the ff\_rate\_matched panel and the absence of a gate in the ASAP panel directly visualize the structural difference between the policies.

**What works well:**
- The annotated gate with "k < F only" and "consume 1 credit / return 1 credit" clearly explains the credit-token mechanics without requiring text.
- The FF processor slot visualization (numbered slots 1–4, with "F slots" label) concretely grounds the abstract concept of FF width as a finite resource.
- The OVERFLOW banner on the ASAP FF Processor is visually striking and correctly represents the overflow condition.
- Per-panel summary stats ("Stall rate ~0%" and "Stall rate ~40-49%") give the quantitative contrast immediately.

**Defects:**

1. **Text overlap in the ASAP panel.** The "BURST: W nodes/cycle arrive simultaneously" label overlaps with the "no gate" and "no credit check" labels, making all three difficult to read. The ASAP panel is visually more cluttered than the ff\_rate\_matched panel, which may mislead a reader into thinking ASAP is more complex (when in fact it is simpler). The BURST annotation should be repositioned above the panel header or alongside the arrows rather than inside the Issue Stage box.

2. **"ff\_in\_flight = k" in the ff\_rate\_matched panel is ambiguous.** The variable $k$ is introduced here without definition. The paper uses `ff_in_flight` as the counter variable throughout Section IV; the figure should use the same symbol directly (e.g., "ff\_in\_flight = k < F") or define $k$ within the figure. A reader who has not memorized the pseudocode in Section IV-A will not know what $k$ represents.

3. **The credit return arrow is only labeled "credit return (on completion)" but does not visually distinguish the completion path from the node issue path.** Both are arrows into/out of the FF Processor, and their directionality (to/from Issue Stage) is not as clear as in Figure 1. Adding an arrowhead label or color distinction (e.g., green for credit return vs. blue for node issue) would help.

4. **The figure title is embedded in the image** ("Figure 3. Credit-based flow control..."), same issue as Figure 1. For journal submission, this should be removed from the image and placed as the caption below.

**Publication quality assessment:** Near-publication quality. The text overlap in the ASAP panel and the undefined $k$ variable are the two corrections needed before journal submission. The overall contrast between the panels is clear and the mechanism is visually conveyed.

---

## 4. Fresh Read: Remaining Weaknesses

Reading draft v4 as if encountering it for the first time, the following residual weaknesses emerge:

### 4.1 Abstract overclaims $F^*$ precision

The abstract states "the minimum FF width for zero stall regression is $F^* = \lceil W/2 \rceil$." But as Section II-D establishes, this is a conservative upper bound (the true $F^*$ may be lower). The abstract should say "at most $\lceil W/2 \rceil$" or "a design-safe threshold of $F = \lceil W/2 \rceil$." The current wording will trigger a referee objection on first read.

### 4.2 Section III-B: cross-study comparison of stall rates uses mismatched $F$ values

In Section III-B, the reported stall rates are:
- "ASAP stall rate (shifted DAG, $F=2$): 39.8% (QAOA), 49.0% (VQE)"
- "Raw DAG stall rate (same $F=4$, from Study 18): 3.5% (QAOA), 0.5% (VQE)"

The parenthetical "same $F=4$" for the raw baseline, when the shifted figure is at $F=2$, will immediately confuse a reader. These are *not* at the same $F$. The comparison is valid (it illustrates stall regression magnitude) but the text implies a direct apples-to-apples comparison that does not exist. The parenthetical should be changed to clarify: "(raw+ASAP baseline at $F=4$, from Study 18; note $F$ differs)."

### 4.3 The $F/W = 0.125$ result is presented as supporting $F^* = W/2$, but it actually suggests $F^*$ could be much lower

Section IV-B's "Intuition for the $F/W = 0.125$ case" explains that cycles\_ratio = 1.000 at $F=2$, $W=16$ because the FF pipeline drains between bursts. This is presented as corroboration of the $F^* = W/2$ result. But a careful reader will notice: if $F/W = 0.125$ achieves zero throughput cost *and* (presumably) low stall rate, then $F^*$ might be $W/8$, not $W/2$. The text acknowledges this tension ("$F^*$ might be as low as $W/8$ for some circuits") but does not resolve it cleanly. The reason for singling out $F^* = W/2$ as the "design-safe threshold" — rather than $F^* = W/8$ (which would be an even better result) — is that the stall regression criterion requires comparison against raw+ASAP at the *same* $F$, and the raw+ASAP baseline is only available at $F \geq 4$. This logic is buried in the $F^*$ definition worked example in Section II-D, not in Section IV-B where the $F/W = 0.125$ case is discussed. A forward pointer ("see Section II-D for why $F^* = W/2$ is identified as the threshold rather than $W/8$") would help.

### 4.4 Figures 6 and 7 remain as text placeholders

The bracket-format placeholder descriptions for Figures 6 and 7 are detailed and imaginable, but they render as literal paragraph-length text blocks in the paper, interrupting the flow of Section V-E. For a workshop-quality draft this is acceptable; for journal submission these figures must be generated. The bracketed descriptions are good specifications — they should be converted to actual figures before submission.

### 4.5 The Little's Law application in Section VI-D is slightly imprecise

Section VI-D states: "at steady state, mean queue length $L = \lambda \cdot \mu$." But Little's Law is $L = \lambda \cdot W_{\mathrm{wait}}$, where $W_{\mathrm{wait}}$ is mean waiting time in system (not service time). For an M/D/1 or D/D/1 queue, mean time in system = $L_{\mathrm{ff}}$ only when utilization is 1.0 — at lower utilization, mean time in system is less than $L_{\mathrm{ff}}$. The derivation as written implicitly assumes the queue is always fully utilized ($\lambda = F/L_{\mathrm{ff}}$), which is the steady-state assumption being invoked. The text should either (a) explicitly state the full-utilization assumption, or (b) replace "mean queue length $L = \lambda \cdot \mu$" with the correct Little's Law statement $L = \lambda \cdot W_{\mathrm{sojourn}}$ and note that at full utilization, $W_{\mathrm{sojourn}} = L_{\mathrm{ff}}$. This is a technical precision issue, not a flaw in the argument, but a referee with queueing theory background will flag it.

### 4.6 The co-design conclusion is buried

The key practical conclusion — that signal shift + ff\_rate\_matched achieves strictly better performance than raw + ASAP at half the FF hardware — is stated clearly in the four-way table of Section V-C and the co-design principle box of Section VII-B, but it is not prominently featured in the abstract or introduction. The abstract focuses on stall regression elimination and hardware reduction (50%), which is correct, but does not state the end-to-end result: shifted + ff\_rate\_matched strictly dominates raw + ASAP in both stall rate and total cycle count. One sentence in the abstract making this co-design dominance explicit would strengthen the paper's headline contribution.

### 4.7 QFT omission in Studies 18–20 is handled consistently but not fully explained

The paper correctly notes the QFT omission in Studies 18–20 due to "a DAG generation artifact at $H=8$, $Q=64$ shifted" (Sections V-C, V-D, V-E, V-F). However, the nature of this artifact is never described. A reader may wonder: is this a bug in the simulator? A property of QFT's structure that prevents shifted-DAG generation? Is it reproducible? A single sentence describing the artifact (e.g., "signal shift applied to the QFT DAG at this parameter produces a cycle in the dependency graph, indicating a correctness issue in the shift compilation that we defer to future work") would satisfy this curiosity and preempt a referee question.

---

## 5. Scores

| Dimension | Round 1 | Round 2 | Round 3 | **Round 4** | Change (R3→R4) | Notes |
|---|:---:|:---:|:---:|:---:|:---:|---|
| **Novelty** | 7 | 7 | 7.5 | **7.5** | 0 | No new experimental results in v4. The co-design claim is now end-to-end anchored by the four-way table. The FF fraction finding (introduced in v3) remains the primary empirical novelty beyond the mechanism contribution. |
| **Technical depth / correctness** | 5 | 6 | 7.5 | **8.0** | +0.5 | The $F^*$ definition ambiguity is resolved. The Design Principle hedging is appropriate. The Little's Law imprecision (§4.5 above) and the Section III-B mismatched-$F$ annotation are the remaining technical precision issues. Both are editorial-level. |
| **Clarity** | 7 | 7 | 7.5 | **8.0** | +0.5 | Figures 1 and 3 are generated and substantially improve the paper's readability for a reader new to credit-based flow control. The figure defects (mislabeled burst, undefined $k$, text overlap) are real but fixable. Figures 6 and 7 remain as placeholders, which is the main remaining drag on this score. |
| **Experimental rigor** | 7 | 7.5 | 8.0 | **8.0** | 0 | No new experimental work in v4. The four-axis validation with 4,120 runs, QFT caveats, and FF fraction measurement remain the empirical backbone. The missing `ff_in_flight` distribution at $F/W = 0.125$ continues to leave the burst inter-arrival argument qualitative. |
| **Overall** | 6.5 | 7.0 | 7.5 | **8.0** | +0.5 | Meaningful progress from v3. The $F^*$ resolution and the two figures bring this solidly into the accept-with-minor-revision band. |

---

## 6. Gap to 8.5

The overall score is **8.0 / 10**. To reach 8.5, the following changes are required, in priority order:

### Priority 1 — Fix the "burst (raw DAG)" label in Figure 1 (critical figure error)

This label is factually wrong. The burst arrows represent the stall regression scenario, which occurs on the *shifted* DAG under ASAP. Mislabeling it "raw DAG" directly contradicts the paper's central argument. A reader who reads only the figure and its caption will come away with the opposite understanding. Fix: change to "burst (shifted DAG, ASAP)" or "burst on shifted DAG → FF overflow." **Estimated effort: 5 minutes.**

### Priority 2 — Align abstract wording with the $F^*$ definition (precision)

The abstract says "the minimum FF width for zero stall regression is $F^* = \lceil W/2 \rceil$." The body correctly says this is a conservative upper bound. Replace with: "a design-safe FF width threshold of $F = \lceil W/2 \rceil$ is sufficient to eliminate stall regression." This matches the language of Section II-D and prevents a first-read objection. **Estimated effort: 10 minutes.**

### Priority 3 — Fix the undefined $k$ in Figure 3 and the text overlap in the ASAP panel

Two figure-quality issues in Fig. 3: (a) `ff_in_flight = k` uses undefined $k$; change to `ff_in_flight < F` or define $k$ in the figure legend. (b) The BURST label overlaps with "no gate / no credit check" in the ASAP panel; reposition the BURST text above the panel. **Estimated effort: 20 minutes.**

### Priority 4 — Fix the mismatched-$F$ cross-study comparison in Section III-B

The sentence "Raw DAG stall rate (same $F=4$, from Study 18): 3.5%" uses "same $F=4$" when the shifted figure is at $F=2$. Change to "(raw+ASAP at $F=4$, from Study 18; note different $F$)". **Estimated effort: 5 minutes.**

### Priority 5 — Correct the Little's Law statement in Section VI-D (technical precision)

Add the full-utilization assumption explicitly, or replace $L = \lambda \cdot \mu$ with the correct $L = \lambda \cdot W_{\mathrm{sojourn}}$ and note that at full utilization $W_{\mathrm{sojourn}} = L_{\mathrm{ff}}$. **Estimated effort: 15 minutes.**

### Priority 6 — Add one sentence on the QFT DAG generation artifact (completeness)

Describe what the artifact is (even if only "signal shift generates a cyclic dependency at this scale; root cause deferred to future work"). **Estimated effort: 5 minutes.**

Completing Priorities 1–4 is sufficient to bring the paper to the 8.5 threshold. Priorities 5–6 are polishing steps that lift the overall to ~8.5–9.0.

**Note:** Figures 6 and 7 (sensitivity heatmap and large-scale stall rate plot) remain as text placeholders. These must be generated for final journal submission but are not blocking for workshop-level acceptance. Generating them would push the Clarity score to 8.5–9.0 and the overall to ~8.5.

---

## 7. Recommendation

**Accept with Minor Revision**

The paper has progressed steadily across four rounds:

| Round | Recommendation | Overall score |
|:---:|---|:---:|
| 1 | Major revision | 6.5 |
| 2 | Major revision | 7.0 |
| 3 | Accept with minor revision | 7.5 |
| **4** | **Accept with minor revision** | **8.0** |

The $F^*$ definition ambiguity — the sole blocking issue from Round 3 — is resolved. Figures 1 and 3 are present and largely effective. The paper's scientific contribution (credit-based FF scheduling eliminates stall regression at $F = W/2$, validated across four axes, zero throughput cost) is correctly established, honestly hedged, and well-supported by 4,120 simulation runs.

The remaining issues (figure label error, abstract precision, Little's Law statement, $k$ definition, text overlap) are all editorial. None require new experiments. A single targeted revision pass addressing Priorities 1–4 above will bring the paper to publication-ready quality.

The paper should be accepted following a focused minor revision. No new experimental work is needed.

---

## 8. Summary for Author Response

**On Figures 1 and 3:** Both are generated and functional. One critical error: the label "burst (raw DAG)" in Figure 1 must be corrected to "burst (shifted DAG, ASAP)" — this label directly contradicts the paper's central argument. In Figure 3, define $k$ or replace it with `ff_in_flight < F`, and reposition the overlapping BURST text in the ASAP panel.

**On the $F^*$ definition:** The resolution in Section II-D is correct and logically consistent. Align the abstract language to match — replace "the minimum FF width is $F^* = \lceil W/2 \rceil$" with "a design-safe threshold of $F = \lceil W/2 \rceil$ suffices to eliminate stall regression."

**On the Little's Law statement:** Either add the full-utilization assumption explicitly, or state the law correctly as $L = \lambda \cdot W_{\mathrm{sojourn}}$ with a note that $W_{\mathrm{sojourn}} = L_{\mathrm{ff}}$ at full utilization. A referee with queueing background will flag $L = \lambda \cdot \mu$ as imprecise.

**On the `ff_in_flight` distribution at $F/W = 0.125$:** Still not empirically grounded. Even a one-line inline note ("at $F=2$, $W=16$, we observed that `ff_in_flight` reaches 2 in fewer than 0.3% of cycles, confirming that the credit gate is rarely triggered") would close this gap. This is non-blocking but strengthens the paper.

**On Figures 6 and 7:** Generate them for final submission. The bracketed placeholder text is a clear specification; the figures themselves are straightforward to produce from the existing simulation data.

---

*End of fourth-round referee report.*
