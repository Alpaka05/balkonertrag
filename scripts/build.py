"""Erzeugt die statische Website aus data/pvgis.json nach site/.

Aufruf: python3 scripts/build.py
"""
import html
import json
import math
import os
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import ratgeber  # noqa: E402
import sim  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
ASSETS = ROOT / "assets"
DATA = ROOT / "data" / os.environ.get("PVGIS_FILE", "pvgis.json")
TODAY = date.today()

STATES = {
    "01": "Baden-Württemberg", "02": "Bayern", "03": "Bremen", "04": "Hamburg", "05": "Hessen",
    "06": "Niedersachsen", "07": "Nordrhein-Westfalen", "08": "Rheinland-Pfalz", "09": "Saarland",
    "10": "Schleswig-Holstein", "11": "Brandenburg", "12": "Mecklenburg-Vorpommern", "13": "Sachsen",
    "14": "Sachsen-Anhalt", "15": "Thüringen", "16": "Berlin",
}
ASPECT_NAMES = {"S": "Süden", "SO": "Südosten", "SW": "Südwesten", "O": "Osten", "W": "Westen"}
HEAT_ORDER = ["O", "SO", "S", "SW", "W"]
SHORT = {"S": "Süd", "SO": "Südost", "SW": "Südwest", "O": "Ost", "W": "West"}
ANGLES = [90, 75, 60, 45, 35, 25, 15]
ANGLE_LABELS = {90: "90° (Geländer)", 75: "75°", 60: "60° (angekippt)", 45: "45°",
                35: "35° (aufgeständert)", 25: "25°", 15: "15°", 0: "0° (flach)"}
MONTHS_LONG = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]
MONTHS = ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
KWP = C.SET_WP / 1000

e = html.escape


def slug(s):
    s = s.lower()
    for a, b in (("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss"), ("é", "e")):
        s = s.replace(a, b)
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def url(path):
    return f"{C.BASE_PATH}/{path}".replace("//", "/")


def fmt(x, d=0):
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def euro(x):
    return fmt(x) + " €"


def datum(d):
    return f"{d.day}. {MONTHS_LONG[d.month - 1]} {d.year}"


def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def amazon(query):
    from urllib.parse import quote_plus
    return f"https://www.amazon.de/s?k={quote_plus(query)}&tag={C.AMAZON_TAG}"


def more(href, text):
    return f'<a class="more" href="{href}">{text} <span aria-hidden="true">→</span></a>'


ICON_SHARE = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M6.5 9.5l3-3M7 4.5l1.3-1.3a2.5 2.5 0 013.5 3.5L10.5 8M9 11.5l-1.3 1.3a2.5 2.5 0 01-3.5-3.5L5.5 8"/></svg>'
ICON_LOC = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="8" cy="8" r="5"/><circle cx="8" cy="8" r="1.5" fill="currentColor"/><path d="M8 1v2M8 13v2M1 8h2M13 8h2"/></svg>'
ICON_PRINT = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><path d="M4 6V2h8v4M4 12H2.5V6.5h11V12H12M4 9.5h8V14H4z"/></svg>'
ICON_COPY = '<svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><rect x="5" y="5" width="9" height="9" rx="1.5"/><path d="M11 5V3.5A1.5 1.5 0 009.5 2h-6A1.5 1.5 0 002 3.5v6A1.5 1.5 0 003.5 11H5"/></svg>'


# ---------------------------------------------------------------- Layout

NAV = [("rechner/", "Rechner", ""), ("speicher-rechner/", "Speicher", "opt"), ("staedte/", "Städte", ""), ("ratgeber/", "Ratgeber", "")]


def page(path, title, desc, body, schema=None, crumbs=None, active=None, byline=False):
    canonical = f"{C.SITE_URL}/{path}"
    crumb_html = ""
    if crumbs:
        items = [f'<li><a href="{url("")}">Start</a></li>'] + [
            f'<li><a href="{url(p)}">{e(n)}</a></li>' if p else f'<li aria-current="page">{e(n)}</li>' for n, p in crumbs]
        crumb_html = f'<nav class="crumbs" aria-label="Brotkrumen"><ol>{"".join(items)}</ol></nav>'
        schema = list(filter(None, [schema, {
            "@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
                {"@type": "ListItem", "position": i + 1, "name": n, "item": f"{C.SITE_URL}/{p}" if p is not None else canonical}
                for i, (n, p) in enumerate([("Start", "")] + list(crumbs))]}]))
    if byline:
        body = body.replace("</h1>", f'</h1>\n<p class="byline">Von der {C.SITE_NAME}-Redaktion · Daten: PVGIS 5.3 (SARAH-3) · Aktualisiert: {datum(TODAY)}</p>', 1)
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    nav = "".join(f'<a href="{url(p)}"{" aria-current=page" if p == active else ""}{f" class={c}" if c else ""}>{n}</a>' for p, n, c in NAV)
    doc = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light dark">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="de_DE">
