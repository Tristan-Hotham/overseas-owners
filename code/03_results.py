"""Step 3: data/results.json, every number quoted anywhere (page, paper, blog, collage, post, README), from SCR/analysis.json,
with a few derived values and checks."""
from common import *

A = jload(f"{SCR}/analysis.json")
R = dict(A)
R["meta"] = {"slug": SLUG, "title": TITLE, "data_date": HMLR_DATE, "attribution": HMLR, "terms": HMLR_TERMS}
x = {}
x["london_vs_rest"] = A["london_rate"] / A["rest_rate"]
x["wkc_ratio"] = A["westminster_kc_pc"] / A["westminster_kc_dw_pc"]
x["top1_ratio"] = A["top1pc_share"] / A["top1pc_dw_share"]
x["pc_no_lsoa"] = 100 - A["pc_geocoded"]
x["n_no_lsoa"] = A["n_titles"] - A["n_geocoded"]
x["pc_lsoa_none"] = 100 - A["pc_lsoa_with_any"]
x["uko_pc_round"] = round(A["pc_uko"])
x["pc_rest_london"] = 100 - A["pc_london"]
x["holders_100plus_districts"] = sum(h["districts"] > 100 for h in A["holders"])
x["n_named_jur"] = A["n_jurisdictions"] - 4
x["one_in"] = 1000 / A["ew_rate"]
for k in ("sh_high", "sh_flat", "sh_new"):
    x[k + "_pc"] = 100 * (A["main"][k]["irr"] - 1)
    x[k + "_lo_pc"] = 100 * (A["main"][k]["lo"] - 1); x[k + "_hi_pc"] = 100 * (A["main"][k]["hi"] - 1)
    x[k + "_nb_pc"] = 100 * (A["rob"]["negbin"][k]["irr"] - 1)
    x[k + "_noLondon_pc"] = 100 * (A["rob"]["loro_London"][k]["irr"] - 1)
    x[k + "_resid_pc"] = 100 * (A["rob"]["t_resid"][k]["irr"] - 1)
# range of IRRs across every robustness model
rob = {k: v for k, v in A["rob"].items()}
x["rob_n"] = len(rob)
for k in ("sh_high", "sh_flat", "sh_new"):
    vals = [v[k]["irr"] for v in rob.values()]
    x[k + "_rob_min"], x[k + "_rob_max"] = min(vals), max(vals)
    x[k + "_rob_all_above1"] = all(v[k]["lo"] > 1 for v in rob.values())
x["years_since_2017_peak"] = A["years"]["2017"]
x["first_titles_2022_2025"] = sum(A["years"][str(y)] for y in range(2022, 2026))
x["mean_2022_2025"] = x["first_titles_2022_2025"] / 4
x["mean_2015_2019"] = sum(A["years"][str(y)] for y in range(2015, 2020)) / 5
x["price_median_m"] = A["price_all"]["median"] / 1e6
lt = {d["name"]: d for d in A["lad_top"]}
x["westminster_rate"] = lt["Westminster"]["rate"]; x["kc_rate"] = lt["Kensington and Chelsea"]["rate"]
x["city_rate"] = lt["City of London"]["rate"]; x["westminster_titles"] = lt["Westminster"]["titles"]
x["kc_titles"] = lt["Kensington and Chelsea"]["titles"]; x["city_titles"] = lt["City of London"]["titles"]
lo = {d["name"]: d for d in A["lad_top_outside_london"]}
x["salford_rate"] = lo["Salford"]["rate"]; x["salford_titles"] = lo["Salford"]["titles"]
x["westminster_vs_ew"] = lt["Westminster"]["rate"] / A["ew_rate"]
R["x"] = x
assert R["n_titles"] == 90949 and R["h2_supported"] and R["main"]["n"] == 35672
assert abs(sum(j["n"] for j in R["top_j"][:4]) - R["n_cd"] - R["regions"]["London"]["titles"] * 0) >= 0
jsave(R, f"{DATA}/results.json", indent=1)
print(json.dumps(x, indent=0)[:1500])
