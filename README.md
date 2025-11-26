# Tool Crawl Dữ Liệu Shopee

Tool để crawl dữ liệu sản phẩm từ Shopee theo nhiều tiêu chí khác nhau.

## Tính năng

- ✅ Crawl theo keyword (từ khóa)
- ✅ Crawl theo category (ngành hàng)
- ✅ Crawl theo shop (gian hàng)
- ✅ Sắp xếp theo % hoa hồng, giá tiền, lượt bán, rating
- ✅ Xuất dữ liệu ra JSON hoặc Excel

## Cài đặt

1. Cài đặt Python 3.7 trở lên

2. Cài đặt các thư viện cần thiết:
```bash
pip install -r requirements.txt
```

## Sử dụng

Chạy chương trình:
```bash
python main.py
```

Sau đó làm theo hướng dẫn trên màn hình:
1. Chọn phương thức crawl (keyword/category/shop)
2. Nhập thông tin cần thiết
3. Chọn cách sắp xếp
4. Chọn định dạng xuất file

## Ví dụ

### Crawl theo keyword:
- Keyword: "điện thoại"
- Số lượng: 100 sản phẩm

### Crawl theo category:
- Category ID: 11036032 (Ví dụ: Điện thoại & Phụ kiện)
- Số lượng: 50 sản phẩm

### Crawl theo shop:
- Shop ID: "12345678"
- Số lượng: 200 sản phẩm

## Lưu ý

- API của Shopee có thể thay đổi, cần cập nhật code nếu có lỗi
- Có delay 1 giây giữa các request để tránh bị block
- Phần trăm hoa hồng có thể cần implement thêm API riêng


