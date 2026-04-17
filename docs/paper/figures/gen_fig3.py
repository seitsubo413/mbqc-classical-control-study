"""Generate Figure 3: ff_rate_matched credit mechanism vs ASAP contrast."""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np

ACCENT = '#2166ac'
GRAY   = '#4d4d4d'
LIGHT  = '#d1e5f0'
RED    = '#d73027'
RED_LT = '#fddbc7'

fig, axes = plt.subplots(1, 2, figsize=(8, 4))

# ─────────────────────────────────────────────────────────────────
#  Helper: draw a box
# ─────────────────────────────────────────────────────────────────
def box(ax, x, y, w, h, label, sub='', fc=LIGHT, ec=GRAY, lw=1.2,
        fs=9, fss=7.5, fc_text='black', sub_color=GRAY):
    p = FancyBboxPatch((x, y), w, h, boxstyle='round,pad=0.04',
                       facecolor=fc, edgecolor=ec, linewidth=lw)
    ax.add_patch(p)
    ax.text(x+w/2, y+h*(0.62 if sub else 0.5), label,
            ha='center', va='center', fontsize=fs, fontweight='bold', color=fc_text)
    if sub:
        ax.text(x+w/2, y+h*0.3, sub, ha='center', va='center',
                fontsize=fss, color=sub_color, style='italic')

# ─────────────────────────────────────────────────────────────────
#  LEFT PANEL: ff_rate_matched (with credit gate)
# ─────────────────────────────────────────────────────────────────
ax = axes[0]
ax.set_xlim(0, 6)
ax.set_ylim(0, 5)
ax.axis('off')
ax.set_title('ff_rate_matched\n(credit gate ACTIVE)', fontsize=9.5,
             color=ACCENT, pad=3, fontweight='bold')

# Issue stage box
box(ax, 0.3, 2.4, 1.9, 1.6, 'Issue Stage', 'ff_in_flight',
    fc=LIGHT, ec=ACCENT, lw=1.5)

# Counter highlight
ax.text(0.3+1.9/2, 2.4+1.6*0.3, 'ff_in_flight',
        ha='center', va='center', fontsize=7.5,
        color=ACCENT, style='italic')

# Gate symbol
ax.add_patch(mpatches.RegularPolygon((2.45, 3.2), numVertices=6, radius=0.22,
                                      facecolor='#fee090', edgecolor=ACCENT, linewidth=1.2))
ax.text(2.45, 3.2, '⊙', ha='center', va='center', fontsize=9, color=ACCENT)
ax.text(2.45, 2.85, 'GATE: issue only if\nff_in_flight < F', ha='center', va='top',
        fontsize=6.5, color=ACCENT, fontweight='bold')

# FF Processor box
box(ax, 3.5, 2.4, 1.9, 1.6, 'FF\nProcessor',
    sub=f'F slots', fc='#f7f7f7', ec=GRAY)

# FF slots (F=4 shown as cells)
slot_colors = ['#c7e9b4', '#c7e9b4', '#ffffcc', '#ffffcc']
for i, sc in enumerate(slot_colors):
    ax.add_patch(FancyBboxPatch((3.58 + i*0.43, 2.52), 0.37, 0.52,
                                boxstyle='square,pad=0.0',
                                facecolor=sc, edgecolor=GRAY, linewidth=0.6))
    ax.text(3.76 + i*0.43, 2.78, str(i+1), ha='center', va='center',
            fontsize=6.5, color=GRAY)
ax.text(4.45, 2.45, 'F = 4 slots', ha='center', va='top', fontsize=6.5, color=GRAY)

# Forward arrow (issue → FF), labeled
ax.annotate('', xy=(3.48, 3.38), xytext=(2.68, 3.38),
            arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.4))
ax.text(3.08, 3.55, 'issue node\n(consume 1 credit)', ha='center', va='bottom',
        fontsize=6.5, color=ACCENT)

# Backward arrow (credit return)
ax.annotate('', xy=(2.22, 2.95), xytext=(3.50, 2.95),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=1.2,
                            connectionstyle='arc3,rad=0.3'))
ax.text(2.86, 2.45, 'credit return\n(on completion)', ha='center', va='top',
        fontsize=6.5, color=GRAY)

# Stall indicator (grayed out = no overflow)
ax.text(0.3+1.9/2, 4.2, 'Queue bounded at F', ha='center', va='bottom',
        fontsize=7, color='green', fontweight='bold')
