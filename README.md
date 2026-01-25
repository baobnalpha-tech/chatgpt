# Báo cáo hiệu suất nhân sự từ Google Sheets

Công cụ này tổng hợp dữ liệu từ các file CSV export từ Google Sheets và tạo báo cáo hiệu suất nhân sự theo từng cơ sở.

## Yêu cầu dữ liệu

Mỗi file CSV cần có các cột sau (có thể đổi tên qua cấu hình):

- `date`: ngày ghi nhận dữ liệu.
- `employee_id`: mã nhân sự (hoặc để trống nếu chỉ dùng tên).
- `employee_name`: tên nhân sự.
- `branch`: cơ sở.
- `metric`: tên chỉ số (ví dụ: doanh thu, số khách).
- `value`: giá trị của chỉ số.

## Cách sử dụng

```bash
python app/main.py data/ --config config.example.json
```

Sau khi chạy, báo cáo được lưu trong thư mục `reports/`:

- `report.csv`: báo cáo dạng CSV.
- `report.md`: báo cáo dạng Markdown.

## Cấu hình

Sao chép file `config.example.json` và chỉnh sửa để khớp với tên cột trong Google Sheets.

```json
{
  "columns": {
    "date": "Ngày",
    "employee_id": "Mã NV",
    "employee_name": "Nhân sự",
    "branch": "Cơ sở",
    "metric": "Chỉ số",
    "value": "Giá trị"
  },
  "date_formats": ["%d/%m/%Y"],
  "recent_days": 14
}
```

## Gợi ý mở rộng

- Nếu cần kết nối trực tiếp Google Sheets, bạn có thể thêm bước export CSV tự động hoặc tích hợp Google Sheets API.
