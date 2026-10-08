(() => {
  const base = document.querySelector('link[rel=stylesheet]').getAttribute('href').replace(/assets\/style\.css.*$/, '');
  const nf = (x, d = 0) => x.toLocaleString('de-DE', { maximumFractionDigits: d, minimumFractionDigits: d });
  const DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
  const MONTHS = ['Jan', 'Feb', 'Mär', 'Apr', 'Mai', 'Jun', 'Jul', 'Aug', 'Sep', 'Okt', 'Nov', 'Dez'];
  const LIMIT = 0.8; // kW Einspeisegrenze des Wechselrichters
  const ETA = 0.95;  // Wirkungsgrad je Lade- bzw. Entladevorgang
  const STANDBY = 0.008; // kWh pro Stunde Eigenverbrauch des Speichers
  const K = 0.8;     // Abschlag fürs geglättete Standardlastprofil, siehe scripts/config.py (KALIBRIERUNG)

  const cache = {};
  const getJSON = p => (cache[p] = cache[p] || fetch(base + p).then(r => r.json()));

  // ---------- Stunden-Simulation
  // monthly: 12 Monatserträge (kWh pro kWp), frac: 8760 Stundenanteile am Monat (1/100000), load: 8760 Anteile am Jahr (1/1e6)
  function simulate(monthly, frac, load, wp, annual, batt) {
    const kwp = wp / 1000;
    let h = 0, soc = 0;
    const r = { pv: 0, used: 0, clipped: 0, mPv: Array(12).fill(0), mUsed: Array(12).fill(0) };
    for (let m = 0; m < 12; m++) {
      for (let i = 0; i < DAYS[m] * 24; i++, h++) {
        const pv = monthly[m] * frac[h] / 1e5 * kwp;
        const need = annual * load[h] / 1e6;
        const direct = Math.min(pv, need, LIMIT) * K;
        let rest = pv - direct, out = direct, used = direct;
        if (batt > 0) {
          const take = Math.min(soc, STANDBY);
          soc -= take; used -= STANDBY - take;
          // DC-gekoppelter Speicher: lädt mit Überschuss, auch mit dem, was über 800 W liegt
          const charge = Math.min(rest, (batt - soc) / ETA);
          soc += charge * ETA; rest -= charge;
          const dis = Math.min(need - direct, soc * ETA, LIMIT - out);
          if (dis > 0) { soc -= dis / ETA; out += dis; used += dis; }
        }
        const exp = Math.min(rest, LIMIT - out);
        out += exp;
        r.clipped += rest - exp;
        r.pv += out; r.used += used; r.mPv[m] += out; r.mUsed[m] += used;
      }
    }
    return r;
  }

  function chart(svg, a, b) {
    const w = 600, h = 230, pad = 28, mx = Math.max(...a, 1), bw = (w - pad) / 12;
    let s = `<line class="axis" x1="${pad}" x2="${w}" y1="${h - pad}" y2="${h - pad}"/>`;
    a.forEach((v, i) => {
      const x = pad + i * bw, bh = (h - 2 * pad) * v / mx, uh = (h - 2 * pad) * (b ? b[i] : 0) / mx;
      s += `<rect x="${(x + 4).toFixed(1)}" y="${(h - pad - bh).toFixed(1)}" width="${(bw - 8).toFixed(1)}" height="${bh.toFixed(1)}" rx="3"><title>${MONTHS[i]}: ${nf(v)} kWh erzeugt</title></rect>`;
      if (b) s += `<rect class="alt" x="${(x + 4).toFixed(1)}" y="${(h - pad - uh).toFixed(1)}" width="${(bw - 8).toFixed(1)}" height="${uh.toFixed(1)}" rx="3"><title>${MONTHS[i]}: ${nf(b[i])} kWh selbst genutzt</title></rect>`;
      s += `<text class="v" x="${(x + bw / 2).toFixed(1)}" y="${(h - pad - bh - 6).toFixed(1)}">${nf(v)}</text><text x="${(x + bw / 2).toFixed(1)}" y="${h - 8}">${MONTHS[i]}</text>`;
    });
    svg.innerHTML = s;
  }

  // ---------- Rechner
  const FIELDS = { aspect: 'a', angle: 'n', wp: 'wp', annual: 'v', batt: 'b', price: 'p', cost: 'c' };
  document.querySelectorAll('.calc').forEach(el => {
    const M = JSON.parse(el.dataset.m);
    const co2 = +el.dataset.co2;
    const f = n => el.querySelector(`[name=${n}]`);
    const out = n => el.querySelector(`[data-out=${n}]`);
    const params = new URLSearchParams(location.search);
    if (el.dataset.share !== undefined) for (const [n, k] of Object.entries(FIELDS)) if (params.has(k) && f(n)) f(n).value = params.get(k);

    const keys = () => {
      const a = f('aspect').value, n = f('angle').value;
      if (n === '0') return ['F0'];
      return a === 'OW' ? ['O' + n, 'W' + n] : [a + n];
    };
    let token = 0;
    const run = async () => {
      const ks = keys(), wp = +f('wp').value || 0, annual = +f('annual').value || 0, batt = +f('batt').value || 0;
      const price = +f('price').value / 100, cost = +f('cost').value;
      const monthly = ks.map(k => M[k]);
      // Schnellwert ohne Stundendaten (nur Jahressumme), wird gleich durch die Simulation ersetzt
      const rough = monthly.reduce((s, m) => s + m.reduce((a, b) => a + b, 0), 0) / ks.length * wp / 1000;
      out('kwh').textContent = nf(rough);
      const t = ++token;
      const [load, ...fr] = await Promise.all([getJSON('assets/load_h25.json'), ...ks.map(k => getJSON(`assets/hourly/${k}.json`))]);
      if (t !== token) return;
      // Ost-West: Module je zur Hälfte nach Osten und Westen
      const sims = ks.map((k, i) => ({ m: monthly[i], fr: fr[i] }));
      let r;
      if (sims.length === 1) r = simulate(sims[0].m, sims[0].fr, load, wp, annual, batt);
      else {
        // Stundenwerte beider Hälften addieren: gemeinsamer Anteil je Stunde, gewichtet mit den Monatserträgen
        const m = sims[0].m.map((v, i) => (v + sims[1].m[i]) / 2);
        let h = 0;
        const mix = new Float64Array(8760);
        for (let mo = 0; mo < 12; mo++) for (let i = 0; i < DAYS[mo] * 24; i++, h++)
          mix[h] = m[mo] ? (sims[0].m[mo] * sims[0].fr[h] + sims[1].m[mo] * sims[1].fr[h]) / 2 / m[mo] : 0;
        r = simulate(m, mix, load, wp, annual, batt);
      }
      const eur = r.used * price;
      out('kwh').textContent = nf(r.pv);
      out('self').textContent = r.pv ? nf(r.used / r.pv * 100) + ' %' : '–';
      out('selfkwh').textContent = `${nf(r.used)} kWh selbst genutzt, deckt ${annual ? nf(r.used / annual * 100) : 0} % deines Verbrauchs`;
      out('eur').textContent = nf(eur) + ' €';
      out('years').textContent = eur > 0 ? nf(cost / eur, 1) + ' Jahre' : '–';
      out('co2').textContent = `spart rund ${nf(r.pv * co2)} kg CO₂ pro Jahr`;
      const aTxt = f('aspect').selectedOptions[0].textContent, nTxt = f('angle').value + '°';
      out('assume').textContent = `${nf(wp)} Wp · ${f('angle').value === '0' ? 'flach' : aTxt + ' · ' + nTxt} · ${nf(annual)} kWh Verbrauch · ${batt ? nf(batt, 1) + ' kWh Speicher' : 'ohne Speicher'} · ${nf(price * 100, 1)} ct/kWh`;
      const notes = [];
      if (r.clipped > 1) notes.push(`Etwa ${nf(r.clipped)} kWh gehen verloren, weil der Wechselrichter auf 800 W begrenzt.${batt ? '' : ' Ein DC-gekoppelter Speicher (zwischen Modulen und Wechselrichter) kann einen Teil davon auffangen.'}`);
      if (wp > 960) notes.push('Über 960 Wp ist laut Produktnorm DIN VDE V 0126-95 statt Schuko-Stecker eine Einspeisesteckdose (z. B. Wieland) nötig.');
      out('note').textContent = notes.join(' ');
      const svg = el.querySelector('svg.chart');
      if (svg) chart(svg, r.mPv, r.mUsed);
    };
    el.addEventListener('input', run);
    run();

    const share = el.querySelector('[data-share-btn]');
    if (share) share.addEventListener('click', async () => {
      const q = new URLSearchParams();
      for (const [n, k] of Object.entries(FIELDS)) q.set(k, f(n).value);
      const link = location.origin + location.pathname + '?' + q;
      try { await navigator.clipboard.writeText(link); share.lastChild.textContent = ' Link kopiert'; }
      catch { prompt('Link zum Kopieren:', link); }
      setTimeout(() => (share.lastChild.textContent = ' Ergebnis teilen'), 2500);
    });
  });

  // ---------- Suche: Stadt, PLZ oder Standort
  const go = s => (location.href = base + 'stadt/' + s + '/');
  document.querySelectorAll('form.search').forEach(form => {
    const inp = form.querySelector('input'), msg = form.parentElement.querySelector('.search-msg');
    const say = t => msg && (msg.textContent = t);
    form.addEventListener('submit', async ev => {
      ev.preventDefault();
      const q = inp.value.trim();
      if (!q) return;
      if (/^\d{5}$/.test(q)) {
        const plz = await getJSON('assets/plz.json');
        return plz[q] ? go(plz[q]) : say('Diese Postleitzahl kennen wir leider nicht.');
      }
      const cities = await getJSON('assets/cities.json');
      const lc = q.toLowerCase();
      const hit = Object.keys(cities).find(n => n.toLowerCase() === lc) || Object.keys(cities).find(n => n.toLowerCase().startsWith(lc));
      hit ? go(cities[hit][0]) : say('Stadt nicht gefunden. Probier die nächstgrößere Stadt oder deine Postleitzahl.');
    });
    const loc = form.querySelector('[data-locate]');
    if (loc) loc.addEventListener('click', () => {
      if (!navigator.geolocation) return say('Dein Browser kann den Standort nicht bestimmen.');
      say('Standort wird bestimmt …');
      navigator.geolocation.getCurrentPosition(async p => {
        const cities = await getJSON('assets/cities.json');
        const { latitude: la, longitude: lo } = p.coords;
        let best, bd = Infinity;
        for (const [, [s, a, b]] of Object.entries(cities)) {
          const d = (a - la) ** 2 + ((b - lo) * Math.cos(la * Math.PI / 180)) ** 2;
          if (d < bd) { bd = d; best = s; }
        }
        go(best);
      }, () => say('Standort nicht verfügbar. Gib einfach deine Stadt oder PLZ ein.'), { timeout: 10000 });
    });
  });

  // ---------- Sortierbare Tabellen
  document.querySelectorAll('th[data-sort]').forEach(th => th.addEventListener('click', () => {
    const tb = th.closest('table').tBodies[0], i = [...th.parentNode.children].indexOf(th);
    const asc = th.getAttribute('aria-sort') !== 'ascending';
    th.parentNode.querySelectorAll('th').forEach(x => x.removeAttribute('aria-sort'));
    th.setAttribute('aria-sort', asc ? 'ascending' : 'descending');
    const val = td => td.dataset.v !== undefined ? +td.dataset.v : td.textContent.trim();
    [...tb.rows].sort((a, b) => {
      const x = val(a.cells[i]), y = val(b.cells[i]);
      return (typeof x === 'number' ? x - y : x.localeCompare(y, 'de')) * (asc ? 1 : -1);
    }).forEach(r => tb.appendChild(r));
  }));

  // ---------- Vermieter-Antrag
  const form = document.querySelector('form.antrag');
  if (form) {
    const box = document.querySelector('.letter');
    const tpl = document.getElementById('antrag-tpl').textContent;
    const render = () => {
      const d = Object.fromEntries(new FormData(form));
      d.datum = new Date().toLocaleDateString('de-DE');
      const label = k => form.querySelector(`[name=${k}]`)?.closest('label')?.firstChild.textContent || k;
      let t = tpl.replace(/\{(\w+)\}/g, (_, k) => (d[k] || '').trim() || `[${label(k)}]`);
      t = t.split('\n').filter(l => !(d.art === 'weg' ? l.startsWith('M|') : l.startsWith('W|'))).map(l => l.replace(/^[MW]\|/, '')).join('\n');
      box.textContent = t;
    };
    form.addEventListener('input', render);
    render();
    document.querySelector('[data-print]').addEventListener('click', () => window.print());
    document.querySelector('[data-copy]').addEventListener('click', async ev => {
      await navigator.clipboard.writeText(box.textContent);
      ev.currentTarget.lastChild.textContent = ' Kopiert';
    });
  }
})();
