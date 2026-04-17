# Referee Report (Round 2): "ff\_rate\_matched: Credit-Based Feedforward Width Scheduling for MBQC Classical Control under Signal Shift Compilation"

**Review date:** 2026-04-17
**Reviewer:** Anonymous Senior Researcher (Quantum Computing Architecture / Classical Computer Architecture)
**Round:** Second review of revised draft (v2)

---

## 1. Overview of Revision

The authors have made a genuine and substantive revision. Several blocking issues from Round 1 have been addressed — most notably, the incorrect formula in Section IV-B has been excised and replaced, the simulator description has been expanded, and several citation errors have been corrected. The prose is tighter and the limitations section has been meaningfully extended. These are real improvements and the authors deserve credit for taking the critique seriously.

That said, two issues from Round 1 remain unresolved at the level required for acceptance, and the revision has introduced one new concern of moderate severity. The paper is now closer to acceptance than it was, but a minor-to-moderate revision is still needed before the theoretical claim at its center can be considered sound.

---

## 2. Status of Round-1 Blocking Issues

### Blocking Issue 3.1 — Theorem 1 is informal and contains an algebraic inconsistency

**Status: Partially resolved. The inconsistency is removed; the informal argument remains and has new gaps.**

The authors correctly acknowledge and remove the formula $F \geq W \cdot L_{\mathrm{ff}} / (L_{\mathrm{ff}}+1)$, explicitly noting in a "Note on the formula from draft v1" that it was incorrect. This is a commendable and honest correction.

However, the replacement argument in Section IV-B introduces a new assumption that does the same work the old formula was supposed to do, without being independently established:

> "A structural property of the MBQC circuit family we study (QAOA, VQE) is that FF nodes constitute at most approximately half of all issued nodes."

This is the load-bearing claim — the entire $F^* = W/2$ result rests on it — yet it is stated as a bare assertion about the circuit family rather than a derived property. No proof, no citation, no measurement is offered. The authors do not show where this structural half-fraction comes from in the MBQC graph model, whether it holds for all valid MBQC programs or only for the specific QAOA/VQE instances tested, or what happens if a future algorithm has FF fraction > 0.5. As stated, this reduces Theorem 1 from a general result to "a result that holds for our test set, which happens to have FF fraction ≤ 0.5."

Furthermore, the Little's Law application in the same section is still circular. The text derives:

> "$\mathbb{E}[{\tt ff\_in\_flight}] = \lambda_{\mathrm{FF}} \cdot L_{\mathrm{ff}} / F = L_{\mathrm{ff}}$, which equals the pipeline depth."

This equality only holds by substituting $\lambda_{\mathrm{FF}} = F$, which is what you want to prove (that $F = W/2$ is a saturation-free capacity). The argument is circular: it assumes the system operates at exactly $\lambda_{\mathrm{FF}} = F$ to show that $F$ suffices.

The statement of Theorem 1 also blurs two distinct claims that should be separated:

1. The FF queue length is bounded above by $F$ (this is *true by construction* of the credit gate — it is a direct consequence of the pseudocode, not a theorem requiring proof).
2. The stall regression is zero (this is *the empirically supported claim* and the one that needs the structural half-fraction argument).

Conflating these two claims in a single "Theorem 1" gives the credit gate's mechanical property the rhetorical weight of the empirical result. The bound `ff_in_flight ≤ F` is guaranteed by the counter logic; the question is whether this bound, at $F = W/2$, prevents stall regression. The paper should state these separately.

**Required action:** Either (a) prove the structural half-fraction property from first principles for the circuit family in scope, with an explicit statement of which circuit-family assumptions are required, or (b) demote Theorem 1 to a "Design Principle supported by simulation" and present the structural half-fraction as an empirical observation measured on the test set. Option (b) is honest and consistent with what the experiments can actually support.

### Blocking Issue 3.2 — Simulator fidelity is a black box

**Status: Substantially resolved. One minor gap remains.**

Section V-A now contains a concise simulator description, states the key model assumptions explicitly, and reports two validation cases: a single-chain circuit and a fully parallel circuit. This is exactly what was requested. The description is clear and the validation cases are appropriately chosen.

The one remaining gap is the `meas_width` parameter. The revised paper states in Section II-A: "In all experiments described in this paper, issue width equals measurement width: $W = {\tt meas\_width}$." This disambiguates the question of whether `meas_width` is infinite (it is not — it equals $W$). The Round-1 concern is resolved.

