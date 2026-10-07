# Balkonertrag

Statische Website mit Ertragsdaten für Balkonkraftwerke in deutschen Städten.

```
python3 scripts/fetch_pvgis.py   # Daten holen (setzt fort, wo es aufgehört hat)
python3 scripts/build.py         # Website nach site/ bauen
```

Einstellungen (Domain, Partner-Tag, Impressum): `scripts/config.py`. Strategie und offene Punkte: `PLAN.md`.
Deployment: GitHub Actions veröffentlicht `site/` bei jedem Push auf `main`.