<meta property="og:site_name" content="{C.SITE_NAME}">
<link rel="icon" href="{url('assets/icon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{url('assets/style.css')}?v={C.ASSET_VERSION}">
{ld}
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{url('')}"><img src="{url('assets/icon.svg')}" alt="" width="28" height="28">{C.SITE_NAME}</a>
<nav aria-label="Hauptnavigation">{nav}</nav>
</div></header>
<main class="wrap">
{crumb_html}
{body}
</main>
<footer><div class="wrap cols3">
<div><h2>{C.SITE_NAME}</h2><p>Unabhängige Ertragsdaten für Balkonkraftwerke in {C.N_CITIES} deutschen Städten. Ertragsdaten: <a href="https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en" rel="noopener">PVGIS 5.3</a> der EU-Kommission (SARAH-3, 14 % Systemverluste), Lastprofil: BDEW H25, Orte: <a href="https://www.geonames.org/" rel="noopener">GeoNames</a> (CC BY 4.0). Alle Angaben sind Schätzungen ohne Gewähr. <a href="{url('methodik/')}">So rechnen wir</a>.</p></div>
<div><h2>Werkzeuge</h2><ul><li><a href="{url('rechner/')}">Ertragsrechner</a></li><li><a href="{url('speicher-rechner/')}">Speicher-Rechner</a></li><li><a href="{url('vermieter-antrag/')}">Antrag an den Vermieter</a></li><li><a href="{url('staedte/')}">Alle Städte</a></li></ul></div>
<div><h2>Über</h2><ul><li><a href="{url('methodik/')}">Methodik</a></li><li><a href="{url('impressum/')}">Impressum</a></li><li><a href="{url('datenschutz/')}">Datenschutz</a></li><li>Seite aktualisiert: {datum(TODAY)}</li></ul></div>
</div></footer>
<script src="{url('assets/app.js')}?v={C.ASSET_VERSION}" defer></script>
</body>
</html>
"""
    target = OUT / path / "index.html" if not path.endswith(".html") else OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc)
    return canonical


def search_form(placeholder="Stadt oder PLZ"):
    return f"""<div class="search-wrap">
<form class="search" role="search">
<input type="search" name="q" list="citylist" placeholder="{placeholder}" aria-label="Stadt oder Postleitzahl" autocomplete="off">
<button class="btn btn-primary" type="submit">Ertrag anzeigen</button>
<button class="btn btn-ghost" type="button" data-locate>{ICON_LOC}<span>Mein Standort</span></button>
</form>
<p class="search-msg" aria-live="polite"></p>
</div>"""


def calculator(title, months, *, wp=None, annual=None, batt=0, aspect="S", angle=90, cost=None, share=True):
    """Interaktiver Rechner mit Stundensimulation. months = {"S35": [12 Monatswerte kWh/kWp], ...}."""
    wp = wp or C.SET_WP
    annual = annual or C.VERBRAUCH_KWH
    opts = "".join(f'<option value="{k}"{" selected" if k == aspect else ""}>{v}</option>' for k, v in ASPECT_NAMES.items())
    opts += f'<option value="OW"{" selected" if aspect == "OW" else ""}>Ost-West (je zur Hälfte)</option>'
    angles = "".join(f'<option value="{a}"{" selected" if a == angle else ""}>{ANGLE_LABELS[a]}</option>' for a in ANGLES + [0])

    def num(name, label, value, unit, mn, mx, step):
        return (f'<label>{label}<span class="field"><input name="{name}" type="number" inputmode="decimal" value="{value}" min="{mn}" max="{mx}" step="{step}">'
                f'<span class="unit">{unit}</span></span></label>')

    return f"""
<section class="calc card" data-m='{json.dumps(months, separators=(",", ":"))}' data-co2="{C.CO2_KG_PRO_KWH}"{" data-share" if share else ""} aria-label="Rechner">
<h2>{title}</h2>
<div class="grid">
<label>Ausrichtung<select name="aspect">{opts}</select></label>
<label>Neigung<select name="angle">{angles}</select></label>
{num("wp", "Modulleistung", wp, "Wp", 100, 2000, 10)}
{num("batt", "Speicher", batt, "kWh", 0, 10, 0.1)}
<p class="sub">Dein Haushalt</p>
{num("annual", "Verbrauch pro Jahr", annual, "kWh", 500, 10000, 100)}
{num("price", "Strompreis", C.STROMPREIS_CT, "ct/kWh", 10, 80, 0.5)}
{num("cost", "Anschaffung", cost or C.SET_PREIS_EUR, "€", 0, 5000, 10)}
</div>
<div class="results" aria-live="polite">
<div><span class="big" data-out="kwh">–</span><small>kWh Strom pro Jahr</small></div>
<div><span class="big" data-out="self">–</span><small data-out="selfkwh">Eigenverbrauch</small></div>
<div><span class="big" data-out="eur">–</span><small>Ersparnis pro Jahr</small></div>
<div><span class="big" data-out="years">–</span><small>bis sich die Anlage bezahlt hat</small></div>
</div>
<p class="assumptions" data-out="assume"></p>
<p class="note" data-out="note"></p>
<figure><svg class="chart" viewBox="0 0 600 230" role="img" aria-label="Monatlicher Ertrag und Eigenverbrauch"></svg>
<div class="legend"><span>erzeugt</span><span class="alt">selbst genutzt</span></div></figure>
<div class="actions noprint">{'<button class="btn btn-ghost" type="button" data-share-btn>' + ICON_SHARE + '<span> Ergebnis teilen</span></button>' if share else ''}
<span class="small" data-out="co2"></span></div>
<details class="method"><summary>So rechnen wir</summary>
<p>Wir simulieren jede Stunde eines Jahres: Solarertrag aus PVGIS-Daten für diesen Ort, Ausrichtung und Neigung, dein Verbrauch nach dem BDEW-Standardlastprofil für Haushalte (H25), die 800-W-Grenze des Wechselrichters und, falls angegeben, ein Speicher mit 90 % Wirkungsgrad und {C.STANDBY_W} W Eigenverbrauch. Gespart wird nur der Strom, den du selbst nutzt; Überschuss wird nicht vergütet.</p>
<p>Ein Standardlastprofil ist der Durchschnitt vieler Haushalte und verläuft glatter als dein echter Verbrauch. Wir rechnen deshalb mit einem Abschlag von {fmt(C.KALIBRIERUNG * 100)} % auf den direkt genutzten Strom. <a href="{url('methodik/')}">Mehr zur Methodik</a></p>
</details>
</section>"""


def product_box():
    if not C.AMAZON_TAG:
        return ""
    links = [
        ("800-W-Komplettsets", "Balkonkraftwerk 800W Komplettset"),
        ("Halterungen fürs Balkongeländer", "Balkonkraftwerk Halterung Balkongeländer"),
        ("Balkonkraftwerk-Speicher", "Balkonkraftwerk Speicher"),
        ("Strommessgerät für die Steckdose", "Energiekostenmessgerät Steckdose"),
    ]
    lis = "".join(f'<li><a href="{amazon(q)}" rel="sponsored noopener" target="_blank">{n}*</a></li>' for n, q in links)
    return f'<aside class="card ad"><p class="tag">Anzeige</p><h3>Passendes Zubehör vergleichen</h3><ul>{lis}</ul><p class="small">* Partnerlink: Wenn du darüber kaufst, erhalten wir eine kleine Provision. Der Preis ändert sich für dich nicht.</p></aside>'


def next_steps():
    return f"""<section class="box"><h2>Nächste Schritte</h2><ol class="steps">
