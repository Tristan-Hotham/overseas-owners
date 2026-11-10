"""House style for the static figures: light paper, Fraunces titles, Source Serif and IBM Plex Mono text, a sequential palette for
overseas-company titles per 1,000 dwellings, and helpers for LSOA maps (shapes cached in scratch)."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
from common import *

_FD = os.path.join(SCR, "fonts")
os.makedirs(_FD, exist_ok=True)
if not os.path.exists(f"{_FD}/Fraunces-Black.ttf"):
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer
    for w, nm in ((900, "Black"), (700, "Bold")):
        instancer.instantiateVariableFont(TTFont(f"{FONTS}/FrauncesVar.ttf"), {"wght": w, "opsz": 144, "SOFT": 0, "WONK": 0}).save(f"{_FD}/Fraunces-{nm}.ttf")
DISP = fm.FontProperties(fname=f"{_FD}/Fraunces-Black.ttf")
DISPB = fm.FontProperties(fname=f"{_FD}/Fraunces-Bold.ttf")
SERP = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-Regular.ttf")
SERI = fm.FontProperties(fname=f"{FONTS}/SourceSerif4-It.ttf")
for f in ("IBMPlexMono-Regular.ttf", "IBMPlexMono-Medium.ttf"):
    fm.fontManager.addfont(f"{FONTS}/{f}")
MONO = "IBM Plex Mono"
plt.rcParams.update({"font.family": MONO, "font.size": 11, "axes.edgecolor": "#636A72", "axes.labelcolor": "#1D2128",
                     "xtick.color": "#636A72", "ytick.color": "#636A72", "axes.unicode_minus": False, "pdf.fonttype": 42})
PAPER, FG, MUT, RULE = "#F6F4EF", "#1D2128", "#636A72", "#DDD8CC"
SEA, SAND, EDGE = "#E4ECF0", "#ECE8DF", "#B9AE98"
HOT = "#B3202A"
NODATA = "#ECE8DF"
UKO_C, OTH_C = "#B3202A", "#2F6A9E"
RATE_B = [0, 0.001, 2, 5, 10, 25, 50, 100, 1e9]
RATE_L = ["none", "under 2", "2 to 5", "5 to 10", "10 to 25", "25 to 50", "50 to 100", "100 or more"]
RATE_C = ["#FFFDF8", "#F7E3C4", "#F1C48E", "#E59A5E", "#D0663D", "#AE3A2B", "#7E1F22", "#4A0F18"]


def rate_col(r):
    import numpy as np
    r = np.nan_to_num(np.asarray(r, float), nan=0)
    return [RATE_C[int(np.searchsorted(RATE_B, v, side="right") - 1)] if v > 0 else RATE_C[0] for v in r]


def lsoa_shapes(tol=40):
    """LSOA polygons in British National Grid, simplified for drawing, cached in SCR (index LSOA21CD)."""
    import geopandas as gpd
    fn = os.path.join(SCR, f"lsoa_bng_s{tol}.gpkg")
    if not os.path.exists(fn):
        import topojson_util
        topojson_util.write_bng(fn, tol)
    return gpd.read_file(fn).set_index("LSOA21CD")


def draw_polys(ax, geoms, colors, lw=0, ec="none", zorder=2, rasterized=True):
    from matplotlib.patches import Polygon as MPoly
    from matplotlib.collections import PatchCollection
    patches, cols = [], []
    for g, c in zip(geoms, colors):
        for p in (g.geoms if g.geom_type == "MultiPolygon" else [g]):
            patches.append(MPoly(np.asarray(p.exterior.coords), closed=True)); cols.append(c)
    pc = PatchCollection(patches, facecolor=cols, edgecolor=ec if lw else cols, linewidth=lw if lw else 0.15, zorder=zorder, rasterized=rasterized)
    ax.add_collection(pc)
    return pc


def context_land(ax, ext=None):
    """Neighbouring land (Scotland, Ireland, France, Isle of Man) in light grey, in BNG, on a sea background."""
    import geopandas as gpd
    fn = os.path.join(SCR, "context_bng.gpkg")
    if not os.path.exists(fn):
        c = gpd.read_file(os.path.join(GEO, "ne_10m_admin_0_countries.geojson"))
        c = c[c.ADM0_A3.isin(["IRL", "IMN", "FRA", "GBR"])].clip((-11, 48.5, 3, 61)).to_crs(27700)
        lad = gpd.read_file(os.path.join(GEO, "lad23_bgc.geojson")).to_crs(27700)
        cc = [k for k in lad.columns if k.upper().startswith("LAD") and k.upper().endswith("CD")][0]
        other = lad[~lad[cc].str[0].isin(["E", "W"])]
        g = gpd.GeoDataFrame(geometry=list(c[c.ADM0_A3 != "GBR"].geometry) + list(other.geometry), crs=27700)
        g["geometry"] = g.geometry.simplify(300)
        g.to_file(fn)
    g = gpd.read_file(fn)
    ax.set_facecolor(SEA)
    draw_polys(ax, g.geometry, ["#E9E6DF"] * len(g), lw=0.3, ec="#CFC8B8", zorder=1)
    if ext:
        ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    for s_ in ax.spines.values():
        s_.set_visible(False)


def style_axes(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color=RULE, lw=0.6)
    ax.set_axisbelow(True)


def savefig(fig, stem, blog=None, img=None, pdf=True):
    """f_<stem>.pdf for the paper, release/blog/b_<blog>.png at 1800 px wide, img/<img>.jpg for the page"""
    os.makedirs(f"{REL}/paper", exist_ok=True); os.makedirs(f"{REL}/blog", exist_ok=True)
    if pdf:
        fig.savefig(f"{REL}/paper/f_{stem}.pdf", facecolor=fig.get_facecolor())
    w = fig.get_figwidth()
    if blog:
        fig.savefig(f"{REL}/blog/b_{blog}.png", dpi=1800 / w, facecolor=fig.get_facecolor())
    if img:
        tmp = f"{SCR}/_tmp.png"
        fig.savefig(tmp, dpi=1400 / w, facecolor=fig.get_facecolor())
        from PIL import Image
        Image.open(tmp).convert("RGB").save(f"{IMG}/{img}.jpg", quality=86, optimize=True)
        os.remove(tmp)
    plt.close(fig)