The area reduction claim in Section VII-A is now properly qualified: "The area reduction claim assumes the pipeline model's assumptions hold (fixed $L_{\mathrm{ff}}$, deterministic correction triggering) — hardware designers should validate these assumptions against their specific implementation before applying the $W/2$ guideline." This is the right caveat.

**No further action required on this issue.**

### Blocking Issue 3.3 — Comparison baseline is too narrow

**Status: Partially resolved. The co-design framing is clearer; the missing four-way comparison remains.**

The paper now provides somewhat better framing of the raw-DAG vs. shifted-DAG comparison in Sections III-B and VII-B. The co-design principle is articulated clearly: "pair signal shift with ff\_rate\_matched and set $F = W/2$."

However, the four-combination comparison table requested in Round 1 — raw/shifted × ASAP/ff\_rm — is still absent. The reader cannot determine from the paper whether the shifted DAG with ff\_rate\_matched is better, worse, or the same as the raw DAG with ASAP in terms of total cycle count. This was a blocking concern in Round 1 and remains unaddressed. Section III-B gives shifted-ASAP stall rates and raw-ASAP stall rates, but cycle counts (not stall rates) are the throughput metric, and the comparison of shifted-ff\_rm against raw-ASAP is nowhere quantified.

Additionally, the concern about alternative scheduling policies (token-bucket limiters, static rate throttles) that might address stall regression without the credit gate is not addressed. The paper still positions ff\_rate\_matched as the unique natural solution without demonstrating that simpler alternatives fail.

**Required action:** Add a table or figure with the four-combination cycle-count comparison (raw-ASAP, raw-ff\_rm, shifted-ASAP, shifted-ff\_rm) for at least one representative circuit configuration. The claim that ff\_rate\_matched "completes the signal shift optimization" requires showing that shifted-ff\_rm outperforms raw-ASAP in cycle count, not merely that it matches shifted-ASAP.

### Blocking Issue 3.4 — Physical realism (probabilistic outcomes, non-Clifford scope)

**Status: Resolved.**

All three sub-issues from Round 1 are now explicitly addressed:

- The universal FF generation assumption is stated in Section II-A with the qualification: "If the fraction of correction-triggering measurements is less than one, the effective FF arrival rate is lower, and $F^* < W/2$ may be achievable."
- The non-Clifford scope limitation is stated upfront in Section II-B: "Note that signal shift applies fully to programs where all corrections are Pauli (Clifford) byproducts. Non-Clifford corrections cannot be absorbed by this technique and require separate treatment; the scope of this paper is circuits where signal shift reduces $D_{\mathrm{ff}}$ to 1–2."
- Heterogeneous FF latency and probabilistic outcomes are now listed in Section VII-C as explicit future work items.

**No further action required on this issue.**

### Blocking Issue 3.5 — Figure referencing inconsistency

**Status: Partially resolved. The placeholder issue is improved; the cross-study figure provenance problem persists.**

Figures 1, 3, 6, and 7 still contain only bracketed textual descriptions (e.g., "[Figure 1 — to be generated: ...]"). This is acceptable for a draft-stage review if the journal's submission policy permits it, but it means the pipeline architecture diagram (Figure 1) and the credit mechanism contrast (Figure 3) — the two most important illustrative figures in the paper — are entirely absent. A reviewer cannot fully evaluate the clarity of the mechanism description without seeing these figures.

More seriously, Figures 4 and 5 still reference a path under `studies/16_ff_rate_matched`, while Section V-E describes Study 20. The caption for Figure 4 states: "ff\_rate\_matched achieves $F^* = 4 = W/2$ universally across all three algorithms" — but the body of Study 20 (Section V-E) explicitly states QFT is excluded. If Figure 4 shows QFT results (the caption names QAOA, QFT, and VQE), it cannot be from Study 20. This inconsistency is unresolved and confusing: either Figure 4 is from a predecessor study (Study 16?) that included QFT and is being used to supplement Study 20's QFT gap, or the figure caption is incorrect. The paper must clarify which study generated Figures 4 and 5 and whether their data is a subset or a superset of Study 20.

**Required action:** State explicitly in the caption of Figures 4 and 5 which study they come from, what parameter ranges they cover, and how they relate to Study 20. If they are from a predecessor study, that study should be briefly described or its relationship to Studies 17–20 clarified.

---

## 3. Citation Corrections: Status

The Round-1 review flagged four citation mismatches as material errors. Status of each:

