"""Ratgeber-Artikel. Zahlen werden aus den PVGIS-Daten berechnet, damit sie zu den Stadtseiten passen."""

DATENSCHUTZ = """<h1>Datenschutzerklärung</h1>
<p>Diese Website wird als statische Seite über GitHub Pages (GitHub Inc., USA) ausgeliefert. Beim Aufruf verarbeitet GitHub technisch notwendige Daten wie IP-Adresse, Zeitpunkt und abgerufene Seite, um die Seite auszuliefern und vor Missbrauch zu schützen. Details: <a href="https://docs.github.com/de/site-policy/privacy-policies/github-general-privacy-statement">Datenschutzerklärung von GitHub</a>.</p>
<p>Wir setzen keine Cookies, kein Tracking und keine Analyse-Tools ein. Der Rechner läuft vollständig in deinem Browser; deine Eingaben werden nicht übertragen.</p>
<p>Links zu Amazon sind als Anzeige gekennzeichnet. Erst wenn du einen solchen Link anklickst, verarbeitet Amazon Daten nach seinen eigenen Datenschutzbestimmungen.</p>"""


def articles(x):
    fmt, euro, url, slug, C, KWP = x["fmt"], x["euro"], x["url"], x["slug"], x["C"], x["KWP"]
    n = x["nat_y"]
    names = {"S": "Süd", "SO": "Südost", "SW": "Südwest", "O": "Ost", "W": "West"}

    def rel(k):
        return n[k] / n["S35"] * 100

    rows = "".join(
        f"<tr><th>{names[a]}</th><td>{fmt(n[a + '35'] * KWP)} kWh <small>({fmt(rel(a + '35'))} %)</small></td>"
        f"<td>{fmt(n[a + '90'] * KWP)} kWh <small>({fmt(rel(a + '90'))} %)</small></td></tr>" for a in names)

    sr = x["state_rank"]
    state_rows = "".join(
        f'<tr><td>{i + 1}.</td><td><a href="{url("bundesland/" + slug(s) + "/")}">{s}</a></td><td>{fmt(x["state_avg"][s] * KWP)} kWh</td></tr>'
        for i, s in enumerate(sr))
    best, worst = x["by_yield"][0], x["by_yield"][-1]
    cy = x["cities"]

    base = n["S90"] * KWP
    sv = lambda kwh, ev, p=C.STROMPREIS_CT: kwh * ev * p / 100  # noqa: E731

    return [
        {
            "slug": "ausrichtung-neigung",
            "title": "Balkonkraftwerk: Welche Ausrichtung und Neigung bringt am meisten?",
            "desc": "Süd, Ost oder West, senkrecht oder schräg: So stark beeinflusst die Montage den Ertrag deines Balkonkraftwerks, ausgewertet für "
                    f"{len(cy)} deutsche Städte.",
            "html": f"""
<p class="lead">Die Ausrichtung entscheidet stärker über den Ertrag als der Standort. Ein senkrecht montiertes West-Modul bringt nur gut halb so viel wie ein schräg aufgeständertes Süd-Modul.</p>
<p>Die Tabelle zeigt den Durchschnitt über {len(cy)} deutsche Städte für ein Set mit {C.SET_WP} Wp. In Klammern steht der Anteil am bestmöglichen Ertrag (Süd, 35°).</p>
<div class="scroll"><table><thead><tr><th>Ausrichtung</th><th>Aufgeständert 35°</th><th>Balkongeländer 90°</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Was das für dich heißt</h2>
<ul>
<li><b>Senkrecht am Geländer kostet etwa {fmt(100 - rel('S90'))} % Ertrag</b> gegenüber der optimalen Neigung. Wenn du die Module mit einer verstellbaren Halterung um 20–30° ankippen kannst, holst du einen guten Teil davon zurück.</li>
<li><b>Südost und Südwest verlieren kaum</b>: Nur rund {fmt(100 - rel('SW35'))} % weniger als genau Süd. Ein Südwest-Balkon ist sogar oft praktischer, weil er abends Strom liefert, wenn du zu Hause bist.</li>
<li><b>Ost oder West lohnt sich trotzdem</b>: Auch mit {fmt(n['W90'] * KWP)} kWh im Jahr sparst du bei {C.STROMPREIS_CT} ct/kWh und {int(C.EIGENVERBRAUCH * 100)} % Eigenverbrauch etwa {euro(sv(n['W90'] * KWP, C.EIGENVERBRAUCH))} pro Jahr. Ein günstiges Set amortisiert sich so in unter zehn Jahren.</li>
<li><b>Ost + West kombinieren</b>: Hast du zwei Seiten, verteilt ein Modul nach Osten und eins nach Westen den Ertrag über den Tag. Das erhöht den Eigenverbrauch, auch wenn die Jahressumme etwas niedriger ist.</li>
</ul>
<h2>Verschattung schlägt Ausrichtung</h2>
<p>Alle Werte gelten ohne Schatten. Ein Baum, die Balkonbrüstung darüber oder ein Nachbarhaus können den Ertrag stärker senken als eine schlechte Ausrichtung. Prüfe über den Tag, wann die Sonne wirklich auf die Module scheint.</p>
<p>Die genauen Werte für deinen Ort findest du auf der <a href="{url('staedte/')}">Seite deiner Stadt</a>.</p>""",
        },
        {
            "slug": "bundeslaender-ranking",
            "title": "Wo lohnt sich ein Balkonkraftwerk am meisten? Ranking der Bundesländer",
            "desc": "Ertrag eines Balkonkraftwerks in allen 16 Bundesländern und den sonnigsten Städten Deutschlands, berechnet mit Satellitendaten.",
            "html": f"""
<p class="lead">Der Süden liegt vorn, aber der Abstand ist kleiner als viele denken: Zwischen der sonnigsten und der trübsten Stadt liegen nur rund {fmt((cy[best]['y']['S35'] / cy[worst]['y']['S35'] - 1) * 100)} % Ertrag.</p>
<p>Am meisten Strom erzeugt ein Balkonkraftwerk in <a href="{url('stadt/' + slug(best) + '/')}">{best}</a> ({fmt(cy[best]['y']['S35'] * KWP)} kWh mit {C.SET_WP} Wp, Süd, 35°), am wenigsten in <a href="{url('stadt/' + slug(worst) + '/')}">{worst}</a> ({fmt(cy[worst]['y']['S35'] * KWP)} kWh).</p>
<h2>Ranking der Bundesländer</h2>
<div class="scroll"><table><thead><tr><th>#</th><th>Bundesland</th><th>Ertrag pro Jahr ({C.SET_WP} Wp, 35° Süd)</th></tr></thead><tbody>{state_rows}</tbody></table></div>
<h2>Die zehn sonnigsten Städte</h2>
<ol>{''.join(f'<li><a href="{url("stadt/" + slug(c) + "/")}">{c}</a>: {fmt(cy[c]["y"]["S35"] * KWP)} kWh</li>' for c in x["by_yield"][:10])}</ol>
<h2>Lohnt es sich im Norden trotzdem?</h2>
<p>Ja. Auch an den ertragsschwächsten Orten erzeugt ein {C.SET_WP}-Wp-Set aufgeständert über {fmt(cy[worst]['y']['S35'] * KWP)} kWh im Jahr. Bei {C.STROMPREIS_CT} ct/kWh spart das rund {euro(sv(cy[worst]['y']['S35'] * KWP, C.EIGENVERBRAUCH))} jährlich. Die Ausrichtung und Verschattung deines Balkons sind wichtiger als das Bundesland.</p>""",
        },
        {
            "slug": "balkonkraftwerk-anmelden",
            "title": "Balkonkraftwerk anmelden 2026: Was wirklich noch nötig ist",
            "desc": "Marktstammdatenregister, Netzbetreiber, Zähler, 800-Watt-Grenze: Die Regeln für Balkonkraftwerke seit dem Solarpaket I verständlich erklärt.",
            "html": """
<p class="lead">Seit dem Solarpaket I (in Kraft seit Mai 2024) ist die Anmeldung deutlich einfacher geworden. Übrig bleibt im Wesentlichen ein Online-Formular.</p>
<h2>1. Eintrag im Marktstammdatenregister</h2>
<p>Jedes Balkonkraftwerk muss im <a href="https://www.marktstammdatenregister.de" rel="noopener">Marktstammdatenregister</a> der Bundesnetzagentur eingetragen werden, und zwar innerhalb eines Monats nach der Inbetriebnahme. Für Steckersolargeräte gibt es ein verkürztes Formular mit wenigen Pflichtangaben. Die Registrierung ist kostenlos.</p>
<h2>2. Netzbetreiber: keine eigene Meldung mehr</h2>
<p>Früher musstest du die Anlage zusätzlich beim Netzbetreiber anmelden. Das ist entfallen: Der Netzbetreiber bekommt die Daten aus dem Marktstammdatenregister.</p>
<h2>3. Der Stromzähler</h2>
<p>Hast du noch einen alten Ferraris-Zähler ohne Rücklaufsperre, darf das Balkonkraftwerk vorübergehend trotzdem betrieben werden. Der Messstellenbetreiber tauscht den Zähler bei Bedarf gegen ein modernes Gerät; für dich entstehen dabei in der Regel keine zusätzlichen Kosten.</p>
<h2>4. Die Grenzwerte</h2>
<ul>
<li><b>800 Watt</b> darf der Wechselrichter höchstens ins Hausnetz einspeisen.</li>
<li><b>2.000 Watt-Peak</b> Modulleistung sind insgesamt erlaubt. Mehr Module bringen vor allem morgens, abends und an trüben Tagen mehr Strom, weil die 800-W-Grenze dann nicht erreicht wird.</li>
</ul>
<h2>5. Stecker und Steckdose</h2>
<p>Viele Sets werden mit Schuko-Stecker verkauft und an einer normalen Außensteckdose betrieben. Wer auf Nummer sicher gehen will, lässt eine spezielle Einspeisesteckdose (z.&nbsp;B. Wieland) von einer Elektrofachkraft setzen. Achte in jedem Fall auf die Angaben des Herstellers und eine intakte, eigene Steckdose ohne Mehrfachstecker.</p>
<h2>6. Steuern</h2>
<p>Für Balkonkraftwerke gilt beim Kauf 0 % Mehrwertsteuer. Erträge aus selbst verbrauchtem Strom sind steuerfrei, eine Gewerbeanmeldung ist nicht nötig.</p>
<p class="note">Dieser Ratgeber ersetzt keine Rechtsberatung. Regeln können sich ändern; maßgeblich sind die Angaben der Bundesnetzagentur und deines Netzbetreibers.</p>""",
        },
        {
            "slug": "balkonkraftwerk-mieter",
            "title": "Balkonkraftwerk als Mieter oder Eigentümer: Darf der Vermieter Nein sagen?",
            "desc": "Seit Oktober 2024 gelten Balkonkraftwerke als privilegierte Maßnahme. Was das für Mieter und Wohnungseigentümer bedeutet.",
            "html": """
<p class="lead">Seit Oktober 2024 haben Mieter und Wohnungseigentümer einen Anspruch darauf, ein Balkonkraftwerk anbringen zu dürfen. Ein pauschales Nein gibt es nicht mehr.</p>
<h2>Mieter</h2>
<p>Steckersolargeräte zählen im Mietrecht zu den Maßnahmen, denen der Vermieter grundsätzlich zustimmen muss, ähnlich wie bei der Ladestation fürs E-Auto. Du brauchst die Zustimmung trotzdem, stell also vorher einen Antrag. Der Vermieter darf mitreden, <em>wie</em> die Anlage angebracht wird, etwa bei Befestigung oder Optik, und kann im Einzelfall aus wichtigen Gründen ablehnen.</p>
<h2>Wohnungseigentümer</h2>
<p>In einer Eigentümergemeinschaft gilt das Gleiche: Jeder Eigentümer kann verlangen, dass ihm das Anbringen gestattet wird. Die Gemeinschaft entscheidet per Beschluss über die Art der Durchführung.</p>
<h2>So stellst du den Antrag</h2>
<ol>
<li>Datenblatt des Sets und Foto oder Skizze der geplanten Montage beilegen.</li>
<li>Befestigung beschreiben: Halterung am Geländer, ohne Bohren in die Fassade, wenn möglich.</li>
<li>Auf Versicherung hinweisen: Ein Balkonkraftwerk ist meist über die Haftpflicht abgedeckt. Kurze Nachfrage bei deiner Versicherung schadet nicht.</li>
<li>Schriftlich zustellen und eine angemessene Frist nennen.</li>
</ol>
<p class="note">Dieser Ratgeber ersetzt keine Rechtsberatung. Im Streitfall helfen Mietervereine oder die Verbraucherzentrale.</p>""",
        },
        {
            "slug": "speicher-lohnt-sich",
            "title": "Lohnt sich ein Speicher fürs Balkonkraftwerk? Die ehrliche Rechnung",
            "desc": "Mit Speicher steigt der Eigenverbrauch, aber rechnet sich das? Beispielrechnung mit echten Ertragsdaten und typischen Preisen.",
            "html": f"""
<p class="lead">Ein Speicher erhöht vor allem, wie viel deines Solarstroms du selbst nutzt. Ob er sich lohnt, hängt fast nur vom Aufpreis und deinem Stromverbrauch am Abend ab.</p>
<h2>Die Beispielrechnung</h2>
<p>Ein Set mit {C.SET_WP} Wp am Süd-Balkon erzeugt im deutschen Schnitt etwa {fmt(base)} kWh im Jahr. Bei {C.STROMPREIS_CT} ct/kWh:</p>
<div class="scroll"><table><thead><tr><th></th><th>Eigenverbrauch</th><th>Ersparnis pro Jahr</th></tr></thead><tbody>
<tr><th>Ohne Speicher</th><td>{int(C.EIGENVERBRAUCH * 100)} %</td><td>{euro(sv(base, C.EIGENVERBRAUCH))}</td></tr>
<tr><th>Mit Speicher</th><td>80 %</td><td>{euro(sv(base, 0.8))}</td></tr>
<tr><th>Unterschied</th><td></td><td><b>{euro(sv(base, 0.8) - sv(base, C.EIGENVERBRAUCH))}</b></td></tr>
</tbody></table></div>
<p>Kostet der Speicher 500 € extra, dauert es bei dieser Anlage rund {fmt(500 / (sv(base, 0.8) - sv(base, C.EIGENVERBRAUCH)), 1)} Jahre, bis er sich bezahlt hat, länger als bei den Modulen selbst.</p>
<h2>Wann ein Speicher sinnvoll ist</h2>
<ul>
<li><b>Mehr Modulleistung:</b> Mit 1.600–2.000 Wp entsteht mittags viel mehr Strom, als 800 W Einspeisung und dein Grundverbrauch abnehmen. Ein Speicher fängt diesen Überschuss auf. Hier lohnt er sich am ehesten.</li>
<li><b>Tagsüber niemand zu Hause:</b> Dann fällt der Eigenverbrauch ohne Speicher eher auf 20–30 %.</li>
<li><b>Hoher Strompreis:</b> Jeder Cent mehr pro kWh verkürzt die Amortisation.</li>
</ul>
<h2>Wann eher nicht</h2>
<p>Bei einem einfachen Set mit zwei Modulen deckt dein Grundverbrauch (Kühlschrank, Router, Standby) einen großen Teil des Ertrags schon direkt. Dann investierst du das Geld besser in ein drittes oder viertes Modul.</p>
<p>Spiel die Zahlen für deine Situation im <a href="{url('rechner/')}">Rechner</a> durch: Setze den Eigenverbrauch einmal auf {int(C.EIGENVERBRAUCH * 100)} % und einmal auf 80 % und rechne den Aufpreis des Speichers dazu.</p>""",
        },
    ]