<li><a href="{url('vermieter-antrag/')}">Zustimmung einholen</a>: Als Mieter oder in einer Eigentümergemeinschaft brauchst du sie. Unser Generator schreibt den Antrag für dich.</li>
<li><a href="{url('ratgeber/balkonkraftwerk-foerderung/')}">Förderung prüfen</a>, bevor du kaufst. Viele Programme zahlen nur bei Antrag vorher.</li>
<li>Set kaufen und montieren, dann innerhalb eines Monats im <a href="{url('ratgeber/balkonkraftwerk-anmelden/')}">Marktstammdatenregister anmelden</a>.</li>
</ol></section>"""


def heatmap(months, wp):
    """Tabelle Neigung × Ausrichtung mit Jahreserträgen, eingefärbt nach Höhe."""
    vals = {(a, g): sum(months[f"{a}{g}"]) * wp / 1000 for a in HEAT_ORDER for g in ANGLES}
    flat = sum(months["F0"]) * wp / 1000
    lo, hi = min(list(vals.values()) + [flat]), max(vals.values())
    best = max(vals, key=vals.get)

    def cell(v, is_best=False):
        p = round(6 + 50 * (v - lo) / (hi - lo or 1))
        return f'<td class="num{" best" if is_best else ""}" style="background:color-mix(in srgb,var(--accent) {p}%,var(--surface))">{fmt(v)}</td>'

    head = "".join(f'<th scope="col">{SHORT[a]}</th>' for a in HEAT_ORDER)
    rows = "".join(f'<tr><th scope="row">{g}°</th>{"".join(cell(vals[(a, g)], (a, g) == best) for a in HEAT_ORDER)}</tr>' for g in ANGLES)
    rows += f'<tr><th scope="row">flach</th><td colspan="5" class="num" style="background:color-mix(in srgb,var(--accent) {round(6 + 50 * (flat - lo) / (hi - lo or 1))}%,var(--surface))">{fmt(flat)}</td></tr>'
    return f'<div class="scroll"><table class="heat"><thead><tr><th>Neigung</th>{head}</tr></thead><tbody>{rows}</tbody></table></div>', best


def bars(values, values2=None, unit="kWh"):
    w, h, pad = 600, 230, 28
    mx = max(values + (values2 or [])) or 1
    bw = (w - pad) / 12
    out = [f'<line class="axis" x1="{pad}" x2="{w}" y1="{h - pad}" y2="{h - pad}"/>']
    for i, v in enumerate(values):
        x = pad + i * bw
        if values2:
            bw2 = (bw - 8) / 2
            for j, vv in enumerate((v, values2[i])):
                bh = (h - 2 * pad) * vv / mx
                out.append(f'<rect{" class=alt" if j else ""} x="{x + 4 + j * bw2:.1f}" y="{h - pad - bh:.1f}" width="{bw2 - 1:.1f}" height="{bh:.1f}" rx="2"><title>{MONTHS[i]}: {fmt(vv)} {unit}</title></rect>')
        else:
            bh = (h - 2 * pad) * v / mx
            out.append(f'<rect x="{x + 4:.1f}" y="{h - pad - bh:.1f}" width="{bw - 8:.1f}" height="{bh:.1f}" rx="3"><title>{MONTHS[i]}: {fmt(v)} {unit}</title></rect>'
                       f'<text x="{x + bw / 2:.1f}" y="{h - pad - bh - 6:.1f}" class="v">{fmt(v)}</text>')
        out.append(f'<text x="{x + bw / 2:.1f}" y="{h - 8}">{MONTHS[i]}</text>')
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Monatlicher Ertrag in {unit}">{"".join(out)}</svg>'


def num_td(v, d=0, suffix=""):
    return f'<td class="num" data-v="{v:.2f}">{fmt(v, d)}{suffix}</td>'


# ---------------------------------------------------------------- Stadtseiten

def build_city(name, c, ctx):
    s = slug(name)
    y, m = c["y"], c["m"]
    state = STATES.get(c["state"], "")
    kwh90, kwh35 = y["S90"] * KWP, y["S35"] * KWP
    rank, total, nat_avg = ctx["ranks"][name], len(ctx["ranks"]), ctx["nat_avg"]
    state_avg = ctx["state_avg"].get(state, nat_avg)
    pct_vs_nat = (y["S35"] / nat_avg - 1) * 100
    near = sorted((n for n in ctx["cities"] if n != name), key=lambda n: dist(c, ctx["cities"][n]))[:8]
    r90 = ctx["sims"][name]
    years = C.SET_PREIS_EUR / r90["eur"]

    rows = "".join(
        f"<tr><th scope=row>{ASPECT_NAMES[a]}</th>{num_td(y[a + '90'] * KWP)}{num_td(y[a + '60'] * KWP)}{num_td(y[a + '35'] * KWP)}</tr>"
        for a in ASPECT_NAMES)
    monthly90 = [v * KWP for v in m["S90"]]
    monthly35 = [v * KWP for v in m["S35"]]
    best, worst = max(range(12), key=lambda i: monthly90[i]), min(range(12), key=lambda i: monthly90[i])
    winter90 = sum(monthly90[i] for i in (10, 11, 0, 1))
    winter35 = sum(monthly35[i] for i in (10, 11, 0, 1))
    heat, (ba, bg) = heatmap(m, C.SET_WP)
    near_html = "".join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a><small>{fmt(ctx["cities"][n]["y"]["S90"] * KWP)} kWh</small></li>' for n in near)

    faq = [
        (f"Wie viel Strom erzeugt ein Balkonkraftwerk in {name}?",
         f"Ein typisches Set mit {C.SET_WP} Wp Modulleistung erzeugt in {name} senkrecht am Balkongeländer nach Süden etwa {fmt(kwh90)} kWh pro Jahr, "
         f"schräg aufgeständert (35°) etwa {fmt(kwh35)} kWh. Grundlage sind langjährige Satellitendaten von PVGIS für den Standort {fmt(c['lat'], 2)}° N, {fmt(c['lon'], 2)}° O."),
        (f"Lohnt sich ein Balkonkraftwerk in {name}?",
         f"In einem Haushalt mit {fmt(C.VERBRAUCH_KWH)} kWh Jahresverbrauch nutzt du am Süd-Balkon rund {fmt(r90['used'])} kWh selbst. Bei {fmt(C.STROMPREIS_CT, 1)} ct/kWh "
         f"spart das etwa {euro(r90['eur'])} im Jahr. Ein Set für {euro(C.SET_PREIS_EUR)} hat sich damit nach etwa {fmt(years, 1)} Jahren bezahlt; die Module halten meist 20 Jahre und länger."),
        (f"Welcher Monat bringt in {name} den meisten Ertrag?",
         f"Senkrecht nach Süden montiert liefert die Anlage im {MONTHS_LONG[best]} am meisten (etwa {fmt(monthly90[best])} kWh) "
         f"und im {MONTHS_LONG[worst]} am wenigsten (etwa {fmt(monthly90[worst])} kWh). Von November bis Februar bringt die senkrechte Montage hier sogar "
         f"{'mehr' if winter90 > winter35 else 'fast so viel'} als die schräge ({fmt(winter90)} statt {fmt(winter35)} kWh)."),
        (f"Welche Ausrichtung ist in {name} am besten?",
         f"Am meisten bringt {ASPECT_NAMES[ba]} mit {bg}° Neigung: rund {fmt(y[f'{ba}{bg}'] * KWP)} kWh mit {C.SET_WP} Wp. Ost oder West senkrecht liefert etwa "
         f"{fmt(y['O90'] * KWP)} bis {fmt(y['W90'] * KWP)} kWh, also gut {fmt(y['W90'] / y[f'{ba}{bg}'] * 100)} % davon."),
        ("Muss ich ein Balkonkraftwerk anmelden?",
         "Ja, aber nur noch im Marktstammdatenregister der Bundesnetzagentur. Die frühere Meldung beim Netzbetreiber ist seit dem Solarpaket I entfallen. "
         f'Mehr dazu im <a href="{url("ratgeber/balkonkraftwerk-anmelden/")}">Ratgeber zur Anmeldung</a>.'),
        (f"Gibt es in {name} eine Förderung für Balkonkraftwerke?",
         "Bundesweit gibt es keinen Zuschuss, aber 0 % Mehrwertsteuer beim Kauf. Kommunale Programme ändern sich häufig; frag bei deiner Stadt oder den Stadtwerken nach "
         f'und stelle den Antrag vor dem Kauf. Details im <a href="{url("ratgeber/balkonkraftwerk-foerderung/")}">Ratgeber zur Förderung</a>.'),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in faq)
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faq]}

    body = f"""
