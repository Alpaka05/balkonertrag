# Ziel: 200 € pro Monat

Gestartet am 07.10.2026. Ziel: dauerhaft 200 € Einnahmen pro Monat.

## Strategie

**Balkonertrag**: eine kostenlose Website mit echten Ertragsdaten für Balkonkraftwerke in ~950 deutschen Städten
(PVGIS-Daten der EU-Kommission), dazu Rechner und Ratgeber. Geld kommt über Partnerlinks (Amazon, später
Fachhändler mit 5–8 % Provision) und später Werbung.

Warum dieses Thema:
- Hohe Suchnachfrage in Deutschland („Balkonkraftwerk Ertrag [Stadt]“, „lohnt sich“, „anmelden“, „Speicher“).
- Teure Produkte (300–1.500 €): Eine Provision bringt 10–60 €, für 200 € reichen also ~10 Verkäufe im Monat.
- Echte, ortsgenaue Daten statt Textwüste: Jede Stadtseite hat eigene Messwerte. Das können Konkurrenten mit Fließtext nicht.
- Komplett statisch, kostet 0 € Betrieb (GitHub Pages).

Rechnung: ~15.000 Besucher/Monat × 3 % Klick auf Partnerlink × 5 % Kaufquote × 40 € Provision ≈ 900 €. Selbst bei
einem Viertel davon ist das Ziel erreicht. Realistische Zeit bis dahin: 4–9 Monate (Google braucht Zeit).

## Was nur du machen kannst (einmalig, zusammen ca. 30 Minuten)

1. **Impressum-Daten** in `scripts/config.py` → `IMPRESSUM` eintragen (Name, Anschrift, E-Mail). Pflicht, sobald Partnerlinks aktiv sind.
2. **Amazon PartnerNet** anmelden (partnernet.amazon.de), den Tag (z. B. `balkonertrag-21`) in `config.py` → `AMAZON_TAG` eintragen.
   Danach `python3 scripts/build.py` und pushen, oder einfach mir Bescheid geben.
3. **Google Search Console**: Eigentum der Seite bestätigen und `sitemap.xml` einreichen. Beschleunigt die Indexierung enorm.
4. Optional: **eigene Domain** (z. B. balkonertrag.de, ~10 €/Jahr). Wirkt seriöser und rankt besser als github.io.

Ich kann diese Schritte nicht für dich erledigen: Sie brauchen deine Identität, Bank-/Steuerdaten oder Zahlungen.

## Fortschritt

| Datum | Stand |
|---|---|
| 08.10.2026 | Großes Update nach Review (Design, Faktencheck, Features): neues Design-System, Rechner mit Stundensimulation (BDEW H25, 800-W-Grenze, Speicher, Ost-West, 8 Neigungen), Speicher-Rechner, Vermieter-Antrag-Generator, PLZ- und Standortsuche, teilbare Rechner-Links, Heatmap Neigung×Ausrichtung pro Stadt, Methodik-Seite, Ratgeber Winter/2000 Watt/Ost-West, Fakten korrigiert (VDE-Norm 960 Wp, Zählerkosten, Mietrecht, Förderung MV, Speicherpreise), Datenschutz ergänzt |
| 08.10.2026 | Neuer Ratgeber „Förderung“ (bundesweite Regeln, Fallen, Amortisationstabelle mit Zuschuss) + FAQ-Eintrag auf allen Stadtseiten verlinkt. Einzelne Städte-Beträge bewusst weggelassen: Quellen widersprüchlich, Primärseiten (LFI, Städte) vom Sandbox-Proxy blockiert |
| 07.10.2026 | Projekt angelegt, Daten für ~950 Städte, Generator, Rechner, 5 Ratgeber-Artikel, Veröffentlichung auf GitHub Pages |

## Nächste Ausbaustufen

- Förderung pro Stadt/Bundesland nur mit geprüften Primärquellen (Stadt-Websites) ergänzen, mit Stand-Datum – falls Zugriff möglich
- Einbett-Widget für andere Websites (Backlinks), Seite /einbinden/
- Vergleichstabellen Speicher/Sets mit Datum (data/produkte.json), sobald Partnerprogramme laufen
- Ratgeber: Verschattung, Halterungen, Versicherung, Stromzähler, Schuko vs. Wieland, Kaufen-Checkliste, Glossar
- Monatsseiten (/monat/januar/ ...) mit nationalem Monatsranking
- Vergleichsseiten für Speicher und Sets (dort sind die Provisionen am höchsten)
- Weitere Rechner-Seiten mit eigenen Suchbegriffen (Wärmepumpe, Stromkosten Geräte, PV-Dach)
