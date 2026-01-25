from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable, Iterator

DEFAULT_CONFIG = {
    "columns": {
        "date": "date",
        "employee_id": "employee_id",
        "employee_name": "employee_name",
        "branch": "branch",
        "metric": "metric",
        "value": "value",
    },
    "date_formats": ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"],
    "recent_days": 30,
}


@dataclass(frozen=True)
class Record:
    record_date: date
    employee_id: str
    employee_name: str
    branch: str
    metric: str
    value: float


@dataclass(frozen=True)
class ReportRow:
    employee_id: str
    employee_name: str
    branch: str
    metric: str
    total_value: float
    average_daily: float
    records_count: int
    recent_value: float
    recent_records: int


@dataclass(frozen=True)
class Report:
    rows: list[ReportRow]
    generated_at: datetime
    recent_cutoff: date


class ConfigError(ValueError):
    pass


def load_config(path: Path | None) -> dict:
    if path is None:
        return DEFAULT_CONFIG.copy()

    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Không tìm thấy file cấu hình: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"File cấu hình JSON không hợp lệ: {path}") from exc

    config = DEFAULT_CONFIG.copy()
    config.update(raw)
    if "columns" in raw:
        merged_columns = DEFAULT_CONFIG["columns"].copy()
        merged_columns.update(raw["columns"])
        config["columns"] = merged_columns

    return config


def parse_date(value: str, formats: Iterable[str]) -> date:
    for fmt in formats:
        try:
            return datetime.strptime(value.strip(), fmt).date()
        except ValueError:
            continue
    raise ConfigError(f"Ngày không đúng định dạng: {value}")


def normalize_field(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def iter_records(paths: Iterable[Path], config: dict) -> Iterator[Record]:
    columns = config["columns"]
    date_formats = config["date_formats"]

    for path in paths:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                try:
                    record_date = parse_date(row.get(columns["date"], ""), date_formats)
                except ConfigError as exc:
                    raise ConfigError(f"{exc} trong file {path}") from exc

                employee_id = normalize_field(row.get(columns["employee_id"]))
                employee_name = normalize_field(row.get(columns["employee_name"]))
                branch = normalize_field(row.get(columns["branch"]))
                metric = normalize_field(row.get(columns["metric"])) or "default"
                value_raw = normalize_field(row.get(columns["value"]))

                if not employee_id and not employee_name:
                    continue

                try:
                    value = float(value_raw)
                except ValueError:
                    raise ConfigError(
                        f"Giá trị không hợp lệ '{value_raw}' trong file {path}"
                    ) from None

                yield Record(
                    record_date=record_date,
                    employee_id=employee_id,
                    employee_name=employee_name,
                    branch=branch,
                    metric=metric,
                    value=value,
                )


def build_report(records: Iterable[Record], recent_days: int) -> Report:
    now = datetime.now()
    cutoff = (now.date() - timedelta(days=recent_days))

    aggregates: dict[tuple[str, str, str, str], list[Record]] = {}
    for record in records:
        key = (record.employee_id, record.employee_name, record.branch, record.metric)
        aggregates.setdefault(key, []).append(record)

    rows: list[ReportRow] = []
    for (employee_id, employee_name, branch, metric), items in aggregates.items():
        total_value = sum(item.value for item in items)
        records_count = len(items)
        date_span = (max(item.record_date for item in items) - min(item.record_date for item in items)).days
        days = max(date_span + 1, 1)
        average_daily = total_value / days
        recent_items = [item for item in items if item.record_date >= cutoff]
        recent_value = sum(item.value for item in recent_items)
        recent_records = len(recent_items)

        rows.append(
            ReportRow(
                employee_id=employee_id,
                employee_name=employee_name,
                branch=branch,
                metric=metric,
                total_value=total_value,
                average_daily=average_daily,
                records_count=records_count,
                recent_value=recent_value,
                recent_records=recent_records,
            )
        )

    rows.sort(key=lambda item: (item.branch, item.employee_name, item.metric))
    return Report(rows=rows, generated_at=now, recent_cutoff=cutoff)


def save_report_csv(report: Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "employee_id",
                "employee_name",
                "branch",
                "metric",
                "total_value",
                "average_daily",
                "records_count",
                "recent_value",
                "recent_records",
            ]
        )
        for row in report.rows:
            writer.writerow(
                [
                    row.employee_id,
                    row.employee_name,
                    row.branch,
                    row.metric,
                    f"{row.total_value:.2f}",
                    f"{row.average_daily:.2f}",
                    row.records_count,
                    f"{row.recent_value:.2f}",
                    row.recent_records,
                ]
            )


def save_report_markdown(report: Report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        handle.write("# Báo cáo hiệu suất nhân sự\n\n")
        handle.write(f"- Thời điểm tạo: {report.generated_at:%Y-%m-%d %H:%M}\n")
        handle.write(f"- Giai đoạn gần đây: từ {report.recent_cutoff:%Y-%m-%d}\n\n")
        handle.write(
            "| Mã nhân sự | Tên nhân sự | Cơ sở | Chỉ số | Tổng | Trung bình/ngày | Số bản ghi | Tổng gần đây | Bản ghi gần đây |\n"
        )
        handle.write(
            "| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |\n"
        )
        for row in report.rows:
            handle.write(
                "| {employee_id} | {employee_name} | {branch} | {metric} | {total:.2f} | {avg:.2f} | {count} | {recent:.2f} | {recent_count} |\n".format(
                    employee_id=row.employee_id or "-",
                    employee_name=row.employee_name or "-",
                    branch=row.branch or "-",
                    metric=row.metric,
                    total=row.total_value,
                    avg=row.average_daily,
                    count=row.records_count,
                    recent=row.recent_value,
                    recent_count=row.recent_records,
                )
            )


def collect_csv_files(paths: Iterable[str]) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("*.csv")))
        else:
            files.append(path)
    if not files:
        raise ConfigError("Không tìm thấy file CSV nào để xử lý.")
    return files
