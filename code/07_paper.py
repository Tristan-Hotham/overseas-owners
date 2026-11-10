"""Step 7: the paper. Fills code/paper_template.tex from data/results.json and the aggregate tables, compiles with xelatex.
Output: release/paper/Hotham_Who_Owns_Your_Street.pdf and .tex. The DOI stays the placeholder https://doi.org/10.5281/zenodo.24115198 unless the
environment variable DOI is set:  DOI=10.5281/zenodo.N python3 code/07_paper.py"""
import subprocess, pandas as pd
from common import *

R = jload(f"{DATA}/results.json")
OUT = os.path.join(REL, "paper"); NAME = "Hotham_Who_Owns_Your_Street"
LD = pd.read_csv(f"{DATA}/lad_counts.csv"); J = pd.read_csv(f"{DATA}/jurisdictions.csv"); RG = pd.read_csv(f"{DATA}/region_counts.csv")
def tex(s): return str(s).replace("&", "\\&").replace("%", "\\%").replace("_", "\\_").replace("#", "\\#")
def ci(c, d=3): return f"{c['irr']:.{d}f} [{c['lo']:.{d}f}, {c['hi']:.{d}f}]"
P = R["prep"]
TD = ("\\begin{table}[tbp]\\centering\\small\\caption{Data flow.}\\label{tab:data}\\begin{tabular}{lr}\\toprule Item & Number\\\\\\midrule\n"
      f"Rows in the HM Land Registry file (November 2026) & {P['rows_raw']:,}\\\\\n\\quad malformed row dropped & {P['malformed']:,}\\\\\n"
      f"Titles & {R['n_titles']:,}\\\\\n\\quad freehold / leasehold & {R['n_freehold']:,} / {R['n_leasehold']:,}\\\\\n"
      f"\\quad flagged multiple address & {R['n_multi']:,}\\\\\n\\quad with a price paid & {R['n_price']:,}\\\\\n"
      f"\\quad postcode matched to an LSOA & {R['n_geocoded']:,}\\\\\n\\quad no postcode (district only) & {R['how']['no postcode']:,}\\\\\n"
      f"\\quad postcode not found (district only) & {R['how']['postcode not found']:,}\\\\\n"
      f"Distinct first-named proprietors & {R['n_owners']:,}\\\\\nNamed jurisdictions & {R['x']['n_named_jur']:,}\\\\\\midrule\n"
      f"LSOAs (England and Wales, 2021) & {R['n_lsoa']:,}\\\\\nDistricts & {R['main']['clusters']:,}\\\\\n"
      f"Dwellings (VOA, 31 March 2025) & {R['n_dwellings']:,}\\\\\\bottomrule\\end{{tabular}}\\end{{table}}")
