from __future__ import annotations

import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = Path(os.getenv("DIANPU_DATA_DIR", REPO_ROOT / "data")).resolve()
EXPORT_FILENAME = os.getenv("DIANPU_EXPORT_FILENAME", "jiangyin_shops.xlsx")
EXPORT_DIR = DATA_DIR
DB_PATH = DATA_DIR / "jiangyin_shops.db"

AMAP_KEY = os.getenv("DIANPU_AMAP_KEY", "").strip()
BMAP_AK = os.getenv("DIANPU_BMAP_AK", "").strip()

JIANGYIN_BOUNDS = {
    "lat_min": 31.676,
    "lat_max": 31.960,
    "lng_min": 119.983,
    "lng_max": 120.575,
}

GRID_STEP = 0.05

AMAP_CATEGORIES = [
    {"code": "050000", "name": "餐饮服务", "standard_type": "餐饮"},
    {"code": "060000", "name": "购物服务", "standard_type": "零售"},
    {"code": "070000", "name": "生活服务", "standard_type": "生活服务"},
    {"code": "080000", "name": "体育休闲服务", "standard_type": "休闲娱乐"},
    {"code": "090000", "name": "医疗保健服务", "standard_type": "医疗健康"},
    {"code": "100000", "name": "住宿服务", "standard_type": "酒店住宿"},
    {"code": "010000", "name": "汽车服务", "standard_type": "汽车服务"},
    {"code": "141200", "name": "培训机构", "standard_type": "教育培训"},
    {"code": "160000", "name": "金融保险服务", "standard_type": "金融通信网点"},
    {"code": "120000", "name": "商务住宅", "standard_type": "商务住宅"},
]

BMAP_KEYWORDS = [
    {"keyword": "餐厅", "standard_type": "餐饮"},
    {"keyword": "小吃快餐", "standard_type": "餐饮"},
    {"keyword": "超市", "standard_type": "商超便利"},
    {"keyword": "便利店", "standard_type": "商超便利"},
    {"keyword": "服装店", "standard_type": "服饰鞋包"},
    {"keyword": "美容美发", "standard_type": "美容美发"},
    {"keyword": "药店", "standard_type": "医疗健康"},
    {"keyword": "教育培训", "standard_type": "教育培训"},
    {"keyword": "汽车维修", "standard_type": "汽车服务"},
    {"keyword": "酒店", "standard_type": "酒店住宿"},
    {"keyword": "家居建材", "standard_type": "家居建材"},
    {"keyword": "手机数码", "standard_type": "数码家电"},
    {"keyword": "银行", "standard_type": "金融通信网点"},
    {"keyword": "休闲娱乐", "standard_type": "休闲娱乐"},
    {"keyword": "生活服务", "standard_type": "生活服务"},
]

REQUEST_DELAY_MIN = 0.3
REQUEST_DELAY_MAX = 0.8
REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
AMAP_PAGE_SIZE = 25
BMAP_PAGE_SIZE = 20


def ensure_runtime_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def require_key(provider: str) -> None:
    if provider == "amap" and not AMAP_KEY:
        raise RuntimeError(
            "Missing AMap key. Set DIANPU_AMAP_KEY with your own key before collecting."
        )
    if provider == "bmap" and not BMAP_AK:
        raise RuntimeError(
            "Missing Baidu Map key. Set DIANPU_BMAP_AK with your own key before collecting."
        )
