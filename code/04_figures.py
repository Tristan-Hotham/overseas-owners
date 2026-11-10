"""Step 4: figures for the paper (release/paper/f_*.pdf), the blog (release/blog/b_*.png, 1800 px wide) and the page (img/*.jpg).
All from aggregate tables in data/ and data/results.json. Every figure carries the HM Land Registry attribution."""
import numpy as np, pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from figstyle import *

R = jload(f"{DATA}/results.json")
L = pd.read_csv(f"{DATA}/lsoa_counts.csv")
LD = pd.read_csv(f"{DATA}/lad_counts.csv")
J = pd.read_csv(f"{DATA}/jurisdictions.csv")
Y = pd.read_csv(f"{DATA}/years.csv")
M = pd.read_csv(f"{DATA}/models.csv")
H = pd.read_csv(f"{DATA}/holders.csv")
CREDIT = f"{HMLR}. Data: November 2026. Dwellings: VOA 2025."


def credit(fig, y=0.012, extra=""):
    fig.text(0.012, y, CREDIT + (("\n" + extra) if extra else ""), fontsize=7, color=MUT, ha="left", va="bottom", linespacing=1.4)


# ---------------- 1. map -----------------
S = lsoa_shapes(40)
L = L.set_index("lsoa")
cols = rate_col(L.reindex(S.index).rate.values)
fig = plt.figure(figsize=(9, 9.6), facecolor=PAPER)
ax = fig.add_axes([0.0, 0.05, 0.64, 0.86])
context_land(ax, (130000, 660000, 8000, 660000))
draw_polys(ax, S.geometry, cols, zorder=2)
fig.text(0.03, 0.965, "Overseas-company titles per 1,000 dwellings", fontproperties=DISP, fontsize=19, color=FG, va="top")
fig.text(0.03, 0.928, f"Every small area (LSOA) of England and Wales. {R['n_geocoded']:,} titles with a usable postcode.",
         fontproperties=SERP, fontsize=10.5, color=MUT, va="top")
# London inset
ax2 = fig.add_axes([0.6, 0.38, 0.39, 0.5])
ax2.set_facecolor(PAPER)
ext = (503000, 562000, 155000, 202000)
sel = S.cx[ext[0]:ext[1], ext[2]:ext[3]]
draw_polys(ax2, sel.geometry, rate_col(L.reindex(sel.index).rate.values), zorder=2)
ax2.set_xlim(ext[0], ext[1]); ax2.set_ylim(ext[2], ext[3]); ax2.set_aspect("equal"); ax2.set_xticks([]); ax2.set_yticks([])
for s_ in ax2.spines.values():
    s_.set_color(FG); s_.set_linewidth(0.8)
ax2.set_title("London", fontproperties=DISPB, fontsize=13, color=FG, loc="left")
ax.add_patch(plt.Rectangle((ext[0], ext[2]), ext[1] - ext[0], ext[3] - ext[2], fill=False, ec=FG, lw=0.8, zorder=5))
handles = [Patch(fc=c, ec="#9C8F78", lw=0.4, label=l) for c, l in zip(RATE_C, RATE_L)]
fig.legend(handles=handles, loc="lower left", bbox_to_anchor=(0.62, 0.08), frameon=False, fontsize=9.5,
           title="Titles per 1,000 dwellings", title_fontproperties=SERP)
credit(fig, extra="Grey: neighbouring countries.")
savefig(fig, "map", blog="map", img="map")

# ---------------- 2. districts -----------------
top = LD.head(20).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 7.2), facecolor=PAPER)
ax.set_facecolor(PAPER)
c = [UKO_C if r == "London" else OTH_C for r in top.region]
ax.barh(top.lad_name, top.rate, color=c, height=0.72)
for i, (r, n) in enumerate(zip(top.rate, top.titles)):
    ax.text(r + 1.5, i, f"{r:.1f}  ({n:,} titles)", va="center", fontsize=9, color=FG)
ax.set_xlabel("Overseas-company titles per 1,000 dwellings")
ax.set_xlim(0, top.rate.max() * 1.32)
style_axes(ax); ax.grid(axis="x", color=RULE, lw=0.6); ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(fc=UKO_C, label="London borough"), Patch(fc=OTH_C, label="Elsewhere")], loc="lower right", frameon=False)
fig.suptitle("The 20 districts with the most overseas-company titles per home", fontproperties=DISP, fontsize=16, x=0.02, ha="left", y=0.985)
fig.subplots_adjust(left=0.27, right=0.97, top=0.92, bottom=0.13)
credit(fig)
savefig(fig, "lad", blog="lad", img="lad")

# ---------------- 3. jurisdictions -----------------
j = J[J.jurisdiction != "Not stated"].head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 6.6), facecolor=PAPER)
ax.set_facecolor(PAPER)
c = [UKO_C if isinstance(u, str) and u else "#8C8577" for u in j.uk_link.fillna("")]
ax.barh(j.jurisdiction, j.titles, color=c, height=0.72)
for i, (n, p) in enumerate(zip(j.titles, j.share)):
    ax.text(n + 250, i, f"{n:,}  ({p:.1f}%)", va="center", fontsize=9, color=FG)
