"""Step 2: the pre-specified analysis (NOTES.md). Reads SCR/titles.parquet and data/lsoa_voa.csv.
Writes aggregate tables to data/ (lsoa_counts.csv, lad_counts.csv, region_counts.csv, jurisdictions.csv, years.csv,
prices.csv, holders.csv, models.csv) and every number to SCR/analysis.json. No row-level title data is written."""
import time
import numpy as np, pandas as pd
import statsmodels.api as sm
from common import *
from ppml import fepois, irr_table

t0 = time.time()
T = pd.read_parquet(f"{SCR}/titles.parquet")
V = pd.read_csv(f"{DATA}/lsoa_voa.csv")
LN = pd.read_csv(f"{DATA}/lad_names.csv").set_index("lad")
A = {"n_titles": len(T)}
A["prep"] = jload(f"{SCR}/prep.json")
A["how"] = T.how.value_counts().to_dict()
A["n_geocoded"] = int((T.how == "postcode").sum())
A["pc_geocoded"] = 100 * A["n_geocoded"] / len(T)
A["n_leasehold"] = int(T.leasehold.sum()); A["n_freehold"] = int((~T.leasehold).sum())
A["pc_leasehold"] = 100 * T.leasehold.mean()
A["n_multi"] = int(T.multi.sum())
A["n_resid"] = int(T.resid.sum()); A["pc_resid"] = 100 * T.resid.mean()
A["n_dwellings"] = int(V.dwellings.sum())
A["n_lsoa"] = len(V)

# ---------------- jurisdictions (H2) -----------------
jc = T.country.value_counts()
J = pd.DataFrame({"jurisdiction": jc.index, "titles": jc.values})
J["share"] = 100 * J.titles / len(T)
J["uk_link"] = J.jurisdiction.map(lambda c: UKO.get(c, ""))
if not os.path.exists(FSI_CSV):
    import urllib.request; os.makedirs(os.path.dirname(FSI_CSV), exist_ok=True); urllib.request.urlretrieve(FSI_URL, FSI_CSV)
fsi = pd.read_csv(FSI_CSV)
fsi["key"] = fsi.Jurisdiction.str.strip()
alias = {"Virgin Islands (British)": "British Virgin Islands", "British Virgin Islands": "British Virgin Islands",
         "USA": "United States", "United States of America": "United States", "Turks & Caicos Islands": "Turks and Caicos Islands",
         "St Kitts & Nevis": "St Kitts and Nevis", "Saint Kitts and Nevis": "St Kitts and Nevis", "Saint Lucia": "St Lucia",
         "St. Lucia": "St Lucia", "Saint Vincent and the Grenadines": "St Vincent and the Grenadines",
         "St Vincent & the Grenadines": "St Vincent and the Grenadines", "Korea": "South Korea", "Macao": "Macau",
         "Curacao": "Curaçao", "Antigua & Barbuda": "Antigua and Barbuda", "Trinidad & Tobago": "Trinidad and Tobago"}
