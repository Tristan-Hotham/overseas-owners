"""Step 2b (exploratory, added after the planned results were seen): how much of the local concentration comes from single
proprietors holding many titles in one place (for example a building sold as separate units). Adds keys to SCR/analysis.json.
No proprietor is named here."""
import numpy as np, pandas as pd
from common import *

A = jload(f"{SCR}/analysis.json")
T = pd.read_parquet(f"{SCR}/titles.parquet")
G = T[T.how == "postcode"]
o = G.groupby(["lsoa", "owner"]).size().rename("n").reset_index()
mx = o.groupby("lsoa").n.max(); tot = o.groupby("lsoa").n.sum()
E = {}
E["top10_lsoa_max_owner_pc"] = [float(100 * mx[x["lsoa"]] / tot[x["lsoa"]]) for x in A["lsoa_top"]]
E["top10_lsoa_single_owner_majority"] = int(sum(v >= 50 for v in E["top10_lsoa_max_owner_pc"]))
# titles held by a proprietor with 20 or more titles in the same LSOA
big = o[o.n >= 20]
E["titles_in_blocks20"] = int(big.n.sum()); E["pc_titles_in_blocks20"] = 100 * big.n.sum() / len(G)
E["lsoas_with_block20"] = int(big.lsoa.nunique())
H = T.groupby("owner").size()
E["pc_titles_owners_100plus"] = float(100 * H[H >= 100].sum() / len(T)); E["owners_100plus"] = int((H >= 100).sum())
E["median_titles_per_owner"] = float(H.median()); E["mean_titles_per_owner"] = float(H.mean())
# share of titles that look residential, by region (London vs rest)
E["pc_resid_london"] = float(100 * T[T.region == "London"].resid.mean()); E["pc_resid_rest"] = float(100 * T[T.region != "London"].resid.mean())
A["explore"] = E
jsave(A, f"{SCR}/analysis.json", indent=1)
print(E)
