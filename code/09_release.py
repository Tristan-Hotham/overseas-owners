"""Step 9: blog post and meta (release/blog), Zenodo files and metadata (release/zenodo).
10.5281/zenodo.24115198, https://doi.org/10.5281/zenodo.24115198 and https://blog.tristanhotham.com/2026/10/31/overseas-owners/ are left for the publisher to fill. The data and code zip holds code and aggregate data
only: never the HM Land Registry file or any title-level record."""
import json as _json, shutil, zipfile
from PIL import Image
from common import *

R = jload(f"{DATA}/results.json"); x = R["x"]
NAME = "Hotham_Who_Owns_Your_Street"
KEEP = {"DOI", "DOI_URL", "BLOG_URL"}
post = open(os.path.join(CODE, "blog_template.html"), encoding="utf-8").read()
post = re.sub(r"\{\{(?!IMG)([^{}|]+)(\|(\w+))?\}\}", lambda m: m.group(0) if m.group(1) in KEEP else fmt(get(R, m.group(1)), m.group(3)), post)
used = re.findall(r"\{\{IMG\|([^|]+)\|", post)
assert 5 <= len(used) <= 8, len(used)
assert all(re.search(r"^\{\{IMG\|" + re.escape(u_), post, re.M) for u_ in used) and "wp:image" not in post
for img in used:
    assert Image.open(f"{REL}/blog/{img}").size[0] == 1800, img
for fn in os.listdir(f"{REL}/blog"):
    if fn.startswith("b_") and fn not in used:
        os.remove(f"{REL}/blog/{fn}")
assert set(re.findall(r"\{\{([^|}]+)\}\}", post)) <= KEEP
vis = re.sub(r"<!--.*?-->", "", post, flags=re.S)
for bad in ("\u2014", "\u2013", "--", " - ", "D" "SIT", "D" "CMS", "civil" " serv", "pre-" "registered"):
    assert bad not in vis, bad
assert AI in post and HMLR in post and "November 2026" in post
open(f"{REL}/blog/post.html", "w", encoding="utf-8").write(post)
words = len(re.sub(r"<[^>]+>|\{\{IMG\|[^}]*\}\}", " ", vis).split())
meta = {"title": "Who owns your street?",
        "slug": "overseas-owners",
        "excerpt": f"{R['n_titles']:,} property titles in England and Wales are held by companies incorporated abroad. I mapped them for every small area: {R['pc_uko']:.0f}% are held from Jersey, Guernsey, the Isle of Man, the BVI and the UK's other islands and territories.",
        "seo_description": f"{R['n_titles']:,} titles in England and Wales held by overseas companies, mapped by small area: {R['pc_uko']:.0f}% from UK-linked islands and territories.",
        "tags": ["maps", "data visualisation", "property", "housing", "offshore", "HM Land Registry", "England", "Wales"],
        "header_alt": f"Title card on pale paper reading 'Who owns your street?' with the numbers {R['n_titles']:,} and {R['pc_uko']:.0f}% beside a map of England and Wales shaded by overseas-company titles per 1,000 homes, darkest in central London."}
assert len(meta["seo_description"]) < 160, len(meta["seo_description"])
_json.dump(meta, open(f"{REL}/blog/meta.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
Z = f"{REL}/zenodo"; os.makedirs(Z, exist_ok=True)
for fn in os.listdir(Z):
    os.remove(os.path.join(Z, fn))
shutil.copy(f"{REL}/paper/{NAME}.pdf", f"{Z}/{NAME}.pdf")
zp = f"{Z}/{SLUG}_data_and_code.zip"
with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
    for fn in sorted(os.listdir(CODE)):
        if fn.endswith((".pyc", ".png")) or fn == "__pycache__":
            continue
        z.write(os.path.join(CODE, fn), f"{SLUG}/code/{fn}")
    for fn in sorted(os.listdir(DATA)):
        z.write(os.path.join(DATA, fn), f"{SLUG}/data/{fn}")
    for fn in ("README.md", "LICENSE", "NOTES.md"):
        z.write(os.path.join(ROOT, fn), f"{SLUG}/{fn}")
    z.write(os.path.join(REL, "paper", "cover_note.md"), f"{SLUG}/release/paper/cover_note.md")
    z.write(os.path.join(ROOT, "reddit", "collage.py"), f"{SLUG}/reddit/collage.py")
# licence check: no title-level content in anything shipped
with zipfile.ZipFile(zp) as z:
    for n in z.namelist():
        assert not n.lower().endswith((".parquet", ".zip")) and "OCOD_FULL" not in n, n
tex = open(f"{REL}/paper/{NAME}.tex", encoding="utf-8").read()
ab = re.search(r"\\begin\{center\}\\textbf\{Abstract\}\\end\{center\}\n(.*?)\n\n", tex, re.S).group(1)
ab = ab.replace("\\%", "%").replace("\\&", "&").replace("$", "").replace("``", "\"").replace("''", "\"")
zmeta = {"title": "Who Owns Your Street? The Small-Area Geography of Property in England and Wales Held by Overseas Companies",
         "upload_type": "publication", "publication_type": "workingpaper",
         "description": f"<p>{ab}</p><p>Interactive version: <a href=\"{PAGE}\">{PAGE}</a>. Data and code: <a href=\"{REPO}\">{REPO}</a>. Blog post: {{https://blog.tristanhotham.com/2026/10/31/overseas-owners/}}.</p>"
                        f"<p>Sources: {HMLR}. Overseas companies that own property in England and Wales, full file, data at November 2026, used under HM Land Registry's licence for non-commercial use; "
                        "only aggregate counts are shared (no title numbers, addresses or postcodes). Valuation Office Agency, Council Tax: stock of properties 2025 (Open Government Licence v3.0); "
                        "ONS boundaries (Open Government Licence v3.0); postcodes.io; Tax Justice Network Financial Secrecy Index 2018. "
                        "Text CC BY 4.0; figures and derived data for non-commercial use (CC BY-NC 4.0 and HM Land Registry terms); code MIT.</p>",
         "creators": [{"name": "Hotham, Tristan", "affiliation": "Independent researcher", "orcid": "0000-0003-4931-9349"}],
         "keywords": ["offshore ownership", "real estate", "tax havens", "financial secrecy", "housing", "small areas", "England and Wales", "HM Land Registry"],
         "license": "cc-by-nc-4.0", "language": "eng",
         "related_identifiers": [{"identifier": REPO, "relation": "isSupplementedBy", "resource_type": "software"},
                                 {"identifier": PAGE, "relation": "isSupplementedBy", "resource_type": "other"}],
         "files": sorted(os.listdir(Z))}
sj = _json.dumps(zmeta, ensure_ascii=False) + _json.dumps(meta, ensure_ascii=False)
for bad in ("\u2014", "\u2013", "--", "D" "SIT", "D" "CMS"):
    assert bad not in sj, bad
_json.dump(zmeta, open(f"{Z}/metadata.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("blog words", words, "figures", len(used), "; zenodo", sorted(os.listdir(Z)), os.path.getsize(zp) // 1024, "KB zip")
