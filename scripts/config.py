"""Zentrale Einstellungen der Website. Alles, was der Betreiber ausfüllen muss, steht hier."""

SITE_NAME = "Balkonertrag"
# Ohne eigene Domain läuft die Seite unter GitHub Pages in einem Unterordner.
SITE_URL = "https://alpaka05.github.io/balkonertrag"
BASE_PATH = "/balkonertrag"

# Amazon-PartnerNet-Tag (z. B. "balkonertrag-21"). Leer = Links ohne Provision.
AMAZON_TAG = ""

# Pflichtangaben nach § 5 DDG. Solange NAME leer ist, zeigt das Impressum einen Platzhalter.
IMPRESSUM = {
    "name": "",
    "strasse": "",
    "ort": "",
    "email": "",
}

# Annahmen (Stand Oktober 2026, in den Rechnern änderbar)
STROMPREIS_CT = 35          # Verivox-Schnitt 34,4 ct (1.10.2026), Arbeitspreis ohne Grundgebühr
SET_PREIS_EUR = 350         # 800-W-Set mit 2 Modulen, Marktspanne 300–500 €
SET_WP = 900                # bleibt unter der Schuko-Grenze von 960 Wp (DIN VDE V 0126-95)
SPEICHER_PREIS_EUR = 700    # Aufpreis Speicher, Stiftung Warentest 2026: 700–1.000 €
VERBRAUCH_KWH = 2500        # Zwei-Personen-Haushalt
CO2_KG_PRO_KWH = 0.36       # Emissionsfaktor Strommix, Umweltbundesamt (rund)
# Ein Standardlastprofil ist glatter als ein echter Haushalt. Anteil des direkt nutzbaren Stroms, der dadurch
# in Wirklichkeit nicht gleichzeitig verbraucht wird (Abgleich mit Verbraucherzentrale: 30–60 % ohne, ~70 % mit Speicher).
KALIBRIERUNG = 0.20
ETA = 0.95                  # Wirkungsgrad je Lade- und Entladevorgang (zusammen ~90 %)
STANDBY_W = 8               # Eigenverbrauch des Speichers (Elektronik, Standby)
ASSET_VERSION = "2"

# IndexNow-Schlüssel (Bing/Yandex); die Datei {KEY}.txt liegt im Seiten-Stamm
INDEXNOW_KEY = "c850840793d447458f63d22a1aaf0cf5"
