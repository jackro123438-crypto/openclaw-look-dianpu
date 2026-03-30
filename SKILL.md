---
name: shop-data-skill
description: Collect Jiangyin shop POI data from AMap and Baidu Map, clean and deduplicate the results, and export them to Excel. Use when the user wants to gather Jiangyin storefront data, refresh a local POI database, or run a repeatable shop-data collection workflow. Before running collection commands, require the user to provide their own API keys through `DIANPU_AMAP_KEY` and `DIANPU_BMAP_AK`.
---

# Shop Data Skill

Use this skill to collect Jiangyin storefront data from AMap and Baidu Map, store the raw results in SQLite, clean the records, and export a shareable Excel file.

## Requirements

- Install dependencies with `pip install -r requirements.txt`
- Set your own keys before collecting data:
  - `DIANPU_AMAP_KEY`
  - `DIANPU_BMAP_AK`
- Never hardcode personal keys into source files or commits

## Key Files

- `scripts/run_shop_data_skill.py`: CLI entrypoint for the full workflow
- `shop_data_skill/config.py`: environment-based configuration
- `shop_data_skill/collectors/`: AMap and Baidu collectors
- `shop_data_skill/cleaner.py`: normalization and deduplication
- `shop_data_skill/exporter.py`: Excel export

## Commands

- `python scripts/run_shop_data_skill.py test amap`
- `python scripts/run_shop_data_skill.py test bmap`
- `python scripts/run_shop_data_skill.py collect amap`
- `python scripts/run_shop_data_skill.py collect bmap`
- `python scripts/run_shop_data_skill.py collect all`
- `python scripts/run_shop_data_skill.py clean`
- `python scripts/run_shop_data_skill.py export`
- `python scripts/run_shop_data_skill.py stats`
- `python scripts/run_shop_data_skill.py all`

## Operating Rules

- For any collection command, verify the corresponding key is present first
- Keep generated databases and Excel files inside `DIANPU_DATA_DIR` or the default `./data`
- Keep the repository itself empty of sampled outputs; this repo should not contain pre-collected data files
- Treat the repository as template code for teammates; do not commit local outputs, keys, or private datasets
