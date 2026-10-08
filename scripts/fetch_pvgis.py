"""Holt Ertragsdaten (kWh pro kWp) von PVGIS für alle Städte in data/cities_raw.tsv.

Ergebnis: data/pvgis.json  {"<name>": {"lat":..,"lon":..,"pop":..,"state":..,"y":{"S35":..},"m":{"S35":[12], ...}}}
Schlüssel: Ausrichtung + Neigung, z. B. "SW60"; "F0" = flach (0°, Ausrichtung egal).
Bereits geholte Städte werden übersprungen, das Skript kann also jederzeit neu gestartet werden.
"""
import json
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / (sys.argv[2] if len(sys.argv) > 2 else "pvgis.json")
API = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"

ASPECTS = {"S": 0, "SO": -45, "SW": 45, "O": -90, "W": 90}
ANGLES = [15, 25, 35, 45, 60, 75, 90]

NAME_FIX = {
    "Munich": "München",
    "Nuremberg": "Nürnberg",
    "Cologne": "Köln",
    "Freiburg": "Freiburg im Breisgau",
    "Offenbach": "Offenbach am Main",
    "Hanover": "Hannover",
    "Brunswick": "Braunschweig",
}


def call(lat, lon, aspect, angle):
    url = (f"{API}?lat={lat}&lon={lon}&peakpower=1&loss=14&angle={angle}"
           f"&aspect={aspect}&outputformat=json")
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                d = json.load(r)
            return d["outputs"]["totals"]["fixed"]["E_y"], [m["E_m"] for m in d["outputs"]["monthly"]["fixed"]]
        except Exception as e:  # PVGIS drosselt gelegentlich
            time.sleep(2 + attempt * 3)
            last = e
    raise RuntimeError(f"PVGIS fehlgeschlagen für {lat},{lon}: {last}")


def city(row):
    name, lat, lon, pop, state = row
    y, m = {}, {}
    combos = [("F0", 0, 0)] + [(f"{a}{g}", asp, g) for a, asp in ASPECTS.items() for g in ANGLES]
    for key, aspect, angle in combos:
        ey, em = call(lat, lon, aspect, angle)
        y[key] = round(ey, 1)
        m[key] = [round(v, 1) for v in em]
    return name, {"lat": float(lat), "lon": float(lon), "pop": int(pop), "state": state, "y": y, "m": m}


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10_000
    data = json.loads(OUT.read_text()) if OUT.exists() else {}
    rows, seen = [], set(data)
    # Städte mit unvollständigem Datensatz (ältere Läufe) neu holen
    data = {n: d for n, d in data.items() if len(d["m"]) == 1 + len(ASPECTS) * len(ANGLES)}
    seen = set(data)
    for line in (ROOT / "data" / "cities_raw.tsv").read_text().splitlines()[:limit]:
        name, lat, lon, pop, state = line.split("\t")
        name = NAME_FIX.get(name, name)
        if name in seen:
            continue  # Doppelte Namen: die größere Stadt gewinnt (Liste ist nach Einwohnern sortiert)
        seen.add(name)
        rows.append((name, lat, lon, pop, state))
    print(f"{len(rows)} Städte offen, {len(data)} schon vorhanden", flush=True)
    with ThreadPoolExecutor(max_workers=16) as ex:
        for i, (name, rec) in enumerate(ex.map(city, rows), 1):
            data[name] = rec
            if i % 25 == 0 or i == len(rows):
                OUT.write_text(json.dumps(data, ensure_ascii=False))
                print(f"{i}/{len(rows)} {name}", flush=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False))


if __name__ == "__main__":
    main()
