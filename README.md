# Nhà Mỹ Cali — 48 căn nhà tại Silicon Valley

Website tĩnh tái dựng danh sách MLS gồm 48 căn nhà, Việt hóa nội dung và kèm
quy đổi diện tích từ feet vuông sang mét vuông.

## Xem website

Mở trực tiếp `index.html` trong trình duyệt. Website không cần máy chủ.

Nếu muốn chạy qua HTTP:

```bash
npm run serve
```

Sau đó mở `http://localhost:8080`.

## Tái tạo website

```bash
# Chỉ cần chạy lại khi URL nguồn còn hiệu lực và muốn cập nhật dữ liệu:
npm run scrape
npm run translate
npm run images

# Sinh lại HTML và dữ liệu client:
npm run build

# Kiểm thử desktop, mobile và toàn bộ 48 trang chi tiết:
npm test
```

`link.txt` chứa URL portal riêng tư và được Git bỏ qua. Dữ liệu đưa lên website
không chứa email, URL portal, ViewState hoặc token phiên.

## Quy đổi diện tích

```text
1 ft² = 0,092903 m²
1 mẫu Anh = 4.046,8564224 m²
```

Số mét vuông hiển thị được làm tròn để dễ đọc. Người mua cần xác minh số đo
chính thức trước khi giao dịch.
