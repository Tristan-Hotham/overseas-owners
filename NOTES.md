# overseas-owners: working notes and analysis plan

"Who owns your street? Property in England and Wales held by overseas companies". Author Dr Tristan Hotham, Independent researcher.

## Status

- Step 1 (this section, written first): the analysis plan below is pre-specified in a written plan, fixed after reading only the
  column names of the HM Land Registry file (39 columns, including `Date Proprietor Added`) and the VOA table layout, and before
  any counts, rates, jurisdictions or models were computed. Anything added later is labelled exploratory in the log and paper.

## Licence (binding)

HM Land Registry "Overseas companies that own property in England and Wales" (OCOD), full file, November 2026, used under the
HMLR licence for personal, non-commercial research. The Information may not be published as a whole or in part as a standalone
product. So: **no title numbers, property addresses, postcodes, proprietor addresses or row-level tables anywhere** (data/,
release zip, map, GIF, collage, blog, paper). Only aggregates are published: counts and price-paid summaries by LSOA, local
authority district (LAD), region, jurisdiction of incorporation, tenure and year of registration. Company names appear only in a
short "largest holders" chart (proprietors by number of titles; companies, not private individuals; no addresses). Every output
carries: "Information produced by HM Land Registry © Crown copyright 2026" and the data date, November 2026. The raw zip is read
where it sits and never copied; the release zip contains code, not the raw file.

## Data

- OCOD full file, November 2026 (one row per registered title held by an overseas company; up to four proprietors each).
- Postcode geocodes for every unique postcode in the file (postcodes.io lookups: lat, lon, LSOA 2021, LAD, region; supplied by
  the lead). Used only to assign titles to LSOAs and LADs; never published.
- Denominator: VOA Council Tax: stock of properties 2025, table CTSOP4.1 (dwellings by band and build period by LSOA 2021, at
  31 March 2025) and CTSOP3.1 (property type), Official Statistics, OGL v3.0.
- LSOA 2021 boundaries: ONS generalised clipped, OGL v3.0, via the GitHub copy drkane/geo-lookups (commit
  e20a072d5fc0918437abaa3622be63f40b71d9dd), simplified TopoJSON shared with the house-age study. LAD boundaries: ONS LAD
  December 2023 BGC (OGL v3.0).

## Definitions fixed in advance

- **Title**: one row of the file. Titles are legal registrations, not dwellings: a title can be a flat, a house, a shop, an office
  block, a plot of land or several properties (Multiple Address Indicator). Every result is stated in titles.
- **Place of a title**: the LSOA and LAD of its postcode. Titles without a postcode (often land or multiple properties) are
  assigned to the LAD named in the `District` field and enter district totals but not the LSOA analysis.
- **Jurisdiction**: `Country Incorporated (1)` (first proprietor), cleaned for spelling variants. A secondary measure counts a
  title for every distinct jurisdiction among its proprietors.
- **UK-linked offshore jurisdictions** (classification fixed now, constitutional fact): the Crown Dependencies (Jersey, Guernsey
  including Alderney and Sark, Isle of Man) and the British Overseas Territories (British Virgin Islands, Cayman Islands, Bermuda,
  Gibraltar, Anguilla, Turks and Caicos Islands, Montserrat, and any other listed). Where the Tax Justice Network Financial
  Secrecy Index secrecy scores can be obtained from a citable copy, jurisdictions are also split at a secrecy score of 65
  (secondary, descriptive only); if not, only the constitutional classification is used.
- **Rate**: titles per 1,000 dwellings (VOA all properties, 2025).
- **Residential-looking title** (measurement check only): property address contains flat, apartment, maisonette, studio or
  penthouse. Address text is used internally only and never written out.

## Hypotheses and models

- **H1 (concentration).** Overseas-company titles are far more concentrated than dwellings. Pre-specified measures: share of all
  titles in London; Gini coefficient of titles across LSOAs compared with that of dwellings; share of titles in the top 1% of
  LSOAs by count; the ten LADs with the highest rate. Expectation: Westminster and Kensington and Chelsea have the two highest
  district rates. Against H1: a titles Gini close to the dwellings Gini, or Westminster and Kensington and Chelsea not in the top
  five.
- **H2 (jurisdictions).** More than half of titles are held by companies incorporated in the UK-linked offshore jurisdictions
  defined above. Against H2: 50% or less. Reported with counts for each jurisdiction (top 15).
- **H3 (where within districts, main model).** Within the same district, overseas-company titles are more common in LSOAs with
  (a) a larger share of dwellings in the top Council Tax bands (England F to H; Wales G to I), (b) a larger share of flats and
  maisonettes, (c) a larger share of dwellings built in 2009 or later. Model: Poisson pseudo-maximum likelihood (PPML), LSOA title
  count ~ high-band share + flat share + new-build share (each per 10 percentage points), offset log(dwellings), LAD fixed
  effects, standard errors clustered by LAD. Report incidence rate ratios (IRR) with 95% CI and N. Against H3 for each component:
  IRR at or below 1 or CI including 1. LSOAs with fewer than 50 dwellings or no VOA data are dropped (count reported).
- **H3s (secondary).** The same model fitted separately to UK-linked offshore titles and to all other jurisdictions, and a pooled
  model with a jurisdiction-group interaction, to test whether the high-band gradient differs.