fsi["key"] = fsi.key.replace(alias)
sec = fsi.set_index("key")["Secrecy Score"]
J["fsi2018_secrecy"] = J.jurisdiction.map(sec)
J.round(3).to_csv(f"{DATA}/jurisdictions.csv", index=False)
A["n_jurisdictions"] = int((J.jurisdiction != "Not stated").sum())
uko = T.group == "UK-linked offshore"
A["n_uko"] = int(uko.sum()); A["pc_uko"] = 100 * uko.mean()
A["n_cd"] = int(T.country.map(lambda c: UKO.get(c) == "Crown Dependency").sum())
A["n_ot"] = int(T.country.map(lambda c: UKO.get(c) == "Overseas Territory").sum())
A["pc_cd"] = 100 * A["n_cd"] / len(T); A["pc_ot"] = 100 * A["n_ot"] / len(T)
A["h2_supported"] = bool(A["pc_uko"] > 50)
A["top_j"] = [{"j": r.jurisdiction, "n": int(r.titles), "pc": float(r.share)} for r in J.head(15).itertuples()]
A["top4_pc"] = float(J.head(4).share.sum())
anyuko = T.countries_all.map(lambda s: any(c in UKO for c in s.split("|")))
A["n_any_uko"] = int(anyuko.sum()); A["pc_any_uko"] = 100 * anyuko.mean()
A["n_multi_jur"] = int((T.countries_all.str.count(r"\|") > 0).sum())
# secondary: FSI 2018 secrecy score >= 65
T["fsi"] = T.country.map(sec)
A["fsi_matched_pc"] = 100 * T.fsi.notna().mean()
A["pc_fsi65"] = 100 * (T.fsi >= 65).sum() / T.fsi.notna().sum()
A["fsi_scores"] = {c: float(sec[c]) for c in ["Jersey", "Guernsey", "Isle of Man", "British Virgin Islands", "Cayman Islands",
                                              "Gibraltar", "Bermuda", "Singapore", "Luxembourg", "Hong Kong", "Ireland",
                                              "Panama", "Seychelles", "Cyprus", "Netherlands"] if c in sec.index}
A["fsi_missing_top"] = [c for c in J.head(25).jurisdiction if c not in sec.index and c != "Not stated"]

# ---------------- geography (H1) -----------------
G = T[T.how == "postcode"]
cnt = G.groupby("lsoa").size()
V["titles"] = V.lsoa.map(cnt).fillna(0).astype(int)
for k, m in {"uko": G.group == "UK-linked offshore", "jersey": G.country == "Jersey", "bvi": G.country == "British Virgin Islands",
             "guernsey": G.country == "Guernsey", "iom": G.country == "Isle of Man", "other": G.group != "UK-linked offshore",
             "resid": G.resid, "single": ~G.multi, "lease": G.leasehold, "free": ~G.leasehold}.items():
    V["t_" + k] = V.lsoa.map(G[m].groupby("lsoa").size()).fillna(0).astype(int)
V["rate"] = 1000 * V.titles / V.dwellings.where(V.dwellings > 0)
A["lsoa_with_any"] = int((V.titles > 0).sum()); A["pc_lsoa_with_any"] = 100 * (V.titles > 0).mean()


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1) @ x / (n * x.sum()))


A["gini_titles"] = gini(V.titles); A["gini_dwellings"] = gini(V.dwellings)
top = V.titles.sort_values(ascending=False)
k1 = int(round(len(V) * 0.01))
A["top1pc_lsoa_n"] = k1; A["top1pc_share"] = 100 * top.head(k1).sum() / V.titles.sum()
A["top1pc_dw_share"] = 100 * V.loc[top.head(k1).index, "dwellings"].sum() / V.dwellings.sum()
A["half_titles_lsoas"] = int((top.cumsum() < V.titles.sum() / 2).sum() + 1)
A["half_titles_lsoas_pc"] = 100 * A["half_titles_lsoas"] / len(V)
A["lsoa_median_rate"] = float(V.rate.median())
big = V[V.dwellings >= 50].sort_values("rate", ascending=False)
A["lsoa_top"] = [{"lsoa": r.lsoa, "name": r.lsoa_name, "titles": int(r.titles), "dw": int(r.dwellings), "rate": float(r.rate)}
                 for r in big.head(10).itertuples()]
A["lsoa_over100"] = int((big.rate >= 100).sum())

