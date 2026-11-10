"""Shared paths, constants and helpers for overseas-owners ("Who owns your street?").

Inputs (read where they sit, never copied into the study):
  OCOD_ZIP   HM Land Registry, Overseas companies that own property in England and Wales (OCOD), full file, November 2026.
             Information produced by HM Land Registry (c) Crown copyright 2026. Used under the HMLR licence for personal,
             non-commercial research: only aggregates leave this pipeline (no title numbers, addresses or postcodes).
  PC_CSV     postcodes.io geocodes for every unique OCOD postcode (lat, lon, LSOA 2021, LAD, region), supplied with the
             raw data. Used only to place titles in LSOAs and districts.
  VOA        Valuation Office Agency, Council Tax: stock of properties 2025, tables CTSOP4.1 (band x build period) and
             CTSOP3.1 (band x property type), LSOA 2021, 31 March 2025. Official Statistics, OGL v3.0.
  TOPO       LSOA 2021 boundaries (ONS BGC, OGL v3.0, GitHub copy drkane/geo-lookups commit e20a072), simplified TopoJSON
             built by the house-age study; data/lsoa_codes.json gives the LSOA code of each geometry in order.
  GEO        ONS LAD December 2023 BGC boundaries (OGL v3.0); Natural Earth land (public domain).
  FSI_CSV    Tax Justice Network Financial Secrecy Index 2018 secrecy scores, from the copy in Global-Witness/
             secret-property-analysis-2019-public (data/processed/financial_secrecy_index_2018.csv), in scratch.
"""
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CODE = os.path.join(ROOT, "code")
DATA = os.path.join(ROOT, "data")
IMG = os.path.join(ROOT, "img")
REL = os.path.join(ROOT, "release")
SCR = os.environ.get("OO_SCRATCH", "/home/claude/scratch/overseas-owners")
RAW = os.environ.get("OO_RAW", "/home/claude/newdata/raw_new14")
OCOD_ZIP = os.path.join(RAW, "ocod", "OCOD_FULL_2026_11.zip")
PC_CSV = os.path.join(RAW, "ocod", "ocod_postcodes.csv")
VOA = os.path.join(RAW, "houseage")
TOPO_SRC = os.environ.get("OO_TOPO", "/home/claude/studies/house-age/data/lsoa.topo.json")
TOPO_CODES_SRC = os.environ.get("OO_TOPO_CODES", "/home/claude/studies/house-age/data/site_lsoa.json")
GEO = os.environ.get("OO_GEO", "/home/claude/newdata/raw/geo")
FONTS = os.environ.get("OO_FONTS", "/home/claude/ref/fonts")
FSI_CSV = os.path.join(SCR, "fsi", "fsi2018.csv")
FSI_URL = ("https://raw.githubusercontent.com/Global-Witness/secret-property-analysis-2019-public/master/"
           "data/processed/financial_secrecy_index_2018.csv")
for d in (DATA, IMG, SCR):
    os.makedirs(d, exist_ok=True)

SLUG = "overseas-owners"
TITLE = "Who owns your street?"
SUBTITLE = "Property in England and Wales held by overseas companies"
PAGE = f"https://maps.tristanhotham.com/{SLUG}/"
REPO = f"https://github.com/Tristan-Hotham/{SLUG}"
AI = ("I wrote the text, with drafting and editing assistance from Claude (Anthropic), which also helped "
      "prepare the analysis code. I reviewed and checked all text and results.")
BYLINE = "Dr Tristan Hotham · Independent researcher · 2026"
HMLR = "Information produced by HM Land Registry © Crown copyright 2026"
HMLR_DATE = "November 2026"
HMLR_FULL = f"{HMLR}. Overseas companies that own property in England and Wales, data as at {HMLR_DATE}."
HMLR_TERMS = ("Used under the HM Land Registry licence for personal, non-commercial use. Only aggregate counts are "
              "published here; no title, address or postcode is reproduced.")