- **D1 (descriptive, time).** Titles by year in which the current proprietor was added. This is the age profile of current
  holdings (survivorship: titles sold on are gone), not a flow of purchases. Note the Register of Overseas Entities (in force
  from 1 August 2022) without causal claims.
- **D2 (descriptive, price).** Median and quartiles of price paid where stated, by jurisdiction group, tenure and region; LAD
  medians only where at least 10 titles have a price.
- **D3 (descriptive).** Largest holders: the 10 proprietors (first-named) with most titles, with their jurisdiction. Neutral
  wording; overseas ownership is legal.

## Robustness (all fixed now)

1. Alternative specification: negative binomial (NB2) with the same terms and LAD fixed effects.
2. Leave one region out (each of the 10 regions incl. Wales); drop London.
3. Drop Westminster and Kensington and Chelsea.
4. Measurement: (a) single-address titles only (Multiple Address Indicator = N); (b) residential-looking titles only;
   (c) leasehold only and freehold only; (d) VOA suppressed cells counted as 2.5 instead of 0 in the shares.
5. Falsification (placebo): within each LAD reallocate its titles across its LSOAs at random in proportion to dwellings
   (multinomial), re-estimate the main model 200 times (seed 2026). The placebo IRRs should centre on 1; report where the
   observed IRR falls in that distribution.
6. Region fixed effects instead of LAD fixed effects (shows how much the within-district design matters).

## Caveats to state

Titles, not homes; OCOD covers companies incorporated overseas (UK companies owned from abroad and individuals are not in it);
a snapshot of November 2026; price paid is often blank and is the price at registration, not today's value; postcodes can be
missing or cover a large estate; Council Tax bands reflect 1991 (England) and 2003 (Wales) values; all results are associations
within districts, not effects.

## Log
- 2026: plan above written first. Then: data prepared (01). OCOD has 90,950 rows; 1 malformed row (no tenure, no proprietor)
  dropped, leaving 90,949 titles. 66,913 titles (73.6%) have a postcode that geocodes to an LSOA; 21,669 have no postcode and
  2,367 have a postcode postcodes.io could not find (terminated or mistyped). Those 24,036 are placed in a district from the
  `District` field (modal LAD of the geocoded titles with the same District value); none is left without a district.
- Jurisdictions: 207 raw values of the first proprietor's jurisdiction cleaned to 136 values: 131 named jurisdictions, four vague labels (Channel Islands, The Virgin Islands, The West Indies, a European Union body) and Not stated (US states to United States, Canadian provinces to Canada,
  emirates and free zones to the UAE, Alderney to Guernsey, "Channel Islands" kept as unspecified Crown Dependency; 2 titles
  "The Virgin Islands" kept as unspecified and not counted as UK-linked; 2 titles with no or invalid jurisdiction "Not stated"; "The West Indies" also kept unspecified).
- FSI: the 2025 FSI table is not on GitHub; the 2018 edition is (Global Witness repo copy). Used only for the secondary,
  descriptive split (matched for 97.9% of titles; the UAE is not in the 2018 table).
- NB model: statsmodels with 318 dummies ran out of memory on the shared machine; replaced by an exact IRLS with weighted
  within-district demeaning (code/ppml.py `fenb`), alpha by profile likelihood. The PPML estimator in ppml.py was checked
  against statsmodels GLM with dummies (identical to 1e-5).
- Results (planned): H1 supported (titles Gini 0.87 vs dwellings 0.14; Westminster 2nd and Kensington and Chelsea 3rd by rate;
  the City of London is 1st, so the expectation that they would be the two highest was wrong in detail). H2 supported (75.7%
  UK-linked offshore). H3 supported for all three components; every robustness model keeps all three CIs above 1; placebo
  IRRs centre on 1.00 (95% range 0.995 to 1.006). H3s: the high-band and flat gradients are somewhat weaker for UK-linked
  offshore titles than for other jurisdictions (interaction IRRs 0.93 and 0.92).
- Exploratory (labelled as such, 02b): top LSOAs are often single developments sold as many units; in 4 of the 10 highest-rate
  LSOAs one proprietor holds more than half the titles; 11.3% of geocoded titles sit in blocks of 20+ titles held by one
  proprietor in one LSOA.
- Outputs built: figures (04), page data and page (05, 06), paper (07; 20 pages, abstract 231 words), header (08), release
  (09: blog 7 figures, meta, Zenodo zip with code and aggregates only, metadata licence cc-by-nc-4.0 because the derived
  data are non-commercial), README (10), collage and post, GIF (/home/claude/gifs/scripts/overseas-owners.py).
- Licence check: data/, release zip, page, blog, collage and GIF contain only area, jurisdiction, year and price-group
  aggregates and the ten largest holders' company names; a regex scan for postcodes in the shipped files finds none.
- References: every item in the paper's list was checked online in 2026 (econpapers/RePEc, publisher, arXiv, NBER,
  legislation.gov.uk, TI UK pages). The Trust for London "tax haven money" report could not be fetched and is not cited.
- Scratch (/home/claude/scratch/overseas-owners: titles.parquet, LSOA shapes, FSI copy, analysis.json) deleted when done;
  rerunning needs the house-age LSOA GeoPackage or the topojson fallback in code/topojson_util.py.
