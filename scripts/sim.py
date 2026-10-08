"""Stundensimulation eines Balkonkraftwerks, identisch zum Rechner in assets/app.js."""
import json

import config as C

DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
LIMIT = 0.8  # kW


class Model:
    def __init__(self, assets):
        self.assets = assets
        self.load = json.loads((assets / "load_h25.json").read_text())
        self.frac = {}

    def hourly(self, key):
        if key not in self.frac:
            self.frac[key] = json.loads((self.assets / "hourly" / f"{key}.json").read_text())
        return self.frac[key]

    def run(self, monthly, key, wp, annual, batt=0, price_ct=None):
        frac, load, kwp = self.hourly(key), self.load, wp / 1000
        eta, k = C.ETA, 1 - C.KALIBRIERUNG
        h, soc = 0, 0.0
        pv_sum = used_sum = clipped = 0.0
        for m in range(12):
            for _ in range(DAYS[m] * 24):
                pv = monthly[m] * frac[h] / 1e5 * kwp
                need = annual * load[h] / 1e6
                direct = min(pv, need, LIMIT) * k
                rest, out, used = pv - direct, direct, direct
                if batt:
                    # Eigenverbrauch des Speichers: aus dem Akku, sonst aus dem Netz
                    sb = C.STANDBY_W / 1000
                    take = min(soc, sb)
                    soc -= take
                    used -= sb - take
                    charge = min(rest, (batt - soc) / eta)
                    soc += charge * eta
                    rest -= charge
                    dis = min(need - direct, soc * eta, LIMIT - out)
                    if dis > 0:
                        soc -= dis / eta
                        out += dis
                        used += dis
                exp = min(rest, LIMIT - out)
                out += exp
                clipped += rest - exp
                pv_sum += out
                used_sum += used
                h += 1
        price = (price_ct if price_ct is not None else C.STROMPREIS_CT) / 100
        return {"pv": pv_sum, "used": used_sum, "clipped": clipped, "eur": used_sum * price}
