"""Step 0: LSOA 2021 -> LAD -> region lookup for all 35,672 LSOAs of England and Wales (data/lsoa_lookup.csv), from the
ONS LSOA 2021 boundary files (OGL v3.0) in the GitHub copy drkane/geo-lookups (commit e20a072). Uses the merged copy made by
the house-age study if present, otherwise downloads the attribute tables. Also copies that study's simplified LSOA TopoJSON
(data/lsoa.topo.json) and writes the LSOA code of each geometry in order (data/lsoa_codes.json)."""
import shutil, urllib.request
import pandas as pd
from common import *

RG = {"E12000001": "North East", "E12000002": "North West", "E12000003": "Yorkshire and The Humber",
      "E12000004": "East Midlands", "E12000005": "West Midlands", "E12000006": "East of England", "E12000007": "London",
      "E12000008": "South East", "E12000009": "South West"}
GPKG = "/home/claude/scratch/house-age/lsoa21_bgc.gpkg"
if os.path.exists(GPKG):
    import geopandas as gpd
    g = gpd.read_file(GPKG, ignore_geometry=True)
else:
    import geopandas as gpd
    base = "https://raw.githubusercontent.com/drkane/geo-lookups/e20a072d5fc0918437abaa3622be63f40b71d9dd/boundaries/lsoa/"
    parts = []
    for c in [f"E1200000{i}" for i in range(1, 10)] + [f"W060000{i:02d}" for i in range(1, 25)]:
        fn = os.path.join(SCR, c + ".geojson")
        try:
            urllib.request.urlretrieve(base + c + ".geojson", fn)
        except Exception:
            continue
        parts.append(gpd.read_file(fn, ignore_geometry=True)); os.remove(fn)
    g = pd.concat(parts).drop_duplicates("LSOA21CD")
g = g[["LSOA21CD", "LSOA21NM", "LADCD_ACTIVE", "RGNCD"]].rename(columns={"LSOA21CD": "lsoa", "LSOA21NM": "lsoa_name", "LADCD_ACTIVE": "lad"})
g["region"] = [("Wales" if l.startswith("W") else RG[r]) for l, r in zip(g.lsoa, g.RGNCD)]
g = g.drop(columns="RGNCD").sort_values("lsoa")
assert len(g) == 35672
g.to_csv(f"{DATA}/lsoa_lookup.csv", index=False)
shutil.copy(TOPO_SRC, f"{DATA}/lsoa.topo.json")
codes = jload(TOPO_CODES_SRC)["codes"]
assert len(codes) == 35672 and set(codes) == set(g.lsoa)
jsave(codes, f"{DATA}/lsoa_codes.json")
print(len(g), g.lad.nunique(), "LADs")
