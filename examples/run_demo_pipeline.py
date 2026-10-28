#!/usr/bin/env python3
"""
End-to-End Runnable Demo of resilient-web-scraper-pipeline.
Parses multi-region public directory fixtures (with full-width numbers & mixed extensions),
computes incremental diff states (NEW / UPDATED / UNCHANGED), and exports:
- examples/output/demo_directory_report.csv (UTF-8-SIG BOM)
- examples/output/demo_directory_report.xlsx (Formatted Excel with diff highlighting)
"""
from __future__ import annotations
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from scraper_pipeline import (
    DiffSnapshotStore,
    DirectoryContactRecord,
    export_diff_to_csv,
    export_diff_to_excel,
    format_alert_message,
)


def main() -> None:
    out_dir = ROOT / "examples" / "output"
    snapshot_file = out_dir / "snapshot_state.json"
    if snapshot_file.exists():
        snapshot_file.unlink()

    store = DiffSnapshotStore(snapshot_path=snapshot_file)

    # Baseline Snapshot (Day 1)
    day1_records = [
        DirectoryContactRecord.from_raw(
            record_id="GOV-HCC-001",
            region="新竹市",
            organization="新竹市政府 民政處",
            department_or_duty="自治行政科、戶政科（市政公共服務）",
            phone="（０３）５２１－６１２１#302",
            fax="03-521-9999",
            address="新竹市中正路120號",
            email_or_url="https://dep-civil.hccg.gov.tw",
            source_url="https://www.hccg.gov.tw/organizationDetail",
            scraped_at="2026-10-27 09:00:00",
        ),
        DirectoryContactRecord.from_raw(
            record_id="GOV-MLC-002",
            region="苗栗縣",
            organization="苗栗縣政府 工商發展處",
            department_or_duty="商業科、公用事業科（企業招商與工商登記）",
            phone="037-322150 分機 5110",
            fax="037-331999",
            address="苗栗縣苗栗市縣府路100號",
            email_or_url="https://www.miaoli.gov.tw",
            source_url="https://www.miaoli.gov.tw/News.aspx",
            scraped_at="2026-10-27 09:00:00",
        ),
    ]
    store.compare_and_update(day1_records, persist=True)

    # Day 2 Run: 1 UNCHANGED, 1 UPDATED (extension changed), 1 NEW (Taichung City)
    day2_records = [
        day1_records[0],
        DirectoryContactRecord.from_raw(
            record_id="GOV-MLC-002",
            region="苗栗縣",
            organization="苗栗縣政府 工商發展處",
            department_or_duty="商業科、公用事業科（企業招商與綠能輔導）",
            phone="037-322150 分機 5128",
            fax="037-331999",
            address="苗栗縣苗栗市縣府路100號",
            email_or_url="https://www.miaoli.gov.tw",
            source_url="https://www.miaoli.gov.tw/News.aspx",
            scraped_at="2026-10-28 09:00:00",
        ),
        DirectoryContactRecord.from_raw(
            record_id="GOV-TXG-003",
            region="臺中市",
            organization="臺中市政府 數位發展局",
            department_or_duty="數位服務科、創新推進科（智慧城市與市民平台）",
            phone="（０４）２２２８－９１１１ 轉 22100",
            fax="04-2259-8658",
            address="407610 臺中市西屯區臺灣大道三段99號",
            email_or_url="https://www.digital.taichung.gov.tw",
            source_url="https://www.taichung.gov.tw/10179/12034",
            scraped_at="2026-10-28 09:00:00",
        ),
    ]

    diff_results = store.compare_and_update(day2_records, persist=True)
    csv_path = export_diff_to_csv(diff_results, out_dir / "demo_directory_report.csv")
    xlsx_path = export_diff_to_excel(diff_results, out_dir / "demo_directory_report.xlsx")

    print(format_alert_message("Gov & Enterprise Directory Tracker", diff_results))
    print(f"Exported CSV:  {csv_path} ({csv_path.stat().st_size} bytes)")
    print(f"Exported XLSX: {xlsx_path} ({xlsx_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
