"""Step 5: page data. data/site_lsoa.json (per LSOA, in the order of the geometries in data/lsoa.topo.json: name, district,
dwellings and title counts by jurisdiction group; aggregates only), data/lad.geojson (district outlines, ONS LAD December 2023
BGC, OGL v3.0, simplified with mapshaper, with district totals) and data/site.json (district list, search places, key numbers)."""
import subprocess
import numpy as np, pandas as pd, geopandas as gpd
from common import *

R = jload(f"{DATA}/results.json")
codes = jload(f"{DATA}/lsoa_codes.json")
L = pd.read_csv(f"{DATA}/lsoa_counts.csv").set_index("lsoa").reindex(codes)
LD = pd.read_csv(f"{DATA}/lad_counts.csv").set_index("lad")
lads = sorted(LD.index)
li = {c: i for i, c in enumerate(lads)}
S = {"names": L.lsoa_name.tolist(), "lad": [li[c] for c in L.lad], "n": L.dwellings.fillna(0).astype(int).tolist()}
for k, c in (("t", "titles"), ("u", "t_uko"), ("j", "t_jersey"), ("b", "t_bvi"), ("g", "t_guernsey"), ("m", "t_iom")):
    S[k] = L[c].astype(int).tolist()
jsave(S, f"{DATA}/site_lsoa.json")

# district polygons with totals
g = gpd.read_file(f"{GEO}/lad23_bgc.geojson")
g["LAD23CD"] = g.LAD23CD.replace({"E08000016": "E08000038", "E08000019": "E08000039"})
g = g[g.LAD23CD.isin(lads)][["LAD23CD", "geometry"]].rename(columns={"LAD23CD": "c"})
assert len(g) == len(lads)
g["i"] = g.c.map(li)
tmp = f"{SCR}/lad_tmp.geojson"; g[["i", "geometry"]].to_crs(4326).to_file(tmp, driver="GeoJSON")
subprocess.run(["mapshaper", tmp, "-simplify", "8%", "weighted", "keep-shapes", "-o", "format=geojson", "precision=0.0001",
                f"{DATA}/lad.geojson"], check=True, capture_output=True)
os.remove(tmp)
b = g.to_crs(4326).set_index("c").bounds
las = []
for c in lads:
    r = LD.loc[c]
    las.append({"c": c, "n": r.lad_name, "rg": r.region, "t": int(r.titles), "tg": int(r.titles_geocoded), "d": int(r.dwellings),
                "r": round(float(r.rate), 2), "rk": int(r["rank"]), "u": None if pd.isna(r.pc_uko) else round(float(r.pc_uko), 1),
                "j": r.top_jur if isinstance(r.top_jur, str) else None, "np": int(r.n_price),
                "mp": None if pd.isna(r.median_price) else int(round(r.median_price, -3)),
                "b": [round(v, 3) for v in b.loc[c].tolist()]})
# places for search: Wikidata settlements (CC0) inside England and Wales, population at least 1,500
w = pd.read_csv("/home/claude/newdata/raw_new8/uk_settlements.tsv", sep="\t")
w["name"] = w["?pl"].str.extract(r'^"?(.*?)"?@en$')[0]
w["pop"] = pd.to_numeric(w["?pop"].astype(str).str.extract(r"([0-9.]+)")[0], errors="coerce")
xy = w["?coord"].str.extract(r"POINT\(([-0-9.]+) ([-0-9.]+)\)").astype(float)
w["lon"], w["lat"] = xy[0], xy[1]
w = w[(w["pop"] >= 1500) & w.lon.notna() & ~w["?typel"].astype(str).str.contains("metropolitan|conurbation|urban area|built-up|region|county|agglomeration", case=False)]
w = w.sort_values("pop", ascending=False).drop_duplicates("name")
pts = gpd.GeoDataFrame(w, geometry=gpd.points_from_xy(w.lon, w.lat), crs=4326).to_crs(27700)
ew = gpd.read_file(f"{SCR}/lsoa_bng_s40.gpkg")[["geometry"]]
pts = gpd.sjoin(pts, ew, predicate="within", how="inner").drop_duplicates("name")
places = [{"n": r.name, "lo": round(r.lon, 4), "la": round(r.lat, 4)} for r in pts.itertuples()]
site = {"las": las, "places": places, "ew_rate": round(R["ew_rate"], 2), "n_titles": R["n_titles"], "n_geo": R["n_geocoded"]}
jsave(site, f"{DATA}/site.json")
for fn in ("lsoa.topo.json", "site_lsoa.json", "site.json", "lad.geojson"):
    print(fn, os.path.getsize(f"{DATA}/{fn}") // 1024, "KB")
print(len(places), "places")
