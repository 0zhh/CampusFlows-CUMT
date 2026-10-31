"""Download the explicitly listed public evidence; no package installation needed."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit, urlunsplit
from urllib.request import Request, urlopen
import hashlib
import json
import re
import argparse

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
ITEMS = [
    ("S01", "https://www.cumtlive.com/Life/Service/Logistics.html", "sources/cumtlive_logistics.html"),
    ("S02", "https://www.cumtlive.com/Freshman/矿大地图快速上手.html", "sources/cumtlive_map.html"),
    ("S03", "https://zwb.cumt.edu.cn/info/1029/7982.htm", "sources/cumt_2025_network.html"),
    ("S04", "https://zwb.cumt.edu.cn/info/1029/5811.htm", "sources/cumt_2022_upgrade.html"),
    ("S05", "https://zwb.cumt.edu.cn/__local/0/15/58/6D6D980C1AABD75CF6FD1E8AB05_2DD5E2AA_3EAED.pdf", "sources/cumt_2026_winter.pdf"),
    ("S06", "https://zwb.cumt.edu.cn/__local/D/95/B2/F447997BEE8B9EB98B44B95AB96_588CBAF3_57F7A.pdf", "sources/cumt_2025_winter.pdf"),
    ("S07", "https://zwb.cumt.edu.cn/info/1027/8255.htm", "sources/cumt_2025_summer_report.html"),
    ("S08", "https://swdt.cumt.edu.cn/ggfw/list.htm", "sources/cumt_official_map_index.html"),
    ("S09", "https://nic.cumt.edu.cn/fwzn2/xydt.htm", "sources/cumt_map_service.html"),
    ("S10", "https://yz.cumt.edu.cn/info/1004/2502.htm", "sources/cumt_2025_exam_map_page.html"),
    ("S11", "https://jjc.cumt.edu.cn/info/1054/1312.htm", "sources/cumt_planning_map_page.html"),
    ("A01", "https://s2.loli.net/2024/08/29/5vHAIrF97Og2ynu.png", "maps/cumtlive_logistics_locations.png"),
    ("A02", "https://s2.loli.net/2025/09/25/NhSnq86P9GMfeB1.png", "reference/cumtlive_pickup_guide.png"),
    ("A03", "https://s2.loli.net/2024/11/13/nZk79doNqsF8ybT.jpg", "reference/cumtlive_mailroom_notice.jpg"),
    ("A04", "https://zwb.cumt.edu.cn/__local/F/BF/FF/29D00949D3AF7BA3302E57D196E_0762541C_44D68.jpg?e=.jpg", "reference/cumt_2022_unmanned_station_photo.jpg"),
    ("A05", "https://yz.cumt.edu.cn/system/_content/download.jsp?urltype=news.DownloadAttachUrl&owner=1754592961&wbfileid=17819843", "maps/cumt_official_campus_traffic_2025.png"),
    ("A06", "https://zwb.cumt.edu.cn/__local/3/D7/42/2080B305DB76CC934D4C4608F97_5F784DE0_E9CEA.png", "reference/cumt_2025_logistics_photo_campus_unconfirmed.png"),
    ("S12", "https://zwb.cumt.edu.cn/info/1029/7595.htm", "sources/cumt_2024_welcome_logistics.html"),
    ("S15", "https://zwb.cumt.edu.cn/info/1027/1675.htm", "sources/cumt_2024_nju_visit.html"),
    ("S16", "https://see.cumt.edu.cn/info/1130/2111.htm", "sources/cumt_2023_station_volunteers.html"),
    ("S17", "https://www.sohu.com/a/692436923_121448078", "sources/yangzi_2023_cumt_sohu.html"),
    ("S18", "https://zwb.cumt.edu.cn/info/1027/1658.htm", "sources/cumt_2024_winter_report.html"),
    ("A07", "https://zwb.cumt.edu.cn/__local/B/D8/E9/80FED613066165AAB892A31584D_84E76304_9FEB51.jpg", "reference/cumt_2024_nanhu_logistics_inspection.jpg"),
    ("A08", "https://zwb.cumt.edu.cn/__local/3/73/A3/705A0B9CD1F6339F080E115D9D0_96CEE635_28D1E.jpg?e=.jpg", "reference/cumt_2024_logistics_visit_interior.jpg"),
    ("A09", "https://see.cumt.edu.cn/__local/3/C2/A7/DB93BB379331CABDBC4D4AD2CFA_5F6A5960_5A51F.jpg", "reference/cumt_2023_station_volunteers_01.jpg"),
    ("A10", "https://see.cumt.edu.cn/__local/9/FC/11/631B7F79AEBA218DFAF43D59D65_FE0FD248_5E4FD.jpg", "reference/cumt_2023_station_volunteers_02.jpg"),
    ("A11", "https://zwb.cumt.edu.cn/__local/5/92/EE/72952E4A8066B3EEDA293999EE1_96890C12_37CBE.jpg?e=.jpg", "reference/cumt_2024_winter_logistics_photo.jpg"),
]


class TextReader(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style"):
            self.skip += 1
        if tag in ("p", "div", "li", "h1", "h2", "h3", "br", "tr"):
            self.parts.append("\n")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def download(item):
    identifier, url, relative = item
    parts = urlsplit(url)
    safe_url = urlunsplit((parts.scheme, parts.netloc, quote(parts.path), parts.query, parts.fragment))
    record = {"id": identifier, "url": url, "local_path": relative,
              "retrieved_at": datetime.now(timezone.utc).isoformat(), "status": "failed"}
    try:
        headers = {"User-Agent": "Mozilla/5.0", "Accept": "*/*"}
        if identifier == "A05":
            headers["Referer"] = "https://yz.cumt.edu.cn/info/1004/2502.htm"
        req = Request(safe_url, headers=headers)
        with urlopen(req, timeout=35) as response:
            content = response.read(25_000_001)
            content_type = response.headers.get("Content-Type", "")
            record.update(http_status=response.status, final_url=response.url, content_type=content_type)
        if len(content) > 25_000_000:
            raise ValueError("Asset exceeds the 25 MB collection limit")
        if relative.endswith(".pdf") and not content.startswith(b"%PDF"):
            raise ValueError("PDF URL did not return PDF bytes")
        if relative.endswith((".jpg", ".png")) and not (content.startswith(b"\xff\xd8") or content.startswith(b"\x89PNG\r\n\x1a\n")):
            raise ValueError("Image URL did not return PNG/JPEG bytes")
        dest = DATA / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(content)
        record.update(status="downloaded", bytes=len(content), sha256=hashlib.sha256(content).hexdigest())
        if relative.endswith(".html"):
            declared = re.search(br'<meta[^>]+charset=["\']?([^\s"\'/>;]+)', content[:6000], re.I)
            encoding = declared.group(1).decode("ascii") if declared else "utf-8"
            html = content.decode(encoding, "replace")
            reader = TextReader()
            reader.feed(html)
            text = re.sub(r"\n\s*\n+", "\n", "".join(reader.parts))
            dest.with_suffix(".txt").write_text(text, encoding="utf-8")
            title = re.search(r"<title>(.*?)</title>", html, re.S | re.I)
            record["title"] = unescape(title.group(1)).strip() if title else None
            record["image_links"] = [unescape(u) for u in re.findall(r'<img[^>]+src=["\']([^"\']+)', html) if not u.startswith("data:")]
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
    return record


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--ids", nargs="*")
    args = parser.parse_args()
    selected = [item for item in ITEMS if not args.ids or item[0] in args.ids]
    manifest = DATA / "research" / "downloads.json"
    records = json.loads(manifest.read_text(encoding="utf-8")) if args.ids and manifest.exists() else []
    records = [record for record in records if record["id"] not in {item[0] for item in selected}]
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = {pool.submit(download, item): item[0] for item in selected}
        for future in as_completed(futures):
            record = future.result()
            records.append(record)
            print(json.dumps({k: record[k] for k in ("id", "status", "bytes", "title", "error", "image_links") if k in record}, ensure_ascii=False), flush=True)
    records.sort(key=lambda r: r["id"])
    (DATA / "research" / "downloads.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
