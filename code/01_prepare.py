"""Step 1: read the HM Land Registry OCOD file and the VOA tables where they sit.
Writes (scratch only, never published): SCR/titles.parquet, one row per title with only the fields the analysis needs
(LSOA, LAD, region, tenure, multiple-address flag, price paid, cleaned jurisdictions, year added, residential-looking flag,
first proprietor name). No title number, address or postcode is kept.
Writes (published, aggregates of OGL data): data/lsoa_voa.csv (dwellings, band, flat and new-build shares by LSOA 2021),
data/lad_names.csv."""
import zipfile
import numpy as np, pandas as pd, geopandas as gpd
from common import *

DASH = float(os.environ.get("OO_DASH", "0"))
L = pd.read_csv(f"{DATA}/lsoa_lookup.csv", dtype=str)

# ---------------- VOA denominators -----------------
def read_voa(t):
    z = zipfile.ZipFile(os.path.join(VOA, f"{t}.zip"))
    fn = [n for n in z.namelist() if n.endswith(".csv")][0]
    d = pd.read_csv(z.open(fn), dtype=str, encoding="utf-8-sig")
    d = d[d.geography == "LSOA"].copy()
    for c in d.columns[5:]:
        d[c] = pd.to_numeric(d[c].str.strip().replace({"-": str(DASH), "..": "0", "": "0"}), errors="coerce").fillna(0)
    return d

d4 = read_voa("CTSOP4.1")
allb = d4[d4.band == "All"].set_index("ecode")
V = pd.DataFrame({"dwellings": allb["all_properties"]})
new = [c for c in d4.columns if re.fullmatch(r"bp_20(09|1\d|2\d)", c)]
V["new2009"] = allb[new].sum(axis=1)
V["age_known"] = allb["all_properties"] - allb["bp_unkw"]
b = d4[d4.band != "All"].pivot_table(index="ecode", columns="band", values="all_properties", aggfunc="sum").fillna(0)
for k in "ABCDEFGHI":
    V["band_" + k] = b.get(k, pd.Series(0, index=b.index)).reindex(V.index).fillna(0)
d3 = read_voa("CTSOP3.1")
t3 = d3[d3.band == "All"].set_index("ecode")
V["flats"] = t3["flat_mais_total"].reindex(V.index).fillna(0)
V.index.name = "lsoa"
V = V.reset_index()
V = L.merge(V, on="lsoa", how="left")
wal = V.lsoa.str.startswith("W")
V["high_band"] = np.where(wal, V.band_G + V.band_H + V.band_I, V.band_F + V.band_G + V.band_H)
bandsum = V[[f"band_{k}" for k in "ABCDEFGHI"]].sum(axis=1)
V["sh_high"] = 100 * V.high_band / bandsum.where(bandsum > 0)
V["sh_flat"] = 100 * V.flats / V.dwellings.where(V.dwellings > 0)
V["sh_new"] = 100 * V.new2009 / V.age_known.where(V.age_known > 0)
suf = "" if DASH == 0 else f"_dash{DASH:g}"
V[["lsoa", "lsoa_name", "lad", "region", "dwellings", "high_band", "flats", "new2009", "sh_high", "sh_flat", "sh_new"]].round(3).to_csv(
    f"{DATA}/lsoa_voa{suf}.csv" if not suf else f"{SCR}/lsoa_voa{suf}.csv", index=False)
print("VOA LSOAs", V.dwellings.notna().sum(), "dwellings", int(V.dwellings.sum()))
if DASH:
    raise SystemExit

# ---------------- LAD names -----------------
lg = gpd.read_file(f"{GEO}/lad23_bgc.geojson", ignore_geometry=True)
lg["LAD23CD"] = lg.LAD23CD.replace({"E08000016": "E08000038", "E08000019": "E08000039"})
names = lg.set_index("LAD23CD").LAD23NM
lads = sorted(L.lad.unique())
assert all(c in names.index for c in lads), [c for c in lads if c not in names.index]
pd.DataFrame({"lad": lads, "lad_name": [names[c] for c in lads],
              "region": [L[L.lad == c].region.iloc[0] for c in lads]}).to_csv(f"{DATA}/lad_names.csv", index=False)

# ---------------- OCOD titles -----------------
z = zipfile.ZipFile(OCOD_ZIP)
d = pd.read_csv(z.open("OCOD_FULL_2026_11.csv"), dtype=str, keep_default_na=False)
n_raw = len(d)
bad = d.Tenure.isin(["Freehold", "Leasehold"]) == False
print("rows", n_raw, "malformed", int(bad.sum()))
d = d[~bad].copy()
P = pd.read_csv(PC_CSV, dtype=str, keep_default_na=False)
P = P[P.lsoa_code != ""].set_index("postcode")
pc = d.Postcode.str.replace(" ", "", regex=False).str.upper()
d["lsoa"] = pc.map(P.lsoa_code)
d = d.merge(L[["lsoa", "lad"]], on="lsoa", how="left")
d["how"] = np.where(d.lsoa.notna(), "postcode", np.where(pc != "", "postcode not found", "no postcode"))
# titles without a usable postcode: district from the HMLR District field, via the modal LAD of geocoded titles
mode = d[d.lad.notna()].groupby("District").lad.agg(lambda s: s.value_counts().index[0])
d.loc[d.lad.isna(), "lad"] = d.loc[d.lad.isna(), "District"].map(mode)
reg = L.drop_duplicates("lad").set_index("lad").region
d["region"] = d.lad.map(reg)
print(d.how.value_counts().to_dict(), "no LAD", int(d.lad.isna().sum()))

cc = [d[f"Country Incorporated ({k})"] for k in range(1, 5)]
names_ = [d[f"Proprietor Name ({k})"] for k in range(1, 5)]
d["country"] = d["Country Incorporated (1)"].map(clean_country)
allc = []
for i in range(len(d)):
    s = {clean_country(c.iat[i]) for c, nm in zip(cc, names_) if nm.iat[i].strip() or c.iat[i].strip()}
    allc.append("|".join(sorted(s - {"Not stated"} or {"Not stated"})))
d["countries_all"] = allc
d["group"] = d.country.map(group_of)
d["n_props"] = sum((n.str.strip() != "").astype(int) for n in names_)
d["price"] = pd.to_numeric(d["Price Paid"], errors="coerce")
d["year"] = pd.to_numeric(d["Date Proprietor Added"].str[-4:], errors="coerce")
d["multi"] = d["Multiple Address Indicator"] == "Y"
d["resid"] = d["Property Address"].str.contains(r"\b(?:flat|apartment|maisonette|studio|penthouse)s?\b", case=False, regex=True)
d["leasehold"] = d.Tenure == "Leasehold"
d["owner"] = d["Proprietor Name (1)"].str.strip()
d["category"] = d["Proprietorship Category (1)"]
keep = ["lsoa", "lad", "region", "how", "leasehold", "multi", "resid", "price", "year", "country", "countries_all", "group",
        "n_props", "owner", "category"]
d[keep].reset_index(drop=True).to_parquet(f"{SCR}/titles.parquet")
jsave({"rows_raw": n_raw, "malformed": int(bad.sum()), "titles": len(d), "how": d.how.value_counts().to_dict(),
       "no_lad": int(d.lad.isna().sum())}, f"{SCR}/prep.json", indent=1)
