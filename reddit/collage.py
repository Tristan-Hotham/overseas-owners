"""Reddit collage (r/dataisbeautiful style), light background, 2700 x 2025 px: the LSOA map of overseas-company titles per
1,000 dwellings with a London inset, the jurisdictions, the top districts and the within-district result. Aggregates only.
Run after code/04_figures.py:  python3 reddit/collage.py"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "code"))
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json"); x = R["x"]
L = pd.read_csv(f"{DATA}/lsoa_counts.csv").set_index("lsoa")
LD = pd.read_csv(f"{DATA}/lad_counts.csv"); J = pd.read_csv(f"{DATA}/jurisdictions.csv")
S = lsoa_shapes(40)
HALO = [pe.withStroke(linewidth=4, foreground=PAPER)]
fig = plt.figure(figsize=(13.5, 10.125), dpi=200, facecolor=PAPER)
fig.text(0.03, 0.965, "Who owns your street?", fontproperties=DISP, fontsize=34, color=FG, va="top")
fig.text(0.03, 0.905, f"{R['n_titles']:,} property titles in England and Wales are held by companies incorporated abroad. "
         f"{R['pc_uko']:.0f}% of them by companies\nfrom the UK's Crown Dependencies and Overseas Territories. Shaded: titles per 1,000 homes in every small area (LSOA).",
         fontproperties=SERP, fontsize=13, color=MUT, va="top", linespacing=1.35)
# map
ax = fig.add_axes([0.0, 0.08, 0.40, 0.74])
context_land(ax, (120000, 660000, 8000, 660000))
cols = rate_col(L.reindex(S.index).rate.values)
draw_polys(ax, S.geometry, cols, zorder=2)
ext = (515000, 545000, 168000, 192000)
ax.add_patch(plt.Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fill=False, ec=FG, lw=1, zorder=5))
ax.text(590000, 420000, "North\nSea", fontproperties=SERI, fontsize=12, color="#7C8A93", ha="center")
ax.text(400000, 35000, "English Channel", fontproperties=SERI, fontsize=12, color="#7C8A93", ha="center")
# London inset
ax2 = fig.add_axes([0.42, 0.50, 0.22, 0.27]); ax2.set_facecolor(PAPER)
sel = S.cx[ext[0]:ext[1], ext[2]:ext[3]]
draw_polys(ax2, sel.geometry, rate_col(L.reindex(sel.index).rate.values), zorder=2)
ax2.set_xlim(ext[0], ext[1]); ax2.set_ylim(ext[2], ext[3]); ax2.set_aspect("equal"); ax2.set_xticks([]); ax2.set_yticks([])
for s_ in ax2.spines.values():
    s_.set_color(FG); s_.set_linewidth(1)
ax2.set_title("Central London", fontproperties=DISPB, fontsize=13, color=FG, loc="left", pad=4)
# legend under the inset, on paper
handles = [Patch(fc=c, ec="#9C8F78", lw=0.4, label=l) for c, l in zip(RATE_C, RATE_L)]
fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.415, 0.475), ncol=2, frameon=False, fontsize=10,
           title="Titles per 1,000 homes", title_fontproperties=SERP, columnspacing=1.0)
fig.text(0.42, 0.33, f"England and Wales: {R['ew_rate']:.1f} per 1,000\nWestminster: {x['westminster_rate']:.0f} per 1,000\n"
         f"Half of mapped titles are in {R['half_titles_lsoas_pc']:.1f}%\nof small areas", fontproperties=SERP, fontsize=11.5, color=FG, va="top", linespacing=1.3)
# jurisdictions
a3 = fig.add_axes([0.80, 0.52, 0.17, 0.25]); a3.set_facecolor(PAPER)
j = J[J.jurisdiction != "Not stated"].head(8).iloc[::-1]
a3.barh(j.jurisdiction, j.share, color=[UKO_C if isinstance(u, str) and u else "#8C8577" for u in j.uk_link], height=0.72)
for i, v in enumerate(j.share):
    a3.text(v + 0.5, i, f"{v:.1f}%", va="center", fontsize=10, color=FG)
a3.set_xlim(0, j.share.max() * 1.3); a3.set_xticks([]); a3.tick_params(axis="y", labelsize=10.5, length=0)
for s in ("top", "right", "bottom"):
    a3.spines[s].set_visible(False)
a3.set_title("Where the companies\nare incorporated", fontproperties=DISPB, fontsize=14, color=FG, loc="left")
a3.legend(handles=[Patch(fc=UKO_C, label="Crown Dependency or\nOverseas Territory"), Patch(fc="#8C8577", label="Elsewhere")],
          loc="upper left", bbox_to_anchor=(-0.75, -0.03), ncol=2, frameon=False, fontsize=9.5)
# districts
a4 = fig.add_axes([0.80, 0.16, 0.17, 0.25]); a4.set_facecolor(PAPER)
d = LD.head(8).iloc[::-1]
a4.barh(d.lad_name.str.replace("Kensington and Chelsea", "Kensington & Chelsea"), d.rate,
        color=UKO_C, height=0.72)
for i, v in enumerate(d.rate):
    a4.text(v + 2, i, f"{v:.0f}", va="center", fontsize=10, color=FG)
a4.set_xlim(0, d.rate.max() * 1.18); a4.set_xticks([]); a4.tick_params(axis="y", labelsize=10.5, length=0)
for s in ("top", "right", "bottom"):
    a4.spines[s].set_visible(False)
a4.set_title("Top districts per 1,000 homes", fontproperties=DISPB, fontsize=14, color=FG, loc="left")
# finding
fig.text(0.42, 0.205, "Within the same district, more titles where:", fontproperties=DISPB, fontsize=13, color=FG, va="top")
fig.text(0.42, 0.17, f"+10 points of homes in top Council Tax bands: {x['sh_high_pc']:+.0f}%\n"
         f"+10 points of flats: {x['sh_flat_pc']:+.0f}%\n+10 points of homes built since 2009: {x['sh_new_pc']:+.0f}%",
         fontproperties=SERP, fontsize=11.5, color=FG, va="top", linespacing=1.3)
fig.text(0.03, 0.015, f"Source: {HMLR}, overseas companies data, November 2026 (non-commercial licence; aggregates only). "
         "\nHomes: VOA 2025 (OGL). Boundaries: ONS (OGL). Dr Tristan Hotham, Independent researcher · maps.tristanhotham.com/overseas-owners · "
         "Owning UK property through an overseas company is legal.", fontsize=8, color=MUT, linespacing=1.5)
out = os.path.join(HERE, "overseas_owners_collage.png")
fig.savefig(out, dpi=200, facecolor=PAPER)
print(out)
