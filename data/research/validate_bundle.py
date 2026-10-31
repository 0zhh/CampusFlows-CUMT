"""Validate evidence integrity and prevent unknowns becoming measured values."""
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image
from pypdf import PdfReader
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
checks = []


def check(name, passed, detail):
    checks.append({"name": name, "passed": bool(passed), "detail": detail})


def read(path):
    return json.loads((DATA / path).read_text(encoding="utf-8"))


def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


json_paths = [p for p in DATA.rglob("*.json") if p.name not in ("validation_report.json", "file_manifest.json")]
for path in json_paths:
    try:
        json.loads(path.read_text(encoding="utf-8"))
        check("JSON parse " + str(path.relative_to(DATA)), True, "UTF-8 JSON parsed")
    except Exception as error:
        check("JSON parse " + str(path.relative_to(DATA)), False, str(error))

sources = read("source_catalog.json")["sources"]
source_ids = {s["id"] for s in sources}
assets = read("assets_catalog.json")["assets"]
asset_ids = {a["id"] for a in assets}
check("Unique source identifiers", len(source_ids) == len(sources), str(len(sources)))
check("Unique asset identifiers", len(asset_ids) == len(assets), str(len(assets)))


def visit(value, location):
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "source_ids":
                check("Source references " + location, all(identifier in source_ids for identifier in item), str(item))
            elif key == "asset_id":
                check("Asset reference " + location, item in asset_ids, str(item))
            visit(item, location + "/" + key)
    elif isinstance(value, list):
        for index, item in enumerate(value):
            visit(item, location + "/" + str(index))


for path in json_paths:
    if path.name not in ("downloads.json", "research_log.json"):
        visit(json.loads(path.read_text(encoding="utf-8")), path.name)

downloads = read("research/downloads.json")
for record in downloads:
    if record["status"] == "downloaded":
        path = DATA / record["local_path"]
        check("Downloaded file " + record["id"], path.is_file() and hash_file(path) == record["sha256"], record["local_path"])
    else:
        check("Unavailable source clearly marked " + record["id"], record["id"] == "S08", record.get("error"))

site_data = read("nanhu_sites.json")
sites = site_data["sites"]
check("Exactly four physical Cainiao sites", len(sites) == site_data["physical_cainiao_site_count"] == 4, [s["name"] for s in sites])
check("Expected site IDs", {s["id"] for s in sites} == {"NH-TAOYUAN", "NH-SONGYUAN", "NH-MEIYUAN", "NH-LANYUAN"}, "No invented station")
for site in sites:
    check("Unknown warehouse values " + site["id"], all(v is None for v in site["warehouse_measured"].values()), "No unverified numeric warehouse parameters")
    hours = site["normal_service_hours"]
    expected = ("08:30", "18:30") if site["id"] == "NH-TAOYUAN" else ("07:00", "23:30")
    check("User-selected hours " + site["id"], (hours["open"], hours["close"]) == expected and hours["demo_baseline_decision_id"] == "USER-001", str(expected))
    check("No invented GPS " + site["id"], site["location"]["latitude"] is None and site["location"]["longitude"] is None, "Image pixels only")
points = site_data["supplementary_service_points"]
check("SF JD are subservices", all(p["parent_site_id"] == "NH-TAOYUAN" and not p["independent_physical_site"] for p in points if p["kind"] == "courier_counter"), "No duplicate warehouse count")

maps = read("maps/map_manifest.json")["maps"]
for mapping in maps:
    path = DATA / mapping["local_path"]
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        size = image.size
    check("Map dimensions and hash " + mapping["id"], size == (mapping["width_px"], mapping["height_px"]) and hash_file(path) == mapping["sha256"], str(size))
for asset in assets:
    path = DATA / asset["local_path"]
    with Image.open(path) as photo:
        photo.verify()
    with Image.open(path) as photo:
        size = photo.size
    check("Photo integrity " + asset["id"], size == (asset["width_px"], asset["height_px"]) and hash_file(path) == asset["sha256"], asset["local_path"])
