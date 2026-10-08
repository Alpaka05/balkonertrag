"""Ratgeber-Artikel und Textseiten. Zahlen werden aus den PVGIS-Daten und der Stundensimulation berechnet,
damit sie zu den Stadtseiten und zum Rechner passen. Rechtliche Angaben: Stand Oktober 2026, geprüft gegen
gesetze-im-internet.de, Bundesnetzagentur und Verbraucherzentrale."""

DATENSCHUTZ = """<h1>Datenschutzerklärung</h1>
<h2>Verantwortlicher</h2>
<p>Verantwortlich für diese Website ist die im <a href="../impressum/">Impressum</a> genannte Person.</p>
<h2>Hosting</h2>
<p>Diese Website ist eine statische Seite und wird über GitHub Pages (GitHub Inc., 88 Colin P. Kelly Jr. Street, San Francisco, USA) ausgeliefert. Beim Aufruf verarbeitet GitHub technisch notwendige Daten wie IP-Adresse, Zeitpunkt und abgerufene Seite, um die Seite auszuliefern und vor Missbrauch zu schützen. Rechtsgrundlage ist unser berechtigtes Interesse an einer sicheren und stabilen Bereitstellung (Art. 6 Abs. 1 lit. f DSGVO). GitHub ist unter dem EU-US Data Privacy Framework zertifiziert. Details: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement">Datenschutzerklärung von GitHub</a>.</p>
<h2>Keine Cookies, kein Tracking</h2>
<p>Wir setzen keine Cookies, kein Tracking und keine Analyse-Tools ein. Rechner und Antrags-Generator laufen vollständig in deinem Browser; deine Eingaben werden nicht übertragen. Die Standort-Funktion fragt deinen Browser nach der Position, um die nächste Stadt zu finden. Die Position verlässt dabei dein Gerät nicht.</p>
<h2>Partnerlinks</h2>
<p>Links zu Amazon sind als Anzeige gekennzeichnet. Erst wenn du einen solchen Link anklickst, verarbeitet Amazon Daten nach seinen eigenen Datenschutzbestimmungen.</p>
<h2>Deine Rechte</h2>
<p>Du hast das Recht auf Auskunft, Berichtigung, Löschung, Einschränkung der Verarbeitung und Widerspruch (Art. 15–21 DSGVO) sowie auf Beschwerde bei einer Datenschutz-Aufsichtsbehörde (Art. 77 DSGVO).</p>"""

NAMES = {"S": "Süd", "SO": "Südost", "SW": "Südwest", "O": "Ost", "W": "West"}


