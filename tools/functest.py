"""Browser-Funktionstest: Rechner, Ost-West, geteilte Links, PLZ-Suche, Sortierung, Antrag.

Aufruf: python tools/functest.py [BASIS-URL]   (braucht playwright + chromium)
"""
import asyncio
from playwright.async_api import async_playwright
import sys
B = sys.argv[1] if len(sys.argv) > 1 else "https://alpaka05.github.io/balkonertrag/"
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(B + "stadt/berlin/"); await pg.wait_for_timeout(600)
        t = lambda n: pg.locator(f".calc [data-out={n}]").first.inner_text()
        print("default", await t("kwh"), await t("self"), await t("eur"), await t("years"))
        await pg.select_option(".calc [name=aspect]", "OW"); await pg.select_option(".calc [name=angle]", "35"); await pg.wait_for_timeout(400)
        print("OW35", await t("kwh"), await t("self"), await t("eur"))
        await pg.fill(".calc [name=wp]", "2000"); await pg.fill(".calc [name=batt]", "2"); await pg.wait_for_timeout(400)
        print("OW35 2000 2kWh", await t("kwh"), await t("self"), await t("eur"), "|", await t("note"))
        await pg.select_option(".calc [name=angle]", "0"); await pg.wait_for_timeout(300)
        print("flat", await t("kwh"), await t("assume"))
        await pg.goto(B + "rechner/?a=SW&n=60&wp=1200&v=3500&b=1.6&p=40&c=900"); await pg.wait_for_timeout(600)
        print("shared", await t("assume"), await t("eur"))
        await pg.goto(B); await pg.fill("form.search input", "10115"); await pg.press("form.search input", "Enter"); await pg.wait_for_timeout(800)
        print("plz ->", pg.url)
        await pg.goto(B); await pg.fill("form.search input", "münch"); await pg.press("form.search input", "Enter"); await pg.wait_for_timeout(800)
        print("prefix ->", pg.url)
        await pg.goto(B + "bundesland/bayern/"); await pg.click("th:has-text('Ersparnis')"); await pg.click("th:has-text('Ersparnis')")
        print("sorted top:", await pg.locator("tbody tr").first.inner_text())
        await pg.goto(B + "vermieter-antrag/"); await pg.fill("[name=name]", "Erika Muster"); await pg.check("[value=weg]"); await pg.wait_for_timeout(200)
        txt = await pg.locator(".letter").inner_text()
        print("letter:", txt.splitlines()[0], "|", [l for l in txt.splitlines() if "WEG" in l][:1], "| has M-line:", "§ 554" in txt)
        print("errors:", errs)
        await b.close()
asyncio.run(main())
