from __future__ import annotations

import argparse
from pathlib import Path

from reporting import (  # noqa: F401
    ConfigError,
    build_report,
    collect_csv_files,
    iter_records,
    load_config,
    save_report_csv,
    save_report_markdown,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tổng hợp số liệu từ Google Sheets và phân tích hiệu suất nhân sự."
    )
    parser.add_argument(
        "inputs",
        nargs="+",
        help="Danh sách file CSV hoặc thư mục chứa CSV đã export từ Google Sheets.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Đường dẫn tới file cấu hình JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports"),
        help="Thư mục lưu báo cáo (mặc định: reports).",
    )
    parser.add_argument(
        "--recent-days",
        type=int,
        help="Số ngày gần đây để tính hiệu suất hiện tại.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = load_config(args.config)
        if args.recent_days is not None:
            config["recent_days"] = args.recent_days
        files = collect_csv_files(args.inputs)
        records = list(iter_records(files, config))
        report = build_report(records, config["recent_days"])
        output_dir = args.output_dir
        save_report_csv(report, output_dir / "report.csv")
        save_report_markdown(report, output_dir / "report.md")
    except ConfigError as exc:
        print(f"Lỗi: {exc}")
        return 1

    print(f"Đã tạo báo cáo: {output_dir / 'report.csv'} và {output_dir / 'report.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
