"""Meldet alle URLs aus site/sitemap.xml per IndexNow an Bing & Co. Nach jedem Deployment ausführen."""
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402

urls = re.findall(r"<loc>(.*?)</loc>", (Path(__file__).resolve().parent.parent / "site" / "sitemap.xml").read_text())
body = json.dumps({
    "host": C.SITE_URL.split("/")[2],
    "key": C.INDEXNOW_KEY,
    "keyLocation": f"{C.SITE_URL}/{C.INDEXNOW_KEY}.txt",
    "urlList": urls,
}).encode()
req = urllib.request.Request("https://www.bing.com/indexnow", body, {"Content-Type": "application/json; charset=utf-8"})
with urllib.request.urlopen(req, timeout=60) as r:
    print(r.status, len(urls), "URLs gemeldet")