<h1>Balkonkraftwerk in {e(name)}: Ertrag &amp; Ersparnis</h1>
<p class="lead">In {e(name)} erzeugt ein Balkonkraftwerk mit {C.SET_WP} Wp am Süd-Balkon rund <strong>{fmt(kwh90)} kWh</strong> im Jahr, aufgeständert sogar <strong>{fmt(kwh35)} kWh</strong>.
Das spart einem typischen Haushalt etwa <strong>{euro(r90['eur'])}–{euro(ctx['sims35'][name]['eur'])}</strong> Stromkosten pro Jahr.</p>
<div class="facts">
<div><b>{rank}.</b><small>von {total} Städten im Ertrags-Ranking</small></div>
<div><b>{'+' if pct_vs_nat >= 0 else '−'}{fmt(abs(pct_vs_nat), 1)} %</b><small>Sonnenertrag gegenüber dem deutschen Schnitt</small></div>
<div><b>{fmt(years, 1)} Jahre</b><small>bis sich ein {euro(C.SET_PREIS_EUR)}-Set bezahlt hat</small></div>
</div>
{calculator(f"Rechner für {e(name)}", m)}
<section>
<h2>Welche Ausrichtung und Neigung in {e(name)} am meisten bringt</h2>
<p>Jahresertrag in kWh für ein Set mit {C.SET_WP} Wp. Je kräftiger die Farbe, desto mehr Strom; das beste Feld ist umrandet.</p>
{heat}
<h3>Die wichtigsten Montagearten im Vergleich</h3>
<div class="scroll"><table>
<thead><tr><th>Ausrichtung</th><th class="num">Geländer 90°</th><th class="num">Angekippt 60°</th><th class="num">Aufgeständert 35°</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="small">kWh pro Jahr mit {C.SET_WP} Wp, ohne Verschattung. Mehr dazu im <a href="{url('ratgeber/ausrichtung-neigung/')}">Ratgeber zu Ausrichtung und Neigung</a>.</p>
</section>
<section>
<h2>Monatlicher Ertrag in {e(name)}</h2>
<figure>{bars(monthly90, monthly35)}
<div class="legend"><span>Senkrecht am Geländer (90°)</span><span class="alt">Aufgeständert (35°)</span></div>
<figcaption>kWh pro Monat, {C.SET_WP} Wp, Ausrichtung Süd</figcaption></figure>
<p>Senkrechte Module liefern im Winter vergleichsweise viel, weil die tief stehende Sonne fast frontal auf sie trifft. Im Sommer steht die Sonne hoch, dann ist die schräge Montage klar im Vorteil. Mehr im <a href="{url('ratgeber/balkonkraftwerk-winter/')}">Ratgeber zum Winterertrag</a>.</p>
</section>
{product_box()}
<section>
<h2>{e(name)} im Vergleich</h2>
<p>Mit {fmt(y['S35'])} kWh pro kWp und Jahr (Süd, 35°) liegt {e(name)} {fmt(abs(pct_vs_nat), 1)} % {'über' if pct_vs_nat >= 0 else 'unter'} dem Durchschnitt aller {total} ausgewerteten deutschen Städte
{f'und {fmt(abs(y["S35"] / state_avg - 1) * 100, 1)} % {"über" if y["S35"] >= state_avg else "unter"} dem Schnitt in <a href="{url("bundesland/" + slug(state) + "/")}">{e(state)}</a>' if state else ''}.</p>
<h3>Städte in der Nähe</h3>
<ul class="cols">{near_html}</ul>
</section>
{next_steps()}
<section class="faq">
<h2>Häufige Fragen</h2>
{faq_html}
</section>
"""
    crumbs = ([(state, f"bundesland/{slug(state)}/")] if state and state != name else [("Städte", "staedte/")]) + [(name, None)]
    return page(f"stadt/{s}/", f"Balkonkraftwerk {name}: Ertrag {fmt(kwh90)}–{fmt(kwh35)} kWh/Jahr | {C.SITE_NAME}",
                f"So viel Strom erzeugt ein Balkonkraftwerk in {name}: {fmt(kwh90)} kWh am Balkon, {fmt(kwh35)} kWh aufgeständert. Ersparnis, beste Ausrichtung und Monatswerte aus PVGIS-Daten.",
                body, schema, crumbs, byline=True)


TABLE_HEAD = ('<thead><tr><th data-sort scope="col">Stadt</th><th class="num" data-sort scope="col">Balkon 90° Süd</th>'
              '<th class="num" data-sort scope="col">Aufgeständert 35° Süd</th><th class="num" data-sort scope="col">Ersparnis/Jahr</th></tr></thead>')


def city_rows(names, ctx):
    cs = ctx["cities"]
    return "".join(
        f'<tr><td><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></td>{num_td(cs[n]["y"]["S90"] * KWP, suffix=" kWh")}'
        f'{num_td(cs[n]["y"]["S35"] * KWP, suffix=" kWh")}{num_td(ctx["sims"][n]["eur"], suffix=" €")}</tr>'
        for n in names)


def avg_months(cities, names):
    keys = next(iter(cities.values()))["m"]
    return {k: [round(sum(cities[n]["m"][k][i] for n in names) / len(names), 1) for i in range(12)] for k in keys}


# ---------------------------------------------------------------- Hauptprogramm

def main():
    cities = json.loads(DATA.read_text())
    C.N_CITIES = fmt(len(cities))
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(ASSETS, OUT / "assets")
    urls = []

    nat_avg = sum(c["y"]["S35"] for c in cities.values()) / len(cities)
    by_yield = sorted(cities, key=lambda n: -cities[n]["y"]["S35"])
    ranks = {n: i + 1 for i, n in enumerate(by_yield)}
    by_state = {}
    for n, c in cities.items():
        by_state.setdefault(STATES.get(c["state"], ""), []).append(n)
    state_avg = {s: sum(cities[n]["y"]["S35"] for n in ns) / len(ns) for s, ns in by_state.items()}
    nat_m = avg_months(cities, list(cities))
    nat_y = {k: sum(v) for k, v in nat_m.items()}

    # Stundensimulation für die Standardfälle (gleiches Modell wie der Rechner im Browser)
    model = sim.Model(ASSETS)
    sims = {n: model.run(c["m"]["S90"], "S90", C.SET_WP, C.VERBRAUCH_KWH) for n, c in cities.items()}
    sims35 = {n: model.run(c["m"]["S35"], "S35", C.SET_WP, C.VERBRAUCH_KWH) for n, c in cities.items()}
    ctx = {"cities": cities, "ranks": ranks, "nat_avg": nat_avg, "state_avg": state_avg, "sims": sims, "sims35": sims35}

    for n, c in cities.items():
        urls.append(build_city(n, c, ctx))

    # Bundesländer
    state_rank = sorted((s for s in by_state if s), key=lambda s: -state_avg[s])
    for s in state_rank:
        ns = sorted(by_state[s], key=lambda n: -cities[n]["pop"])
        top = sorted(ns, key=lambda n: -cities[n]["y"]["S35"])
        body = f"""<h1>Balkonkraftwerk in {e(s)}: Ertrag in {len(ns)} Städten</h1>