- **[DanosKashefi2007]** — The citation year mismatch (key says 2007, paper is 2006) persists in the references section: `"Physical Review A, vol. 74, no. 5, p. 052310, 2006."` The key should be corrected to [DanosKashefi2006]. Minor, but still present.
- **[O'BrienBrowne2017]** — This citation has been removed from the paper entirely. The concern is resolved.
- **[BenjaminBrowne2005]** — This citation has been removed from the paper entirely. The concern is resolved.
- **[MoravanouKent2023]** — This citation has been removed from the paper entirely. The concern is resolved.

The references section in v2 is substantially cleaner. The remaining [DanosKashefi2007] key mismatch is trivial and should be corrected.

---

## 4. Minor Issues: Status and New Items

### Carried over from Round 1

- **"F* = W/2 universally" overstated.** The paper now uses "universally across all tested configurations" in the body text (e.g., Section V-F summary box correctly qualifies: "for QAOA and VQE algorithms"). However, Figure 4's caption still says "universally across all three algorithms" (including QFT), which contradicts the summary box and the QFT exclusion in Studies 18–20. This inconsistency must be corrected.

- **Study 17 discrepant pairs.** The revised paper provides a mechanistic explanation: "These arise because ASAP and ff\_rate\_matched make different but equally valid ordering choices among ready nodes that are simultaneously eligible; the total cycle count is unchanged but the sequence of issued nodes differs." This is clearer than before and the note that deviations are "reproducible across re-runs with the same seed" is helpful. The concern is adequately addressed.

- **Table V-E convergence at F=4.** The revised text explains: "The convergence at $F=4$ is expected: when $F = W/2$, ASAP itself rarely triggers the overflow condition (since the structural half-fraction property means the instantaneous FF arrival rate is at most $W/2 \leq F$)." This explanation is reasonable and closes the Round-1 concern, though it again relies on the unestablished structural half-fraction claim.

- **Rate Monotonic Scheduling analogy.** Section IV-C now explicitly labels this analogy "intuition only" and adds: "This analogy is offered as intuition and does not constitute a formal proof, since RMS applies to periodic independent tasks while the MBQC FF pipeline operates on a DAG-constrained arrival stream." This is exactly the right treatment. Concern resolved.

- **Grammar / "stall is reactive."** The phrase "the burst damage is done" remains in Section III-C. The informal register has not been corrected. This is minor.

- **QFT coverage gap.** A QFT caveat now appears consistently in Section V-C, V-D, V-E, and the Section V-F summary box. Concern resolved.

- **Abstract vs. conclusion count mismatch.** The revised abstract says "1,080 paired comparisons at large scale." The conclusion states "360 paired comparisons in Study 17 + 1,080 in Study 20 = 1,440 total." This arithmetic is now explicit and the two numbers refer to different scopes (large-scale only vs. all studies). The distinction is clear and consistent. Concern resolved.

### New concerns introduced by the revision

**New concern A: The structural half-fraction claim is unsubstantiated and load-bearing.**
As discussed under Issue 3.1 above, this is the central new gap introduced in v2. The claim "FF nodes constitute at most approximately half of all issued nodes" appears without proof, measurement, or citation. This is not a minor issue: it is now the sole pillar on which $F^* = W/2$ rests. The vague qualifier "approximately" is especially problematic — if the fraction is 0.55 in some circuits, the $W/2$ bound could fail.

**New concern B: The Little's Law formula in Section VI-D is inconsistent with Section IV-B.**
Section VI-D restates Little's Law as: "at steady state, mean occupancy $L = \lambda \cdot W_{\mathrm{service}}$." But it uses $W_{\mathrm{service}}$ as a variable name that collides with the paper's use of $W$ for issue width. This typographic collision (Little's $W$ vs. pipeline $W$) will confuse readers. The service time parameter in Little's Law should be labeled $T_s$ or $\bar{S}$ or any symbol not already used in the paper.

**New concern C: The [IyerKim2001] citation is likely incorrect.**
The reference entry reads: "S. Iyer and N. K. Jha, 'Credit-based flow control for high-performance interconnection networks,' IEEE Transactions on Parallel and Distributed Systems, vol. 12, no. 7, pp. 743–760, 2001." TPDS vol. 12 no. 7 (2001) contains work by different authors; the title and authorship do not match well-known 2001 TPDS papers on credit-based flow control. The canonical early credit-based flow control reference for interconnection networks is typically attributed to Kermani & Kleinrock (1979) or the later NI work by Dally et al. The authors should verify this citation against the actual source.

---

## 5. Remaining Issues Before Acceptance

**Must resolve:**

1. **(High priority — Blocking)** The structural half-fraction claim in Section IV-B must either be derived from the MBQC circuit model or clearly labeled as an empirical observation measured on the test set. Until this is done, Theorem 1 is unsupported for any circuit outside the test set and the generality of $F^* = W/2$ is unjustified.

2. **(Moderate priority — Blocking for completeness)** The four-combination cycle-count comparison (raw-ASAP vs. shifted-ff\_rm vs. shifted-ASAP vs. raw-ff\_rm) must appear somewhere in the paper to substantiate the end-to-end co-design claim. A single table for one representative circuit suffices.

3. **(Moderate priority)** Figures 4 and 5 must have their study provenance explicitly stated, and the caption for Figure 4 must not claim QFT coverage if the figure is from a study (16?) that predates the QFT exclusion noted in Studies 18–20.

**Should resolve:**

4. Replace $W_{\mathrm{service}}$ in Section VI-D with a non-colliding symbol.
5. Verify and correct the [IyerKim2001] citation.
6. Correct the [DanosKashefi2007] key to [DanosKashefi2006].
7. Correct Figure 4 caption to remove "universally across all three algorithms" or qualify it appropriately.

---

## 6. Updated Recommendation

**Minor Revision** (downgraded from Major Revision)

The paper has made meaningful progress. The simulator is now described, the erroneous formula has been removed, the citation debris has been cleaned up, and the scope limitations are now stated clearly. The paper reads as a stronger, more honest contribution than v1.

The remaining blocking issue — the unsubstantiated structural half-fraction claim — is the single most important thing standing between this paper and acceptance. It is not a fundamental flaw in the approach; the experimental evidence for $F^* = W/2$ is strong and the credit-gate mechanism is correct. But the paper needs to either measure and report the FF fraction for all tested circuits (which would instantly justify the claim empirically) or restrict the scope of Theorem 1 to "circuits with FF fraction ≤ 0.5." Either fix is achievable without new experiments. Similarly, the four-combination table and the figure provenance note are both low-effort additions.

---

## 7. Updated Scores

| Dimension | Round 1 Score | Round 2 Score | Change | Notes |
|-----------|:---:|:---:|:---:|-------|
| **Novelty** | 7 | 7 | — | Unchanged; the contribution is well-scoped and genuine. |
| **Technical depth** | 5 | 6 | +1 | The erroneous formula is removed; the simulator is described. The structural half-fraction gap prevents a higher score. |
| **Clarity** | 7 | 7 | — | Writing has improved in places but Figures 1, 3, 6, 7 remain placeholders and Figure 4/5 provenance is still murky. |
| **Experimental rigor** | 7 | 7.5 | +0.5 | QFT caveat now consistently stated; four-way comparison still missing. |
| **Overall** | 6.5 | 7.0 | +0.5 | Substantial improvement. A focused minor revision addressing the structural half-fraction and figure provenance issues would bring this to acceptance. |

---

## 8. Summary for Author Response

The most important remaining issue is the structural half-fraction claim in Section IV-B, which is now the sole pillar supporting the $F^* = W/2$ result following the removal of the incorrect $L_{\mathrm{ff}}$ formula. The claim — that FF nodes constitute at most approximately half of all issued nodes in QAOA and VQE circuits — is stated as if it were a known structural property of these circuit families, but it is given without proof, measurement, or citation. As written, Theorem 1 is circular: the credit gate guarantees `ff_in_flight ≤ F` by construction (that is a mechanical fact, not a theorem), and the zero-regression claim reduces to whether the FF arrival rate is at most $F = W/2$, which holds if and only if the FF fraction is ≤ 0.5 — the unproven claim. The simplest fix is to measure the FF fraction for each circuit in the test set and report it (e.g., as a column in the study tables or as a new supplementary figure showing FF fraction vs. algorithm/scale); if every measured circuit has FF fraction ≤ 0.5, the claim becomes an empirical finding with data support rather than a bare assertion, and Theorem 1 can be honestly labeled a "result confirmed across all tested configurations." Alternatively, the authors should restrict the theorem's scope explicitly to "circuits with FF fraction ≤ 0.5" and reframe the structural half-fraction as a characterization of the circuit family rather than a general property of MBQC.

---

*End of second-round referee report.*
