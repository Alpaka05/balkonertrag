(() => {
  const base = document.querySelector('link[rel=stylesheet]').getAttribute('href').replace(/assets\/style\.css$/, '');
  const nf = (x, d = 0) => x.toLocaleString('de-DE', { maximumFractionDigits: d, minimumFractionDigits: d });

  // Rechner
  document.querySelectorAll('.calc').forEach(el => {
    const y = JSON.parse(el.dataset.yields);
    const v = n => el.querySelector(`[name=${n}]`).value;
    const out = n => el.querySelector(`[data-out=${n}]`);
    const run = () => {
      const angle = v('angle'), wp = +v('wp');
      const perKwp = y[v('aspect') + angle];
      // Wechselrichter-Grenze 800 W: grobe Schätzung des Verlusts durch abgeschnittene Mittagsspitzen
      const r = wp / 800;
      const clip = Math.min(0.35, Math.max(0, (angle === '35' ? 0.13 : 0.07) * (r - 1.15)));
      const kwh = perKwp * wp / 1000 * (1 - clip);
      const eur = kwh * (+v('self') / 100) * (+v('price') / 100);
      const years = eur > 0 ? +v('cost') / eur : Infinity;
      out('kwh').textContent = nf(kwh);
      out('eur').textContent = nf(eur) + ' €';
      out('years').textContent = isFinite(years) ? nf(years, 1) + ' Jahre' : '–';
      out('note').textContent = clip > 0.005
        ? `Enthält ca. ${nf(clip * 100)} % Abzug, weil der Wechselrichter bei ${nf(wp)} Wp auf 800 W begrenzt (Schätzung). Ein Speicher kann diesen Überschuss teilweise nutzen.`
        : '';
    };
    el.addEventListener('input', run);
    run();
  });

  // Stadtsuche
  let cities;
  document.querySelectorAll('[data-citysearch]').forEach(inp => {
    const go = async () => {
      cities = cities || await (await fetch(base + 'assets/cities.json')).json();
      const s = cities[inp.value.trim()];
      if (s) location.href = base + 'stadt/' + s + '/';
    };
    inp.addEventListener('change', go);
    inp.addEventListener('keydown', ev => { if (ev.key === 'Enter') go(); });
  });
})();
