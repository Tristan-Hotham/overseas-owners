"""Step 10: README.md, filled from data/results.json. https://doi.org/10.5281/zenodo.24115198 and https://blog.tristanhotham.com/2026/10/31/overseas-owners/ are left for the publisher."""
from common import *

R = jload(f"{DATA}/results.json"); x = R["x"]
t = f"""# Who owns your street?

**Property in England and Wales held by overseas companies, mapped for every small area.**

Dr Tristan Hotham · Independent researcher · 2026

- Interactive map: {PAGE}
- Paper (Zenodo): {{https://doi.org/10.5281/zenodo.24115198}}
- Blog post: {{https://blog.tristanhotham.com/2026/10/31/overseas-owners/}}
- Code and data: {REPO}

{HMLR}. Overseas companies that own property in England and Wales, data at {HMLR_DATE}.
Used under HM Land Registry's licence for non-commercial use. This repository contains **aggregate counts only**: no title
number, property address, postcode, proprietor address or row-level record from the dataset.

![Header](header.png)

## Headline results

- {R['n_titles']:,} titles in England and Wales are held by companies incorporated overseas: {R['ew_rate']:.2f} per 1,000 homes.
- Westminster ({x['westminster_rate']:.1f} per 1,000) and Kensington and Chelsea ({x['kc_rate']:.1f}) hold {R['westminster_kc_pc']:.1f}% of all titles with {R['westminster_kc_dw_pc']:.2f}% of homes. The City of London has the highest rate ({x['city_rate']:.0f}). Outside London the highest is Salford ({x['salford_rate']:.1f}).
- Titles are far more concentrated than homes: Gini {R['gini_titles']:.2f} across {R['n_lsoa']:,} LSOAs against {R['gini_dwellings']:.2f} for dwellings; half of all geocoded titles are in {R['half_titles_lsoas']:,} LSOAs ({R['half_titles_lsoas_pc']:.1f}%). Yet {R['pc_lsoa_with_any']:.1f}% of LSOAs have at least one.
- {R['pc_uko']:.1f}% of titles are held by companies from the Crown Dependencies and British Overseas Territories: Jersey {R['top_j'][0]['pc']:.1f}%, British Virgin Islands {R['top_j'][1]['pc']:.1f}%, Guernsey {R['top_j'][2]['pc']:.1f}%, Isle of Man {R['top_j'][3]['pc']:.1f}%.
- Within districts (PPML, district fixed effects, N = {R['main']['n']:,} LSOAs, {R['main']['clusters']} clusters), per 10 percentage points: top Council Tax bands rate ratio {R['main']['sh_high']['irr']:.3f} (95% CI {R['main']['sh_high']['lo']:.3f} to {R['main']['sh_high']['hi']:.3f}); flats {R['main']['sh_flat']['irr']:.3f} ({R['main']['sh_flat']['lo']:.3f} to {R['main']['sh_flat']['hi']:.3f}); built since 2009 {R['main']['sh_new']['irr']:.3f} ({R['main']['sh_new']['lo']:.3f} to {R['main']['sh_new']['hi']:.3f}). All {x['rob_n']} planned checks keep every interval above 1; the within-district placebo centres on 1.00.

Overseas ownership of property is legal. The register records legal owners, not beneficial owners, uses or motives.

## Files

| Path | What |
|---|---|
| `index.html`, `js/page.js` | Interactive map (MapLibre, OpenFreeMap Positron): LSOA rates with a jurisdiction filter, district view, search by place or postcode (postcodes.io) |
| `data/results.json` | Every number quoted anywhere |
| `data/lsoa_counts.csv` | Per LSOA 2021: dwellings, titles (all, UK-linked, Jersey, BVI, Guernsey, Isle of Man, other), rate, housing shares |
| `data/lad_counts.csv`, `data/region_counts.csv` | Per district and region: titles (including those without a postcode), rate, rank, UK-linked share, most common jurisdiction, median price where at least 10 titles have one |
| `data/jurisdictions.csv`, `data/years.csv`, `data/prices.csv`, `data/holders.csv` | Titles by jurisdiction (with FSI 2018 score), by year owner added, price summaries, ten largest holders |
| `data/models.csv` | All model estimates |
| `data/lsoa_voa.csv`, `data/lsoa_lookup.csv`, `data/lad_names.csv` | VOA dwellings and housing shares by LSOA; LSOA to district lookup (OGL) |
| `data/lsoa.topo.json`, `data/lsoa_codes.json`, `data/lad.geojson`, `data/site*.json` | Page data |
| `release/paper/` | Paper (PDF, LaTeX, figures), cover note |
| `release/blog/` | Blog post (WordPress blocks), figures, meta |
| `release/zenodo/` | Paper PDF, data and code zip, metadata |
| `reddit/` | Collage, `collage.py`, GIF, `post.md` |
| `NOTES.md` | Analysis plan (written before any counts) and log |

## Method

Titles are placed in LSOAs by postcode ({R['n_geocoded']:,}, {R['pc_geocoded']:.1f}%); the other {x['n_no_lsoa']:,} enter district totals through the file's district field. Denominator: dwellings on the Council Tax list, 31 March 2025 (VOA CTSOP4.1). Jurisdictions are cleaned from free text; UK-linked offshore = Crown Dependencies and British Overseas Territories (fixed in advance). The within-district model is Poisson pseudo-maximum likelihood with district fixed effects, an offset for log dwellings and standard errors clustered by district. Robustness: negative binomial, leave one region out, without Westminster and Kensington and Chelsea, single-address, residential-looking, leasehold and freehold titles, suppressed VOA cells as 2.5, region fixed effects, and a 200-draw within-district placebo. The analysis was pre-specified in a written plan (NOTES.md).

## Sources and licences

- {HMLR}. HM Land Registry, Overseas companies that own property in England and Wales, full file, {HMLR_DATE}. Non-commercial licence; aggregates only.
- Valuation Office Agency (2025) Council Tax: stock of properties, tables CTSOP3.1 and CTSOP4.1. Open Government Licence v3.0.
- ONS LSOA 2021 and LAD 2023 boundaries (OGL v3.0; contains OS data © Crown copyright and database right), LSOAs via github.com/drkane/geo-lookups. postcodes.io (ONS Postcode Directory, OGL v3.0).
- Tax Justice Network, Financial Secrecy Index 2018 secrecy scores, via github.com/Global-Witness/secret-property-analysis-2019-public.
- Wikidata (CC0) for search places; OpenFreeMap / OpenStreetMap (ODbL) base map.
- Licences: code MIT; text CC BY 4.0; figures and derived data non-commercial (CC BY-NC 4.0 and HM Land Registry's terms). See LICENSE.

## Rerun

The HM Land Registry file is not included; obtain it from HM Land Registry (https://use-land-property-data.service.gov.uk/) under its licence and set `OO_RAW`.

```
cd code
python3 00_lookup.py && python3 01_prepare.py && OO_DASH=2.5 python3 01_prepare.py
python3 02_analysis.py && python3 02b_exploratory.py && python3 03_results.py
python3 04_figures.py && python3 05_site_data.py && python3 06_site.py
python3 07_paper.py        # DOI=10.5281/zenodo.N python3 07_paper.py to fill the DOI
python3 08_header.py && python3 ../reddit/collage.py && python3 10_readme.py && python3 09_release.py
```

## Cite

Hotham, T. (2026) Who owns your street? The small-area geography of property in England and Wales held by overseas companies. Zenodo. {{https://doi.org/10.5281/zenodo.24115198}}

{AI}
"""
for bad in ("—", "–", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in t, bad
open(f"{ROOT}/README.md", "w", encoding="utf-8").write(t)
print("README", len(t.split()), "words")
