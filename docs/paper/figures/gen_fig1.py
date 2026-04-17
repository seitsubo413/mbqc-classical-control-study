"""Generate Figure 1: MBQC 3-stage pipeline architecture diagram."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import numpy as np

fig, ax = plt.subplots(figsize=(8, 4))
ax.set_xlim(0, 10)
ax.set_ylim(0, 4)
ax.axis('off')

ACCENT = '#2166ac'   # blue accent
GRAY   = '#4d4d4d'
LIGHT  = '#d1e5f0'
BURST  = '#d73027'   # red for burst/overflow

# ── Stage boxes ──────────────────────────────────────────────────────────────
def draw_box(ax, x, y, w, h, label, sublabel, color=LIGHT, textcolor='black'):
    box = FancyBboxPatch((x, y), w, h,
                         boxstyle="round,pad=0.05",
                         facecolor=color, edgecolor=GRAY, linewidth=1.2)
    ax.add_patch(box)
    ax.text(x + w/2, y + h*0.62, label,
            ha='center', va='center', fontsize=9.5, fontweight='bold', color=textcolor)
    ax.text(x + w/2, y + h*0.3, sublabel,
            ha='center', va='center', fontsize=7.5, color=GRAY, style='italic')

# Stage positions
s1_x, s2_x, s3_x = 1.6, 4.2, 6.8
s_y, s_w, s_h = 1.3, 2.1, 1.4

draw_box(ax, s1_x, s_y, s_w, s_h, 'Issue Stage', 'width  W')
draw_box(ax, s2_x, s_y, s_w, s_h, 'Measurement\nStage', 'latency  $L_{\\mathrm{meas}}$')
draw_box(ax, s3_x, s_y, s_w, s_h, 'Feedforward\n(FF) Stage', 'width  $F$, latency  $L_{\\mathrm{ff}}$')

# ── Ready queue ───────────────────────────────────────────────────────────────
ax.text(0.55, s_y + s_h/2, 'Ready\nqueue', ha='center', va='center',
        fontsize=7.5, color=GRAY,
        bbox=dict(boxstyle='round,pad=0.25', facecolor='#f7f7f7', edgecolor=GRAY, linewidth=0.8))
ax.annotate('', xy=(s1_x, s_y + s_h/2), xytext=(0.9, s_y + s_h/2),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.3))

# ── Forward arrows between stages ────────────────────────────────────────────
for x_from, x_to in [(s1_x + s_w, s2_x), (s2_x + s_w, s3_x)]:
    ax.annotate('', xy=(x_to, s_y + s_h/2), xytext=(x_from, s_y + s_h/2),
                arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.5))

# ── FF queue label between Measurement and FF ────────────────────────────────
mid_x = (s2_x + s_w + s3_x) / 2
ax.text(mid_x, s_y + s_h/2 + 0.35, 'FF\nqueue', ha='center', va='bottom',
        fontsize=6.8, color=BURST, fontstyle='italic')

# ── Burst arrows: cluster of 4 thin arrows into FF queue ─────────────────────
burst_ys = [s_y + s_h * f for f in [0.25, 0.42, 0.58, 0.75]]
for by in burst_ys:
    ax.annotate('', xy=(s3_x, by), xytext=(s2_x + s_w + 0.05, by),
                arrowprops=dict(arrowstyle='->', color=BURST, lw=0.8, alpha=0.75))
ax.text(mid_x - 0.05, s_y - 0.22, 'burst (shifted DAG, ASAP)', ha='center', va='top',
        fontsize=6.5, color=BURST)

# ── Feedback arrow: FF stage → Issue stage (dependency resolved) ──────────────
ax.annotate('', xy=(s1_x + s_w/2, s_y), xytext=(s3_x + s_w/2, s_y),
            arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.3,
                            connectionstyle='arc3,rad=-0.35'))
ax.text(5.0, s_y - 0.55, 'dependency resolved → node unblocked',
        ha='center', va='top', fontsize=7, color=ACCENT)

# ── Credit return arrow (ff_rate_matched) ────────────────────────────────────
ax.annotate('', xy=(s1_x + s_w/2, s_y + s_h + 0.05),
            xytext=(s3_x + s_w/2, s_y + s_h + 0.05),
            arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.1, linestyle='dashed',
                            connectionstyle='arc3,rad=0.3'))
ax.text(5.0, s_y + s_h + 0.72, 'credit return on FF completion (ff_rate_matched)',
        ha='center', va='bottom', fontsize=7, color=ACCENT, style='italic')

# ── Stall gate symbol ────────────────────────────────────────────────────────
gate_x = s1_x - 0.02
gate_y = s_y + s_h/2 - 0.18
ax.add_patch(mpatches.RegularPolygon((gate_x + 0.18, gate_y + 0.18),
                                      numVertices=6, radius=0.2,
                                      facecolor='#fee090', edgecolor=BURST, linewidth=1.0))
ax.text(gate_x + 0.18, gate_y + 0.18, '⊗', ha='center', va='center',
        fontsize=8, color=BURST)
ax.text(gate_x + 0.18, gate_y - 0.17,
        'stall if\nff_in_flight ≥ F',
        ha='center', va='top', fontsize=6, color=BURST)

# ── D_ff annotations ─────────────────────────────────────────────────────────
ax.text(mid_x, s_y + s_h + 1.05,
        '$D_{\\mathrm{ff}}^{\\mathrm{raw}} \\approx 28$–$226$ cycles (QAOA), $15$–$99$ (VQE)',
        ha='center', va='bottom', fontsize=7.5, color=GRAY,
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#f7f7f7',
                  edgecolor='#bbbbbb', linewidth=0.7))
ax.text(mid_x, s_y + s_h + 0.55,
        '$D_{\\mathrm{ff}}^{\\mathrm{shifted}} = 1$–$2$ cycles',
        ha='center', va='bottom', fontsize=7.5, color=ACCENT,
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#d1e5f0',
                  edgecolor=ACCENT, linewidth=0.7))

# ── Title ─────────────────────────────────────────────────────────────────────
ax.set_title('Figure 1. MBQC Classical Control Pipeline (3-Stage Model)',
             fontsize=9.5, pad=4, color=GRAY)

plt.tight_layout(pad=0.3)
plt.savefig('/Users/seitsubo/Project/mbqc-classical-control-study/docs/paper/figures/fig1_pipeline.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Saved fig1_pipeline.png")
