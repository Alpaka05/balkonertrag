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

# Annahmen für die Wirtschaftlichkeit (Stand Oktober 2026, in den Rechnern änderbar)
STROMPREIS_CT = 35
EIGENVERBRAUCH = 0.40
SET_PREIS_EUR = 350
SET_WP = 900
