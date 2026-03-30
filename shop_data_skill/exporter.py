from __future__ import annotations

import os

import pandas as pd

from .config import EXPORT_DIR, EXPORT_FILENAME, ensure_runtime_dirs
from .models import get_connection


VALIDITY_LABELS = {
    "valid": "有效",
    "maybe_valid": "疑似有效",
    "invalid": "无效",
}


def run_export() -> str:
    ensure_runtime_dirs()
    conn = get_connection()

    df_clean = pd.read_sql_query(
        """
        SELECT
            id AS 序号,
            name AS 门店名称,
            phone AS 联系电话,
            address AS 地址,
            type AS 类型,
            district AS 所属区域,
            road AS 所属道路,
            source AS 数据来源,
            crawl_time AS 抓取时间,
            validity AS 有效性状态,
            dup_flag AS 去重标记,
            lng AS 经度,
            lat AS 纬度
        FROM clean_shops
        WHERE dup_flag != 'duplicate'
        ORDER BY type, name
        """,
        conn,
    )

    df_raw = pd.read_sql_query(
        """
        SELECT
            id AS 序号,
            raw_name AS 原始名称,
            raw_phone AS 原始电话,
            raw_address AS 原始地址,
            raw_type AS 原始类型,
            source AS 数据来源,
            source_id AS 来源ID,
            lng AS 经度,
            lat AS 纬度,
            crawl_time AS 抓取时间,
            grid_id AS 网格编号,
            category_code AS 类别编码
        FROM raw_shops
        ORDER BY source, raw_type, raw_name
        """,
        conn,
    )

    df_issues = pd.read_sql_query(
        """
        SELECT
            id AS 序号,
            name AS 门店名称,
            phone AS 联系电话,
            address AS 地址,
            type AS 类型,
            source AS 数据来源,
            validity AS 有效性状态,
            dup_flag AS 去重标记,
            dup_group_id AS 重复组ID,
            dup_confidence AS 重复置信度
        FROM clean_shops
        WHERE dup_flag = 'duplicate' OR validity != 'valid'
        ORDER BY dup_group_id, dup_flag, name
        """,
        conn,
    )

    conn.close()

    for frame in (df_clean, df_issues):
        if "有效性状态" in frame.columns:
            frame["有效性状态"] = frame["有效性状态"].map(VALIDITY_LABELS).fillna(frame["有效性状态"])

    export_path = os.path.join(EXPORT_DIR, EXPORT_FILENAME)
    with pd.ExcelWriter(export_path, engine="openpyxl") as writer:
        df_clean.to_excel(writer, sheet_name="清洗标准表", index=False)
        df_raw.to_excel(writer, sheet_name="原始采集表", index=False)
        df_issues.to_excel(writer, sheet_name="异常与重复", index=False)

    print(f"[export] Wrote Excel file to {export_path}")
    return export_path