# districts (all titles, incl. those placed by the District field)
lc = T.groupby("lad").size()
LD = LN.copy()
LD["titles"] = lc.reindex(LD.index).fillna(0).astype(int)
LD["titles_geocoded"] = G.groupby("lad").size().reindex(LD.index).fillna(0).astype(int)
LD["dwellings"] = V.groupby("lad").dwellings.sum().reindex(LD.index)
LD["rate"] = 1000 * LD.titles / LD.dwellings
LD["uko"] = T[uko].groupby("lad").size().reindex(LD.index).fillna(0).astype(int)
LD["pc_uko"] = 100 * LD.uko / LD.titles.where(LD.titles > 0)
LD["top_jur"] = T.groupby("lad").country.agg(lambda s: s.value_counts().index[0]).reindex(LD.index)
pp = T[T.price.notna() & (T.price > 0)]
LD["n_price"] = pp.groupby("lad").size().reindex(LD.index).fillna(0).astype(int)
LD["median_price"] = pp.groupby("lad").price.median().reindex(LD.index).where(LD.n_price >= 10)
LD = LD.sort_values("rate", ascending=False)
LD["rank"] = np.arange(1, len(LD) + 1)
LD.reset_index().round(2).to_csv(f"{DATA}/lad_counts.csv", index=False)
A["lad_top"] = [{"lad": i, "name": r.lad_name, "titles": int(r.titles), "rate": float(r.rate), "pc_uko": float(r.pc_uko),
                 "region": r.region} for i, r in LD.head(15).iterrows()]
A["lad_top_by_count"] = [{"name": r.lad_name, "titles": int(r.titles), "rate": float(r.rate)}
                         for i, r in LD.sort_values("titles", ascending=False).head(10).iterrows()]
rk = LD.set_index("lad_name")["rank"]
A["rank_westminster"] = int(rk["Westminster"]); A["rank_kc"] = int(rk["Kensington and Chelsea"])
A["h1_supported"] = bool(A["gini_titles"] > A["gini_dwellings"] + 0.2 and max(A["rank_westminster"], A["rank_kc"]) <= 5)
A["lad_top_outside_london"] = [{"name": r.lad_name, "titles": int(r.titles), "rate": float(r.rate), "region": r.region}
                               for i, r in LD[LD.region != "London"].head(10).iterrows()]
A["lad_median_rate"] = float(LD.rate.median())
A["lad_with_zero"] = int((LD.titles == 0).sum())
A["ew_rate"] = 1000 * len(T) / V.dwellings.sum()
A["westminster_kc_titles"] = int(LD.loc[LD.lad_name.isin(["Westminster", "Kensington and Chelsea"]), "titles"].sum())
A["westminster_kc_pc"] = 100 * A["westminster_kc_titles"] / len(T)
A["westminster_kc_dw_pc"] = 100 * LD.loc[LD.lad_name.isin(["Westminster", "Kensington and Chelsea"]), "dwellings"].sum() / V.dwellings.sum()

# regions
RG = pd.DataFrame({"titles": T.groupby("region").size()})
RG["dwellings"] = V.groupby("region").dwellings.sum()
RG["rate"] = 1000 * RG.titles / RG.dwellings
RG["share"] = 100 * RG.titles / len(T)
RG["pc_uko"] = 100 * T[uko].groupby("region").size() / RG.titles
RG["median_price"] = pp.groupby("region").price.median()
RG = RG.sort_values("rate", ascending=False)
RG.round(2).reset_index().to_csv(f"{DATA}/region_counts.csv", index=False)
A["regions"] = {r: {"titles": int(x.titles), "rate": float(x.rate), "share": float(x.share), "pc_uko": float(x.pc_uko)}
                for r, x in RG.iterrows()}
A["pc_london"] = float(RG.loc["London", "share"])
A["pc_london_dw"] = 100 * float(RG.loc["London", "dwellings"]) / V.dwellings.sum()
A["london_rate"] = float(RG.loc["London", "rate"])
A["rest_rate"] = 1000 * (len(T) - RG.loc["London", "titles"]) / (V.dwellings.sum() - RG.loc["London", "dwellings"])