visual = read("nanhu_visual_evidence.json")
check("No layout inferred from low-information photos", visual["layout_reconstruction_ready"] is False and visual["floor_plans_obtained"] == [] and visual["high_information_layout_asset_ids"] == [], "User requires identifiable functional zones and their relationships")
check("User photo feedback recorded", visual["user_photo_review"]["status"] == "answered_insufficient_layout_information", "A08 remains background only")
markers = read("maps/logistics_markers.json")
check("All four map markers in image bounds", len(markers["markers"]) == 4 and all(0 <= m["x"] < markers["image_width"] and 0 <= m["y"] < markers["image_height"] for m in markers["markers"]), "1821 x 1123 image coordinates")

for filename in ("cumt_2026_winter.pdf", "cumt_2025_winter.pdf"):
    reader = PdfReader(DATA / "sources" / filename)
    text = reader.pages[3].extract_text()
    check("Official PDF logistics table " + filename, len(reader.pages) == 7 and all(word in text for word in ("桃苑", "松苑", "梅苑", "兰苑")), "Seven pages; page four contains all four stations")
    check("Rendered PDF reference " + filename, (DATA / "reference" / (filename.removesuffix(".pdf") + "_logistics_page4.png")).is_file(), "Visual review artifact exists")

raw_csv = (DATA / "nanhu_sites.csv").read_bytes()
rows = list(csv.DictReader(raw_csv.decode("utf-8-sig").splitlines()))
check("CSV BOM and four unknown-capacity rows", raw_csv.startswith(b"\xef\xbb\xbf") and len(rows) == 4 and all(row["capacity_parcels"] == "" for row in rows), "UTF-8 BOM; no 0 substituted for unknown")
template = read("demo/scenario_template.json")
check("Demo isolated and empty", template["not_real_operations"] is True and template["demand"] == [] and all(r["assumed_pickup_inventory_capacity"] is None for r in template["initial_state"]), "No fictitious traffic called real")

markdown_files = [DATA / "README.md", DATA / "资料核验与缺口.md", DATA / "reference/实景素材索引.md", ROOT / "CampusFlow_总体开发计划与实施路线_v1.2_南湖校区驿链演示版.md"]
for path in markdown_files:
    text = path.read_text(encoding="utf-8")
    check("No replacement characters " + path.name, "\ufffd" not in text, "UTF-8 text")
    for target in re.findall(r"\]\(([^)]+)\)", text):
        if not re.match(r"https?://", target):
            check("Local markdown link " + target, (path.parent / target).exists(), path.name)
    refs = set(re.findall(r"\bS\d{2}\b", text))
    check("Markdown source references " + path.name, refs <= source_ids, sorted(refs))

baseline = next((DATA / "baseline").glob("*.md"))
original = Path("C:/Users/zhh/Downloads/CampusFlow_总体开发计划与实施路线_v1.1_软件工程规范版.md")
check("Original preserved exactly", original.exists() and hash_file(original) == hash_file(baseline), "Downloads original equals project backup")

report = {"checked_at": datetime.now(timezone.utc).isoformat(), "scope": "Research bundle integrity; not application tests or field validation",
          "passed": all(row["passed"] for row in checks), "check_count": len(checks),
          "failed_checks": [row for row in checks if not row["passed"]], "checks": checks,
          "limitations": ["No field survey", "Warehouse numeric parameters still unknown", "No frontend or Java application built in this task"]}
write_path = DATA / "research/validation_report.json"
write_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
manifest = []
for path in sorted(ROOT.rglob("*")):
    if path.is_file() and path.name != "file_manifest.json" and "__pycache__" not in path.parts:
        manifest.append({"path": path.relative_to(ROOT).as_posix(), "bytes": path.stat().st_size, "sha256": hash_file(path)})
(DATA / "research/file_manifest.json").write_text(json.dumps({"files": manifest}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"passed": report["passed"], "checks": len(checks), "failed_checks": report["failed_checks"], "file_count": len(manifest), "total_bytes": sum(x["bytes"] for x in manifest)}, ensure_ascii=False))
raise SystemExit(0 if report["passed"] else 1)
