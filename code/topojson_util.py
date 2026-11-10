"""Fallback for figstyle.lsoa_shapes: rebuild BNG LSOA shapes for drawing from data/lsoa.topo.json (needs `pip install topojson`
is NOT required: arcs are decoded here) when the cached GeoPackage in scratch is missing."""
import numpy as np, geopandas as gpd
from shapely.geometry import Polygon, MultiPolygon
from common import *


def write_bng(fn, tol=40):
    T = jload(f"{DATA}/lsoa.topo.json"); codes = jload(f"{DATA}/lsoa_codes.json")
    sc, tr = T["transform"]["scale"], T["transform"]["translate"]
    arcs = []
    for a in T["arcs"]:
        a = np.cumsum(np.asarray(a, float), axis=0); arcs.append(a * sc + tr)
    def ring(ix):
        pts = []
        for i in ix:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a[1:] if pts else a)
        return pts
    geoms = []
    for g in T["objects"]["lsoa"]["geometries"]:
        polys = [g["arcs"]] if g["type"] == "Polygon" else g["arcs"]
        geoms.append(MultiPolygon([Polygon(ring(p[0]), [ring(h) for h in p[1:]]) for p in polys]))
    d = gpd.GeoDataFrame({"LSOA21CD": codes}, geometry=geoms, crs=4326).to_crs(27700)
    d["geometry"] = d.geometry.simplify(tol, preserve_topology=True)
    d.to_file(fn)
