from __future__ import annotations

import re

from .models import get_connection


def normalize_name(raw_name: str | None) -> str:
    if not raw_name:
        return ""
    return str(raw_name).strip()


def normalize_phone(raw_phone: str | None) -> str:
    if not raw_phone:
        return ""

    phones = re.split(r"[;,，、\\s/]+", str(raw_phone))
    valid: list[str] = []
    for phone in phones:
        phone = phone.strip().replace("-", "")
        if not phone:
            continue
        if re.fullmatch(r"1[3-9]\d{9}", phone):
            valid.append(phone)
        elif re.fullmatch(r"0\d{2,3}\d{7,8}", phone):
            valid.append(phone)
        elif re.fullmatch(r"[48]00\d{7,8}", phone):
            valid.append(phone)
    return ";".join(dict.fromkeys(valid))


def normalize_address(raw_address: str | None) -> str:
    if not raw_address:
        return ""

    address = str(raw_address).strip()
    prefixes = [
        "江苏省无锡市江阴市",
        "江苏省江阴市",
        "无锡市江阴市",
        "江阴市",
        "江苏省无锡市",
        "江苏省",
    ]
    for prefix in prefixes:
        if address.startswith(prefix):
            address = address[len(prefix) :]
            break
    return address.strip(" ,，")


def extract_road(address: str | None) -> str:
    if not address:
        return ""
    match = re.search(r"([\u4e00-\u9fa5A-Za-z0-9]+(?:路|街|巷|大道|大街|弄|里|广场))", address)
    return match.group(1) if match else ""


TYPE_MAPPING = {
    "餐饮": "餐饮",
    "中餐": "餐饮",
    "火锅": "餐饮",
    "小吃": "餐饮",
    "快餐": "餐饮",
    "咖啡": "餐饮",
    "茶": "餐饮",
    "超市": "商超便利",
    "便利": "商超便利",
    "购物": "零售",
    "商场": "零售",
    "服装": "服饰鞋包",
    "鞋": "服饰鞋包",
    "箱包": "服饰鞋包",
    "美容": "美容美发",
    "美发": "美容美发",
    "药": "医疗健康",
    "医疗": "医疗健康",
    "教育": "教育培训",
    "培训": "教育培训",
    "酒店": "酒店住宿",
    "民宿": "酒店住宿",
    "数码": "数码家电",
    "手机": "数码家电",
    "银行": "金融通信网点",
    "汽车": "汽车服务",
    "维修": "汽车服务",
    "休闲": "休闲娱乐",
    "娱乐": "休闲娱乐",
    "生活": "生活服务",
}


def map_type(raw_type: str | None) -> str:
    if not raw_type:
        return "其他"
    raw = str(raw_type)
    for keyword, standard_type in TYPE_MAPPING.items():
        if keyword in raw:
            return standard_type
    return "其他"


def judge_validity(name: str, phone: str, address: str) -> str:
    if not name or len(name) <= 1:
        return "invalid"
    if phone and address:
        return "valid"
    if phone or address:
        return "maybe_valid"
    return "invalid"


def simple_similarity(left: str, right: str) -> float:
    if not left or not right:
        return 0.0
    left_chars = set(left)
    right_chars = set(right)
    union = left_chars | right_chars
    return len(left_chars & right_chars) / len(union) if union else 0.0


def find_duplicates(shops: list[dict]) -> dict[int, dict]:
    dup_map: dict[int, dict] = {}
    group_id = 0
    processed: set[int] = set()

    for index, shop_a in enumerate(shops):
        shop_a_id = shop_a["id"]
        if shop_a_id in processed:
            continue

        group_members: list[tuple[int, str]] = []
        for compare_index in range(index + 1, len(shops)):
            shop_b = shops[compare_index]
            shop_b_id = shop_b["id"]
            if shop_b_id in processed:
                continue

            confidence = None
            if shop_a["name"] and shop_a["name"] == shop_b["name"]:
                if shop_a["phone"] and shop_a["phone"] == shop_b["phone"]:
                    confidence = "high"
                elif simple_similarity(shop_a["address"], shop_b["address"]) > 0.7:
                    confidence = "high"
                else:
                    confidence = "medium"
            elif shop_a["phone"] and shop_a["phone"] == shop_b["phone"]:
                confidence = "high" if simple_similarity(shop_a["address"], shop_b["address"]) > 0.5 else "medium"
            elif simple_similarity(shop_a["name"], shop_b["name"]) > 0.8:
                road_a = extract_road(shop_a["address"])
                road_b = extract_road(shop_b["address"])
                if road_a and road_a == road_b:
                    confidence = "medium"

            if confidence:
                group_members.append((shop_b_id, confidence))

        if group_members:
            group_id += 1
            dup_map[shop_a_id] = {
                "dup_flag": "primary",
                "dup_group_id": group_id,
                "dup_confidence": group_members[0][1],
            }
            for member_id, confidence in group_members:
                dup_map[member_id] = {
                    "dup_flag": "duplicate",
                    "dup_group_id": group_id,
                    "dup_confidence": confidence,
                }
                processed.add(member_id)

    return dup_map


def run_cleaning() -> None:
    conn = get_connection()
    conn.execute("DELETE FROM clean_shops")
    conn.commit()

    raw_rows = conn.execute("SELECT * FROM raw_shops").fetchall()
    if not raw_rows:
        print("[clean] No raw data found.")
        conn.close()
        return

    for row in raw_rows:
        name = normalize_name(row["raw_name"])
        phone = normalize_phone(row["raw_phone"])
        address = normalize_address(row["raw_address"])
        road = extract_road(address)
        shop_type = map_type(row["raw_type"])
        validity = judge_validity(name, phone, address)

        conn.execute(
            """
            INSERT INTO clean_shops
            (name, phone, address, type, district, road, source, crawl_time,
             validity, dup_flag, raw_id, lng, lat)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                name,
                phone,
                address,
                shop_type,
                "江阴市",
                road,
                row["source"],
                row["crawl_time"],
                validity,
                "unique",
                row["id"],
                row["lng"],
                row["lat"],
            ),
        )

    conn.commit()

    clean_rows = conn.execute("SELECT * FROM clean_shops").fetchall()
    dup_map = find_duplicates([dict(row) for row in clean_rows])
    for shop_id, dup_info in dup_map.items():
        conn.execute(
            """
            UPDATE clean_shops
            SET dup_flag = ?, dup_group_id = ?, dup_confidence = ?
            WHERE id = ?
            """,
            (dup_info["dup_flag"], dup_info["dup_group_id"], dup_info["dup_confidence"], shop_id),
        )

    conn.commit()
    conn.close()
    print(f"[clean] Finished cleaning {len(raw_rows)} rows.")
