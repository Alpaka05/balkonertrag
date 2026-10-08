"""Screenshot einer Seite. Aufruf: python tools/screenshot.py URL ziel.png BREITE light|dark [full]"""
import sys, asyncio
from playwright.async_api import async_playwright
async def main():
    url, out, w, scheme = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
    full = len(sys.argv) > 5
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": w, "height": 900}, color_scheme=scheme, device_scale_factor=1)
        msgs = []
        pg.on("console", lambda m: msgs.append(m.text))
        pg.on("pageerror", lambda e: msgs.append("ERR " + str(e)))
        await pg.goto(url); await pg.wait_for_timeout(800)
        await pg.screenshot(path=out, full_page=full)
        for m in msgs: print(m)
        await b.close()
asyncio.run(main())