def articles(x):
    fmt, euro, url, slug, C, KWP, model, bars, more = (x[k] for k in ("fmt", "euro", "url", "slug", "C", "KWP", "model", "bars", "more"))
    n, nm, cy = x["nat_y"], x["nat_m"], x["cities"]
    V, P = C.VERBRAUCH_KWH, C.STROMPREIS_CT

    def rel(k):
        return n[k] / n["S35"] * 100

    def run(key, wp, batt=0, annual=V):
        if key.startswith("OW"):
            return ow_run(key[2:], wp, batt, annual)
        return model.run(nm[key], key, wp, annual, batt)

    def ow_run(angle, wp, batt, annual):
        mo, mw = nm["O" + angle], nm["W" + angle]
        fo, fw = model.hourly("O" + angle), model.hourly("W" + angle)
        mix_m = [(a + b) / 2 for a, b in zip(mo, mw)]
        mix, h = [], 0
        for mi, days in enumerate((31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)):
            for _ in range(days * 24):
                mix.append((mo[mi] * fo[h] + mw[mi] * fw[h]) / 2 / mix_m[mi] if mix_m[mi] else 0)
                h += 1
        model.frac["OW" + angle] = mix
        return model.run(mix_m, "OW" + angle, wp, annual, batt)

    rows = "".join(
        f"<tr><th scope=row>{NAMES[a]}</th>" + "".join(f"<td class=num>{fmt(n[a + str(g)] * KWP)} kWh <small>({fmt(rel(a + str(g)))} %)</small></td>" for g in (35, 60, 90)) + "</tr>"
        for a in NAMES)

    sr = x["state_rank"]
    state_rows = "".join(
        f'<tr><td class=num>{i + 1}.</td><td><a href="{url("bundesland/" + slug(s) + "/")}">{s}</a></td><td class=num>{fmt(x["state_avg"][s] * KWP)} kWh</td></tr>'
        for i, s in enumerate(sr))
    best, worst = x["by_yield"][0], x["by_yield"][-1]

    # Simulationen für die Artikel
    s90 = run("S90", C.SET_WP)
    s90b = run("S90", C.SET_WP, 2)
    big = {wp: {k: run(k, wp) for k in ("S35", "S90", "OW35")} for wp in (900, 1200, 1600, 2000)}
    big_b = run("S35", 2000, 2)
    ow35, s35 = big[900]["OW35"], big[900]["S35"]
    win = [10, 11, 0, 1]
    w90, w35 = sum(nm["S90"][i] for i in win) * KWP, sum(nm["S35"][i] for i in win) * KWP
    month_rows = "".join(f"<tr><th scope=row>{m}</th><td class=num>{fmt(nm['S90'][i] * KWP)}</td><td class=num>{fmt(nm['S35'][i] * KWP)}</td><td class=num>{fmt(nm['S90'][i] / nm['S35'][i] * 100)} %</td></tr>"
                         for i, m in enumerate(["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]))
    dez_rank = sorted(cy, key=lambda c: -cy[c]["m"]["S90"][11])

    speicher_extra = s90b["eur"] - s90["eur"]
    big_extra = big_b["eur"] - big[2000]["S35"]["eur"]

    return [
        {
            "slug": "ausrichtung-neigung",
            "title": "Balkonkraftwerk: Welche Ausrichtung und Neigung bringt am meisten?",
            "desc": f"Süd, Ost oder West, senkrecht oder schräg: So stark beeinflusst die Montage den Ertrag deines Balkonkraftwerks, ausgewertet für {len(cy)} deutsche Städte.",
            "html": f"""
<p class="lead">Die Ausrichtung entscheidet stärker über den Ertrag als der Standort. Ein senkrecht montiertes West-Modul bringt nur etwa halb so viel wie ein schräg aufgeständertes Süd-Modul.</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Senkrecht am Geländer kostet rund {fmt(100 - rel('S90'))} % Ertrag gegenüber 35° Neigung.</li>
<li>Südost und Südwest verlieren nur etwa {fmt(100 - rel('SW35'))} % gegenüber genau Süd.</li>
<li>Auch Ost oder West lohnt sich meist, nur langsamer.</li></ul></div>
<p>Die Tabelle zeigt den Durchschnitt über {len(cy)} deutsche Städte für ein Set mit {C.SET_WP} Wp. In Klammern steht der Anteil am Ertrag bei Süd und 35°.</p>
<div class="scroll"><table><thead><tr><th>Ausrichtung</th><th class=num>35° aufgeständert</th><th class=num>60° angekippt</th><th class=num>90° Geländer</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Was das für dich heißt</h2>
<ul>
<li><b>Ankippen lohnt sich:</b> Schon 60° statt senkrecht bringen im Schnitt {fmt((n['S60'] / n['S90'] - 1) * 100)} % mehr. Viele Geländer-Halterungen lassen sich um 20–30° verstellen.</li>
<li><b>Südwest ist oft praktischer als Süd:</b> Der Strom kommt eher am Nachmittag, wenn du zu Hause bist.</li>
<li><b>Ost oder West:</b> Senkrecht nach Westen erzeugt ein {C.SET_WP}-Wp-Set im Schnitt {fmt(n['W90'] * KWP)} kWh. Das spart je nach Verbrauch etwa {euro(run('W90', C.SET_WP)['eur'])} im Jahr; ein günstiges Set hat sich nach rund {fmt(C.SET_PREIS_EUR / run('W90', C.SET_WP)['eur'], 1)} Jahren bezahlt.</li>
<li><b>Ost und West kombinieren:</b> Ein Modul nach Osten, eins nach Westen verteilt den Strom über den Tag. Mehr dazu im <a href="{url('ratgeber/ost-west/')}">Ost-West-Ratgeber</a>.</li>
</ul>
<h2>Verschattung schlägt Ausrichtung</h2>
<p>Alle Werte gelten ohne Schatten. Ein Baum, der Balkon darüber oder ein Nachbarhaus können den Ertrag stärker senken als eine ungünstige Ausrichtung. Beobachte an einem sonnigen Tag, wann die Sonne wirklich auf die Module scheint.</p>
<p>Die genauen Werte für jede Ausrichtung und Neigung an deinem Ort zeigt die Tabelle auf der {more(url('staedte/'), 'Seite deiner Stadt')}</p>""",
        },
        {
            "slug": "ost-west",
            "title": "Balkonkraftwerk Ost-West: Lohnt sich die geteilte Ausrichtung?",
            "desc": "Ein Modul nach Osten, eins nach Westen: weniger Spitzenertrag, aber mehr Strom zu den Zeiten, in denen du ihn brauchst. Mit Simulation und Zahlen.",
            "html": f"""
<p class="lead">Wer zwei Seiten hat, kann die Module auf Ost und West verteilen. Die Jahressumme ist kleiner als nach Süden, aber der Strom fließt morgens und abends und passt so besser zum Verbrauch.</p>
<h2>Der Vergleich</h2>
<p>Ein Set mit {C.SET_WP} Wp, 35° Neigung, {fmt(V)} kWh Jahresverbrauch, deutscher Durchschnittsstandort:</p>
<div class="scroll"><table><thead><tr><th></th><th class=num>Ertrag</th><th class=num>Selbst genutzt</th><th class=num>Eigenverbrauch</th><th class=num>Ersparnis</th></tr></thead><tbody>
<tr><th scope=row>Süd</th><td class=num>{fmt(s35['pv'])} kWh</td><td class=num>{fmt(s35['used'])} kWh</td><td class=num>{fmt(s35['used'] / s35['pv'] * 100)} %</td><td class=num>{euro(s35['eur'])}</td></tr>
<tr><th scope=row>Ost-West</th><td class=num>{fmt(ow35['pv'])} kWh</td><td class=num>{fmt(ow35['used'])} kWh</td><td class=num>{fmt(ow35['used'] / ow35['pv'] * 100)} %</td><td class=num>{euro(ow35['eur'])}</td></tr>
</tbody></table></div>
<p>Ost-West erzeugt {fmt((1 - ow35['pv'] / s35['pv']) * 100)} % weniger Strom, du nutzt davon aber einen größeren Anteil selbst. Unterm Strich liegt die Ersparnis {fmt(abs(1 - ow35['eur'] / s35['eur']) * 100)} % {'unter' if ow35['eur'] < s35['eur'] else 'über'} der Süd-Variante.</p>
<h2>Wann Ost-West besonders sinnvoll ist</h2>
<ul>
<li><b>Bei großer Modulleistung:</b> Mit {fmt(2000)} Wp gehen nach Süden {fmt(big[2000]['S35']['clipped'])} kWh an der 800-W-Grenze verloren, bei Ost-West nur {fmt(big[2000]['OW35']['clipped'])} kWh, weil die Spitzen flacher sind.</li>
<li><b>Wenn du morgens und abends viel verbrauchst</b>, etwa durch Kaffeemaschine, Kochen oder Homeoffice.</li>
<li><b>Wenn es keine Südseite gibt.</b> Zwei Seiten sind dann besser als nur eine.</li>
</ul>
<p>Im {more(url('rechner/'), 'Rechner')} kannst du unter „Ausrichtung“ auch „Ost-West“ wählen.</p>""",
        },
        {
            "slug": "balkonkraftwerk-winter",
            "title": "Balkonkraftwerk im Winter: Wie viel Strom kommt noch?",
            "desc": "Ertrag im Dezember, Januar und Februar, und warum senkrechte Module am Balkongeländer im Winter fast so gut sind wie schräge. Monatswerte aus PVGIS.",
            "html": f"""
<p class="lead">Im Winter erzeugt ein Balkonkraftwerk deutlich weniger, aber nicht nichts. Und hier spielt die senkrechte Montage am Geländer ihre Stärke aus.</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Von November bis Februar liefert ein {C.SET_WP}-Wp-Set im Schnitt {fmt(w90)} kWh senkrecht und {fmt(w35)} kWh aufgeständert.</li>
<li>Im Dezember bringt die senkrechte Montage {fmt(nm['S90'][11] / nm['S35'][11] * 100)} % des Ertrags der schrägen, im Juni nur {fmt(nm['S90'][5] / nm['S35'][5] * 100)} %.</li>
<li>Am meisten Winterstrom gibt es im Süden, etwa in {dez_rank[0]} und {dez_rank[1]}.</li></ul></div>
<h2>Monat für Monat</h2>
<figure>{bars([v * KWP for v in nm['S90']], [v * KWP for v in nm['S35']])}
<div class="legend"><span>Senkrecht (90°)</span><span class="alt">Aufgeständert (35°)</span></div>
<figcaption>kWh pro Monat, {C.SET_WP} Wp, Süd, Durchschnitt aus {len(cy)} Städten</figcaption></figure>
<div class="scroll"><table><thead><tr><th>Monat</th><th class=num>Senkrecht 90°</th><th class=num>Aufgeständert 35°</th><th class=num>Verhältnis</th></tr></thead><tbody>{month_rows}</tbody></table></div>
<h2>Warum senkrecht im Winter gut ist</h2>
<p>Im Dezember steht die Sonne mittags in Deutschland nur 13–18° über dem Horizont. Ein senkrechtes Modul trifft sie fast frontal. Im Sommer steht sie über 60° hoch, dann fällt das Licht sehr flach auf senkrechte Module. Deshalb ist der Abstand zwischen beiden Montagearten im Winter klein und im Sommer groß.</p>
<h2>Tipps für den Winter</h2>
<ul>
<li><b>Schnee:</b> Senkrechte Module bleiben meist frei, schräge können zuschneien. Nicht mit harten Gegenständen abkratzen.</li>
<li><b>Grundlast decken:</b> Im Winter reicht der Ertrag oft genau für Kühlschrank, Router und Standby. Fast alles wird selbst genutzt.</li>
<li><b>Speicher:</b> Im Winter wird er kaum voll. Er lohnt sich vor allem durch den Sommer.</li>
</ul>
<p>Winterwerte für deinen Ort: {more(url('staedte/'), 'Stadt auswählen')}</p>""",
        },
        {
            "slug": "2000-watt",
            "title": "Balkonkraftwerk mit 2000 Watt: Was bringen mehr Module?",
            "desc": "Erlaubt sind bis zu 2.000 Wp Modulleistung, aber nur 800 W Einspeisung. Wie viel mehr Strom vier Module wirklich bringen, mit und ohne Speicher.",
            "html": f"""
<p class="lead">Seit dem Solarpaket I darfst du bis zu 2.000 Wp Module an ein Balkonkraftwerk anschließen. Der Wechselrichter speist aber höchstens 800 W ein. Lohnen sich mehr Module trotzdem?</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Mehr Module bringen vor allem morgens, abends und an trüben Tagen mehr Strom.</li>
<li>Mittags gehen Spitzen über 800 W verloren: bei {fmt(2000)} Wp nach Süden etwa {fmt(big[2000]['S35']['clipped'] / (big[2000]['S35']['pv'] + big[2000]['S35']['clipped']) * 100)} % des Ertrags.</li>
<li>Über 960 Wp ist laut Produktnorm statt Schuko-Stecker eine Einspeisesteckdose (z. B. Wieland) nötig.</li></ul></div>
<h2>So viel bringen mehr Module</h2>
<p>Süd, 35° aufgeständert, {fmt(V)} kWh Jahresverbrauch, deutscher Durchschnittsstandort, ohne Speicher:</p>
<div class="scroll"><table><thead><tr><th class=num>Module</th><th class=num>Nutzbarer Ertrag</th><th class=num>Verlust an der 800-W-Grenze</th><th class=num>Selbst genutzt</th><th class=num>Ersparnis</th></tr></thead><tbody>
{''.join(f"<tr><td class=num>{fmt(wp)} Wp</td><td class=num>{fmt(r['S35']['pv'])} kWh</td><td class=num>{fmt(r['S35']['clipped'])} kWh</td><td class=num>{fmt(r['S35']['used'])} kWh</td><td class=num>{euro(r['S35']['eur'])}</td></tr>" for wp, r in big.items())}
</tbody></table></div>
<p>Der Ertrag steigt deutlich, die Ersparnis aber weniger: Ohne Speicher fließt ein großer Teil des zusätzlichen Stroms ungenutzt ins Netz. Mit einem Speicher von 2 kWh steigt die Ersparnis bei {fmt(2000)} Wp auf etwa {euro(big_b['eur'])}, das sind {euro(big_extra)} mehr im Jahr.</p>
<h2>Senkrecht und Ost-West: weniger Verlust</h2>
<p>Am Balkongeländer (90°) sind die Mittagsspitzen niedriger. Mit {fmt(2000)} Wp gehen dort nur etwa {fmt(big[2000]['S90']['clipped'])} kWh verloren, bei Ost-West (35°) {fmt(big[2000]['OW35']['clipped'])} kWh. Für viele Module am Geländer ist die 800-W-Grenze deshalb kaum ein Problem.</p>
<h2>Worauf du achten musst</h2>
<ul>
<li><b>Stecker:</b> Bis 960 Wp genügt nach DIN VDE V 0126-95 ein Schuko-Stecker, darüber brauchst du eine Einspeisesteckdose, die eine Elektrofachkraft setzt.</li>
<li><b>Wechselrichter:</b> Er muss genug Eingänge haben oder du brauchst einen Speicher mit eigenen Solar-Eingängen.</li>
<li><b>Platz und Statik:</b> Vier Module wiegen 80–100 kg. Kläre die Befestigung, als Mieter auch mit dem <a href="{url('vermieter-antrag/')}">Vermieter</a>.</li>
</ul>
<p>Rechne deine Variante durch: {more(url('speicher-rechner/'), 'Speicher-Rechner')}</p>""",
        },
        {
            "slug": "speicher-lohnt-sich",
            "title": "Lohnt sich ein Speicher fürs Balkonkraftwerk? Die ehrliche Rechnung",
            "desc": "Mit Speicher steigt der Eigenverbrauch, aber rechnet sich das? Stundengenaue Simulation mit echten Ertragsdaten und aktuellen Preisen.",
            "html": f"""
<p class="lead">Ein Speicher erhöht vor allem, wie viel deines Solarstroms du selbst nutzt. Ob er sich lohnt, hängt fast nur von der Modulleistung und vom Aufpreis ab.</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Bei einem kleinen Set mit {C.SET_WP} Wp bringt ein Speicher nur rund {euro(speicher_extra)} mehr im Jahr.</li>
<li>Bei {fmt(2000)} Wp sind es etwa {euro(big_extra)} im Jahr, weil sonst viel Mittagsstrom verloren geht.</li>
<li>Speicher kosten laut Stiftung Warentest (2026) etwa 700–1.000 € Aufpreis.</li></ul></div>
<h2>Beispiel 1: Kleines Set am Geländer</h2>
<p>{C.SET_WP} Wp, Süd, senkrecht, {fmt(V)} kWh Jahresverbrauch, deutscher Durchschnittsstandort, {fmt(P, 1)} ct/kWh:</p>
<div class="scroll"><table><thead><tr><th></th><th class=num>Eigenverbrauch</th><th class=num>Ersparnis pro Jahr</th></tr></thead><tbody>
<tr><th scope=row>Ohne Speicher</th><td class=num>{fmt(s90['used'] / s90['pv'] * 100)} %</td><td class=num>{euro(s90['eur'])}</td></tr>
<tr><th scope=row>Mit 2 kWh Speicher</th><td class=num>{fmt(s90b['used'] / s90b['pv'] * 100)} %</td><td class=num>{euro(s90b['eur'])}</td></tr>
</tbody></table></div>
<p>Bei {euro(C.SPEICHER_PREIS_EUR)} Aufpreis dauert es hier rund {fmt(C.SPEICHER_PREIS_EUR / speicher_extra)} Jahre, bis der Speicher sich bezahlt hat. Das ist länger, als viele Speicher halten.</p>
<h2>Beispiel 2: {fmt(2000)} Wp aufgeständert</h2>
<div class="scroll"><table><thead><tr><th></th><th class=num>Eigenverbrauch</th><th class=num>Ersparnis pro Jahr</th></tr></thead><tbody>
<tr><th scope=row>Ohne Speicher</th><td class=num>{fmt(big[2000]['S35']['used'] / big[2000]['S35']['pv'] * 100)} %</td><td class=num>{euro(big[2000]['S35']['eur'])}</td></tr>
<tr><th scope=row>Mit 2 kWh Speicher</th><td class=num>{fmt(big_b['used'] / big_b['pv'] * 100)} %</td><td class=num>{euro(big_b['eur'])}</td></tr>
</tbody></table></div>
<p>Hier hat sich ein Speicher für {euro(C.SPEICHER_PREIS_EUR)} nach etwa {fmt(C.SPEICHER_PREIS_EUR / big_extra, 1)} Jahren bezahlt.</p>
<h2>Gut zu wissen</h2>
<ul>
<li><b>Verluste:</b> Beim Laden und Entladen gehen zusammen etwa 10 % verloren, dazu kommt der Eigenverbrauch der Elektronik. Die Simulation rechnet mit {C.STANDBY_W} W, das sind rund {fmt(C.STANDBY_W * 8.76)} kWh im Jahr. Achte beim Kauf auf einen niedrigen Standby-Verbrauch.</li>
<li><b>DC- oder AC-gekoppelt:</b> Nur ein Speicher zwischen Modulen und Wechselrichter (DC-seitig) kann Strom über der 800-W-Grenze auffangen.</li>
<li><b>Anmeldung:</b> Der Speicher wird im Marktstammdatenregister zusätzlich als eigene Einheit eingetragen. Die Produktnorm DIN VDE V 0126-95 gilt nicht für Geräte mit Speicher.</li>
</ul>
<p>Spiel deine eigene Situation durch: {more(url('speicher-rechner/'), 'Speicher-Rechner')}</p>""",
        },
        {
            "slug": "bundeslaender-ranking",
            "title": "Wo lohnt sich ein Balkonkraftwerk am meisten? Ranking der Bundesländer",
            "desc": "Ertrag eines Balkonkraftwerks in allen 16 Bundesländern und den sonnigsten Städten Deutschlands, berechnet mit Satellitendaten.",
            "html": f"""
<p class="lead">Der Süden liegt vorn, aber der Abstand ist kleiner als viele denken: Zwischen der sonnigsten und der trübsten Stadt liegen nur rund {fmt((cy[best]['y']['S35'] / cy[worst]['y']['S35'] - 1) * 100)} % Ertrag.</p>
<p>Am meisten Strom erzeugt ein Balkonkraftwerk in <a href="{url('stadt/' + slug(best) + '/')}">{best}</a> ({fmt(cy[best]['y']['S35'] * KWP)} kWh mit {C.SET_WP} Wp, Süd, 35°), am wenigsten in <a href="{url('stadt/' + slug(worst) + '/')}">{worst}</a> ({fmt(cy[worst]['y']['S35'] * KWP)} kWh).</p>
<h2>Ranking der Bundesländer</h2>
<div class="scroll"><table><thead><tr><th class=num>#</th><th>Bundesland</th><th class=num>Ertrag pro Jahr ({C.SET_WP} Wp, 35° Süd)</th></tr></thead><tbody>{state_rows}</tbody></table></div>
<h2>Die zehn sonnigsten Städte</h2>
<ol>{''.join(f'<li><a href="{url("stadt/" + slug(c) + "/")}">{c}</a>: {fmt(cy[c]["y"]["S35"] * KWP)} kWh</li>' for c in x["by_yield"][:10])}</ol>
<h2>Lohnt es sich im Norden trotzdem?</h2>
<p>Meistens ja. Auch an den ertragsschwächsten Orten erzeugt ein {C.SET_WP}-Wp-Set aufgeständert über {fmt(cy[worst]['y']['S35'] * KWP)} kWh im Jahr. Ausrichtung und Verschattung deines Balkons sind wichtiger als das Bundesland.</p>""",
        },
        {
            "slug": "balkonkraftwerk-anmelden",
            "title": "Balkonkraftwerk anmelden 2026: Was wirklich noch nötig ist",
            "desc": "Marktstammdatenregister, Netzbetreiber, Zähler, 800-Watt-Grenze, Stecker: Die Regeln für Balkonkraftwerke seit dem Solarpaket I und der neuen VDE-Norm.",
            "html": """
<p class="lead">Seit dem Solarpaket I (in Kraft seit 16. Mai 2024) ist die Anmeldung deutlich einfacher geworden. Übrig bleibt im Wesentlichen ein Online-Formular.</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Nur noch Eintrag im Marktstammdatenregister, innerhalb eines Monats nach Inbetriebnahme.</li>
<li>Bis 800 VA Wechselrichterleistung und 2.000 Wp Modulleistung.</li>
<li>Schuko-Stecker ist bis 960 Wp Modulleistung zulässig, darüber braucht es eine Einspeisesteckdose.</li></ul></div>
<h2>1. Eintrag im Marktstammdatenregister</h2>
<p>Jedes Balkonkraftwerk muss im <a href="https://www.marktstammdatenregister.de" rel="noopener">Marktstammdatenregister</a> der Bundesnetzagentur eingetragen werden, und zwar innerhalb eines Monats nach der Inbetriebnahme. Für Steckersolargeräte gibt es seit April 2024 ein verkürztes Formular mit wenigen Pflichtangaben. Die Registrierung ist kostenlos. Ein Speicher wird zusätzlich als eigene Einheit eingetragen.</p>
<h2>2. Netzbetreiber: keine eigene Meldung mehr</h2>
<p>Früher musstest du die Anlage zusätzlich beim Netzbetreiber anmelden. Das ist entfallen: Der Netzbetreiber bekommt die Daten aus dem Marktstammdatenregister.</p>
<h2>3. Der Stromzähler</h2>
<p>Hast du noch einen alten Ferraris-Zähler ohne Rücklaufsperre, darfst du das Balkonkraftwerk trotzdem sofort betreiben; der Zähler darf vorübergehend rückwärts laufen. Der Messstellenbetreiber tauscht ihn bei Bedarf gegen eine moderne Messeinrichtung. Der Tausch selbst kostet nichts extra, für den neuen Zähler dürfen aber bis zu 25 € brutto im Jahr berechnet werden (§ 32 MsbG).</p>
<h2>4. Die Grenzwerte</h2>
<ul>
<li><b>800 Voltampere</b> (praktisch 800 W) darf der Wechselrichter höchstens abgeben (§ 8 Abs. 5a EEG).</li>
<li><b>2.000 Watt-Peak</b> Modulleistung sind nach dem EEG erlaubt. Mehr Module bringen vor allem morgens, abends und an trüben Tagen mehr Strom. Details im <a href="../2000-watt/">Ratgeber zu 2.000 Watt</a>.</li>
</ul>
<h2>5. Stecker und Steckdose</h2>
<p>Seit dem 1. Dezember 2025 gibt es mit der DIN VDE V 0126-95 eine eigene Produktnorm für Steckersolargeräte ohne Speicher. Danach ist ein normaler Schuko-Stecker bis 960 Wp Modulleistung zulässig. Darüber brauchst du eine spezielle Einspeisesteckdose (z.&nbsp;B. Wieland), die eine Elektrofachkraft setzt. Manche Förderprogramme verlangen sie generell. Nutze in jedem Fall eine intakte, eigene Steckdose ohne Mehrfachstecker.</p>
<h2>6. Steuern</h2>
<p>Für Balkonkraftwerke, Speicher und Montage gilt beim Kauf 0 % Mehrwertsteuer (§ 12 Abs. 3 UStG). Einnahmen aus dem Betrieb sind nach § 3 Nr. 72 EStG einkommensteuerfrei. Eine Gewerbeanmeldung ist für ein Balkonkraftwerk nicht nötig.</p>
<p class="note">Dieser Ratgeber ersetzt keine Rechtsberatung. Regeln können sich ändern; maßgeblich sind die Angaben der Bundesnetzagentur und deines Netzbetreibers.</p>""",
        },
        {
            "slug": "balkonkraftwerk-mieter",
            "title": "Balkonkraftwerk als Mieter oder Eigentümer: Darf der Vermieter Nein sagen?",
            "desc": "Seit dem 17. Oktober 2024 haben Mieter und Wohnungseigentümer einen Anspruch auf ein Balkonkraftwerk. Was der Vermieter noch mitbestimmen darf.",
            "html": f"""
<p class="lead">Seit dem 17. Oktober 2024 können Mieter und Wohnungseigentümer verlangen, dass sie ein Balkonkraftwerk anbringen dürfen. Ein pauschales Nein gibt es nicht mehr.</p>
<div class="box"><h2>Das Wichtigste in Kürze</h2><ul>
<li>Mieter haben einen Anspruch auf Erlaubnis (§ 554 BGB), brauchen sie aber trotzdem.</li>
<li>Der Vermieter darf bei der Art der Montage mitreden und eine Sicherheit für den Rückbau verlangen.</li>
<li>In der Eigentümergemeinschaft gilt ein ähnlicher Anspruch (§ 20 WEG); vor dem Beschluss nicht montieren.</li></ul></div>
<h2>Mieter</h2>
<p>Du kannst verlangen, dass der Vermieter dir die Anbringung erlaubt (§ 554 Abs. 1 BGB). Ablehnen darf er nur, wenn ihm die Maßnahme auch unter Würdigung deiner Interessen nicht zugemutet werden kann. Er kann Vorgaben zur Art der Montage machen und eine zusätzliche Sicherheit für den Rückbau verlangen. Beim Auszug musst du die Anlage in der Regel wieder entfernen.</p>
<h2>Wohnungseigentümer</h2>
<p>Jeder Wohnungseigentümer kann angemessene bauliche Veränderungen für Steckersolargeräte verlangen (§ 20 Abs. 2 WEG). Über die Durchführung beschließt die Gemeinschaft. Montiere erst, wenn der Beschluss gefasst ist.</p>
<h2>So stellst du den Antrag</h2>
<ol>
<li>Datenblatt des Sets und ein Foto oder eine Skizze der geplanten Montage beilegen.</li>
<li>Befestigung beschreiben, möglichst mit Halterung am Geländer und ohne Bohren in die Fassade.</li>
<li>Versicherung klären: Frag kurz bei deiner Haftpflichtversicherung nach, ob das Balkonkraftwerk mitversichert ist.</li>
<li>Schriftlich zustellen und eine angemessene Frist nennen.</li>
</ol>
<p>Den fertigen Brief erstellst du mit unserem {more(url('vermieter-antrag/'), 'Antrags-Generator')}</p>
<p class="note">Dieser Ratgeber ersetzt keine Rechtsberatung. Im Streitfall helfen Mietervereine oder die Verbraucherzentrale.</p>""",
        },
        {
            "slug": "balkonkraftwerk-foerderung",
            "title": "Balkonkraftwerk Förderung 2026: So findest du Zuschüsse in deiner Stadt",
            "desc": "Gibt es Geld vom Staat fürs Balkonkraftwerk? Was bundesweit gilt, wie du kommunale Zuschüsse findest und wie sie die Amortisation verkürzen.",
            "html": f"""
<p class="lead">Eine bundesweite Förderung für Balkonkraftwerke gibt es nicht. Zuschüsse zahlen einzelne Länder, Städte und Stadtwerke, und diese Programme ändern sich ständig: Töpfe sind schnell leer, manche enden ohne Vorwarnung.</p>
<p class="note">Stand: Oktober 2026. Wir nennen nur Programme, die wir bei der ausschreibenden Stelle prüfen konnten. Prüfe die Bedingungen immer dort, bevor du kaufst.</p>
<h2>Was bundesweit gilt</h2>
<ul>
<li><b>0 % Mehrwertsteuer</b> auf Steckersolargeräte, Speicher und Montage (§ 12 Abs. 3 UStG). Das wirkt automatisch an der Kasse und spart rund 16 % gegenüber dem früheren Preis.</li>
<li><b>Keine Einspeisevergütung:</b> Überschuss geht unvergütet ins Netz. Eine Vergütung wäre nur ohne die Steckersolar-Vereinfachungen möglich und lohnt bei Balkonkraftwerken praktisch nie.</li>
<li><b>Kein Bundeszuschuss.</b> Der KfW-Förderkredit 270 ist für Anlagen dieser Größe praktisch irrelevant.</li>
</ul>
<h2>Geprüftes Landesprogramm</h2>
<p><b>Mecklenburg-Vorpommern:</b> Das Landesförderinstitut zahlt Mietern 500 € pro Anlage (Programm bis 31.12.2027). Den Antrag stellst du nach Installation und Inbetriebnahme. Das Kontingent für selbstnutzende Eigentümer ist erschöpft. Quelle: <a href="https://www.mv-serviceportal.de/leistung?leistungId=124386998" rel="noopener">MV-Serviceportal</a>.</p>
<h2>Wo es sonst Zuschüsse geben kann</h2>
<ol>
<li><b>Gemeinde oder Stadt:</b> Die meisten Programme laufen kommunal. Suche auf der Website deiner Stadt nach „Balkonkraftwerk Förderung“ oder „Steckersolar Zuschuss“.</li>
<li><b>Stadtwerke und Energieversorger:</b> Manche zahlen Kunden einen Bonus oder bieten vergünstigte Sets an.</li>
<li><b>Verbraucherzentrale:</b> Beratungsstellen kennen die lokale Lage und wissen, ob ein Programm gerade ausgeschöpft ist.</li>
</ol>
<h2>Die häufigsten Fallen</h2>
<ul>
<li><b>Reihenfolge beachten:</b> Manche Programme verlangen den Antrag vor dem Kauf, andere (wie Mecklenburg-Vorpommern) erst nach der Inbetriebnahme. Lies die Bedingungen genau.</li>
<li><b>Technische Anforderungen:</b> Oft verlangt werden eine Mindest-Modulleistung, ein normgerechter Wechselrichter, teils ein Wieland-Stecker und die Registrierung im <a href="{url('ratgeber/balkonkraftwerk-anmelden/')}">Marktstammdatenregister</a>.</li>
<li><b>Nur ein Gerät pro Haushalt</b> oder pro Zählpunkt ist üblich.</li>
<li><b>Ausgeschöpfte Töpfe:</b> Auf Übersichtsseiten steht oft noch „Förderung 2026“, obwohl keine Mittel mehr da sind. Frag im Zweifel per E-Mail nach.</li>
</ul>
<h2>Wie stark verkürzt ein Zuschuss die Amortisation?</h2>
<p>Beispiel: Ein Set mit {C.SET_WP} Wp für {euro(C.SET_PREIS_EUR)} am Süd-Balkon (senkrecht) spart einem Haushalt mit {fmt(V)} kWh Verbrauch im deutschen Schnitt rund {euro(s90['eur'])} im Jahr.</p>
<div class="scroll"><table><thead><tr><th class=num>Zuschuss</th><th class=num>Eigenanteil</th><th class=num>Amortisation</th></tr></thead><tbody>
{''.join(f"<tr><td class=num>{euro(f)}</td><td class=num>{euro(C.SET_PREIS_EUR - f)}</td><td class=num>{fmt((C.SET_PREIS_EUR - f) / s90['eur'], 1)} Jahre</td></tr>" for f in (0, 100, 200, 300))}
</tbody></table></div>
<p>In den meisten Fällen rechnet sich ein Balkonkraftwerk auch ohne Förderung, sofern Ausrichtung und Verschattung passen. Wie viel dein Standort bringt, siehst du auf der <a href="{url('staedte/')}">Seite deiner Stadt</a>.</p>
<p class="note">Keine Rechts- oder Steuerberatung. Förderbedingungen ändern sich; maßgeblich sind die Angaben der jeweiligen Stelle.</p>""",
        },
    ]


ANTRAG_TPL = """{name}
{adresse}

M|{empfaenger}
W|An die Wohnungseigentümergemeinschaft
W|vertreten durch die Verwaltung {empfaenger}

{ort}, {datum}

M|Antrag auf Erlaubnis zur Anbringung eines Steckersolargeräts (Balkonkraftwerk)
W|Antrag auf Gestattung eines Steckersolargeräts (Balkonkraftwerk) nach § 20 Abs. 2 WEG

Sehr geehrte Damen und Herren,

M|hiermit bitte ich um Ihre Erlaubnis, an meiner Wohnung {lage} ein Steckersolargerät anzubringen und zu betreiben. Nach § 554 Abs. 1 BGB kann ein Mieter verlangen, dass ihm bauliche Veränderungen erlaubt werden, die der Stromerzeugung durch Steckersolargeräte dienen.
W|als Eigentümer der Wohnung {lage} beantrage ich, mir die Anbringung und den Betrieb eines Steckersolargeräts zu gestatten und über die Art der Durchführung in der nächsten Eigentümerversammlung oder im Umlaufverfahren zu beschließen. Nach § 20 Abs. 2 WEG kann jeder Wohnungseigentümer angemessene bauliche Veränderungen verlangen, die der Stromerzeugung durch Steckersolargeräte dienen.

Geplant ist:
- Gerät: {geraet}
- Modulleistung: {wp} Wp, Wechselrichter höchstens 800 W
- Montage: {montage}
- Anschluss: {stecker}

Das Gerät wird fachgerecht montiert und im Marktstammdatenregister der Bundesnetzagentur angemeldet. Die Montage erfolgt ohne Eingriff in die Bausubstanz, soweit nicht anders vereinbart. Für Schäden durch die Anlage komme ich auf; meine Haftpflichtversicherung ist informiert. Bei {rueckbau} entferne ich die Anlage und stelle den ursprünglichen Zustand wieder her.

Datenblatt und eine Skizze der Montage füge ich bei. Für Rückfragen und Vorgaben zur Ausführung stehe ich gern zur Verfügung.

M|Ich bitte um Ihre Rückmeldung bis zum {frist}.
W|Ich bitte darum, den Antrag auf die Tagesordnung zu setzen, und um eine Rückmeldung bis zum {frist}.

Mit freundlichen Grüßen

{name}

Anlagen: Datenblatt des Geräts, Skizze der Montage"""


def antrag_page(url, icons):
    def inp(name, label, value="", placeholder=""):
        return f'<label>{label}<input name="{name}" value="{value}" placeholder="{placeholder}"></label>'

    return f"""<div class="noprint"><h1>Balkonkraftwerk: Antrag an Vermieter oder Eigentümergemeinschaft</h1>
<p class="lead">Seit dem 17. Oktober 2024 hast du als Mieter oder Wohnungseigentümer einen Anspruch auf ein Balkonkraftwerk, brauchst aber trotzdem die Zustimmung. Trag deine Daten ein, dann entsteht der Brief automatisch. Nichts davon verlässt deinen Browser.</p></div>
<div class="card noprint">
<form class="antrag grid2">
<fieldset class="lbl" style="border:0;padding:0;margin:0;grid-column:1/-1;gap:8px"><legend>Ich bin</legend>
<label class="radio"><input type="radio" name="art" value="miete" checked> Mieter und schreibe an den Vermieter</label>
<label class="radio"><input type="radio" name="art" value="weg"> Wohnungseigentümer und schreibe an die Gemeinschaft</label>
</fieldset>
{inp("name", "Dein Name", placeholder="Max Mustermann")}
{inp("adresse", "Deine Anschrift", placeholder="Musterstraße 1, 12345 Musterstadt")}
{inp("empfaenger", "Vermieter bzw. Verwaltung", placeholder="Hausverwaltung Beispiel GmbH, Beispielweg 2, 12345 Musterstadt")}
{inp("lage", "Lage der Wohnung", placeholder="im 2. OG links")}
{inp("geraet", "Gerät (Hersteller und Modell)", placeholder="z. B. 800-W-Komplettset mit 2 Modulen")}
{inp("wp", "Modulleistung (Wp)", "900")}
{inp("montage", "Montage", "mit Halterungen am Balkongeländer, ohne Bohrungen in der Fassade")}
<label>Anschluss<select name="stecker"><option>über eine vorhandene Außensteckdose (Schuko, bis 960 Wp zulässig)</option><option>über eine Einspeisesteckdose (Wieland), gesetzt durch eine Elektrofachkraft</option></select></label>
{inp("rueckbau", "Rückbau bei", "Auszug")}
{inp("ort", "Ort", placeholder="Musterstadt")}
{inp("frist", "Antwort bis", placeholder="15.11.2026")}
</form>
<div class="actions"><button class="btn btn-primary" type="button" data-print>{icons["print"]}<span> Drucken oder als PDF speichern</span></button>
<button class="btn btn-ghost" type="button" data-copy>{icons["copy"]}<span> Text kopieren</span></button></div>
</div>
<h2 class="noprint">Dein Brief</h2>
<div class="letter"></div>
<script type="text/plain" id="antrag-tpl">{ANTRAG_TPL}</script>
<section class="noprint prose">
<h2>Was du wissen solltest</h2>
<ul>
<li><b>Mieter:</b> Der Vermieter darf nur ablehnen, wenn ihm die Anlage auch unter Würdigung deiner Interessen nicht zugemutet werden kann (§ 554 BGB). Er darf Vorgaben zur Montage machen und eine Sicherheit für den Rückbau verlangen.</li>
<li><b>Eigentümer:</b> Über die Durchführung beschließt die Gemeinschaft (§ 20 WEG). Montiere erst nach dem Beschluss.</li>
<li><b>Anlagen:</b> Leg das Datenblatt und ein Foto oder eine Skizze bei; das beschleunigt die Antwort.</li>
</ul>
<p>Hintergründe im <a href="{url('ratgeber/balkonkraftwerk-mieter/')}">Ratgeber für Mieter und Eigentümer</a>.</p>
<p class="note">Muster ohne Gewähr, keine Rechtsberatung. Im Streitfall helfen Mietervereine oder die Verbraucherzentrale.</p>
</section>"""


def methodik_page(url, fmt, C):
    return f"""<h1>Methodik: So berechnen wir Ertrag und Ersparnis</h1>
<div class="prose">
<p class="lead">Alle Zahlen auf {C.SITE_NAME} entstehen aus öffentlichen Daten und einem einfachen, offen beschriebenen Modell. Hier steht, woher die Daten kommen und wo die Grenzen liegen.</p>
<h2>1. Solarertrag: PVGIS</h2>
<p>Die Erträge stammen aus <a href="https://joint-research-centre.ec.europa.eu/photovoltaic-geographical-information-system-pvgis_en" rel="noopener">PVGIS 5.3</a>, dem Solarwerkzeug der Gemeinsamen Forschungsstelle der EU-Kommission. Für jede Stadt haben wir die Monats- und Jahreserträge eines fest montierten Systems mit 1 kWp abgefragt, für 5 Ausrichtungen (Süd, Südost, Südwest, Ost, West) und 8 Neigungen (0° bis 90°).</p>
<ul>
<li>Strahlungsdaten: SARAH-3 (Satellitendaten, langjähriges Mittel)</li>
<li>Systemverluste: 14 % (PVGIS-Empfehlung, enthält Kabel, Wechselrichter, Verschmutzung)</li>
<li>Koordinaten: Stadtmittelpunkt laut GeoNames</li>
<li>Keine Verschattung durch Gebäude, Bäume oder Balkone darüber</li>
</ul>
<h2>2. Stundensimulation</h2>
<p>Für Eigenverbrauch und Speicher reicht eine Jahressumme nicht. Der Rechner verteilt den Monatsertrag deiner Stadt auf die 8.760 Stunden eines Jahres. Den Tagesverlauf mit sonnigen und trüben Tagen liefert eine stündliche PVGIS-Zeitreihe (Referenzort Kassel, Jahr 2020) für dieselbe Ausrichtung und Neigung.</p>
<ul>
<li><b>Verbrauch:</b> BDEW-Standardlastprofil H25 für Haushalte (2025), skaliert auf deinen Jahresverbrauch</li>
<li><b>Einspeisegrenze:</b> höchstens 0,8 kWh pro Stunde (800 W); was darüber liegt, geht verloren</li>
<li><b>Speicher:</b> lädt mit Überschuss, auch über 800 W (DC-gekoppelt), entlädt bei Bedarf bis 800 W, Wirkungsgrad {fmt(C.ETA * 100)} % je Lade- und Entladevorgang, dazu {C.STANDBY_W} W Dauerverbrauch der Elektronik</li>
<li><b>Abschlag:</b> Ein Standardlastprofil ist der Mittelwert vieler Haushalte und viel glatter als ein einzelner Haushalt. Ohne Korrektur würde das Modell den Eigenverbrauch überschätzen. Wir ziehen deshalb {fmt(C.KALIBRIERUNG * 100)} % vom direkt genutzten Strom ab. Damit liegen die Ergebnisse im Bereich, den die Verbraucherzentrale nennt (30–60 % ohne, rund 70 % mit Speicher).</li>
</ul>
<h2>3. Ersparnis und Amortisation</h2>
<ul>
<li>Ersparnis = selbst genutzter Strom × Strompreis. Eingespeister Überschuss wird nicht vergütet.</li>
<li>Strompreis-Vorgabe: {fmt(C.STROMPREIS_CT, 1)} ct/kWh (Verivox-Durchschnitt Oktober 2026, ohne Grundgebühr)</li>
<li>Set-Preis-Vorgabe: {fmt(C.SET_PREIS_EUR)} € für {C.SET_WP} Wp, Speicher-Aufpreis {fmt(C.SPEICHER_PREIS_EUR)} € (Stiftung Warentest 2026: 700–1.000 €)</li>
<li>CO₂: {fmt(C.CO2_KG_PRO_KWH, 2).replace(',', ',')} kg pro kWh Solarstrom, der Netzstrom ersetzt (Strommix laut Umweltbundesamt, gerundet)</li>
<li>Amortisation = Anschaffungspreis ÷ Ersparnis pro Jahr, ohne Strompreissteigerung und ohne Zinsen</li>
</ul>
<h2>4. Grenzen</h2>
<p>Die Werte sind gute Richtwerte, keine Garantie. Abweichen können sie vor allem durch Verschattung, verschmutzte Module, ein besonders sonniges oder trübes Jahr, einen anderen Wechselrichter und deinen echten Tagesablauf. Wer es genau wissen will, misst nach dem ersten Jahr mit einem Steckdosen-Messgerät nach.</p>
<p>Fehler gefunden? Die Rechenwege sind offen: <a href="https://github.com/Alpaka05/balkonertrag" rel="noopener">Quellcode auf GitHub</a>.</p>
</div>"""
