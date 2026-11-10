/* Who owns your street? Property in England and Wales held by overseas companies. Every LSOA coloured by overseas-company
 * titles per 1,000 dwellings, with a jurisdiction filter, and a district view. MapLibre on OpenFreeMap Positron; LSOA polygons
 * from a simplified TopoJSON joined by position to data/site_lsoa.json. Aggregate counts only: no title, address or postcode
 * from the HM Land Registry file is in this page. Information produced by HM Land Registry © Crown copyright 2026.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const qs = new URLSearchParams(location.search);
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const fmt = n => Number(n).toLocaleString('en-GB');
  const small = matchMedia('(max-width:800px)').matches;
  const NONE = '#FFFDF8', NODATA = '#D9D6CF';
  const COLS = ['#F7E3C4', '#F1C48E', '#E59A5E', '#D0663D', '#AE3A2B', '#7E1F22', '#4A0F18'];
  const BRK = [0, 2, 5, 10, 25, 50, 100];
  const LBL = ['under 2', '2 to 5', '5 to 10', '10 to 25', '25 to 50', '50 to 100', '100 or more'];
  const MODES = [['t', 'All overseas companies'], ['u', 'Crown Dependencies and Overseas Territories'], ['j', 'Jersey'],
    ['b', 'British Virgin Islands'], ['g', 'Guernsey'], ['m', 'Isle of Man'], ['o', 'Everywhere else'], ['lad', 'District view (all titles)']];
  let map = null, S = null, D = null, mode = 't', feats = null, ladF = null;
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const ct = document.getElementById('cartouche'); const fold = f => ct.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('ctToggle').addEventListener('click', () => fold(!ct.classList.contains('folded')));
  document.getElementById('ctFold').addEventListener('click', () => fold(true));

  const steps = v => { const e = ['step', v, COLS[0]]; for (let k = 1; k < COLS.length; k++) e.push(BRK[k], COLS[k]); return e; };
  function colourExpr() {
    const k = mode === 'lad' ? 't' : mode;
    const r = ['*', 1000, ['/', ['get', k], ['max', ['get', 'n'], 1]]];
    return ['case', ['==', ['get', 'n'], 0], NODATA, ['==', ['get', k], 0], NONE, steps(r)];
  }
  function ladExpr() { return ['case', ['==', ['get', 't'], 0], NONE, steps(['get', 'r'])]; }
  function legend() {
    const kt = document.getElementById('keyTitle'), kb = document.getElementById('keyBody');
    const lab = MODES.find(m => m[0] === mode)[1];
    kt.textContent = mode === 'lad' ? 'Titles per 1,000 dwellings, by district' : 'Titles per 1,000 dwellings';
    kb.innerHTML = `<div class="row kx">${mode === 'lad' ? 'Includes titles without a postcode' : 'Companies from: <b>' + esc(lab) + '</b>'}</div>` +
      `<div class="bands"><span style="background:${NONE};outline:1px solid #CFC6B0"></span>${COLS.map(c => `<span style="background:${c}"></span>`).join('')}</div>` +
      `<div class="bl"><span>0</span>${BRK.slice(1).map(b => `<span>${b}</span>`).join('')}</div>` +
      `<div class="row kx">England and Wales: ${D.ew_rate} per 1,000</div>`;
  }
  function setMode(m) {
    mode = m; document.getElementById('mode').value = m;
    if (map && map.getLayer('rate')) {
      map.setPaintProperty('rate', 'fill-color', colourExpr());
      map.setLayoutProperty('rate', 'visibility', m === 'lad' || !document.getElementById('lyA').checked ? 'none' : 'visible');
      map.setLayoutProperty('ladfill', 'visibility', m === 'lad' ? 'visible' : 'none');
      document.getElementById('lyA').disabled = m === 'lad';
    }
    legend();
  }
  const SRC = '<p class="nt">Information produced by HM Land Registry © Crown copyright 2026 (overseas companies data, November 2026); dwellings: VOA 2025 (OGL). Counts of titles, not homes.</p>';
  function areaHtml(i) {
    const n = S.n[i], t = S.t[i], la = D.las[S.lad[i]];
    const r = n ? (1000 * t / n) : null;
    let h = `<b class="t">${esc(S.names[i])}</b><div class="nt">${esc(la.n)} · ${esc(la.rg)}</div>`;
    h += `<table><tr><td>Dwellings</td><td>about ${fmt(n)}</td></tr><tr><td>Overseas-company titles</td><td><b>${fmt(t)}</b></td></tr>`;
    h += `<tr><td>Per 1,000 dwellings</td><td><b>${r === null ? 'n/a' : r.toFixed(1)}</b> (England and Wales ${D.ew_rate})</td></tr></table>`;
    if (t) {
      const o = t - S.u[i];
      const rows = [['Jersey', S.j[i]], ['British Virgin Islands', S.b[i]], ['Guernsey', S.g[i]], ['Isle of Man', S.m[i]], ['Other Crown Dep. or Territory', S.u[i] - S.j[i] - S.b[i] - S.g[i] - S.m[i]], ['Everywhere else', o]].filter(x => x[1] > 0);
      const mx = Math.max(...rows.map(x => x[1]), 1);
      h += '<div class="pl"><b>Where the companies are incorporated</b><table class="bars">' + rows.map(([l, v]) => `<tr><td>${esc(l)}</td><td><span class="bar" style="width:${Math.max(v / mx * 70, 2)}px;background:${l === 'Everywhere else' ? '#8C8577' : '#B3202A'}"></span> ${fmt(v)}</td></tr>`).join('') + '</table></div>';
    }
    return h + SRC;
  }
  function ladHtml(k) {
    const la = D.las[k];
    let h = `<b class="t">${esc(la.n)}</b><div class="nt">${esc(la.rg)} · district ${la.rk} of ${D.las.length} by rate</div>`;
    h += `<table><tr><td>Overseas-company titles</td><td><b>${fmt(la.t)}</b></td></tr><tr><td>of which with a postcode</td><td>${fmt(la.tg)}</td></tr>`;
    h += `<tr><td>Dwellings</td><td>about ${fmt(la.d)}</td></tr><tr><td>Per 1,000 dwellings</td><td><b>${la.r.toFixed(1)}</b></td></tr>`;
    if (la.u !== null) h += `<tr><td>Crown Dep. or Territory</td><td>${la.u.toFixed(0)}% of titles</td></tr>`;
    if (la.j) h += `<tr><td>Most common</td><td>${esc(la.j)}</td></tr>`;
    h += `<tr><td>Median price paid</td><td>${la.mp ? '£' + fmt(la.mp) + ` (${fmt(la.np)} titles with a price)` : 'fewer than 10 titles with a price'}</td></tr></table>`;
    return h + SRC;
  }
  function setup(topo, lad) {
    feats = topojson.feature(topo, topo.objects.lsoa).features;
    feats.forEach((f, i) => { f.properties = { i, n: S.n[i], t: S.t[i], u: S.u[i], j: S.j[i], b: S.b[i], g: S.g[i], m: S.m[i], o: S.t[i] - S.u[i] }; f.id = i; });
    ladF = lad; ladF.features.forEach(f => { const la = D.las[f.properties.i]; f.properties.t = la.t; f.properties.r = la.r; });
    const firstSym = map.getStyle().layers.find(l => l.type === 'symbol');
    const before = firstSym ? firstSym.id : undefined;
    map.addSource('lsoa', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Information produced by HM Land Registry © Crown copyright 2026; VOA 2025 (OGL); ONS boundaries (OGL)', tolerance: 0.25 });
    map.addSource('lad', { type: 'geojson', data: ladF });
    map.addLayer({ id: 'rate', type: 'fill', source: 'lsoa', paint: { 'fill-color': colourExpr(), 'fill-opacity': ['interpolate', ['linear'], ['zoom'], 5, 0.92, 13, 0.75], 'fill-antialias': false } }, before);
    map.addLayer({ id: 'ladfill', type: 'fill', source: 'lad', layout: { visibility: 'none' }, paint: { 'fill-color': ladExpr(), 'fill-opacity': 0.9 } }, before);
    map.addLayer({ id: 'outline', type: 'line', source: 'lsoa', minzoom: 11, paint: { 'line-color': '#FFFFFF', 'line-width': ['interpolate', ['linear'], ['zoom'], 11, 0.3, 14, 1.1], 'line-opacity': 0.8 } }, before);
    map.addLayer({ id: 'ladline', type: 'line', source: 'lad', paint: { 'line-color': '#4A3F33', 'line-width': ['interpolate', ['linear'], ['zoom'], 5, 0.35, 10, 1.3], 'line-opacity': 0.7 } }, before);
    map.addSource('hl', { type: 'geojson', data: { type: 'FeatureCollection', features: [] } });
    map.addLayer({ id: 'hl', type: 'line', source: 'hl', paint: { 'line-color': '#1D2128', 'line-width': 2.6 } });
    map.on('click', e => {
      if (mode === 'lad') { const f = map.queryRenderedFeatures(e.point, { layers: ['ladfill'] }); if (f.length) openLad(f[0].properties.i, e.lngLat); return; }
      const f = map.queryRenderedFeatures(e.point, { layers: ['rate'] });
      if (f.length) openArea(f[0].properties.i, e.lngLat);
    });
    ['rate', 'ladfill'].forEach(id => { map.on('mousemove', id, () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', id, () => map.getCanvas().style.cursor = ''); });
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    const vis = (ids, v) => ids.forEach(id => map.setLayoutProperty(id, 'visibility', v ? 'visible' : 'none'));
    document.getElementById('lyA').addEventListener('change', e => vis(['rate'], e.target.checked && mode !== 'lad'));
    document.getElementById('lyO').addEventListener('change', e => vis(['outline'], e.target.checked));
    document.getElementById('lyD').addEventListener('change', e => vis(['ladline'], e.target.checked));
    const baseSym = map.getStyle().layers.filter(l => l.type === 'symbol').map(l => l.id);
    document.getElementById('lyB').addEventListener('change', e => vis(baseSym, e.target.checked));
    const sel = document.getElementById('mode');
    sel.innerHTML = MODES.map(([v, l]) => `<option value="${v}">${esc(l)}</option>`).join('');
    sel.addEventListener('change', () => setMode(sel.value));
    const m0 = qs.get('mode'); setMode(m0 && MODES.some(m => m[0] === m0) ? m0 : 't');
    document.getElementById('nojs').style.display = 'none';
    if (small) { const a = document.querySelector('.maplibregl-ctrl-attrib'); if (a) a.classList.remove('maplibregl-compact-show'); }
  }
  function bboxOf(g) { let x0 = 180, y0 = 90, x1 = -180, y1 = -90; const walk = c => { if (typeof c[0] === 'number') { x0 = Math.min(x0, c[0]); x1 = Math.max(x1, c[0]); y0 = Math.min(y0, c[1]); y1 = Math.max(y1, c[1]); } else c.forEach(walk); }; walk(g.coordinates); return [[x0, y0], [x1, y1]]; }
  const popup = (ll, html, f) => new maplibregl.Popup({ maxWidth: '340px', anchor: small ? 'bottom' : undefined }).setLngLat(ll).setHTML(html).addTo(map)
    .on('close', () => map.getSource('hl').setData({ type: 'FeatureCollection', features: [] }));
  function openArea(i, ll) {
    map.getSource('hl').setData({ type: 'FeatureCollection', features: [feats[i]] });
    if (!ll) { const b = bboxOf(feats[i].geometry); ll = [(b[0][0] + b[1][0]) / 2, (b[0][1] + b[1][1]) / 2]; }
    popup(ll, areaHtml(i));
  }
  function openLad(k, ll) {
    const f = ladF.features.find(x => x.properties.i === k);
    map.getSource('hl').setData({ type: 'FeatureCollection', features: f ? [f] : [] });
    const b = D.las[k].b; if (!ll) ll = [(b[0] + b[2]) / 2, (b[1] + b[3]) / 2];
    popup(ll, ladHtml(k));
  }
  function go(it) {
    fold(true);
    if (it.k === 'area') { const b = bboxOf(feats[it.i].geometry); map.fitBounds(b, { padding: 80, maxZoom: 14, duration: 1000 }); map.once('moveend', () => openArea(it.i)); return; }
    if (it.k === 'la') { const b = it.o.b; map.fitBounds([[b[0], b[1]], [b[2], b[3]]], { padding: 30, duration: 1000 }); map.once('moveend', () => openLad(D.las.indexOf(it.o))); return; }
    map.flyTo({ center: [it.o.lo, it.o.la], zoom: it.k === 'pc' ? 14 : 12.5, duration: 1100 });
    map.once('moveend', () => { if (mode === 'lad') return; const p = map.project([it.o.lo, it.o.la]); const f = map.queryRenderedFeatures(p, { layers: ['rate'] }); if (f.length) openArea(f[0].properties.i, [it.o.lo, it.o.la]); });
  }
  const PC = /^[A-Z]{1,2}[0-9][A-Z0-9]?\s*[0-9][A-Z]{2}$/i;
  function postcode(v) {
    fetch('https://api.postcodes.io/postcodes/' + encodeURIComponent(v.replace(/\s+/g, ''))).then(r => r.json()).then(j => {
      if (j && j.result && j.result.longitude) go({ k: 'pc', o: { lo: j.result.longitude, la: j.result.latitude } });
      else document.getElementById('q').value = 'Postcode not found';
    }).catch(() => { document.getElementById('q').value = 'Postcode lookup failed'; });
  }
  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = [].concat(D.las.map(o => ({ t: o.n, s: 'district', k: 'la', o })), D.places.map(o => ({ t: o.n, s: 'place', k: 'place', o })),
      S.names.map((n, i) => ({ t: n, s: 'small area', k: 'area', i })));
    idx.forEach(x => x.nn = norm(x.t));
    const show = () => { const raw = q.value.trim(), v = norm(raw); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      if (PC.test(raw)) { items = [{ t: raw.toUpperCase(), s: 'postcode (looked up at postcodes.io)', k: 'pcq' }]; }
      else { const a = [], b = []; for (const x of idx) { if (x.nn.startsWith(v)) a.push(x); else if (v.length > 2 && x.nn.includes(v)) b.push(x); if (a.length > 14) break; } items = a.concat(b).slice(0, 12); }
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.t)} <span>${esc(it.s)}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.t; sug.style.display = 'none'; if (it.k === 'pcq') postcode(it.t); else go(it); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
    const chips = document.getElementById('chips');
    ['Westminster', 'Kensington and Chelsea', 'City of London', 'Tower Hamlets', 'Salford', 'Manchester', 'Liverpool', 'Colchester', 'Leeds', 'Cardiff'].forEach(n => {
      const o = D.las.find(c => c.n === n); if (!o) return;
      const b = document.createElement('button'); b.className = 'chip'; b.textContent = n.replace('Kensington and Chelsea', 'Kensington'); b.addEventListener('click', () => go({ k: 'la', o })); chips.appendChild(b); });
    document.querySelectorAll('[data-go]').forEach(a => a.addEventListener('click', e => { e.preventDefault(); const [n, m] = a.dataset.go.split('|'); const o = D.las.find(c => c.n === n);
      if (m) setMode(m); document.getElementById('mapWrap').scrollIntoView({ behavior: 'smooth' }); if (o) go({ k: 'la', o }); }));
  }
  Promise.all([fetch('data/site.json').then(r => r.json()), fetch('data/site_lsoa.json').then(r => r.json())]).then(([d, s]) => {
    D = d; S = s; legend();
    const at = (qs.get('at') || '').split(',').map(Number);
    const mo = at.length === 3 && at.every(isFinite) ? { center: [at[1], at[0]], zoom: at[2] } : { bounds: [[-5.8, 49.95], [1.8, 55.8]], fitBoundsOptions: { padding: small ? { top: 60, bottom: 90, left: 10, right: 10 } : { top: 40, bottom: 70, left: 360, right: 60 } } };
    const m0 = new maplibregl.Map(Object.assign({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 15, minZoom: 4.5 }, mo));
    m0.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    window.__map = m0; map = m0;
    setupSearch();
    return Promise.all([new Promise((res, rej) => { m0.once('load', res); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); }),
      fetch('data/lsoa.topo.json').then(r => r.json()), fetch('data/lad.geojson').then(r => r.json())]);
  }).then(([, topo, lad]) => setup(topo, lad)).catch(err => { document.getElementById('nojs').textContent = 'The map could not load: ' + err; console.error(err); });
})();