ax.set_xlim(0, j.titles.max() * 1.3); ax.set_xlabel("Titles held (first-named proprietor's place of incorporation)")
style_axes(ax); ax.grid(axis="x", color=RULE, lw=0.6); ax.grid(axis="y", visible=False)
ax.legend(handles=[Patch(fc=UKO_C, label="Crown Dependency or British Overseas Territory"), Patch(fc="#8C8577", label="Elsewhere")],
          loc="lower right", frameon=False)
fig.suptitle(f"Where the companies are incorporated: {R['pc_uko']:.0f}% in places linked to the UK", fontproperties=DISP, fontsize=15.5,
             x=0.02, ha="left", y=0.985)
fig.subplots_adjust(left=0.25, right=0.97, top=0.92, bottom=0.14)
credit(fig)
savefig(fig, "jur", blog="jur", img="jur")

# ---------------- 4. concentration (Lorenz) -----------------
fig, ax = plt.subplots(figsize=(7.5, 6.4), facecolor=PAPER)
ax.set_facecolor(PAPER)
for col, lab, cc in (("titles", f"Overseas-company titles (Gini {R['gini_titles']:.2f})", UKO_C),
                     ("dwellings", f"Dwellings (Gini {R['gini_dwellings']:.2f})", OTH_C)):
    v = np.sort(L[col].values)[::-1]
    cum = np.cumsum(v) / v.sum()
    ax.plot(np.arange(1, len(v) + 1) / len(v) * 100, cum * 100, color=cc, lw=2.4, label=lab)
ax.plot([0, 100], [0, 100], color=MUT, lw=0.8, ls=":")
ax.axvline(R["half_titles_lsoas_pc"], color=UKO_C, lw=0.8, ls="--")
ax.text(23, 80, f"Dashed line: half of mapped titles\nsit in {R['half_titles_lsoas']:,} areas ({R['half_titles_lsoas_pc']:.1f}%)",
        fontsize=9.5, color=UKO_C, va="center")
ax.set_xlabel("Small areas, from most to fewest (%)"); ax.set_ylabel("Cumulative share (%)")
ax.set_xlim(0, 100); ax.set_ylim(0, 101); style_axes(ax); ax.legend(loc="lower right", frameon=False)
fig.suptitle("Far more concentrated than homes", fontproperties=DISP, fontsize=16, x=0.02, ha="left", y=0.985)
fig.subplots_adjust(left=0.12, right=0.97, top=0.91, bottom=0.15)
credit(fig)
savefig(fig, "conc", blog="conc")

# ---------------- 5. years -----------------
y = Y[(Y.year >= 1995) & (Y.year <= 2026)]
fig, ax = plt.subplots(figsize=(9, 5.4), facecolor=PAPER)
ax.set_facecolor(PAPER)
ax.bar(y.year, y["UK-linked offshore"], color=UKO_C, width=0.8, label="Crown Dependencies and Overseas Territories")
ax.bar(y.year, y["Elsewhere"], bottom=y["UK-linked offshore"], color="#8C8577", width=0.8, label="Elsewhere")
ax.axvline(2022.58, color=FG, lw=0.9, ls="--")
ax.text(2022.85, y["all"].max() * 0.97, "Register of\nOverseas\nEntities\n(August 2022)", ha="left", va="top", fontsize=8.5, color=FG)
ax.text(2026, y[y.year == 2026]["all"].iloc[0] + 150, "part\nyear", ha="center", fontsize=8, color=MUT)
ax.set_ylabel("Titles, by year owner added")
style_axes(ax); ax.legend(loc="upper left", frameon=False, fontsize=9)
fig.suptitle("When today's overseas owners were added to the register", fontproperties=DISP, fontsize=15.5, x=0.02, ha="left", y=0.985)
fig.subplots_adjust(left=0.1, right=0.98, top=0.9, bottom=0.16)
credit(fig, extra="Titles sold on since are not in the file.")
savefig(fig, "years", blog="years", img="years")

# ---------------- 6. models (forest) -----------------
TERM = {"sh_high": "Share in the top Council Tax bands", "sh_flat": "Share of flats", "sh_new": "Share built since 2009"}
show = [("main", "Main model"), ("negative binomial", "Negative binomial"),
        ("region FE", "Region instead of district effects"), ("leave out London", "Without London"),
        ("drop Westminster, K&C", "Without Westminster, K. and Chelsea"), ("single-address titles", "Single-address titles only"),
        ("residential-looking titles", "Flats and apartments only"), ("leasehold titles", "Leasehold titles only"),
        ("freehold titles", "Freehold titles only"), ("VOA suppressed cells as 2.5", "Suppressed VOA cells as 2.5")]
