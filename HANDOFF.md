# Handoff: Balkonertrag (Ziel 200 € pro Monat)

Stand: 8. Oktober 2026. Dieses Dokument reicht, um auf einem anderen Rechner oder in einem neuen Thread ohne Vorwissen weiterzumachen.

## Worum es geht

Der Besitzer (GitHub `Alpaka05`) hat als Ziel gesetzt, **dauerhaft 200 € pro Monat** zu verdienen, möglichst ohne eigenes Zutun. Gewählte Strategie:

**Balkonertrag** ist eine kostenlose, statische deutsche Website mit Ertragsdaten für Balkonkraftwerke in 958 Städten. Sie soll über Google-Traffic wachsen und mit Partnerlinks (Amazon, später Fachhändler) und eventuell Werbung Geld verdienen. Für 200 € im Monat braucht es grob 7.000–10.000 Besucher pro Monat. Realistisch dauert das 4–9 Monate ab Indexierung.

- Live: https://alpaka05.github.io/balkonertrag/
- Repo: https://github.com/Alpaka05/balkonertrag (öffentlich, Branch `main`)
- Deployment: GitHub Actions (`.github/workflows/pages.yml`) baut bei jedem Push auf `main` mit `python3 scripts/build.py` und veröffentlicht `site/`
- Kosten: 0 € (GitHub Pages, keine Dienste, kein Tracking)

## Was nur der Besitzer tun kann (offen)

Ohne diese Schritte kommt **kein Geld** rein. Partnerlinks sind bewusst ausgeschaltet, solange kein Impressum existiert, weil sonst Abmahnungen drohen.

1. **Impressum-Daten** (Name, Anschrift, E-Mail) in `scripts/config.py` → `IMPRESSUM` eintragen.
2. **Amazon PartnerNet** (partnernet.amazon.de): Tag in `config.py` → `AMAZON_TAG` eintragen. Sobald der Tag gesetzt ist, erscheinen die Partnerlink-Boxen automatisch (`product_box()` in `build.py`). Der Besitzer sollte sich erst anmelden, wenn Traffic da ist: Amazon verlangt 3 Verkäufe in 180 Tagen.
3. **Google Search Console**: Seite bestätigen und `sitemap.xml` einreichen.
4. Optional **eigene Domain** (z. B. balkonertrag.de). Dann in `config.py` `SITE_URL` und `BASE_PATH` anpassen, eine CNAME-Datei ergänzen und in den Repo-Einstellungen unter Pages die Domain setzen.

Die Datenschutzerklärung verweist auf das Impressum für den Verantwortlichen. Sie ist erst vollständig, wenn das Impressum gefüllt ist.

## Automatik, die bereits läuft

