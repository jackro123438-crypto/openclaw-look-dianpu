from __future__ import annotations

import random
import time
from datetime import datetime

import requests

from ..config import (
    BMAP_AK,
    BMAP_KEYWORDS,
    BMAP_PAGE_SIZE,
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


BMAP_SEARCH_URL = "https://api.map.baidu.com/place/v2/search"


def search_bmap_poi(query: str, region: str = "江阴市", page_num: int = 0) -> tuple[list[dict] | None, int]:
    params = {
        "ak": BMAP_AK,
        "query": query,
        "region": region,
        "city_limit": "true",
        "output": "json",
        "page_size": BMAP_PAGE_SIZE,
        "page_num": page_num,
        "scope": "2",
    }

    for _ in range(MAX_RETRIES):
        try:
            response = requests.get(BMAP_SEARCH_URL, params=params, timeout=REQUEST_TIMEOUT)
            payload = response.json()
            if payload.get("status") == 0:
                return payload.get("results", []), int(payload.get("total", 0))
            if payload.get("status") in {302, 401, 4}:
                time.sleep(60)
                continue
            return None, 0
        except requests.RequestException:
            time.sleep(2)
    return None, 0


def parse_bmap_poi(poi: dict, keyword: str) -> dict:
    detail = poi.get("detail_info", {}) or {}
    location = poi.get("location", {}) or {}
    address = poi.get("address", "") or ""
    if not address:
        address = f"{poi.get('province', '')}{poi.get('city', '')}{poi.get('area', '')}"

    return {
        "raw_name": poi.get("name", ""),
        "raw_phone": detail.get("phone", "") or poi.get("telephone", "") or "",
        "raw_address": address,
        "raw_type": detail.get("tag", "") or keyword,
        "source": "bmap",
        "source_id": poi.get("uid", ""),
        "lng": location.get("lng"),
        "lat": location.get("lat"),
        "crawl_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "grid_id": "全市",
        "category_code": keyword,
        "raw_extra": "",
    }


def collect_keyword(conn, keyword_config: dict, test_mode: bool = False) -> int:
    keyword = keyword_config["keyword"]
    if is_task_done(conn, "bmap", "全市", keyword):
        return 0

    total_collected = 0
    page_num = 0
    while True:
        time.sleep(random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX))
        results, total = search_bmap_poi(keyword, page_num=page_num)
        if results is None or not results:
            break

        inserted, skipped = batch_insert_raw_shops(
            conn, [parse_bmap_poi(result, keyword) for result in results]
        )
        total_collected += inserted
        print(
            f"[bmap] {keyword} page={page_num} rows={len(results)} "
            f"inserted={inserted} skipped={skipped} total={total}"
        )

        fetched_so_far = (page_num + 1) * BMAP_PAGE_SIZE
        if len(results) < BMAP_PAGE_SIZE or fetched_so_far >= total or fetched_so_far >= 400 or test_mode:
            break
        page_num += 1

    update_progress(conn, "bmap", "全市", keyword, "done", total_collected)
    return total_collected


def run_bmap_collection(test_mode: bool = False) -> int:
    init_db()
    conn = get_connection()
    total_new = 0

    for index, keyword_config in enumerate(BMAP_KEYWORDS, start=1):
        keyword = keyword_config["keyword"]
        if is_task_done(conn, "bmap", "全市", keyword):
            continue
        print(f"[bmap] task {index}/{len(BMAP_KEYWORDS)}: {keyword}")
        total_new += collect_keyword(conn, keyword_config, test_mode=test_mode)
        if test_mode:
            conn.close()
            return total_new

    total_count = get_raw_shop_count(conn)
    conn.close()
    print(f"[bmap] finished. new_rows={total_new} raw_total={total_count}")
    return total_new
