"""Erzeugt die statische Website aus data/pvgis.json nach site/.

Aufruf: python3 scripts/build.py
"""
import html
import json
import math
import re
import shutil
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
import ratgeber  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "site"
ASSETS = ROOT / "assets"
TODAY = date.today().isoformat()

STATES = {
    "01": "Baden-Württemberg", "02": "Bayern", "03": "Bremen", "04": "Hamburg", "05": "Hessen",
    "06": "Niedersachsen", "07": "Nordrhein-Westfalen", "08": "Rheinland-Pfalz", "09": "Saarland",
    "10": "Schleswig-Holstein", "11": "Brandenburg", "12": "Mecklenburg-Vorpommern", "13": "Sachsen",
    "14": "Sachsen-Anhalt", "15": "Thüringen", "16": "Berlin",
}
ASPECT_NAMES = {"S": "Süden", "SO": "Südosten", "SW": "Südwesten", "O": "Osten", "W": "Westen"}
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


def dist(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def savings(kwh):
    return kwh * C.EIGENVERBRAUCH * C.STROMPREIS_CT / 100


def amazon(query):
    from urllib.parse import quote_plus
    return f"https://www.amazon.de/s?k={quote_plus(query)}&tag={C.AMAZON_TAG}"


# ---------------------------------------------------------------- Layout

def page(path, title, desc, body, schema=None, crumbs=None):
    canonical = f"{C.SITE_URL}/{path}"
    crumb_html = ""
    if crumbs:
        items = [f'<a href="{url("")}">Start</a>'] + [
            f'<a href="{url(p)}">{e(n)}</a>' if p else f"<span>{e(n)}</span>" for n, p in crumbs]
        crumb_html = f'<nav class="crumbs" aria-label="Brotkrumen">{" › ".join(items)}</nav>'
    ld = f'<script type="application/ld+json">{json.dumps(schema, ensure_ascii=False)}</script>' if schema else ""
    doc = f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title>
<meta name="description" content="{e(desc)}">
<link rel="canonical" href="{canonical}">
<meta property="og:title" content="{e(title)}">
<meta property="og:description" content="{e(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{canonical}">
<meta property="og:locale" content="de_DE">
<link rel="icon" href="{url('assets/icon.svg')}" type="image/svg+xml">
<link rel="stylesheet" href="{url('assets/style.css')}">
{ld}
</head>
<body>
<header class="top"><div class="wrap">
<a class="brand" href="{url('')}"><img src="{url('assets/icon.svg')}" alt="" width="28" height="28">{C.SITE_NAME}</a>
<nav><a href="{url('rechner/')}">Rechner</a><a href="{url('staedte/')}">Städte</a><a href="{url('ratgeber/')}">Ratgeber</a></nav>
</div></header>
<main class="wrap">
{crumb_html}
{body}
</main>
<footer><div class="wrap">
<p>Ertragsdaten: <a href="https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en" rel="noopener">PVGIS</a> der Europäischen Kommission (Gemeinsame Forschungsstelle), Strahlungsdaten SARAH-3, 14 % Systemverluste. Alle Angaben sind Schätzungen ohne Gewähr.</p>
<p><a href="{url('impressum/')}">Impressum</a> · <a href="{url('datenschutz/')}">Datenschutz</a> · Stand {TODAY}</p>
</div></footer>
<script src="{url('assets/app.js')}" defer></script>
</body>
</html>
"""
    target = OUT / path / "index.html" if not path.endswith(".html") else OUT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(doc)
    return canonical


def calculator(city_name, y, compact=False):
    """Interaktiver Rechner. y = Jahreserträge pro kWp für alle Ausrichtungen/Neigungen."""
    opts = "".join(f'<option value="{k}"{" selected" if k == "S" else ""}>{v}</option>' for k, v in ASPECT_NAMES.items())
    return f"""
<section class="calc card" data-yields='{json.dumps(y)}'>
<h2>{"Rechner" if compact else "Ertrag &amp; Amortisation berechnen"}{f" für {e(city_name)}" if city_name else ""}</h2>
<div class="grid">
<label>Ausrichtung<select name="aspect">{opts}</select></label>
<label>Montage<select name="angle"><option value="90">Senkrecht am Balkongeländer (90°)</option><option value="35">Aufgeständert / Dach (35°)</option></select></label>
<label>Modulleistung (Wp)<input name="wp" type="number" value="{C.SET_WP}" min="100" max="2000" step="10"></label>
<label>Strompreis (ct/kWh)<input name="price" type="number" value="{C.STROMPREIS_CT}" min="10" max="80" step="0.5"></label>
<label>Eigenverbrauch (%)<input name="self" type="number" value="{int(C.EIGENVERBRAUCH * 100)}" min="10" max="100" step="5"></label>
<label>Anschaffung (€)<input name="cost" type="number" value="{C.SET_PREIS_EUR}" min="0" max="5000" step="10"></label>
</div>
<div class="results">
<div><span class="big" data-out="kwh">–</span><small>kWh Strom pro Jahr</small></div>
<div><span class="big" data-out="eur">–</span><small>Ersparnis pro Jahr</small></div>
<div><span class="big" data-out="years">–</span><small>bis sich die Anlage bezahlt hat</small></div>
</div>
<p class="note" data-out="note"></p>
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
    lis = "".join(f'<li><a href="{amazon(q)}" rel="sponsored noopener" target="_blank">{n}</a></li>' for n, q in links)
    return f'<aside class="card ad"><p class="tag">Anzeige</p><h3>Passendes Zubehör vergleichen</h3><ul>{lis}</ul><p class="small">Partnerlinks: Wenn du darüber kaufst, erhalten wir eine kleine Provision. Der Preis ändert sich für dich nicht.</p></aside>'


def bars(values, unit="kWh"):
    w, h, pad = 600, 220, 28
    mx = max(values) or 1
    bw = (w - pad) / 12
    out = []
    for i, v in enumerate(values):
        bh = (h - 2 * pad) * v / mx
        x = pad + i * bw
        out.append(f'<rect x="{x + 4:.1f}" y="{h - pad - bh:.1f}" width="{bw - 8:.1f}" height="{bh:.1f}" rx="3"><title>{MONTHS[i]}: {fmt(v)} {unit}</title></rect>'
                   f'<text x="{x + bw / 2:.1f}" y="{h - pad - bh - 5:.1f}" class="v">{fmt(v)}</text>'
                   f'<text x="{x + bw / 2:.1f}" y="{h - 8}" class="m">{MONTHS[i]}</text>')
    return f'<svg class="chart" viewBox="0 0 {w} {h}" role="img" aria-label="Monatlicher Ertrag in {unit}">{"".join(out)}</svg>'


# ---------------------------------------------------------------- Seiten

def build_city(name, c, all_c, ranks, state_avg, nat_avg):
    s = slug(name)
    y = c["y"]
    state = STATES.get(c["state"], "")
    kwh90, kwh35 = y["S90"] * KWP, y["S35"] * KWP
    rank, total = ranks[name], len(ranks)
    pct_vs_nat = (y["S35"] / nat_avg - 1) * 100
    near = sorted((n for n in all_c if n != name), key=lambda n: dist(c, all_c[n]))[:8]

    rows = "".join(
        f"<tr><th>{ASPECT_NAMES[a]}</th><td>{fmt(y[a + '90'] * KWP)} kWh</td><td>{euro(savings(y[a + '90'] * KWP))}</td>"
        f"<td>{fmt(y[a + '35'] * KWP)} kWh</td><td>{euro(savings(y[a + '35'] * KWP))}</td></tr>"
        for a in ASPECT_NAMES)
    years = C.SET_PREIS_EUR / savings(kwh90)
    monthly = [v * KWP for v in c["m"]["S90"]]
    best, worst = max(range(12), key=lambda i: monthly[i]), min(range(12), key=lambda i: monthly[i])
    near_html = "".join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a> <small>{fmt(all_c[n]["y"]["S90"] * KWP)} kWh</small></li>' for n in near)
    vergleich = "mehr" if pct_vs_nat >= 0 else "weniger"

    faq = [
        (f"Wie viel Strom erzeugt ein Balkonkraftwerk in {name}?",
         f"Ein typisches Set mit {C.SET_WP} Wp Modulleistung erzeugt in {name} senkrecht am Balkongeländer nach Süden etwa {fmt(kwh90)} kWh pro Jahr, "
         f"schräg aufgeständert (35°) etwa {fmt(kwh35)} kWh. Grundlage sind langjährige Satellitendaten von PVGIS für den Standort {fmt(c['lat'], 2)}° N, {fmt(c['lon'], 2)}° O."),
        (f"Lohnt sich ein Balkonkraftwerk in {name}?",
         f"Bei {C.STROMPREIS_CT} ct/kWh und {int(C.EIGENVERBRAUCH * 100)} % Eigenverbrauch sparst du mit einem Süd-Balkon rund {euro(savings(kwh90))} im Jahr. "
         f"Ein Set für {euro(C.SET_PREIS_EUR)} hat sich damit nach etwa {fmt(years, 1)} Jahren bezahlt; die Module halten meist 20 Jahre und länger."),
        (f"Welcher Monat bringt in {name} den meisten Ertrag?",
         f"Am meisten liefert die Anlage im {MONTHS_LONG[best]} (etwa {fmt(monthly[best])} kWh), "
         f"am wenigsten im {MONTHS_LONG[worst]} (etwa {fmt(monthly[worst])} kWh) bei senkrechter Montage nach Süden."),
        ("Muss ich ein Balkonkraftwerk anmelden?",
         "Ja, aber nur noch im Marktstammdatenregister der Bundesnetzagentur. Die frühere Meldung beim Netzbetreiber ist seit dem Solarpaket I entfallen. "
         f'Mehr dazu im <a href="{url("ratgeber/balkonkraftwerk-anmelden/")}">Ratgeber zur Anmeldung</a>.'),
    ]
    faq_html = "".join(f"<details><summary>{e(q)}</summary><p>{a}</p></details>" for q, a in faq)
    schema = {"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": re.sub("<[^>]+>", "", a)}} for q, a in faq]}

    body = f"""
<h1>Balkonkraftwerk in {e(name)}: Ertrag &amp; Ersparnis</h1>
<p class="lead">In {e(name)} erzeugt ein Balkonkraftwerk mit {C.SET_WP} Wp am Süd-Balkon rund <strong>{fmt(kwh90)} kWh</strong> im Jahr, aufgeständert sogar <strong>{fmt(kwh35)} kWh</strong>.
Das spart etwa <strong>{euro(savings(kwh90))}–{euro(savings(kwh35))}</strong> Stromkosten pro Jahr.</p>
<div class="facts">
<div><b>{rank}.</b><small>von {total} Städten im Ertrags-Ranking</small></div>
<div><b>{'+' if pct_vs_nat >= 0 else ''}{fmt(pct_vs_nat, 1)} %</b><small>{vergleich} Sonne als der deutsche Schnitt</small></div>
<div><b>{fmt(years, 1)} Jahre</b><small>bis sich ein {euro(C.SET_PREIS_EUR)}-Set bezahlt hat</small></div>
</div>
{calculator(name, y)}
<section>
<h2>Ertrag nach Ausrichtung in {e(name)}</h2>
<p>Werte für ein Set mit {C.SET_WP} Wp, Ersparnis bei {C.STROMPREIS_CT} ct/kWh und {int(C.EIGENVERBRAUCH * 100)} % Eigenverbrauch.</p>
<div class="scroll"><table>
<thead><tr><th>Ausrichtung</th><th colspan="2">Balkongeländer (90°)</th><th colspan="2">Aufgeständert (35°)</th></tr></thead>
<tbody>{rows}</tbody></table></div>
</section>
<section>
<h2>Monatlicher Ertrag (Süd, Balkongeländer)</h2>
{bars(monthly)}
<p>Senkrecht montierte Module liefern im Winter vergleichsweise viel, weil die tief stehende Sonne fast frontal auf sie trifft. Im Sommer ist der Winkel ungünstiger, dafür scheint die Sonne länger.</p>
</section>
{product_box()}
<section>
<h2>{e(name)} im Vergleich</h2>
<p>Mit {fmt(y['S35'])} kWh pro kWp und Jahr (optimal aufgeständert) liegt {e(name)} {fmt(abs(pct_vs_nat), 1)} % {'über' if pct_vs_nat >= 0 else 'unter'} dem Durchschnitt aller {total} ausgewerteten deutschen Städte
{f'und {fmt(abs(y["S35"] / state_avg - 1) * 100, 1)} % {"über" if y["S35"] >= state_avg else "unter"} dem Schnitt in <a href="{url("bundesland/" + slug(state) + "/")}">{e(state)}</a>' if state else ''}.</p>
<h3>Städte in der Nähe</h3>
<ul class="cols">{near_html}</ul>
</section>
<section class="faq">
<h2>Häufige Fragen</h2>
{faq_html}
</section>
"""
    crumbs = ([(state, f"bundesland/{slug(state)}/")] if state else []) + [(name, None)]
    return page(f"stadt/{s}/", f"Balkonkraftwerk {name}: Ertrag {fmt(kwh90)}–{fmt(kwh35)} kWh/Jahr | {C.SITE_NAME}",
                f"So viel Strom erzeugt ein Balkonkraftwerk in {name}: {fmt(kwh90)} kWh am Balkon, {fmt(kwh35)} kWh aufgeständert. Ersparnis, Amortisation und Monatswerte aus PVGIS-Daten.",
                body, schema, crumbs)