- **Cloud-Routine** `trig_01V6c3cZLs1vKC8Ao5VnaExR` (claude.ai → Code → Routines, https://claude.ai/code/routines/trig_01V6c3cZLs1vKC8Ao5VnaExR): läuft montags und donnerstags um 05:00 UTC mit Sonnet 5.5. Pro Lauf macht sie einen Ausbauschritt aus `PLAN.md` → „Nächste Ausbaustufen“, prüft Fakten per Websuche, baut, committet und pusht direkt auf `main`.
  - **Vor eigener Arbeit immer `git pull`**, die Routine pusht selbstständig.
  - Ändert sich die Architektur, muss der Prompt der Routine angepasst werden (RemoteTrigger `update`, ganzes `job_config` mitschicken). Die Routine hat absichtlich keine Konnektoren (`mcp_connections` leer).
- **IndexNow (Bing)**: Nach größeren Deploys `python3 scripts/indexnow.py` lokal ausführen. Das meldet alle URLs aus `site/sitemap.xml`. Den Schlüssel liefert `config.INDEXNOW_KEY`, die Datei `site/<key>.txt` erzeugt der Build. Der Endpunkt muss `www.bing.com/indexnow` sein, `api.indexnow.org` gab 403.

## Projektstruktur

```
scripts/
  build.py          Generator: alle Seiten, Layout, Rechner-HTML, Heatmap, Diagramme, Sitemap, PLZ-Zuordnung
  ratgeber.py       Ratgeber-Artikel, Vermieter-Antrag-Seite (+ Brief-Vorlage), Methodik, Datenschutz
  sim.py            Stundensimulation in Python (für Texte/Tabellen)
  config.py         Alle Annahmen und Betreiber-Einstellungen (Preise, Verbrauch, Kalibrierung, Tag, Impressum)
  fetch_pvgis.py    PVGIS-Monats-/Jahreserträge je Stadt → data/pvgis.json (~35.000 API-Aufrufe, ~1 h, fortsetzbar)
  fetch_profiles.py Stündliche PVGIS-Zeitreihe (Kassel, 2020) je Ausrichtung/Neigung → assets/hourly/*.json
  make_load.py      BDEW-Lastprofil H25 → assets/load_h25.json (braucht openpyxl + BDEW-Excel)
  indexnow.py       URLs an Bing melden
assets/             style.css, app.js (Rechner, Suche, Sortierung, Brief), icon.svg, hourly/, load_h25.json
data/
  pvgis.json        958 Städte: lat/lon/pop/state, y{key: kWh/kWp/Jahr}, m{key: [12 Monate]}
  cities_raw.tsv    Städteliste aus GeoNames cities15000 (DE, ohne Stadtteile PPLX), Eingabe für fetch_pvgis.py
  plz.tsv           PLZ-Mittelpunkte aus GeoNames (CC BY 4.0)
tools/              functest.py (Browser-Funktionstest), screenshot.py (Playwright)
PLAN.md             Strategie, Fortschrittstabelle, nächste Ausbaustufen (wird von der Routine gepflegt)
```

Schlüssel in `pvgis.json`: Ausrichtung `S, SO, SW, O, W` + Neigung `15, 25, 35, 45, 60, 75, 90`, dazu `F0` (flach). PVGIS-Parameter: v5_3, SARAH-3, `peakpower=1`, `loss=14`, Azimut S=0, SO=−45, SW=45, O=−90, W=90.

## Seiten (990)

- `/`: Startseite mit Suche (Stadt, PLZ, Standort), Rechner, Top-Städte
- `/stadt/<slug>/` (958): Rechner mit Stadtdaten, Heatmap Neigung × Ausrichtung, Montagearten-Tabelle, Monatsdiagramm 90° gegen 35°, Nachbarstädte, nächste Schritte, FAQ mit FAQPage-Schema
- `/bundesland/<slug>/` (16): Landesdurchschnitt im Rechner, sortierbare Städtetabelle
- `/staedte/`, `/rechner/`, `/speicher-rechner/`, `/vermieter-antrag/`, `/methodik/`, `/impressum/`, `/datenschutz/`
- `/ratgeber/`: ausrichtung-neigung, ost-west, balkonkraftwerk-winter, 2000-watt, speicher-lohnt-sich, bundeslaender-ranking, balkonkraftwerk-anmelden, balkonkraftwerk-mieter, balkonkraftwerk-foerderung

## Das Rechenmodell (wichtig)

Die Simulation existiert **zweimal und muss identisch bleiben**: `scripts/sim.py` (`Model.run`) und `simulate()` in `assets/app.js`.

- 8.760 Stunden. PV-Stunde = Monatsertrag der Stadt × Stundenanteil aus `assets/hourly/<key>.json` (1/100000 des Monats) × kWp.
- Verbrauch = Jahresverbrauch × `load_h25.json` (1/1e6 des Jahres, BDEW H25, dynamisiert).
- Direkt genutzt = min(PV, Bedarf, 0,8 kWh) × (1 − `KALIBRIERUNG`). Die Kalibrierung ist 0,20, weil das Standardlastprofil glatter ist als ein echter Haushalt. Damit liegt das Modell im Bereich der Verbraucherzentrale: 30–60 % ohne, ca. 70 % mit Speicher. Das ist eine **Schätzung, keine Messung**.
- Speicher (DC-gekoppelt angenommen): lädt aus Überschuss, auch über 800 W. Entlädt bis zur 800-W-Grenze. `ETA` 0,95 je Richtung, `STANDBY_W` 8 W Dauerverbrauch.
- Einspeisung maximal 800 W. Der Rest gilt als abgeregelt. Überschuss wird nicht vergütet.
- Ost-West = je halbe Modulleistung, Stundenprofile gemischt.
- Ersparnis = selbst genutzt × Strompreis. Amortisation = Preis ÷ Ersparnis.

Wenn `style.css` oder `app.js` geändert werden, `ASSET_VERSION` in `config.py` erhöhen (Cache-Busting).

## Lokal arbeiten

```bash
git clone https://github.com/Alpaka05/balkonertrag.git && cd balkonertrag
python3 scripts/build.py                       # baut site/ (Python ≥ 3.12, keine Abhängigkeiten)
# Vorschau: Seite erwartet den Pfad /balkonertrag/
mkdir -p /tmp/srv && ln -sfn "$PWD/site" /tmp/srv/balkonertrag && (cd /tmp/srv && python3 -m http.server 8765)
# → http://localhost:8765/balkonertrag/

# Tests (optional): pip install playwright && playwright install chromium
python tools/functest.py http://localhost:8765/balkonertrag/
python tools/screenshot.py http://localhost:8765/balkonertrag/stadt/berlin/ /tmp/b.png 390 dark full
```

Daten neu holen ist nur nötig, wenn sich Städte, Winkel oder PVGIS-Version ändern:
- `python3 scripts/fetch_pvgis.py 10000 pvgis_neu.json` erzeugt `data/pvgis_neu.json`. Danach auf `pvgis.json` umbenennen. Der Build liest per Umgebungsvariable `PVGIS_FILE` auch andere Dateien.
- Lastprofil: BDEW-Datei `BDEW_H25_G25_L25_P25_S25.xlsx`, zum Beispiel aus https://github.com/flrd/standardlastprofile (`inst/extdata/`). Dann `python3 scripts/make_load.py <datei>`.

## Geprüfte Fakten (Stand Oktober 2026, Quellen im Faktencheck)

- Solarpaket I in Kraft seit 16.05.2024: 800 VA Wechselrichter (§ 8 Abs. 5a EEG), 2.000 Wp Module, nur Marktstammdatenregister binnen 1 Monat. Keine Meldung beim Netzbetreiber.
- DIN VDE V 0126-95 seit 01.12.2025 (ohne Speicher): Schuko bis 960 Wp, darüber Einspeisesteckdose (Wieland).
- Ferraris-Zähler darf vorübergehend rückwärts laufen. Der neue Zähler darf bis 25 € brutto im Jahr kosten (§ 32 MsbG).
- § 554 BGB / § 20 WEG für Steckersolar seit 17.10.2024.
- 0 % USt (§ 12 Abs. 3 UStG), auch auf Speicher und Montage. Einkommensteuerfrei nach § 3 Nr. 72 EStG.
- Förderung Mecklenburg-Vorpommern: LFI zahlt 500 € für Mieter (bis 31.12.2027, Antrag nach Inbetriebnahme). Das Kontingent für Eigentümer ist erschöpft.
- Strompreis 35 ct (Verivox 34,4 ct am 01.10.2026). Speicher-Aufpreis 700–1.000 € (Stiftung Warentest 2026).

## Nächste sinnvolle Schritte

Siehe `PLAN.md` → „Nächste Ausbaustufen“. Mit dem größten Hebel:
1. **Einbett-Widget** (`/widget/`, `/einbinden/`) für Backlinks von Städten, Energieagenturen und Blogs. Eine github.io-Seite braucht Links.
2. **Produkt-Vergleichsseiten** (Speicher, 2.000-Wp-Sets, Halterungen) mit `data/produkte.json`. Die lohnen erst, wenn Partnerprogramme aktiv sind.
3. Weitere Ratgeber (Verschattung, Halterung, Stromzähler, Schuko gegen Wieland, Checkliste, Glossar) und Monatsseiten.
4. Sobald die Search Console läuft: Seiten mit Impressionen, aber wenig Klicks (Titel/Description) gezielt verbessern.

## Regeln, die bisher galten

- Keine Spam-Werbung, keine Massenmails, kein Auftreten im Namen des Besitzers nach außen. Keine Konten mit seiner Identität anlegen.
- Fakten nur mit Quelle. Lieber weglassen als raten. Ratgeber auf Deutsch, Du-Form, knapp.
- Commits enden mit einer `Co-Authored-By`-Zeile des jeweiligen Modells.