<p class="lead">Im Schnitt erzeugt ein Balkonkraftwerk mit {C.SET_WP} Wp in {e(s)} aufgeständert nach Süden <strong>{fmt(state_avg[s] * KWP)} kWh</strong> pro Jahr.
Am sonnigsten ist <a href="{url('stadt/' + slug(top[0]) + '/')}">{e(top[0])}</a>, am wenigsten Ertrag gibt es in {e(top[-1])}. {e(s)} liegt auf Platz {state_rank.index(s) + 1} von {len(state_rank)} Bundesländern.</p>
{calculator(f"Rechner für {e(s)} (Landesdurchschnitt)", avg_months(cities, ns))}
<h2>Alle Städte in {e(s)}</h2>
<p class="small">Klick auf eine Spaltenüberschrift sortiert die Tabelle.</p>
<div class="scroll"><table>{TABLE_HEAD}<tbody>{city_rows(ns, ctx)}</tbody></table></div>"""
        urls.append(page(f"bundesland/{slug(s)}/", f"Balkonkraftwerk {s}: Ertrag in {len(ns)} Städten | {C.SITE_NAME}",
                         f"Wie viel bringt ein Balkonkraftwerk in {s}? Ertrag, Ersparnis und Ranking für {len(ns)} Städte auf Basis von PVGIS-Daten.",
                         body, crumbs=[("Städte", "staedte/"), (s, None)], active="staedte/"))

    # Städteübersicht
    big = sorted(cities, key=lambda n: -cities[n]["pop"])
    datalist = f'<datalist id="citylist">{"".join(f"<option value=\"{e(n)}\">" for n in big)}</datalist>'
    state_rows = "".join(f'<tr><td class="num">{i + 1}.</td><td><a href="{url("bundesland/" + slug(s) + "/")}">{e(s)}</a></td>{num_td(state_avg[s] * KWP, suffix=" kWh")}<td class="num">{len(by_state[s])}</td></tr>' for i, s in enumerate(state_rank))
    body = f"""<h1>Balkonkraftwerk-Ertrag in {len(cities)} deutschen Städten</h1>