# ---------------- time (D1) -----------------
Y = T.groupby(["year", "group"]).size().unstack(fill_value=0)
Y["all"] = Y.sum(axis=1)
Y.index = Y.index.astype(int)
Y.reset_index().to_csv(f"{DATA}/years.csv", index=False)
A["year_missing"] = int(T.year.isna().sum())
A["year_peak"] = int(Y["all"].idxmax()); A["year_peak_n"] = int(Y["all"].max())
A["since_2022"] = int(T.year.ge(2022).sum()); A["pc_since_2022"] = 100 * T.year.ge(2022).mean()
A["before_2000"] = int(T.year.lt(2000).sum())
A["pc_uko_by_period"] = {p: float(100 * (T[(T.year >= a) & (T.year <= b)].group == "UK-linked offshore").mean())
                         for p, (a, b) in {"1999_2009": (1999, 2009), "2010_2016": (2010, 2016), "2017_2021": (2017, 2021),
                                           "2022_2026": (2022, 2026)}.items()}
A["years"] = {int(y): int(n) for y, n in Y["all"].items()}
A["latest_year"] = int(T.year.max())

# ---------------- prices (D2) -----------------
A["n_price"] = len(pp); A["pc_price"] = 100 * len(pp) / len(T)
q = lambda s: {"n": int(len(s)), "p25": float(s.quantile(.25)), "median": float(s.median()), "p75": float(s.quantile(.75))}
A["price_all"] = q(pp.price)
A["price_by_group"] = {k: q(s.price) for k, s in pp.groupby("group") if len(s) >= 10}
A["price_by_tenure"] = {("Leasehold" if k else "Freehold"): q(s.price) for k, s in pp.groupby("leasehold")}
A["price_london"] = q(pp[pp.region == "London"].price); A["price_rest"] = q(pp[pp.region != "London"].price)
A["price_resid_london"] = q(pp[(pp.region == "London") & pp.resid & ~pp.multi].price)
A["price_sum_bn"] = float(pp.price.sum() / 1e9)
A["price_over_1m"] = int((pp.price >= 1e6).sum()); A["pc_price_over_1m"] = 100 * (pp.price >= 1e6).mean()
pr = pd.DataFrame([dict(scope="all", **A["price_all"])] + [dict(scope=k, **v) for k, v in A["price_by_group"].items()] +
                  [dict(scope=k, **v) for k, v in A["price_by_tenure"].items()] +
                  [dict(scope="London", **A["price_london"]), dict(scope="outside London", **A["price_rest"])])
pr.round(0).to_csv(f"{DATA}/prices.csv", index=False)

# ---------------- largest holders (D3) -----------------
H = T.groupby("owner").agg(titles=("owner", "size"), jurisdiction=("country", lambda s: s.value_counts().index[0]),
                           districts=("lad", "nunique")).sort_values("titles", ascending=False)
A["n_owners"] = int(len(H))
A["owners_one_title"] = int((H.titles == 1).sum()); A["pc_owners_one_title"] = 100 * (H.titles == 1).mean()
A["top10_owner_titles"] = int(H.head(10).titles.sum()); A["top10_owner_pc"] = 100 * A["top10_owner_titles"] / len(T)
A["top100_owner_pc"] = 100 * H.head(100).titles.sum() / len(T)
H.head(10).reset_index().rename(columns={"owner": "proprietor"}).to_csv(f"{DATA}/holders.csv", index=False)
A["holders"] = [{"name": r.Index, "titles": int(r.titles), "jur": r.jurisdiction, "districts": int(r.districts)}
                for r in H.head(10).itertuples()]
A["category"] = T.category.value_counts().to_dict()

# ---------------- H3 models -----------------
M = V[(V.dwellings >= 50) & V.sh_high.notna() & V.sh_flat.notna() & V.sh_new.notna()].copy()
A["model_lsoa_dropped"] = int(len(V) - len(M))
XN = ["sh_high", "sh_flat", "sh_new"]
LAB = {"sh_high": "Top Council Tax bands (per 10 points)", "sh_flat": "Flats and maisonettes (per 10 points)",
       "sh_new": "Built 2009 or later (per 10 points)"}
A["shares_mean"] = {k: float(M[k].mean()) for k in XN}
A["shares_sd"] = {k: float(M[k].std()) for k in XN}
A["shares_corr"] = M[XN].corr().round(3).to_dict()


