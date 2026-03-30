from __future__ import annotations

import random
import time
from datetime import datetime

import requests

from ..config import (
    AMAP_CATEGORIES,
    AMAP_KEY,
    AMAP_PAGE_SIZE,
    GRID_STEP,
    JIANGYIN_BOUNDS,
    MAX_RETRIES,
    REQUEST_DELAY_MAX,
    REQUEST_DELAY_MIN,
    REQUEST_TIMEOUT,
)
from ..models import (
    batch_insert_raw_shops,
    get_connection,
    get_raw_shop_count,
    init_db,
    is_task_done,
    update_progress,
)


AMAP_POLYGON_SEARCH_URL = "https://restapi.amap.com/v3/place/polygon"


def generate_grids() -> list[tuple[str, float, float, float, float]]:
    grids: list[tuple[str, float, float, float, float]] = []
    lat = JIANGYIN_BOUNDS["lat_min"]
    row = 0
    while lat < JIANGYIN_BOUNDS["lat_max"]:
        lng = JIANGYIN_BOUNDS["lng_min"]
        col = 0
        while lng < JIANGYIN_BOUNDS["lng_max"]:
            grid_id = f"G{row:02d}_{col:02d}"
            lat_end = min(lat + GRID_STEP, JIANGYIN_BOUNDS["lat_max"])
            lng_end = min(lng + GRID_STEP, JIANGYIN_BOUNDS["lng_max"])
            grids.append((grid_id, lng, lat, lng_end, lat_end))
            lng += GRID_STEP
            col += 1
        lat += GRID_STEP
        row += 1
    return grids


def search_amap_poi(types: str, polygon: str, page: int = 1) -> tuple[list[dict] | None, int]:
    params = {
        "key": AMAP_KEY,
        "types": types,
        "polygon": polygon,
        "offset": AMAP_PAGE_SIZE,
        "page": page,
        "extensions": "all",
        "output": "json",
    }

    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(AMAP_POLYGON_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
            payload = response.json()
            if payload.get("status") == "1":
                return payload.get("pois", []), int(payload.get("count", 0))
            if payload.get("infocode") in {"10003", "10004", "10044"}:
                time.sleep(60)
                continue
            return None, 0
        except requests.RequestException:
            time.sleep(2)
    return None, 0


def parse_amap_poi(poi: dict, grid_id: str, category_code: str) -> dict:
    phone = poi.get("tel", "") or ""
    if isinstance(phone, list):
        phone = ";".join(phone)

    lng = None
    lat = None
    location = poi.get("location", "")
    if location and "," in str(location):
        parts = str(location).split(",")
        if len(parts) == 2:
            try:
                lng = float(parts[0])
                lat = float(parts[1])
            except ValueError:
                lng = None
                lat = None

    return {
        "raw_name": poi.get("name", ""),
        "raw_phone": phone,
        "raw_address": poi.get("address", "")
        or f"{poi.get('pname', '')}{poi.get('cityname', '')}{poi.get('adname', '')}",
        "raw_type": poi.get("type", "") or "",
        "source": "amap",
        "source_id": poi.get("id", ""),
        "lng": lng,
        "lat": lat,
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "grid_id": grid_id,
        "category_code": category_code,
        "raw_extra": "",
    }


def collect_grid_category(conn, grid, category, test_mode: bool = False) -> int:
    grid_id, lng_min, lat_min, lng_max, lat_max = grid
    category_code = category["code"]

    if is_task_done(conn, "amap", grid_id, category_code):
        return 0

    polygon = f"{lng_min},{lat_min}|{lng_max},{lat_max}"
    total_collected = 0
    page = 1

    while True:
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        pois, total = search_amap_poi(category_code, polygon, page)
        if pois is None or not pois:
            break

        inserted, skipped = batch_insert_raw_shops(
            conn, [parse_amap_poi(poi, grid_id, category_code) for poi in pois]
        )
        total_collected += inserted
        print(
            f"[amap] {grid_id} {category['name']} page={page} rows={len(pois)} "
            f"inserted={inserted} skipped={skipped} total={total}"
        )

        if len(pois) < AMAP_PAGE_SIZE or page * AMAP_PAGE_SIZE >= total or page >= 100 or test_mode:
            break
        page += 1

    update_progress(conn, "amap", grid_id, category_code, "done", total_collected)
    return total_collected


def run_amap_collection(test_mode: bool = False) -> int:
    init_db()
    conn = get_connection()
    grids = generate_grids()
    categories = AMAP_CATEGORIES
    total_new = 0
    total_tasks = len(grids) * len(categories)
    task_index = 0

    for grid in grids:
        for category in categories:
            task_index += 1
            if is_task_done(conn, "amap", grid[0], category["code"]):
                continue
            print(f"[amap] task {task_index}/{total_tasks}: {grid[0]} {category['name']}")
            total_new += collect_grid_category(conn, grid, category, test_mode=test_mode)
            if test_mode:
                conn.close()
                return total_new

    total_count = get_raw_shop_count(conn)
    conn.close()
    print(f"[amap] finished. new_rows={total_new} raw_total={total_count}")
    return total_new
