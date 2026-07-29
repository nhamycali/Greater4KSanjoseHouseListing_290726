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

## Filter thông minh theo vị trí

Website có thể kết hợp nhiều nhu cầu:

- Gần khu thương mại, văn hóa và sinh hoạt cộng đồng Việt công khai
- Gần hồ hoặc hồ chứa nước đáng kể
- Gần bãi biển
- Gần cao tốc
- Gần công viên
- Có nhiều nhà hàng trong bán kính gần
- Gần khu mua sắm
- Gần ga Caltrain, BART hoặc VTA

Mỗi loại tiện ích có ba mức bán kính: `Rất gần`, `Gần, hợp lý` và `Mở rộng`.
Khoảng cách là đường chim bay, không phải thời gian lái xe. Người dùng có thể
chọn điều kiện `Đáp ứng tất cả` hoặc `Đáp ứng ít nhất một`.

Filter “gần khu người Việt” đo tới các địa điểm công khai như Little Saigon,
Trung tâm Văn hóa Việt-Mỹ, Vietnamese Heritage Garden và các trung tâm thương
mại Việt. Hệ thống không suy đoán sắc tộc của cư dân trong khu phố.

Tọa độ căn nhà được lấy chủ yếu từ U.S. Census Geocoder. Dữ liệu đường, công
viên, nhà hàng, mua sắm, hồ và giao thông công cộng được tổng hợp từ
OpenStreetMap và cần ghi nguồn `© OpenStreetMap contributors, ODbL`.

File `data/location-insights.json` là snapshot nghiên cứu vị trí. Khi muốn tạo
lại file này từ cache nghiên cứu trong `.m/location/`:

```bash
npm run locations
npm run build
```

## Quy đổi diện tích

```text
1 ft² = 0,092903 m²
1 mẫu Anh = 4.046,8564224 m²
```

Số mét vuông hiển thị được làm tròn để dễ đọc. Người mua cần xác minh số đo
chính thức trước khi giao dịch.