ax.text(0.3+1.9/2, 3.98, 'Stall rate ~ 0%', ha='center', va='bottom',
        fontsize=7, color='green')

# Ready queue
ax.text(0.3+1.9/2, 4.55, '...ready queue...', ha='center', va='bottom',
        fontsize=6.5, color=GRAY, style='italic')
ax.annotate('', xy=(0.3+1.9/2, 4.05), xytext=(0.3+1.9/2, 4.38),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=0.9))

# ─────────────────────────────────────────────────────────────────
#  RIGHT PANEL: ASAP (no gate, overflow)
# ─────────────────────────────────────────────────────────────────
ax = axes[1]
ax.set_xlim(0, 6)
ax.set_ylim(0, 5)
ax.axis('off')
ax.set_title('ASAP\n(no gate — reactive stall)', fontsize=9.5,
             color=RED, pad=3, fontweight='bold')

# Issue stage box
box(ax, 0.3, 2.4, 1.9, 1.6, 'Issue Stage', 'no credit check',
    fc=RED_LT, ec=RED, lw=1.5)

# No gate — just open pass-through
ax.text(2.45, 3.25, '(no gate)', ha='center', va='center',
        fontsize=7.5, color=RED, style='italic', alpha=0.7)

# FF Processor box (overflow)
box(ax, 3.5, 2.4, 1.9, 1.6, 'FF\nProcessor',
    sub='F slots', fc='#fddbc7', ec=RED, lw=1.5)

# Overflow indicator — extra arrows stacking up
overflow_ys = [2.58, 2.72, 2.86, 3.00, 3.14, 3.28]
for i, oy in enumerate(overflow_ys):
    color = RED if i >= 4 else GRAY
    ax.annotate('', xy=(3.48, oy), xytext=(2.22, oy),
                arrowprops=dict(arrowstyle='->', color=color, lw=0.9, alpha=0.9))

# BURST label moved above the arrow cluster to avoid overlap; red arrow points down to overflowing queue
ax.text(2.85, 4.7, 'BURST: W nodes/cycle arrive\nsimultaneously → OVERFLOW',
        ha='center', va='top', fontsize=7, color=RED, fontweight='bold',
        bbox=dict(boxstyle='round,pad=0.2', facecolor='#fff0f0', edgecolor=RED, linewidth=0.8))
ax.annotate('', xy=(2.85, 3.42), xytext=(2.85, 4.42),
            arrowprops=dict(arrowstyle='->', color=RED, lw=1.5))

# Overflow label
ax.add_patch(FancyBboxPatch((3.52, 3.45), 1.86, 0.42,
                            boxstyle='round,pad=0.04',
                            facecolor=RED, edgecolor='darkred', linewidth=1.0, alpha=0.85))
ax.text(4.45, 3.66, 'OVERFLOW', ha='center', va='center',
        fontsize=9, color='white', fontweight='bold')

# Stall indicator (bad)
ax.text(0.3+1.9/2, 4.2, 'Queue overflows', ha='center', va='bottom',
        fontsize=7, color=RED, fontweight='bold')
ax.text(0.3+1.9/2, 3.98, 'Stall rate ~ 40–49%', ha='center', va='bottom',
        fontsize=7, color=RED)

# Ready queue
ax.text(0.3+1.9/2, 4.55, '...ready queue...', ha='center', va='bottom',
        fontsize=6.5, color=GRAY, style='italic')
ax.annotate('', xy=(0.3+1.9/2, 4.05), xytext=(0.3+1.9/2, 4.38),
            arrowprops=dict(arrowstyle='->', color=GRAY, lw=0.9))

# ─────────────────────────────────────────────────────────────────
#  Bottom footnote
# ─────────────────────────────────────────────────────────────────
fig.text(0.5, 0.02,
         'Figure 3.  Credit-based flow control (ff_rate_matched, left) vs. greedy ASAP (right).\n'
         'ff_rate_matched bounds queue occupancy at F by construction; ASAP overflows and stalls reactively.',
         ha='center', va='bottom', fontsize=7.5, color=GRAY)

plt.tight_layout(rect=[0, 0.07, 1, 1], pad=0.6)
plt.savefig('/Users/seitsubo/Project/mbqc-classical-control-study/docs/paper/figures/fig3_credit_mechanism.png',
            dpi=150, bbox_inches='tight', facecolor='white')
print("Saved fig3_credit_mechanism.png")
