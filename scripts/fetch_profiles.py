"""Holt ein Jahr stündlicher PVGIS-Werte für einen Referenzort (Kassel, Mitte Deutschlands), je Ausrichtung/Neigung.

Ergebnis: assets/hourly/<key>.json = 8760 Ganzzahlen: Anteil der Stunde am Monatsertrag in 1/100000.
Der Speicher-Rechner multipliziert das mit dem Monatsertrag der Stadt. So bleiben die Monatssummen ortsgenau,
und sonnige und trübe Tage wechseln sich realistisch ab (wichtig für den Speicher).
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://re.jrc.ec.europa.eu/api/v5_3/seriescalc"
LAT, LON = 51.31, 9.49
YEAR = 2020
ASPECTS = {"S": 0, "SO": -45, "SW": 45, "O": -90, "W": 90}
ANGLES = [15, 25, 35, 45, 60, 75, 90]


def profile(item):
    key, aspect, angle = item
    url = (f"{API}?lat={LAT}&lon={LON}&startyear={YEAR}&endyear={YEAR}&pvcalculation=1"
           f"&peakpower=1&loss=14&angle={angle}&aspect={aspect}&outputformat=json")
    with urllib.request.urlopen(url, timeout=120) as r:
        rows = json.load(r)["outputs"]["hourly"]
    # UTC -> MEZ (+1 h, ganzjährig; reicht für die Bilanz), 29. Februar weglassen -> 8760 Stunden
    rows = [r for r in rows if r["time"][4:8] != "0229"]
    power = [r["P"] for r in rows]
    vals = list(zip((r["time"][4:8] for r in rows), power[-1:] + power[:-1]))
    month = [int(t[:2]) - 1 for t, _ in vals]
    tot = [0.0] * 12
    for m, (_, p) in zip(month, vals):
        tot[m] += p
    out = [round(p / (tot[m] or 1) * 100000) for m, (_, p) in zip(month, vals)]
    return key, out


def main():
    items = [("F0", 0, 0)] + [(f"{a}{g}", asp, g) for a, asp in ASPECTS.items() for g in ANGLES]
    with ThreadPoolExecutor(max_workers=6) as ex:
        res = dict(ex.map(profile, items))
    d = ROOT / "assets" / "hourly"
    d.mkdir(exist_ok=True)
    for k, v in res.items():
        (d / f"{k}.json").write_text(json.dumps(v, separators=(",", ":")))
    print(len(res), "Profile")


if __name__ == "__main__":
    main()
