# Balkonertrag

Statische Website mit Ertragsdaten für Balkonkraftwerke in deutschen Städten.

```
python3 scripts/fetch_pvgis.py   # Monats-/Jahreserträge je Stadt holen (setzt fort, wo es aufgehört hat)
python3 scripts/fetch_profiles.py  # stündliche Ertragsprofile (assets/hourly/)
python3 scripts/make_load.py BDEW_H25.xlsx  # Lastprofil H25 (assets/load_h25.json, braucht openpyxl)
python3 scripts/build.py         # Website nach site/ bauen
```

Die Stundensimulation steht zweimal im Code und muss gleich bleiben: `scripts/sim.py` (für die Texte) und `simulate()` in `assets/app.js` (Rechner).

Einstellungen (Domain, Partner-Tag, Impressum): `scripts/config.py`. Strategie und offene Punkte: `PLAN.md`.
Deployment: GitHub Actions veröffentlicht `site/` bei jedem Push auf `main`.