def run(df, y="titles", fe="lad", X=XN):
    f = fepois(df[y], df[X] / 10, np.log(df.dwellings), df[fe], df.lad)
    t = irr_table(f, X)
    return f, t


rows = []


def rec(name, f, t, extra=""):
    for r in t.itertuples():
        rows.append({"model": name, "term": r.term, "irr": r.irr, "lo": r.lo, "hi": r.hi, "b": r.b, "se": r.se,
                     "n": f["n"], "clusters": f["clusters"], "note": extra})
    return {r.term: {"irr": float(r.irr), "lo": float(r.lo), "hi": float(r.hi), "p": float(2 * (1 - __import__("scipy").stats.norm.cdf(abs(r.z))))}
            for r in t.itertuples()} | {"n": f["n"], "clusters": f["clusters"], "dropped": f["dropped"]}


F0, T0 = run(M)
A["main"] = rec("main", F0, T0)
A["main_titles"] = int(M.titles.sum())
A["h3"] = {k: bool(A["main"][k]["lo"] > 1) for k in XN}
# check against statsmodels GLM with LAD dummies
D = pd.get_dummies(M.lad, drop_first=True, dtype=float)
Xs = pd.concat([M[XN] / 10, D], axis=1); Xs.insert(0, "const", 1.0)
g = sm.GLM(M.titles, Xs, family=sm.families.Poisson(), offset=np.log(M.dwellings)).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(M.lad)[0]})
A["check_glm"] = {k: [float(np.exp(g.params[k])), float(g.bse[k])] for k in XN}
assert all(abs(g.params[k] - F0["b"][i]) < 1e-5 for i, k in enumerate(XN)), (g.params[XN], F0["b"])
del g, D, Xs
import gc; gc.collect()
print("main", T0[["term", "irr", "lo", "hi"]].round(3).values.tolist(), f"{time.time() - t0:.0f}s")

# univariate (descriptive)
A["uni"] = {}
for k in XN:
    f, t = run(M, X=[k]); A["uni"][k] = rec("univariate " + k, f, t)[k]

# H3s: by jurisdiction group, separately and stacked
f, t = run(M, y="t_uko"); A["m_uko"] = rec("UK-linked offshore titles", f, t)
f, t = run(M, y="t_other"); A["m_other"] = rec("other jurisdictions", f, t)
S = pd.concat([M.assign(y=M.t_uko, uk=1.0), M.assign(y=M.t_other, uk=0.0)])
S["fe"] = S.lad + "_" + S.uk.astype(int).astype(str)
for k in XN:
    S[k + "_x"] = S[k] * S.uk
fS = fepois(S.y, S[XN + [k + "_x" for k in XN]] / 10, np.log(S.dwellings), S.fe, S.lad)
tS = irr_table(fS, XN + [k + "_x" for k in XN])
A["m_stacked"] = rec("stacked interaction", fS, tS)

# Robustness
A["rob"] = {}
print("models", f"{time.time() - t0:.0f}s", flush=True)
f, t = run(M, fe="region"); A["rob"]["region_fe"] = rec("region FE", f, t)
nb_t = time.time()
from ppml import fenb
Xm, offm = M[XN].values / 10, np.log(M.dwellings.values)
fit_a = lambda al: fenb(M.titles.values, Xm, offm, M.lad.values, M.lad.values, al)
grid = {al: fit_a(al)["ll"] for al in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.25, 1.5, 2.0, 2.5, 3.0, 4.0]}
al = max(grid, key=grid.get)
for step in (0.05, 0.01):
    cand = [round(al + k * step, 3) for k in range(-4, 5) if al + k * step > 0]
    lls = {c: fit_a(c)["ll"] for c in cand}
    al = max(lls, key=lls.get)
