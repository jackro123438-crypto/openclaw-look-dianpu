from __future__ import annotations

import sqlite3

from .config import DB_PATH, ensure_runtime_dirs


def get_connection() -> sqlite3.Connection:
    ensure_runtime_dirs()
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_name TEXT,
            raw_phone TEXT,
            raw_address TEXT,
            raw_type TEXT,
            source TEXT,
            source_id TEXT,
            lng REAL,
            lat REAL,
            crawl_time TEXT,
            grid_id TEXT,
            category_code TEXT,
            raw_extra TEXT,
            UNIQUE(source, source_id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clean_shops (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            phone TEXT,
            address TEXT,
            type TEXT,
            district TEXT,
            road TEXT,
            source TEXT,
            crawl_time TEXT,
            validity TEXT DEFAULT 'valid',
            dup_flag TEXT DEFAULT 'unique',
            dup_group_id INTEGER,
            dup_confidence TEXT,
            raw_id INTEGER,
            lng REAL,
            lat REAL,
            FOREIGN KEY (raw_id) REFERENCES raw_shops(id)
        )
        """
    )

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS crawl_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT,
            grid_id TEXT,
            category TEXT,
            status TEXT DEFAULT 'pending',
            total_count INTEGER DEFAULT 0,
            crawl_time TEXT,
            UNIQUE(source, grid_id, category)
        )
        """
    )

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_source_id ON raw_shops(source, source_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_name ON raw_shops(raw_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_raw_address ON raw_shops(raw_address)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_name ON clean_shops(name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_clean_phone ON clean_shops(phone)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_progress ON crawl_progress(source, grid_id, category)")

    conn.commit()
    conn.close()


def batch_insert_raw_shops(conn: sqlite3.Connection, shop_list: list[dict]) -> tuple[int, int]:
    inserted = 0
    skipped = 0
    for shop in shop_list:
        conn.execute(
            """
            INSERT OR IGNORE INTO raw_shops
            (raw_name, raw_phone, raw_address, raw_type, source, source_id,
             lng, lat, crawl_time, grid_id, category_code, raw_extra)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                shop.get("raw_name", ""),
                shop.get("raw_phone", ""),
                shop.get("raw_address", ""),
                shop.get("raw_type", ""),
                shop.get("source", ""),
                shop.get("source_id", ""),
                shop.get("lng"),
                shop.get("lat"),
                shop.get("crawl_time", ""),
                shop.get("grid_id", ""),
                shop.get("category_code", ""),
                shop.get("raw_extra", ""),
            ),
        )
        if conn.total_changes > 0:
            inserted += 1
        else:
            skipped += 1
    conn.commit()
    return inserted, skipped


def update_progress(
    conn: sqlite3.Connection,
    source: str,
    grid_id: str,
    category: str,
    status: str,
    total_count: int = 0,
) -> None:
    from datetime import datetime

    conn.execute(
        """
        INSERT OR REPLACE INTO crawl_progress
        (source, grid_id, category, status, total_count, crawl_time)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (source, grid_id, category, status, total_count, datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
    )
    conn.commit()


def is_task_done(conn: sqlite3.Connection, source: str, grid_id: str, category: str) -> bool:
    row = conn.execute(
        """
        SELECT status FROM crawl_progress
        WHERE source = ? AND grid_id = ? AND category = ?
        """,
        (source, grid_id, category),
    ).fetchone()
    return row is not None and row["status"] == "done"


def get_raw_shop_count(conn: sqlite3.Connection) -> int:
    return conn.execute("SELECT COUNT(*) AS cnt FROM raw_shops").fetchone()["cnt"]


def get_stats(conn: sqlite3.Connection) -> dict:
    stats: dict[str, object] = {}
    stats["total_raw"] = conn.execute("SELECT COUNT(*) FROM raw_shops").fetchone()[0]
    stats["total_clean"] = conn.execute("SELECT COUNT(*) FROM clean_shops").fetchone()[0]
    stats["with_phone"] = conn.execute(
        "SELECT COUNT(*) FROM raw_shops WHERE raw_phone IS NOT NULL AND raw_phone != ''"
    ).fetchone()[0]
    stats["phone_coverage"] = (
        f"{stats['with_phone'] / stats['total_raw'] * 100:.1f}%"
        if stats["total_raw"]
        else "0%"
    )
    stats["tasks_done"] = conn.execute(
        "SELECT COUNT(*) FROM crawl_progress WHERE status = 'done'"
    ).fetchone()[0]
    stats["tasks_total"] = conn.execute("SELECT COUNT(*) FROM crawl_progress").fetchone()[0]

    by_source_rows = conn.execute(
        "SELECT source, COUNT(*) AS cnt FROM raw_shops GROUP BY source"
    ).fetchall()
    stats["by_source"] = {row["source"]: row["cnt"] for row in by_source_rows}

    by_type_rows = conn.execute(
        "SELECT raw_type, COUNT(*) AS cnt FROM raw_shops GROUP BY raw_type ORDER BY cnt DESC"
    ).fetchall()
    stats["by_type"] = {row["raw_type"]: row["cnt"] for row in by_type_rows}
    return stats
