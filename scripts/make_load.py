"""Erzeugt assets/load_h25.json: Haushalts-Lastgang über ein Jahr (8760 Stunden), Anteil am Jahresverbrauch in 1/1.000.000.

Quelle: BDEW-Standardlastprofil H25 (Haushalt, 2025), Viertelstundenwerte je Monat und Tagtyp
(Werktag, Samstag, Sonn-/Feiertag). Dynamisiert mit der BDEW-Polynomfunktion für Haushaltsprofile.
Die Excel-Datei des BDEW wird als Argument übergeben:
    python3 scripts/make_load.py BDEW_H25_G25_L25_P25_S25.xlsx   (braucht openpyxl)
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent


def main(path):
    ws = openpyxl.load_workbook(path, read_only=True, data_only=True)["H25"]
    rows = list(ws.iter_rows(values_only=True))
    types = rows[3][2:38]  # SA / FT / WT je Monat
    quarter = [r[2:38] for r in rows[4:100]]  # 96 Viertelstunden
    # hourly[(monat, tagtyp)] = 24 Stundenwerte
    hourly = {}
    for col, t in enumerate(types):
        m = col // 3
        hourly[(m, t)] = [sum(quarter[h * 4 + q][col] for q in range(4)) for h in range(24)]

    out, d = [], date(2021, 1, 1)
    while d.year == 2021:
        t = "SA" if d.weekday() == 5 else "FT" if d.weekday() == 6 else "WT"
        n = d.timetuple().tm_yday
        dyn = -3.92e-10 * n ** 4 + 3.2e-7 * n ** 3 - 7.02e-5 * n ** 2 + 2.1e-3 * n + 1.24
        out.extend(v * dyn for v in hourly[(d.month - 1, t)])
        d += timedelta(days=1)
    total = sum(out)
    res = [round(v / total * 1e6) for v in out]
    (ROOT / "assets" / "load_h25.json").write_text(json.dumps(res, separators=(",", ":")))
    print(len(res), "Stunden, Spitze", max(res), "Minimum", min(res))


if __name__ == "__main__":
    main(sys.argv[1])