nbf = fit_a(al)
A["rob"]["negbin"] = {}
for i, k in enumerate(XN):
    b_, se = nbf["b"][i], nbf["se"][i]
    A["rob"]["negbin"][k] = {"irr": float(np.exp(b_)), "lo": float(np.exp(b_ - 1.96 * se)), "hi": float(np.exp(b_ + 1.96 * se))}
    rows.append({"model": "negative binomial", "term": k, "irr": np.exp(b_), "lo": np.exp(b_ - 1.96 * se), "hi": np.exp(b_ + 1.96 * se),
                 "b": b_, "se": se, "n": nbf["n"], "clusters": nbf["clusters"], "note": f"alpha={al:.2f} (profile likelihood)"})
A["rob"]["negbin"]["alpha"] = float(al)
A["rob"]["negbin"]["n"] = nbf["n"]
print("negbin", f"{time.time() - nb_t:.0f}s")
for reg in sorted(M.region.unique()):
    f, t = run(M[M.region != reg]); A["rob"]["loro_" + reg] = rec("leave out " + reg, f, t)
f, t = run(M[~M.lad.isin(LN[LN.lad_name.isin(["Westminster", "Kensington and Chelsea"])].index)]); A["rob"]["no_wkc"] = rec("drop Westminster, K&C", f, t)
for y, nm in [("t_single", "single-address titles"), ("t_resid", "residential-looking titles"), ("t_lease", "leasehold titles"),
              ("t_free", "freehold titles")]:
    f, t = run(M, y=y); A["rob"][y] = rec(nm, f, t)
V25 = pd.read_csv(f"{SCR}/lsoa_voa_dash2.5.csv").set_index("lsoa")
M25 = M.copy()
for k in XN:
    M25[k] = M25.lsoa.map(V25[k])
M25 = M25.dropna(subset=XN)
f, t = run(M25); A["rob"]["dash25"] = rec("VOA suppressed cells as 2.5", f, t)
loro = [A["rob"][k] for k in A["rob"] if k.startswith("loro_")]
A["loro_range"] = {k: [min(r[k]["irr"] for r in loro), max(r[k]["irr"] for r in loro),
                       all(r[k]["lo"] > 1 for r in loro)] for k in XN}

# Placebo: reallocate each LAD's titles across its LSOAs in proportion to dwellings, 200 times
rng = np.random.default_rng(2026)
pl = []
grp = M.groupby("lad")
idx = {l: g.index.values for l, g in grp}
pos = {l: M.index.get_indexer(v) for l, v in idx.items()}
p_ = {l: (g.dwellings / g.dwellings.sum()).values for l, g in grp}
tot = grp.titles.sum()
for r in range(200):
    yy = np.zeros(len(M))
    for l in idx:
        yy[pos[l]] = rng.multinomial(int(tot[l]), p_[l])
    f = fepois(yy, M[XN].values / 10, np.log(M.dwellings.values), M.lad.values, M.lad.values)
    pl.append(np.exp(f["b"]))
pl = np.array(pl)
A["placebo"] = {k: {"mean": float(pl[:, i].mean()), "p2_5": float(np.percentile(pl[:, i], 2.5)), "p97_5": float(np.percentile(pl[:, i], 97.5)),
                    "share_ge_obs": float((pl[:, i] >= A["main"][k]["irr"]).mean()) if A["main"][k]["irr"] >= 1 else float((pl[:, i] <= A["main"][k]["irr"]).mean())}
                for i, k in enumerate(XN)}
A["placebo_reps"] = 200
pd.DataFrame(rows).round(5).to_csv(f"{DATA}/models.csv", index=False)

# ---------------- LSOA table for the map and reuse -----------------
out = V[["lsoa", "lsoa_name", "lad", "region", "dwellings", "titles", "t_uko", "t_jersey", "t_bvi", "t_guernsey", "t_iom", "t_other",
         "rate", "sh_high", "sh_flat", "sh_new"]].copy()
out.round(3).to_csv(f"{DATA}/lsoa_counts.csv", index=False)
A["runtime_s"] = time.time() - t0
jsave(A, f"{SCR}/analysis.json", indent=1)
print("done", f"{time.time() - t0:.0f}s")