rows = "".join(f"{r['rank']} & {tex(r.lad_name)} & {tex(r.region)} & {int(r.titles):,} & {int(r.dwellings):,} & {r.rate:.1f} & {r.pc_uko:.0f}\\\\\n" for _, r in LD.head(20).iterrows())
TL = ("\\begin{table}[tbp]\\centering\\small\\caption{The 20 districts with the highest rates of overseas-company titles per 1,000 dwellings. "
      "UK-linked: share of titles held from the Crown Dependencies and Overseas Territories.}\\label{tab:lad}"
      "\\begin{tabular}{rllrrrr}\\toprule & District & Region & Titles & Dwellings & Per 1,000 & UK-linked \\%\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
rows = "".join(f"{tex(r.jurisdiction)} & {tex(r.uk_link) if isinstance(r.uk_link, str) else ''} & {int(r.titles):,} & {r.share:.1f} & "
               f"{'' if pd.isna(r.fsi2018_secrecy) else f'{r.fsi2018_secrecy:.1f}'}\\\\\n" for _, r in J[J.jurisdiction != 'Not stated'].head(15).iterrows())
TJ = ("\\begin{table}[tbp]\\centering\\small\\caption{The 15 most common jurisdictions of incorporation (first-named proprietor), with the 2018 Financial Secrecy Index secrecy score.}\\label{tab:jur}"
      "\\begin{tabular}{llrrr}\\toprule Jurisdiction & UK link & Titles & \\% & FSI 2018 score\\\\\\midrule\n" + rows +
      f"\\midrule All Crown Dependencies and Overseas Territories & & {R['n_uko']:,} & {R['pc_uko']:.1f} & \\\\\n\\bottomrule\\end{{tabular}}\\end{{table}}")
TERMS = [("sh_high", "Top Council Tax bands (per 10 points)"), ("sh_flat", "Flats and maisonettes (per 10 points)"), ("sh_new", "Built 2009 or later (per 10 points)")]
cols = [("Main", R["main"]), ("Univariate", None), ("UK-linked", R["m_uko"]), ("Elsewhere", R["m_other"]), ("Interaction", R["m_stacked"])]
rows = ""
for k, lab in TERMS:
    cells = [ci(R["main"][k]), ci(R["uni"][k]), ci(R["m_uko"][k]), ci(R["m_other"][k]), ci(R["m_stacked"][k + "_x"])]
    rows += f"{lab} & " + " & ".join(cells) + "\\\\\n"
rows += f"N (LSOAs) & {R['main']['n']:,} & {R['main']['n']:,} & {R['m_uko']['n']:,} & {R['m_other']['n']:,} & {R['m_stacked']['n']:,}\\\\\n"
rows += f"Districts (clusters) & {R['main']['clusters']} & {R['main']['clusters']} & {R['m_uko']['clusters']} & {R['m_other']['clusters']} & {R['m_stacked']['clusters']}\\\\\n"
TM = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Overseas-company titles per dwelling and the housing stock of the LSOA: incidence rate ratios per 10 percentage points [95\\% CI]. "
      "PPML with district fixed effects (district by jurisdiction group in the interaction model), offset log dwellings, standard errors clustered by district. "
      "Univariate: each share alone. UK-linked and Elsewhere: titles from those jurisdiction groups only. Interaction: ratio of the UK-linked to the Elsewhere gradient in a stacked model. "
      "Districts with no titles in a group drop out of that model.}\\label{tab:main}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lccccc}\\toprule & Main & Univariate & UK-linked & Elsewhere & Interaction\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
LAB = {"region_fe": "Region instead of district fixed effects", "negbin": "Negative binomial (NB2), district fixed effects",
       "no_wkc": "Without Westminster and Kensington and Chelsea", "t_single": "Single-address titles only", "t_resid": "Residential-looking titles only",
       "t_lease": "Leasehold titles only", "t_free": "Freehold titles only", "dash25": "VOA suppressed cells as 2.5"}
rows = f"Main model & {ci(R['main']['sh_high'], 2)} & {ci(R['main']['sh_flat'], 2)} & {ci(R['main']['sh_new'], 2)} & {R['main']['n']:,}\\\\\\midrule\n"
for k, v in R["rob"].items():
    lab = LAB.get(k) or ("Without " + k.replace("loro_", ""))
    rows += f"{tex(lab)} & {ci(v['sh_high'], 2)} & {ci(v['sh_flat'], 2)} & {ci(v['sh_new'], 2)} & {v.get('n', R['main']['n']):,}\\\\\n"
pl = R["placebo"]
rows += "\\midrule " + f"Placebo: mean [2.5th, 97.5th percentile] of 200 draws & " + " & ".join(
    f"{pl[k]['mean']:.3f} [{pl[k]['p2_5']:.3f}, {pl[k]['p97_5']:.3f}]" for k in ("sh_high", "sh_flat", "sh_new")) + f" & {R['main']['n']:,}\\\\\n"
TR = ("\\begin{table}[tbp]\\centering\\footnotesize\\caption{Robustness: incidence rate ratios per 10 percentage points [95\\% CI] under each planned check.}\\label{tab:robust}"
      "\\resizebox{\\textwidth}{!}{\\begin{tabular}{lcccr}\\toprule Check & Top bands & Flats & Built 2009 or later & N\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}}\\end{table}")
rows = "".join(f"{tex(r.region)} & {int(r.titles):,} & {r.share:.1f} & {int(r.dwellings):,} & {r.rate:.2f} & {r.pc_uko:.1f} & {'' if pd.isna(r.median_price) else f'{r.median_price:,.0f}'}\\\\\n" for _, r in RG.iterrows())
TG = ("\\begin{table}[htbp]\\centering\\small\\caption{Titles by region (all titles, including those placed by district only).}\\label{tab:region}"
      "\\begin{tabular}{lrrrrrr}\\toprule Region & Titles & \\% & Dwellings & Per 1,000 & UK-linked \\% & Median price (\\pounds)\\\\\\midrule\n" + rows + "\\bottomrule\\end{tabular}\\end{table}")
t = open(f"{CODE}/paper_template.tex", encoding="utf-8").read()
for k, v in (("TABLE_DATA", TD), ("TABLE_LAD", TL), ("TABLE_JUR", TJ), ("TABLE_MAIN", TM), ("TABLE_ROBUST", TR), ("TABLE_REGION", TG)):
    t = t.replace("{{" + k + "}}", v)
t = t.replace("{{AI}}", AI)
doi = os.environ.get("DOI")
t = re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in ("DOI", "DOI_URL", "BLOG_URL")
           else fmt(get(R, m.group(1)), m.group(3)).replace("%", "\\%").replace("£", "\\pounds{}"), t)
t_out = t.replace("https://doi.org/10.5281/zenodo.24115198", f"https://doi.org/{doi}" if doi else "\\{\\{DOI\\_URL\\}\\}")
assert "{{" not in t_out.replace("\\{\\{DOI\\_URL\\}\\}", ""), re.findall(r"\{\{[^}]*\}\}", t_out)[:5]
for bad in ("—", "–", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in t_out, bad
os.makedirs(OUT, exist_ok=True)
open(f"{OUT}/{NAME}.tex", "w", encoding="utf-8").write(t_out)
for _ in range(2):
    r = subprocess.run(["xelatex", "-interaction=nonstopmode", f"{NAME}.tex"], cwd=OUT, capture_output=True, text=True)
log = open(f"{OUT}/{NAME}.log", encoding="utf-8", errors="ignore").read()
print("undefined refs:", log.count("undefined"), "| pages:", re.findall(r"Output written on .*?\((\d+) pages", log))
print([l for l in log.splitlines() if l.startswith("!")][:5])
for e in ("aux", "log", "out"):
    p = f"{OUT}/{NAME}.{e}"
    if os.path.exists(p): os.remove(p)
txt = subprocess.run(["pdftotext", f"{OUT}/{NAME}.pdf", "-"], capture_output=True, text=True).stdout
body = txt.split("References")[0] if "References" in txt else txt
print("words (whole pdf):", len(txt.split()), "| before references:", len(body.split()))
ab = re.search(r"Abstract(.*?)Keywords", txt, re.S)
print("abstract words:", len(ab.group(1).split()) if ab else None)
