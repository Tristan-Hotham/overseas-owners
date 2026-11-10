"""Step 8: header.png (1200 x 630 social card): title, two key numbers and the LSOA map of England and Wales."""
import pandas as pd
import matplotlib.pyplot as plt
from figstyle import *

R = jload(f"{DATA}/results.json")
L = pd.read_csv(f"{DATA}/lsoa_counts.csv").set_index("lsoa")
S = lsoa_shapes(40)
fig = plt.figure(figsize=(12, 6.3), dpi=100, facecolor=PAPER)
ax = fig.add_axes([0.56, 0.02, 0.43, 0.96])
context_land(ax, (140000, 660000, 8000, 660000))
draw_polys(ax, S.geometry, rate_col(L.reindex(S.index).rate.values), zorder=2)
fig.text(0.045, 0.86, "Who owns", fontproperties=DISP, fontsize=46, color=FG, va="top")
fig.text(0.045, 0.73, "your street?", fontproperties=DISP, fontsize=46, color=HOT, va="top")
fig.text(0.045, 0.58, "Property in England and Wales held by overseas companies", fontproperties=SERP, fontsize=15, color=FG, va="top")
fig.text(0.045, 0.47, f"{R['n_titles']:,}", fontproperties=DISP, fontsize=34, color=HOT, va="top")
fig.text(0.045, 0.365, "titles held by companies incorporated abroad", fontproperties=SERP, fontsize=12.5, color=MUT, va="top")
fig.text(0.045, 0.30, f"{R['pc_uko']:.0f}%", fontproperties=DISP, fontsize=34, color=HOT, va="top")
fig.text(0.045, 0.195, "from Jersey, Guernsey, the Isle of Man, the BVI\nand other UK islands and territories", fontproperties=SERP, fontsize=12.5, color=MUT, va="top", linespacing=1.3)
fig.text(0.045, 0.025, "maps.tristanhotham.com/overseas-owners\n" + HMLR + ", data November 2026", fontsize=8, color=MUT, linespacing=1.4)
fig.savefig(f"{ROOT}/header.png", dpi=100, facecolor=PAPER)
from PIL import Image
assert Image.open(f"{ROOT}/header.png").size == (1200, 630)
print("header ok")