fig, axs = plt.subplots(1, 3, figsize=(11, 5.8), facecolor=PAPER, sharey=True)
for ax, (k, lab) in zip(axs, TERM.items()):
    ax.set_facecolor(PAPER)
    for i, (m, ml) in enumerate(show):
        r = M[(M.model == m) & (M.term == k)].iloc[0]
        yy = len(show) - 1 - i
        ax.plot([r.lo, r.hi], [yy, yy], color=FG if i == 0 else MUT, lw=1.6)
        ax.plot(r.irr, yy, "o", color=UKO_C if i == 0 else FG, ms=7 if i == 0 else 5)
    p = R["placebo"][k]
    ax.plot([p["p2_5"], p["p97_5"]], [-1.2, -1.2], color=OTH_C, lw=1.6); ax.plot(p["mean"], -1.2, "s", color=OTH_C, ms=5)
    ax.axvline(1, color=MUT, lw=0.8, ls=":")
    ax.set_title(lab, fontproperties=SERP, fontsize=11, loc="left")
    ax.set_xlim(0.9, 1.7); ax.grid(axis="x", color=RULE, lw=0.6); ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
axs[0].set_yticks(list(range(len(show) - 1, -1, -1)) + [-1.2])
axs[0].set_yticklabels([s[1] for s in show] + ["Placebo: shuffled in districts"], fontsize=8.5)
axs[1].set_xlabel("Rate ratio for 10 more percentage points (95% interval)")
fig.suptitle("Within the same district, more titles where homes are dearer, flatter and newer", fontproperties=DISP, fontsize=15,
             x=0.02, ha="left", y=0.985)
fig.subplots_adjust(left=0.3, right=0.98, top=0.86, bottom=0.19, wspace=0.12)
credit(fig, extra=f"{R['main']['n']:,} small areas, {R['main']['clusters']} districts.")
savefig(fig, "models", blog="models", img="models")

# ---------------- 7. largest holders -----------------
h = H.iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 5.6), facecolor=PAPER)
ax.set_facecolor(PAPER)
c = [UKO_C if j_ in UKO else "#8C8577" for j_ in h.jurisdiction]
lab = [f"{p.title()}" for p in h.proprietor]
lab = [re.sub(r"\bB\.v\.", "B.V.", re.sub(r"\bPte\b", "Pte", re.sub(r"\bNo\.1\b", "No.1", re.sub(r"\bSfr\b", "SFR", re.sub(r"\bMrf\b", "MRF", re.sub(r"\bPfs\b", "PFS", re.sub(r"\bGkgh\b", "GKGH", x))))))) for x in lab]
ax.barh(lab, h.titles, color=c, height=0.7)
for i, (n, jj, d) in enumerate(zip(h.titles, h.jurisdiction, h.districts)):
    ax.text(n + 15, i, f"{n:,}  {jj}, {d} district{'s' if d > 1 else ''}", va="center", fontsize=8.5, color=FG)
ax.set_xlim(0, h.titles.max() * 2.1); ax.set_xlabel("Titles held as first-named proprietor")
ax.legend(handles=[Patch(fc=UKO_C, label="Crown Dependency or\nOverseas Territory"), Patch(fc="#8C8577", label="Elsewhere")], loc="lower right", frameon=False, fontsize=8.5)
style_axes(ax); ax.grid(axis="x", color=RULE, lw=0.6); ax.grid(axis="y", visible=False)
ax.tick_params(axis="y", labelsize=8.5)
fig.suptitle("The ten largest holders by number of titles", fontproperties=DISP, fontsize=15.5, x=0.02, ha="left", y=0.985)
fig.text(0.02, 0.915, "Companies, not people; counts of titles, not value. Holding property in England and Wales through an overseas company is legal.",
         fontsize=8, color=MUT, fontproperties=SERP)
fig.subplots_adjust(left=0.38, right=0.98, top=0.87, bottom=0.16)
credit(fig)
savefig(fig, "holders", blog="holders")

# ---------------- 8. price by group (paper only) -----------------
P = pd.read_csv(f"{DATA}/prices.csv").set_index("scope")
fig, ax = plt.subplots(figsize=(8, 3.8), facecolor=PAPER)
ax.set_facecolor(PAPER)
rows = [("all", "All titles with a price"), ("UK-linked offshore", "Crown Dependencies and Overseas Territories"), ("Elsewhere", "Elsewhere"),
        ("Freehold", "Freehold"), ("Leasehold", "Leasehold"), ("London", "London"), ("outside London", "Outside London")]
for i, (k, lab) in enumerate(rows[::-1]):
    r = P.loc[k]
    ax.plot([r.p25 / 1e6, r.p75 / 1e6], [i, i], color=MUT, lw=5, solid_capstyle="butt", alpha=.5)
    ax.plot(r["median"] / 1e6, i, "o", color=UKO_C, ms=7)
    ax.text(r.p75 / 1e6 + 0.08, i, f"median £{r["median"] / 1e3:,.0f}k  (n={int(r.n):,})", va="center", fontsize=8.5)
ax.set_yticks(range(len(rows))); ax.set_yticklabels([r[1] for r in rows[::-1]], fontsize=9)
ax.set_xlim(0, 5.6); ax.set_xlabel("Price paid at registration, £ million (dot: median; bar: middle half)")
style_axes(ax); ax.grid(axis="x", color=RULE, lw=0.6); ax.grid(axis="y", visible=False)
fig.subplots_adjust(left=0.36, right=0.98, top=0.95, bottom=0.22)
credit(fig)
savefig(fig, "price")
print("figures done")