def city_list(names, cities):
    return "".join(
        f'<tr><td><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></td><td>{fmt(cities[n]["y"]["S90"] * KWP)} kWh</td><td>{fmt(cities[n]["y"]["S35"] * KWP)} kWh</td><td>{euro(savings(cities[n]["y"]["S90"] * KWP))}</td></tr>'
        for n in names)


TABLE_HEAD = f"<thead><tr><th>Stadt</th><th>Balkon (90°, Süd)</th><th>Aufgeständert (35°, Süd)</th><th>Ersparnis/Jahr</th></tr></thead>"


def main():
    cities = json.loads((ROOT / "data" / "pvgis.json").read_text())
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
    nat_y = {k: sum(c["y"][k] for c in cities.values()) / len(cities) for k in next(iter(cities.values()))["y"]}

    for n, c in cities.items():
        urls.append(build_city(n, c, cities, ranks, state_avg.get(STATES.get(c["state"], ""), nat_avg), nat_avg))

    # Bundesländer
    state_rank = sorted((s for s in by_state if s), key=lambda s: -state_avg[s])
    for s in state_rank:
        ns = sorted(by_state[s], key=lambda n: -cities[n]["pop"])
        top = sorted(ns, key=lambda n: -cities[n]["y"]["S35"])
        body = f"""<h1>Balkonkraftwerk in {e(s)}: Ertrag in {len(ns)} Städten</h1>
<p class="lead">Im Schnitt erzeugt ein Balkonkraftwerk mit {C.SET_WP} Wp in {e(s)} aufgeständert nach Süden <strong>{fmt(state_avg[s] * KWP)} kWh</strong> pro Jahr.
Am sonnigsten ist <a href="{url('stadt/' + slug(top[0]) + '/')}">{e(top[0])}</a>, am wenigsten Ertrag gibt es in {e(top[-1])}. {e(s)} liegt auf Platz {state_rank.index(s) + 1} von {len(state_rank)} Bundesländern.</p>
{calculator(s, {k: round(sum(cities[n]['y'][k] for n in ns) / len(ns), 1) for k in nat_y}, compact=True)}
<h2>Alle Städte in {e(s)}</h2>
<div class="scroll"><table class="sortable">{TABLE_HEAD}<tbody>{city_list(ns, cities)}</tbody></table></div>"""
        urls.append(page(f"bundesland/{slug(s)}/", f"Balkonkraftwerk {s}: Ertrag in {len(ns)} Städten | {C.SITE_NAME}",
                         f"Wie viel bringt ein Balkonkraftwerk in {s}? Ertrag, Ersparnis und Ranking für {len(ns)} Städte auf Basis von PVGIS-Daten.",
                         body, crumbs=[(s, None)]))

    # Städteübersicht
    state_rows = "".join(f'<tr><td>{i + 1}.</td><td><a href="{url("bundesland/" + slug(s) + "/")}">{e(s)}</a></td><td>{fmt(state_avg[s] * KWP)} kWh</td><td>{len(by_state[s])}</td></tr>' for i, s in enumerate(state_rank))
    big = sorted(cities, key=lambda n: -cities[n]["pop"])
    body = f"""<h1>Balkonkraftwerk-Ertrag in {len(cities)} deutschen Städten</h1>
<p class="lead">Wähle deine Stadt und sieh, wie viel Strom ein Balkonkraftwerk dort erzeugt. Alle Werte stammen aus PVGIS-Satellitendaten der EU-Kommission.</p>
<label class="search">Stadt suchen<input type="search" list="citylist" data-citysearch placeholder="z. B. Leipzig"></label>
<datalist id="citylist">{''.join(f'<option value="{e(n)}">' for n in big)}</datalist>
<h2>Bundesländer-Ranking</h2>
<div class="scroll"><table><thead><tr><th>#</th><th>Bundesland</th><th>Ertrag ({C.SET_WP} Wp, 35° Süd)</th><th>Städte</th></tr></thead><tbody>{state_rows}</tbody></table></div>
<h2>Die sonnigsten Städte</h2>
<div class="scroll"><table>{TABLE_HEAD}<tbody>{city_list(by_yield[:25], cities)}</tbody></table></div>
<h2>Alle Städte nach Einwohnerzahl</h2>
<ul class="cols">{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></li>' for n in big)}</ul>"""
    urls.append(page("staedte/", f"Balkonkraftwerk-Ertrag für {len(cities)} Städte in Deutschland | {C.SITE_NAME}",
                     f"Ertrag eines Balkonkraftwerks in {len(cities)} deutschen Städten und allen Bundesländern im Vergleich. Mit Ranking der sonnigsten Orte.",
                     body, crumbs=[("Städte", None)]))
    (OUT / "assets" / "cities.json").write_text(json.dumps({n: slug(n) for n in big}, ensure_ascii=False))

    # Rechner
    body = f"""<h1>Balkonkraftwerk-Rechner</h1>
<p class="lead">Berechne Ertrag, Ersparnis und Amortisation deines Balkonkraftwerks. Die Grundwerte sind der Durchschnitt aus {len(cities)} deutschen Städten. Für genauere Werte wähle <a href="{url('staedte/')}">deine Stadt</a>.</p>
{calculator('', {k: round(v, 1) for k, v in nat_y.items()})}
{product_box()}
<h2>So rechnet der Rechner</h2>
<ul>
<li><b>Ertrag:</b> Jahresertrag pro kWp aus PVGIS (SARAH-3, 14 % Systemverluste) für die gewählte Ausrichtung und Neigung, multipliziert mit deiner Modulleistung.</li>
<li><b>Wechselrichter-Grenze:</b> Ein Balkonkraftwerk darf höchstens 800 W einspeisen. Bei mehr Modulleistung kappt der Wechselrichter die Mittagsspitzen; dafür ziehen wir einen geschätzten Verlust ab.</li>
<li><b>Ersparnis:</b> Nur selbst verbrauchter Strom spart Geld. Ohne Speicher sind 30–50 % Eigenverbrauch typisch, mit Speicher deutlich mehr. Eingespeister Überschuss wird bei Balkonkraftwerken in der Regel nicht vergütet.</li>
</ul>"""
    urls.append(page("rechner/", f"Balkonkraftwerk-Rechner: Ertrag, Ersparnis & Amortisation | {C.SITE_NAME}",
                     "Kostenloser Balkonkraftwerk-Rechner mit echten Wetterdaten: Wie viel Strom erzeugt dein Set, wie viel sparst du und wann hat es sich bezahlt gemacht?",
                     body, crumbs=[("Rechner", None)]))

    # Ratgeber
    ctx = {"cities": cities, "nat_y": nat_y, "state_avg": state_avg, "state_rank": state_rank, "by_yield": by_yield,
           "KWP": KWP, "fmt": fmt, "euro": euro, "url": url, "slug": slug, "savings": savings, "C": C}
    arts = ratgeber.articles(ctx)
    for a in arts:
        schema = {"@context": "https://schema.org", "@type": "Article", "headline": a["title"], "dateModified": TODAY,
                  "inLanguage": "de"}
        urls.append(page(f"ratgeber/{a['slug']}/", f"{a['title']} | {C.SITE_NAME}", a["desc"],
                         f"<article><h1>{e(a['title'])}</h1>{a['html']}</article>{product_box()}", schema,
                         [("Ratgeber", "ratgeber/"), (a["title"], None)]))
    lis = "".join(f'<li><a href="{url("ratgeber/" + a["slug"] + "/")}"><b>{e(a["title"])}</b></a><br><small>{e(a["desc"])}</small></li>' for a in arts)
    urls.append(page("ratgeber/", f"Balkonkraftwerk-Ratgeber | {C.SITE_NAME}", "Anmeldung, Ausrichtung, Speicher, Mietrecht: Antworten auf die wichtigsten Fragen zum Balkonkraftwerk.",
                     f"<h1>Ratgeber</h1><ul class='list'>{lis}</ul>", crumbs=[("Ratgeber", None)]))

    # Startseite
    top10 = by_yield[:10]
    body = f"""<section class="hero">
<h1>Wie viel bringt ein Balkonkraftwerk bei dir?</h1>
<p class="lead">Echte Ertragsdaten für {len(cities)} Städte in Deutschland, getrennt nach Ausrichtung und Montage. Kostenlos, ohne Anmeldung, ohne Tracking.</p>
<label class="search">Deine Stadt<input type="search" list="citylist" data-citysearch placeholder="Stadt eingeben, z. B. Köln"></label>
<datalist id="citylist">{''.join(f'<option value="{e(n)}">' for n in big)}</datalist>
</section>
{calculator('', {k: round(v, 1) for k, v in nat_y.items()})}
<section class="two">
<div><h2>Die sonnigsten Städte</h2><ol>{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a> <small>{fmt(cities[n]["y"]["S35"] * KWP)} kWh</small></li>' for n in top10)}</ol>
<p class="small">Jahresertrag mit {C.SET_WP} Wp, Süd, 35° aufgeständert.</p>
<p><a href="{url('staedte/')}">Alle {len(cities)} Städte ansehen →</a></p></div>
<div><h2>Ratgeber</h2><ul>{''.join(f'<li><a href="{url("ratgeber/" + a["slug"] + "/")}">{e(a["title"])}</a></li>' for a in arts)}</ul></div>
</section>
<section><h2>Große Städte</h2><ul class="cols">{''.join(f'<li><a href="{url("stadt/" + slug(n) + "/")}">{e(n)}</a></li>' for n in big[:40])}</ul></section>"""
    urls.insert(0, page("", f"{C.SITE_NAME}: Balkonkraftwerk-Ertrag für deine Stadt berechnen",
                        f"Wie viel Strom erzeugt ein Balkonkraftwerk in deiner Stadt? Ertrag, Ersparnis und Amortisation für {len(cities)} Städte, berechnet mit PVGIS-Wetterdaten.",
                        body, {"@context": "https://schema.org", "@type": "WebSite", "name": C.SITE_NAME, "url": C.SITE_URL + "/"}))

    # Rechtliches
    i = C.IMPRESSUM
    imp = (f"<p>{e(i['name'])}<br>{e(i['strasse'])}<br>{e(i['ort'])}</p><p>E-Mail: {e(i['email'])}</p>" if i["name"]
           else "<p>Angaben gemäß § 5 DDG folgen.</p>")
    page("impressum/", f"Impressum | {C.SITE_NAME}", "Impressum", f"<h1>Impressum</h1>{imp}<h2>Haftung für Inhalte</h2><p>Alle Berechnungen sind Schätzungen auf Basis öffentlich verfügbarer Wetterdaten und ersetzen keine Fachberatung.</p>")
    page("datenschutz/", f"Datenschutz | {C.SITE_NAME}", "Datenschutzerklärung", ratgeber.DATENSCHUTZ)
    (OUT / "404.html").write_text((OUT / "index.html").read_text().replace("<h1>Wie viel bringt ein Balkonkraftwerk bei dir?</h1>", "<h1>Seite nicht gefunden</h1><p>Aber vielleicht hilft dir das hier:</p>"))

    sm = "".join(f"<url><loc>{u}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls)
    (OUT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>')
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {C.SITE_URL}/sitemap.xml\n")
    (OUT / ".nojekyll").write_text("")
    (OUT / f"{C.INDEXNOW_KEY}.txt").write_text(C.INDEXNOW_KEY)
    print(f"{len(urls)} Seiten gebaut")


if __name__ == "__main__":
    main()