<p class="lead">Wähle deine Stadt oder gib deine Postleitzahl ein. Alle Werte stammen aus PVGIS-Satellitendaten der EU-Kommission.</p>
{search_form()}{datalist}
<h2>Bundesländer-Ranking</h2>
<div class="scroll"><table><thead><tr><th class="num">#</th><th>Bundesland</th><th class="num">Ertrag ({C.SET_WP} Wp, 35° Süd)</th><th class="num">Städte</th></tr></thead><tbody>{state_rows}</tbody></table></div>
<h2>Die sonnigsten Städte</h2>
<div class="scroll"><table>{TABLE_HEAD}<tbody>{city_rows(by_yield[:25], ctx)}</tbody></table></div>
<h2>Alle Städte nach Einwohnerzahl</h2>
<ul class="cols">{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></li>' for n in big)}</ul>"""
    urls.append(page("staedte/", f"Balkonkraftwerk-Ertrag für {len(cities)} Städte in Deutschland | {C.SITE_NAME}",
                     f"Ertrag eines Balkonkraftwerks in {len(cities)} deutschen Städten und allen Bundesländern im Vergleich. Mit Ranking der sonnigsten Orte und PLZ-Suche.",
                     body, crumbs=[("Städte", None)], active="staedte/"))
    (OUT / "assets" / "cities.json").write_text(json.dumps(
        {n: [slug(n), round(cities[n]["lat"], 3), round(cities[n]["lon"], 3)] for n in big}, ensure_ascii=False, separators=(",", ":")))

    # PLZ -> nächste Stadt
    plz = {}
    pts = [(slug(n), math.radians(cities[n]["lat"]), math.radians(cities[n]["lon"])) for n in big]
    for line in (ROOT / "data" / "plz.tsv").read_text().splitlines():
        if line.startswith("#"):
            continue
        p, la, lo = line.split("\t")
        la, lo = math.radians(float(la)), math.radians(float(lo))
        plz[p] = min(pts, key=lambda t: (t[1] - la) ** 2 + ((t[2] - lo) * math.cos(la)) ** 2)[0]
    (OUT / "assets" / "plz.json").write_text(json.dumps(plz, separators=(",", ":")))

    # Rechner
    body = f"""<h1>Balkonkraftwerk-Rechner</h1>
<p class="lead">Wie viel Strom erzeugt dein Balkonkraftwerk, wie viel davon nutzt du selbst, und wann hat es sich bezahlt? Der Rechner simuliert jede Stunde eines Jahres. Die Grundwerte sind der Durchschnitt aus {len(cities)} deutschen Städten; für deinen Ort wähle <a href="{url('staedte/')}">deine Stadt</a>.</p>
{calculator("Ertrag, Eigenverbrauch &amp; Amortisation", nat_m)}
{product_box()}
<h2>Was die Eingaben bedeuten</h2>
<ul class="prose">
<li><b>Ausrichtung und Neigung:</b> Senkrecht am Geländer sind 90°, ein Aufständer auf dem Boden oder Flachdach meist 25–35°. „Ost-West“ verteilt die Module je zur Hälfte auf beide Seiten.</li>
<li><b>Modulleistung:</b> Die Summe der Watt-Peak-Angaben aller Module, typisch 800–900 Wp bei zwei Modulen. Erlaubt sind bis zu 2.000 Wp.</li>
<li><b>Speicher:</b> Nutzbare Kapazität in kWh, 0 für ohne. Gängige Balkonspeicher haben 1,6–2,7 kWh je Einheit.</li>
<li><b>Stromverbrauch:</b> Steht auf deiner Jahresabrechnung. Ein Ein-Personen-Haushalt liegt oft bei 1.500 kWh, zwei Personen bei 2.500 kWh, eine Familie bei 3.500–4.500 kWh.</li>
</ul>
<p>{more(url('methodik/'), 'Ausführliche Methodik')}</p>"""
    urls.append(page("rechner/", f"Balkonkraftwerk-Rechner: Ertrag, Eigenverbrauch & Amortisation | {C.SITE_NAME}",
                     "Kostenloser Balkonkraftwerk-Rechner mit Stundensimulation: Ertrag, Eigenverbrauch, Ersparnis und Amortisation für jede Ausrichtung, Neigung und mit Speicher.",
                     body, crumbs=[("Rechner", None)], active="rechner/"))

    # Speicher-Rechner
    model_rows = []
    nat_s35 = nat_m["S35"]
    base0 = model.run(nat_s35, "S35", 2000, C.VERBRAUCH_KWH)
    for b in (0, 1, 1.6, 2, 2.7, 4, 5.4):
        r = model.run(nat_s35, "S35", 2000, C.VERBRAUCH_KWH, b)
        model_rows.append(f'<tr><td class="num">{fmt(b, 1) if b else "ohne"}{" kWh" if b else ""}</td>{num_td(r["pv"], suffix=" kWh")}{num_td(r["used"] / r["pv"] * 100, suffix=" %")}{num_td(r["eur"], suffix=" €")}'
                          f'{num_td(r["eur"] - base0["eur"], suffix=" €") if b else "<td class=num>–</td>"}</tr>')
    body = f"""<h1>Balkonkraftwerk-Speicher-Rechner</h1>
<p class="lead">Lohnt sich ein Speicher für dein Balkonkraftwerk, und wie groß sollte er sein? Der Rechner simuliert Stunde für Stunde, wie viel Solarstrom du mit und ohne Speicher selbst nutzt.</p>
{calculator("Speicher durchrechnen", nat_m, wp=2000, batt=2, angle=35, cost=1300)}
{product_box()}
<h2>Wie viel Speicher ist sinnvoll?</h2>
<p>Beispiel: {fmt(2000)} Wp, Süd, 35° aufgeständert, {fmt(C.VERBRAUCH_KWH)} kWh Jahresverbrauch, deutscher Durchschnittsstandort, {fmt(C.STROMPREIS_CT, 1)} ct/kWh.</p>
<div class="scroll"><table><thead><tr><th class="num">Speicher</th><th class="num">Nutzbarer Ertrag</th><th class="num">Eigenverbrauch</th><th class="num">Ersparnis/Jahr</th><th class="num">Mehr als ohne</th></tr></thead><tbody>{''.join(model_rows)}</tbody></table></div>
<p>Die ersten 1–2 kWh bringen am meisten. Jede weitere kWh wird seltener ganz gefüllt und spart deshalb weniger. Ob sich der Aufpreis lohnt, siehst du, wenn du ihn durch die zusätzliche Ersparnis teilst.</p>
<p>{more(url('ratgeber/speicher-lohnt-sich/'), 'Ratgeber: Lohnt sich ein Speicher?')}</p>"""
    urls.append(page("speicher-rechner/", f"Balkonkraftwerk-Speicher-Rechner: Lohnt sich ein Speicher? | {C.SITE_NAME}",
                     "Rechne nach, ob sich ein Speicher für dein Balkonkraftwerk lohnt: Eigenverbrauch, Ersparnis und sinnvolle Speichergröße mit Stundensimulation.",
                     body, crumbs=[("Speicher-Rechner", None)], active="speicher-rechner/"))

    # Vermieter-Antrag
    urls.append(page("vermieter-antrag/", f"Balkonkraftwerk: Antrag an den Vermieter (Muster & Generator) | {C.SITE_NAME}",
                     "Kostenloser Generator für den Antrag an Vermieter oder Eigentümergemeinschaft: Daten eintragen, Brief ausdrucken oder kopieren. Mit Rechtslage seit Oktober 2024.",
                     ratgeber.antrag_page(url, {"print": ICON_PRINT, "copy": ICON_COPY}), crumbs=[("Antrag an den Vermieter", None)]))

    # Methodik
    urls.append(page("methodik/", f"Methodik: So berechnen wir den Ertrag | {C.SITE_NAME}",
                     "Datenquellen, Annahmen und Rechenweg hinter den Ertrags- und Ersparniswerten von Balkonertrag.",
                     ratgeber.methodik_page(url, fmt, C), crumbs=[("Methodik", None)], byline=True))

    # Ratgeber
    actx = {"cities": cities, "nat_y": nat_y, "nat_m": nat_m, "state_avg": state_avg, "state_rank": state_rank, "by_yield": by_yield,
            "KWP": KWP, "fmt": fmt, "euro": euro, "url": url, "slug": slug, "C": C, "model": model, "bars": bars, "more": more}
    arts = ratgeber.articles(actx)
    for a in arts:
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "dateModified": TODAY.isoformat(),
                  "inLanguage": "de", "author": {"@type": "Organization", "name": C.SITE_NAME}}
        urls.append(page(f"ratgeber/{a['slug']}/", f"{a['title']} | {C.SITE_NAME}", a["desc"],
                         f"<article class='prose'><h1>{e(a['title'])}</h1>{a['html']}</article>{product_box()}{next_steps()}", schema,
                         [("Ratgeber", "ratgeber/"), (a["title"], None)], active="ratgeber/", byline=True))
    lis = "".join(f'<li><a href="{url("ratgeber/" + a["slug"] + "/")}">{e(a["title"])}</a><p>{e(a["desc"])}</p></li>' for a in arts)
    urls.append(page("ratgeber/", f"Balkonkraftwerk-Ratgeber | {C.SITE_NAME}", "Anmeldung, Förderung, Ausrichtung, Speicher, Winter, Mietrecht: Antworten auf die wichtigsten Fragen zum Balkonkraftwerk.",
                     f"<h1>Ratgeber</h1><p class='lead'>Antworten auf die wichtigsten Fragen rund ums Balkonkraftwerk, mit Zahlen aus unseren Ertragsdaten.</p><ul class='list'>{lis}</ul>",
                     crumbs=[("Ratgeber", None)], active="ratgeber/"))

    # Startseite
    top10 = by_yield[:10]
    body = f"""<section class="hero">
<h1>Wie viel bringt ein Balkonkraftwerk bei dir?</h1>
<p class="lead">Ertrag, Eigenverbrauch und Ersparnis für {len(cities)} Städte in Deutschland, für jede Ausrichtung und Neigung. Kostenlos, ohne Anmeldung, ohne Tracking.</p>
{search_form()}{datalist}
<ul class="trust"><li>{len(cities)} Städte</li><li>Satellitendaten der EU-Kommission</li><li>Stundengenaue Simulation</li><li>Ohne Tracking</li></ul>
</section>
{calculator("Schnell durchrechnen (deutscher Durchschnitt)", nat_m)}
<section class="two">
<div><h2>Die sonnigsten Städte</h2><ol>{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a> <small class="num">{fmt(cities[n]["y"]["S35"] * KWP)} kWh</small></li>' for n in top10)}</ol>
<p class="small">Jahresertrag mit {C.SET_WP} Wp, Süd, 35° aufgeständert.</p>
<p>{more(url('staedte/'), f'Alle {len(cities)} Städte ansehen')}</p></div>
<div><h2>Werkzeuge &amp; Ratgeber</h2><ul>
<li><a href="{url('speicher-rechner/')}">Speicher-Rechner</a>: Wie groß sollte der Speicher sein?</li>
<li><a href="{url('vermieter-antrag/')}">Antrag an den Vermieter</a>: fertiger Brief in zwei Minuten</li>
{''.join(f'<li><a href="{url("ratgeber/" + a["slug"] + "/")}">{e(a["title"])}</a></li>' for a in arts)}</ul></div>
</section>
<section><h2>Große Städte</h2><ul class="cols">{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></li>' for n in big[:45])}</ul></section>"""
    urls.insert(0, page("", f"{C.SITE_NAME}: Balkonkraftwerk-Ertrag für deine Stadt berechnen",
                        f"Wie viel Strom erzeugt ein Balkonkraftwerk in deiner Stadt? Ertrag, Eigenverbrauch und Amortisation für {len(cities)} Städte, berechnet mit PVGIS-Wetterdaten.",
                        body, {"@context": "https://schema.org", "@type": "WebSite", "name": C.SITE_NAME, "url": C.SITE_URL + "/"}))

    # Rechtliches
    i = C.IMPRESSUM
    imp = (f"<p>{e(i['name'])}<br>{e(i['strasse'])}<br>{e(i['ort'])}</p><p>E-Mail: {e(i['email'])}</p>" if i["name"]
           else "<p>Angaben gemäß § 5 DDG folgen.</p>")
    page("impressum/", f"Impressum | {C.SITE_NAME}", "Impressum", f"<h1>Impressum</h1>{imp}<h2>Haftung für Inhalte</h2><p>Alle Berechnungen sind Schätzungen auf Basis öffentlich verfügbarer Wetterdaten und ersetzen keine Fachberatung.</p>")
    page("datenschutz/", f"Datenschutz | {C.SITE_NAME}", "Datenschutzerklärung", ratgeber.DATENSCHUTZ)
    (OUT / "404.html").write_text((OUT / "index.html").read_text().replace("<h1>Wie viel bringt ein Balkonkraftwerk bei dir?</h1>", "<h1>Seite nicht gefunden</h1><p>Aber vielleicht hilft dir das hier:</p>"))

    sm = "".join(f"<url><loc>{u}</loc><lastmod>{TODAY.isoformat()}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {C.SITE_URL}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / f"{C.INDEXNOW_KEY}.txt").write_text(C.INDEXNOW_KEY)
    print(f"{len(urls)} Seiten gebaut")


if __name__ == "__main__":
    main()