# --- jurisdictions -------------------------------------------------------------------------------------------------
UKO = {  # UK-linked offshore jurisdictions: Crown Dependencies and British Overseas Territories
    "Jersey": "Crown Dependency", "Guernsey": "Crown Dependency", "Isle of Man": "Crown Dependency",
    "Channel Islands (unspecified)": "Crown Dependency",
    "British Virgin Islands": "Overseas Territory", "Cayman Islands": "Overseas Territory", "Bermuda": "Overseas Territory",
    "Gibraltar": "Overseas Territory", "Anguilla": "Overseas Territory", "Turks and Caicos Islands": "Overseas Territory",
    "Montserrat": "Overseas Territory",
}
FIX = {
    "ALDERNEY": "Guernsey", "CHANNEL ISLANDS": "Channel Islands (unspecified)",
    "DUBAI": "United Arab Emirates", "ABU DHABI": "United Arab Emirates", "SHARJAH": "United Arab Emirates",
    "AJMAN": "United Arab Emirates", "AJMAN FREE ZONE": "United Arab Emirates", "RAS AL KHAIMAH": "United Arab Emirates",
    "RAS AL KHAIMAH FREE TRADE ZONE": "United Arab Emirates", "JEBEL ALI FREE ZONE": "United Arab Emirates",
    "MACAO": "Macau", "KOREA": "South Korea", "REPUBLIC OF KOREA": "South Korea", "THE REPUBLIC OF KOREA": "South Korea",
    "WESTERN SAMOA": "Samoa", "SAMAO": "Samoa", "NUIE": "Niue", "THE ISLAND OF NIUE": "Niue",
    "LABUAN, MALAYSIA": "Malaysia", "PENANG": "Malaysia", "THE REPUBLIC OF LIBE RIA": "Liberia",
    "UNITED REPUBLIC OF TANZANIA": "Tanzania", "THE GAMBIA": "Gambia", "DUTCH ANTILLES": "Netherlands Antilles",
    "CURACAO": "Curaçao", "CHONBURI": "Thailand", "HAMBURG": "Germany", "BREDA": "Netherlands",
    "ROVEREDO GR": "Switzerland", "TENERIFE": "Spain", "SWAZILAND": "Eswatini", "NORTH CYPRUS": "Northern Cyprus",
    "COTE D'IVOIRE": "Côte d'Ivoire", "U.S.A.": "United States", "ST KITTS AND NEVIS": "St Kitts and Nevis",
    "ST VINCENT AND GRENADINES": "St Vincent and the Grenadines", "ST LUCIA": "St Lucia",
    "THE EUROPEAN UNION": "European Union body",
    "EUROPE UNDER THE TREATY ON EUROPEAN UNION AND THE TREATY ON THE FUNCTIONING OF THE EUROPEAN UNION": "European Union body",
    "THE EUROPEAN UNION UNDER THE TREATY ON EUROPEAN UNION AND THE TREATY ON THE FUNCTIONING OF THE EUROPEAN UNION": "European Union body",
    "THE VIRGIN ISLANDS": "Virgin Islands (unspecified)", "THE WEST INDIES": "West Indies (unspecified)",
    "1811435": "Not stated", "PART VII OF THE CHARITIES ACT 1993": "Not stated", "": "Not stated",
}
SMALLWORDS = {"and", "of", "the"}


def clean_country(s):
    s = str(s).strip()
    if s in FIX:
        return FIX[s]
    if s.endswith(", U.S.A."):
        return "United States"
    if s.endswith(", CANADA"):
        return "Canada"
    t = " ".join(w if w.lower() not in SMALLWORDS else w.lower() for w in s.title().split())
    return t[0].upper() + t[1:] if t else "Not stated"


def group_of(c):
    return "UK-linked offshore" if c in UKO else ("Not stated" if c == "Not stated" else "Elsewhere")


# --- helpers -------------------------------------------------------------------------------------------------------
def nonan(v):
    if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))):
        return None
    if isinstance(v, (list, tuple)):
        return [nonan(x) for x in v]
    if isinstance(v, dict):
        return {str(k): nonan(x) for k, x in v.items()}
    if hasattr(v, "item"):
        return nonan(v.item())
    return v


def jload(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def jsave(obj, p, indent=None):
    with open(p, "w", encoding="utf-8") as f:
        json.dump(nonan(obj), f, ensure_ascii=False, allow_nan=False, indent=indent,
                  separators=None if indent else (",", ":"))


def get(R, path):
    v = R
    for k in path.split("."):
        v = v[int(k)] if isinstance(v, list) else v[k]
    return v


def fmt(v, f=None):
    if f is None or f == "raw": return str(v)
    if f == "int": return f"{round(float(v)):,}"
    if f == "pc": return f"{round(float(v))}%"
    if f == "pc1": return f"{float(v):.1f}%"
    if f == "f0": return f"{float(v):.0f}"
    if f == "f1": return f"{float(v):.1f}"
    if f == "f2": return f"{float(v):.2f}"
    if f == "f3": return f"{float(v):.3f}"
    if f == "gbp": return f"£{round(float(v)):,}"
    if f == "gbpm": return f"£{float(v) / 1e6:.1f} million"
    if f == "gbpk": return f"£{round(float(v) / 1000):,},000"
    raise ValueError(f)


def fill(t, R, keep=("DOI", "DOI_URL", "BLOG_URL")):
    return re.sub(r"\{\{([^{}|]+)(\|(\w+))?\}\}",
                  lambda m: m.group(0) if m.group(1) in keep or m.group(1).startswith("IMG") or m.group(1).startswith("TABLE")
                  else fmt(get(R, m.group(1)), m.group(3)), t)
