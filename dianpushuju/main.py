from __future__ import annotations

import sys

from .cleaner import run_cleaning
from .collectors.amap_collector import run_amap_collection
from .collectors.bmap_collector import run_bmap_collection
from .config import require_key
from .exporter import run_export
from .models import get_connection, get_stats, init_db


def print_usage() -> None:
    print(
        """
Usage:
  python scripts/run_dianpushuju.py collect amap
  python scripts/run_dianpushuju.py collect bmap
  python scripts/run_dianpushuju.py collect all
  python scripts/run_dianpushuju.py test amap
  python scripts/run_dianpushuju.py test bmap
  python scripts/run_dianpushuju.py clean
  python scripts/run_dianpushuju.py export
  python scripts/run_dianpushuju.py stats
  python scripts/run_dianpushuju.py all
"""
    )


def print_stats() -> None:
    conn = get_connection()
    stats = get_stats(conn)
    conn.close()

    print("=" * 60)
    print("Database stats")
    print("=" * 60)
    print(f"Raw rows: {stats['total_raw']}")
    print(f"Clean rows: {stats['total_clean']}")
    print(f"Rows with phone: {stats['with_phone']}")
    print(f"Phone coverage: {stats['phone_coverage']}")
    print(f"Finished tasks: {stats['tasks_done']}/{stats['tasks_total']}")
    if stats["by_source"]:
        print(f"By source: {stats['by_source']}")
    if stats["by_type"]:
        print(f"Top types: {list(stats['by_type'].items())[:10]}")


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if not args:
        print_usage()
        return 1

    init_db()
    command = args[0].lower()

    if command == "collect":
        if len(args) < 2:
            print("Specify amap, bmap, or all.")
            return 1
        source = args[1].lower()
        if source == "amap":
            require_key("amap")
            run_amap_collection(test_mode=False)
            return 0
        if source == "bmap":
            require_key("bmap")
            run_bmap_collection(test_mode=False)
            return 0
        if source == "all":
            require_key("amap")
            require_key("bmap")
            run_amap_collection(test_mode=False)
            run_bmap_collection(test_mode=False)
            return 0
        print(f"Unknown source: {source}")
        return 1

    if command == "test":
        if len(args) < 2:
            print("Specify amap or bmap.")
            return 1
        source = args[1].lower()
        if source == "amap":
            require_key("amap")
            run_amap_collection(test_mode=True)
            return 0
        if source == "bmap":
            require_key("bmap")
            run_bmap_collection(test_mode=True)
            return 0
        print(f"Unknown source: {source}")
        return 1

    if command == "clean":
        run_cleaning()
        return 0

    if command == "export":
        run_export()
        return 0

    if command == "stats":
        print_stats()
        return 0

    if command == "all":
        require_key("amap")
        require_key("bmap")
        run_amap_collection(test_mode=False)
        run_bmap_collection(test_mode=False)
        run_cleaning()
        run_export()
        print_stats()
        return 0

    print_usage()
    return 1
