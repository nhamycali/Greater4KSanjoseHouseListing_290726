# Kỹ năng: Đọc, nghiên cứu vị trí, Việt hóa và dựng website danh sách nhà từ MLS

> Phiên bản nâng cấp ngày 29/07/2026. Bản này bổ sung quy trình đọc hồ sơ từng
> căn nhà, nghiên cứu tiện ích theo tọa độ, tạo dữ liệu có nguồn gốc rõ ràng và
> biến dữ liệu đó thành bộ lọc nhu cầu trên website.

## 1. Mục đích

Kỹ năng này hướng dẫn AI Agent biến một liên kết danh sách bất động sản do người dùng cung cấp thành website tĩnh hoàn chỉnh bằng tiếng Việt, bao gồm:

- Trang danh sách tất cả bất động sản.
- Một trang chi tiết riêng cho từng căn nhà.
- Toàn bộ mô tả, nhãn và thông số được Việt hóa.
- Diện tích gốc bằng feet vuông và số quy đổi sang mét vuông.
- Thư viện ảnh được lưu cục bộ.
- Giao diện theo đúng nhận diện thương hiệu.
- Bộ lọc, tìm kiếm, sắp xếp và lightbox xem ảnh.
- Hồ sơ nghiên cứu vị trí cho từng căn, có ngày snapshot và phương pháp tính.
- Bộ lọc theo nhu cầu như gần công viên, mua sắm, nhà hàng, giao thông công
  cộng, cao tốc, hồ, biển hoặc các điểm sinh hoạt cộng đồng công khai.
- Kiểm thử tự động trên desktop, mobile và toàn bộ trang chi tiết.

Đây không phải là tác vụ “dịch HTML”. Agent phải thu thập dữ liệu có cấu trúc,
đọc và phân loại thông tin của từng căn, kiểm tra tính đầy đủ, dịch theo ngữ
cảnh bất động sản, nghiên cứu vị trí bằng dữ liệu địa lý có thể kiểm chứng, lưu
ảnh ổn định, rồi sinh lại website từ các nguồn dữ liệu có thể tái sử dụng.

Agent phải giữ riêng ba lớp bằng chứng:

1. **Dữ kiện MLS:** giá, diện tích, phòng, năm xây dựng và nội dung do bên niêm
   yết cung cấp.
2. **Bằng chứng nghiên cứu độc lập:** tọa độ, địa điểm công khai, khoảng cách và
   mật độ tiện ích.
3. **Suy luận phục vụ giao diện:** cờ đạt ngưỡng, thứ tự phù hợp và câu tóm tắt.

Không biến lời quảng cáo trong MLS thành dữ kiện độc lập. Không biến khoảng
cách đường chim bay thành thời gian lái xe. Không suy đoán đặc điểm nhân khẩu
học của cư dân.

---

## 2. Khi nào dùng kỹ năng này

Dùng khi người dùng cung cấp:

- Một URL portal/listing chứa nhiều căn nhà.
- Logo, tên thương hiệu, slogan hoặc màu nhận diện.
- Yêu cầu tái dựng cả trang danh sách và trang con.
- Yêu cầu Việt hóa thông tin bất động sản.
- Yêu cầu quy đổi đơn vị Mỹ sang hệ mét.

Không dùng để:

- Vượt đăng nhập, paywall, CAPTCHA hoặc kiểm soát truy cập.
- Thu thập dữ liệu mà người dùng không có quyền truy cập.
- Công bố thông tin cá nhân, URL portal riêng tư hoặc token phiên.
- Sao chép nguyên website bên thứ ba khi không được phép.

Luôn tôn trọng quyền truy cập, điều khoản nguồn dữ liệu, bản quyền ảnh và yêu cầu riêng tư của người dùng.

---

## 3. Hợp đồng chức năng

### 3.1. Người dùng cung cấp gì

Bắt buộc:

- URL nguồn, ưu tiên lưu trong `link.txt`.
- Số lượng bất động sản dự kiến nếu người dùng biết.

Tùy chọn:

- Logo.
- Tên thương hiệu.
- Slogan.
- Màu thương hiệu.
- Ngôn ngữ đích.
- Yêu cầu bố cục hoặc tính năng.

### 3.2. Hệ thống trả về gì

- `index.html`: trang danh sách.
- `listings/*.html`: trang chi tiết riêng.
- `data/listings-source.json`: dữ liệu chuẩn hóa còn URL ảnh nguồn.
- `data/location-insights.json`: snapshot nghiên cứu vị trí, phương pháp, nguồn,
  khoảng cách, số lượng tiện ích và cờ filter của từng MLS.
- `data/listings.json`: dữ liệu cuối dành cho website.
- `assets/js/listings-data.js`: dữ liệu JavaScript để website mở trực tiếp bằng `file://`.
- `assets/properties/<mls>/NNN.jpg`: ảnh lưu cục bộ.
- `assets/css/styles.css`: giao diện.
- `assets/js/site.js`: tìm kiếm, lọc, gallery và tương tác.
- Script build, downloader và kiểm thử.
- Trace đủ để tái chạy và xác minh.

### 3.3. Tác vụ có thể thất bại thế nào

- URL hết hạn hoặc yêu cầu đăng nhập.
- Portal dùng JavaScript/browser thay vì HTML có thể POST trực tiếp.
- ASP.NET ViewState thay đổi hoặc token phiên hết hạn.
- Số record hiển thị không khớp số marker trong HTML.
- Trang chi tiết có nhiều template khác nhau.
- Mô tả bị parser cắt nhầm.
- Hàng dữ liệu dạng label/value bị lệch cột.
- Địa chỉ không geocode được hoặc chỉ khớp ở mức đường/khoảng địa chỉ.
- Dữ liệu POI thiếu tên, trùng điểm, sai loại hoặc không bao phủ đủ vùng.
- Overpass/API địa lý timeout, giới hạn tải hoặc trả snapshot không đầy đủ.
- Một tiện ích dạng đường bị đo sai nếu dùng tâm hình học thay vì đoạn gần nhất.
- Ngưỡng “gần” được chọn tùy tiện hoặc bị chỉnh để tạo ra số kết quả mong muốn.
- Giao diện gọi khoảng cách đường chim bay là thời gian lái xe.
- URL ảnh hết hạn trước khi tải.
- Dịch máy làm sai thuật ngữ hoặc tự đổi sai đơn vị.
- Font không có đầy đủ glyph tiếng Việt.
- Website đúng ở desktop nhưng tràn ngang ở mobile.

Khi một bước thất bại, giữ lại HTML/JSON thô và trace. Đọc bằng chứng trước khi sửa parser; không đoán.

### 3.4. Tác vụ gây thay đổi gì

- Tạo hoặc cập nhật dữ liệu JSON.
- Tạo cache geocode, POI, đường và trace nghiên cứu trong thư mục làm việc riêng.
- Tạo hoặc cập nhật snapshot `data/location-insights.json`.
- Tải ảnh vào repo.
- Sinh lại HTML.
- Cập nhật CSS/JavaScript.
- Tạo test và ảnh chụp kiểm chứng.
- Có thể tạo commit và push khi người dùng yêu cầu.

### 3.5. Quyền cần thiết

- Đọc URL và tệp dự án.
- Truy cập mạng đến portal và máy chủ ảnh.
- Truy cập các dịch vụ geocode, bản đồ và nguồn công khai được phép sử dụng.
- Ghi tệp trong repo.
- Chạy Python, Node.js và trình duyệt headless.
- Quyền Git push chỉ khi người dùng yêu cầu.

Không cần và không nên yêu cầu quyền root nếu có thể dùng thư viện cục bộ.

---

## 4. Nguyên tắc bắt buộc

1. **Dữ liệu trước giao diện.** Chốt schema và tính đầy đủ trước khi viết UI.
2. **Không tin một dấu hiệu duy nhất.** Record count, marker HTML và danh sách index có thể lệch nhau.
3. **Không đưa bản dịch máy thô lên website.** Luôn có glossary và hậu kiểm.
4. **Bảo vệ số đo trước khi dịch.** Không cho dịch vụ dịch tự biến `ft²` thành `m²`.
5. **Lưu ảnh cục bộ.** URL gallery thường có token và có thể hết hạn.
6. **Build có thể tái chạy.** HTML đầu ra phải được sinh từ JSON nguồn ổn định.
7. **Kiểm thử toàn bộ trang con.** Không chỉ mở căn đầu tiên.
8. **Không làm lộ URL riêng tư hoặc email.** URL portal có thể chứa dữ liệu nhận dạng được mã hóa.
9. **Font phải hỗ trợ tiếng Việt cục bộ.** Tránh trình duyệt trộn glyph từ nhiều font.
10. **Commit có chọn lọc.** Không commit session log, token, URL nguồn riêng hoặc artifact tạm.
11. **Tách lời quảng cáo khỏi bằng chứng độc lập.** MLS “gần công viên” chỉ là
    một tín hiệu cần kiểm tra, không phải kết luận.
12. **Research phải có provenance.** Mỗi snapshot phải ghi ngày, nguồn, đơn vị,
    kiểu khoảng cách, ngưỡng và ngoại lệ tọa độ.
13. **Đo đúng hình học.** POI dùng khoảng cách điểm; cao tốc/đường dùng khoảng
    cách tới đoạn gần nhất, không dùng tâm toàn tuyến.
14. **Ngưỡng phải có nghĩa với người dùng.** Chốt `strict`, `balanced`, `broad`
    trước khi nhìn số căn đạt; không tối ưu ngưỡng để tạo kết quả đẹp.
15. **Không suy đoán dữ liệu nhạy cảm.** “Gần khu người Việt” chỉ được đo tới
    địa điểm thương mại, văn hóa hoặc sinh hoạt cộng đồng Việt công khai.
16. **Filter phải giải thích được.** Người dùng phải thấy lý do căn nhà khớp,
    khoảng cách hoặc mật độ dùng để quyết định, và giới hạn của phương pháp.

---

## 5. Kiến trúc dữ liệu đề xuất

### 5.1. Dữ liệu nguồn chuẩn hóa

Mỗi listing nên có tối thiểu:

```json
{
  "index": 0,
  "key": "record-key",
  "address": "123 Example Street",
  "city": "San Jose, California 95100",
  "mls": "ML12345678",
  "price": "$2,500,000",
  "status": "Active",
  "description": "Original English remarks...",
  "description_vi": "Mô tả tiếng Việt đã hiệu đính...",
  "bedrooms": "4",
  "bathrooms": "3",
  "full_baths": "3",
  "half_baths": "0",
  "sqft": "2,500",
  "lot": "8,000 SqFt",
  "year": "2001",
  "building_type": "Detached",
  "sections": {
    "General Description": [["Beds Total", "4"]],
    "Interior": [["Cooling", "Central AC"]],
    "Exterior": [["Garage Spaces", "2"]],
    "Additional Information": [["Listed By", "Agent Name"]]
  },
  "images": ["<remote-image-url>"],
  "sections_translated": {}
}
```

### 5.2. Dữ liệu đầu ra cho website

Thêm các trường đã tính:

- `slug`
- `detail_url`
- `status_vi`
- `sqft_m2`
- `lot_m2`
- `sqft_display`
- `lot_display`
- `price_number`
- `sqft_number`
- `beds_number`
- `baths_number`
- `sections_vi`
- `location`

Trong đó `location` tối thiểu gồm:

- `amenities`
- `matches`
- `summary_vi`
- `mls_evidence_categories`

Loại bỏ khỏi dữ liệu client nếu không cần:

- URL portal nguồn.
- Email.
- ViewState.
- Record key nội bộ.
- Nội dung tiếng Anh thô.
- Trace parser.
- Tọa độ chính xác nếu sản phẩm không cần hiển thị bản đồ và việc công bố làm
  tăng rủi ro riêng tư.

---

## 6. Quy trình hoàn chỉnh

## Pha A — Khảo sát nguồn và môi trường

### Bước A1. Kiểm kê đầu vào

Kiểm tra:

```bash
cat link.txt
file logo.png
find . -maxdepth 3 -type f -printf '%p\t%s bytes\n' | sort
git status --short --branch
```

Không in URL nguồn vào log công khai nếu URL chứa query riêng tư. Khi cần debug, có thể chỉ in:

- HTTP status.
- URL host.
- Kích thước response.
- Form action đã loại query nhạy cảm.

### Bước A2. Kiểm tra công cụ

Tối thiểu:

- Python 3.
- `requests`.
- Node.js/npm.
- Playwright hoặc Chromium headless.

Ưu tiên thư viện chuẩn Python như `html.parser` nếu môi trường không có BeautifulSoup/lxml. Không dừng chỉ vì thiếu parser phụ.

### Bước A3. Lấy trang mẹ

```python
url = Path("link.txt").read_text().strip()
session = requests.Session()
session.headers["User-Agent"] = "Mozilla/5.0"
response = session.get(url, timeout=45)
response.raise_for_status()
```

Lưu bản HTML thô làm artifact debug, nhưng không commit nếu chứa URL/token riêng:

```text
.m/source-parent.html
```

Xác nhận:

- HTTP 200.
- Có `<form>`.
- Có hidden fields kiểu ASP.NET.
- Có các lời gọi mở record chi tiết.
- Số listing nhìn thấy khớp kỳ vọng của người dùng.

---

## Pha B — Reverse-engineer portal ASP.NET/WebForms

Nhiều portal Matrix dùng một trang ASP.NET duy nhất. Nhấp vào listing không đổi URL theo cách thông thường mà POST lại form với:

```text
__EVENTTARGET
__EVENTARGUMENT
__VIEWSTATE
__EVENTVALIDATION
```

### Bước B1. Parse form và hidden fields

Tạo parser lấy:

- `form action`
- Mọi `<input type="hidden" name="...">`

Pseudocode:

```python
class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.action = ""
        self.hidden = {}

    def handle_starttag(self, tag, attrs):
        attr = dict(attrs)
        if tag == "form" and not self.action:
            self.action = attr.get("action", "")
        if (
            tag == "input"
            and attr.get("type", "").lower() == "hidden"
            and attr.get("name")
        ):
            self.hidden[attr["name"]] = attr.get("value", "")
```

### Bước B2. Phát hiện pattern mở trang chi tiết

Ở portal đã xử lý, thao tác chi tiết dùng dạng:

```python
data["__EVENTTARGET"] = "_ctl0$m_DisplayCore"
data["__EVENTARGUMENT"] = f"Redisplay|<view-id>,,{index}"
```

`<view-id>` là tham số riêng của template. Không nên mặc định nó luôn giống nhau. Hãy lấy từ:

- `onclick`
- `href`
- JavaScript trong trang mẹ
- Các chuỗi `Redisplay|...,,N`

### Bước B3. Không phụ thuộc hoàn toàn vào marker record

Một lỗi thực tế đã gặp:

- Portal báo 27 listing.
- HTML chỉ có 26 comment dạng `<!--@Record:...@-->`.
- Nếu dùng comment làm nguồn sự thật, một căn sẽ bị bỏ sót.

Quy tắc:

1. Lấy số lượng dự kiến từ UI hoặc yêu cầu người dùng.
2. Tìm toàn bộ index `Redisplay`.
3. Nếu marker thiếu, thử tuần tự `0..count-1`.
4. Sau mỗi POST, lấy record key/MLS thật từ chính trang chi tiết.
5. Xác nhận địa chỉ và MLS không trùng.

Không tạo danh sách chỉ từ một regex marker.

### Bước B4. Giữ cùng session

GET trang mẹ và mọi POST trang con phải dùng cùng `requests.Session()`. Hidden fields phải lấy từ response hợp lệ của phiên hiện tại.

Nếu POST bắt đầu trả trang mẹ hoặc lỗi validation:

- GET lại trang mẹ.
- Refresh hidden fields.
- Không tái dùng ViewState cũ qua phiên khác.

---

## Pha C — Parse trang chi tiết

### Bước C1. Tách visible text

Bỏ qua:

- `<script>`
- `<style>`

Chuẩn hóa whitespace và `html.unescape`.

Các mốc hữu ích trong template đã xử lý:

```text
See Previous Results
General Description
Interior
Exterior
Additional Information
Notes for you and your agent
```

Luồng parse:

1. Nội dung bắt đầu sau `See Previous Results`.
2. Kết thúc trước `Notes for you and your agent`.
3. Khối trước `General Description` chứa:
   - địa chỉ
   - thành phố
   - MLS
   - giá
   - trạng thái
   - mô tả
4. Các section sau đó thường là cặp label/value.

### Bước C2. Không lấy mô tả bằng vị trí cứng

Một số template chèn:

- nickname của căn nhà
- badge
- nhãn mở bán
- trạng thái phụ

Do đó `pre[-1]` có thể không phải mô tả đầy đủ.

Chiến lược bền hơn:

- Xác định vùng giữa status/giá và `General Description`.
- Chọn đoạn văn dài nhất hợp lý.
- So sánh độ dài mô tả giữa các listing.
- In và kiểm tra các outlier ngắn bất thường.

Ví dụ quality check:

```python
for item in listings:
    if len(item["description"]) < 300:
        inspect_manually(item["index"])
```

### Bước C3. Parse section label/value

Với mỗi section:

```python
pairs = [[values[i], values[i + 1]] for i in range(0, len(values) - 1, 2)]
```

Nhưng trước khi ghép:

- Kiểm tra số phần tử chẵn/lẻ.
- In section lẻ để phân tích.
- Không âm thầm bỏ phần tử cuối.

### Bước C4. Sửa dữ liệu trường học bị flatten

Portal có thể xuất dữ liệu trường học thành chuỗi cặp lệch vai trò, ví dụ:

- Tên trường nằm ở label.
- Học khu bắt đầu bằng `/`.
- Giá trị chỉ là `Middle School` hoặc `High`.

Cần state machine để chuẩn hóa thành:

```json
[
  {"label": "Trường tiểu học", "value": "Tên trường · Học khu ..."},
  {"label": "Trường trung học cơ sở", "value": "Tên trường · Học khu ..."},
  {"label": "Trường trung học", "value": "Tên trường · Học khu ..."}
]
```

Không dịch tên riêng của trường hoặc học khu.

### Bước C5. Lấy toàn bộ ảnh gallery

Ảnh `<img>` nhìn thấy ban đầu thường chỉ là:

- logo portal
- ảnh đại diện
- một vài ảnh gallery

Toàn bộ gallery có thể nằm trong JavaScript map, ví dụ khóa tương tự:

```text
'<index>_3':'<media-url>'
```

Quy trình:

1. Regex map URL ảnh medium/full trong script.
2. `html.unescape`.
3. Giữ thứ tự.
4. Loại trùng mà không đổi thứ tự.
5. Fallback sang `<img class="...ivrImg..." src="...">`.
6. Chỉ nhận URL media phù hợp.

Kích thước medium khoảng 640 px thường đủ cho website tĩnh nhẹ. Nếu người dùng yêu cầu ảnh lớn, kiểm tra `Size` variant của media server.

### Bước C6. Log từng record

Mỗi listing in một dòng:

```text
03/27 ML12345678 imgs=42 fields=38 123 Example Street
```

Cuối run in:

```json
{"listings": 27, "errors": 0, "images": 1405}
```

Nếu `errors > 0`, chưa được chuyển sang dịch hoặc UI.

---

## Pha D — Chuẩn hóa và kiểm tra dữ liệu thô

### Bước D1. Giữ nhiều lớp dữ liệu

Nên có:

1. `raw`: response đã parse gần nguồn nhất.
2. `clean`: đã sửa parser edge cases.
3. `translated`: có bản dịch nháp.
4. `final source`: đã hiệu đính và khử PII.
5. `site output`: dữ liệu nhẹ dùng trong browser.

Không ghi đè dữ liệu thô ngay từ đầu.

### Bước D2. Kiểm tra bắt buộc

- Đúng số listing.
- MLS duy nhất.
- Địa chỉ duy nhất.
- Mỗi listing có mô tả.
- Mỗi listing có ít nhất một ảnh.
- Các trường diện tích parse được.
- Tổng ảnh hợp lý.
- Không có section lẻ không giải thích được.

### Bước D3. Khử PII

Trước khi đưa dữ liệu vào repo:

- Thay URL nguồn bằng metadata chung.
- Xóa email.
- Xóa query token.
- Xóa portal ID riêng.
- Xóa ViewState/EventValidation.

Scan:

```python
email_pattern = r"[\w.+-]+@[\w.-]+"
```

Không ghi nguyên `link.txt` vào skill, README hoặc commit nếu URL có dữ liệu nhận dạng.

---

## Pha E — Đọc hồ sơ căn nhà và nghiên cứu vị trí

Pha này biến địa chỉ và mô tả MLS thành dữ liệu vị trí có thể kiểm tra, sau đó
biến dữ liệu đó thành filter phục vụ nhu cầu thật. Không bắt đầu bằng UI.

### E1. Hợp đồng của chức năng nghiên cứu vị trí

#### Người dùng hoặc pipeline cung cấp gì

- Danh sách đã chuẩn hóa, tối thiểu có `index`, `mls`, `address`, `city`,
  `description` và `description_vi`.
- Vùng nghiên cứu.
- Các nhu cầu cần lọc.
- Chính sách nguồn dữ liệu và mức chính xác được phép công bố.

#### Hệ thống trả về gì

- Một geocode cho mỗi listing, kèm mức chính xác và nguồn.
- POI/đường đã chuẩn hóa và khử trùng.
- Tiện ích gần nhất hoặc mật độ tiện ích cho từng loại.
- Cờ `strict`, `balanced`, `broad`.
- Tóm tắt tiếng Việt ngắn, có thể giải thích.
- Ngày snapshot, phương pháp, đơn vị, ngưỡng và nguồn dữ liệu.

#### Có thể thất bại thế nào

- Thiếu geocode hoặc geocode nhầm thành phố.
- API timeout, rate limit hoặc response không đủ vùng.
- Một loại POI không có record hợp lệ.
- Tất cả điểm đều không tên nên không thể giải thích cho người dùng.
- Tọa độ override không có nguồn hoặc chỉ là phỏng đoán.
- Số listing trong snapshot không khớp dữ liệu nguồn.

Nếu có lỗi trên, lệnh phải exit khác 0 hoặc đánh dấu record là chưa đủ bằng
chứng. Không âm thầm gán khoảng cách `0`, không mặc định mọi cờ là `false`, và
không xây filter từ dữ liệu thiếu.

#### Tác dụng phụ

- Tạo cache thô trong `.m/location/`.
- Tạo snapshot công khai `data/location-insights.json`.
- Có thể cập nhật dữ liệu client và HTML khi chạy build.

#### Quyền cần thiết

- Đọc dữ liệu listing.
- Gọi dịch vụ geocode/bản đồ công khai theo điều khoản sử dụng.
- Ghi cache và snapshot trong repo.
- Không cần vị trí thiết bị, hồ sơ cư dân hoặc dữ liệu nhân khẩu học cá nhân.

### E2. Đọc hồ sơ từng căn trước khi research

Tạo một bảng kiểm nội bộ cho mỗi MLS:

```json
{
  "mls": "ML12345678",
  "identity": {
    "address": "123 Example Street",
    "city": "San Jose, California 95100"
  },
  "property_facts": {
    "price": 3500000,
    "beds": 5,
    "baths": 4.5,
    "sqft": 3200,
    "lot_sqft": 8000,
    "year": 2005,
    "building_type": "Detached"
  },
  "claimed_location_signals": [
    "park",
    "restaurants",
    "shopping",
    "highway",
    "transit"
  ]
}
```

Đọc theo thứ tự:

1. Xác nhận danh tính căn bằng địa chỉ + thành phố + MLS.
2. Parse số thành kiểu số; giữ chuỗi gốc để đối chiếu.
3. Đọc mô tả và section để hiểu đặc điểm nhà, nhưng không để câu quảng cáo sửa
   dữ kiện định lượng.
4. Tìm tín hiệu vị trí bằng regex/glossary song ngữ.
5. Lưu tín hiệu vào `claimed_location_signals` hoặc
   `mls_evidence_categories`.
6. Research độc lập từng tín hiệu bằng dữ liệu địa lý.

Ví dụ rule:

```python
LOCATION_SIGNAL_RULES = [
    ("park", r"\bpark\b|\btrail\b|công viên|đường mòn"),
    ("restaurants", r"\bdining\b|\brestaurants?\b|ăn uống|nhà hàng"),
    ("shopping", r"\bshopping\b|\bshops?\b|\bmall\b|mua sắm"),
    ("highway", r"\bfreeways?\b|\bhighways?\b|cao tốc|xa lộ"),
    ("lake", r"\blake\b|\breservoir\b|hồ nước|hồ chứa"),
    ("transit", r"\bBART\b|\bCaltrain\b|\blight rail\b|ga đường sắt"),
]
```

Các rule này chỉ tạo **bằng chứng MLS có nhắc tới**, không tạo cờ “gần”.

### E3. Chốt taxonomy của filter trước khi lấy dữ liệu

Mỗi filter là một hàm có hợp đồng rõ:

| Loại | Dữ liệu dùng | Giá trị chính | Cách đạt |
|---|---|---|---|
| `vietnamese_community` | Điểm công khai đã kiểm chứng | Điểm gần nhất | Khoảng cách ≤ ngưỡng |
| `lake` | Hồ/hồ chứa đáng kể, có tên | Điểm gần nhất | Khoảng cách ≤ ngưỡng |
| `coast` | Bãi biển/điểm tiếp cận bờ biển phù hợp | Điểm gần nhất | Khoảng cách ≤ ngưỡng |
| `highway` | Hình học motorway/trunk phù hợp | Đoạn đường gần nhất | Khoảng cách ≤ ngưỡng |
| `park` | Công viên công khai | Điểm gần nhất, có thể thêm mật độ | Khoảng cách ≤ ngưỡng |
| `restaurants` | Nhà hàng | Số điểm trong bán kính | Số lượng ≥ ngưỡng |
| `shopping` | Siêu thị, mall, department store | Điểm gần nhất | Khoảng cách ≤ ngưỡng |
| `transit` | Ga Caltrain/BART/VTA hoặc mạng phù hợp | Ga gần nhất | Khoảng cách ≤ ngưỡng |

Không gộp các khái niệm khác nhau chỉ vì cùng có tọa độ:

- Quán cà phê không tự động là nhà hàng.
- Cửa hàng nhỏ không tự động là “khu mua sắm”.
- Ao trang trí không tự động là “gần hồ”.
- Trạm xe buýt đơn lẻ không tự động là “gần ga / transit” nếu nhãn UI hứa về
  đường sắt.
- Tâm một thành phố không phải là vị trí “khu cộng đồng”.

Tên filter, query nguồn và điều kiện match phải cùng nghĩa.

### E4. Geocode địa chỉ theo lô

Ưu tiên geocoder chính phủ hoặc nguồn địa chỉ đáng tin cậy. Với Hoa Kỳ, có thể
dùng U.S. Census Geocoder theo batch để giảm request và tạo artifact dễ kiểm.

Input mẫu:

```csv
0,123 Example Street,San Jose,CA,95100
1,456 Sample Avenue,Campbell,CA,95000
```

Với mỗi kết quả, lưu:

```json
{
  "lat": 37.000000,
  "lon": -121.000000,
  "precision": "address",
  "source": "U.S. Census Geocoder",
  "matched_address": "123 EXAMPLE ST, SAN JOSE, CA, 95100"
}
```

Quality gate:

- Đủ geocode cho mọi index.
- Thành phố/ZIP khớp hợp lý.
- Tọa độ nằm trong vùng nghiên cứu.
- Không có hai địa chỉ xa nhau nhưng nhận cùng tọa độ một cách bất thường.
- Ghi rõ `address`, `address_range`, `street` hoặc `approximate_street`.

Nếu địa chỉ mới chưa có trong geocoder:

1. Tìm đường hoặc khu phát triển bằng nguồn bản đồ khác.
2. Dùng tâm đoạn đường phù hợp chỉ khi không có số nhà.
3. Gắn precision thấp hơn.
4. Ghi nguồn và lý do override.
5. Kiểm tra thủ công trên bản đồ.

Không dùng tọa độ phỏng đoán mà gắn nhãn `address`.

### E5. Xác định vùng truy vấn

Tính bounding box từ toàn bộ geocode rồi thêm padding đủ lớn cho ngưỡng rộng
nhất. Với tiện ích xa như biển, có thể dùng danh sách anchor riêng thay vì mở
rộng một query POI khổng lồ.

Quy tắc:

- Bbox phải bao phủ mọi listing.
- Padding phải lớn hơn ngưỡng filter rộng nhất cho POI lấy từ bbox.
- Chia vùng hoặc chia loại query nếu response vượt giới hạn.
- Lưu chính câu query vào cache để chạy lại.
- Không dựa vào một query tương tác không có trace.

Ví dụ Overpass cho POI:

```overpass
[out:json][timeout:240][maxsize:268435456];
(
  nwr["amenity"="restaurant"](<south>,<west>,<north>,<east>);
  nwr["leisure"="park"](<south>,<west>,<north>,<east>);
  nwr["shop"~"^(supermarket|mall|department_store)$"](<bbox>);
  nwr["natural"="water"]["name"](<bbox>);
  nwr["water"~"^(lake|reservoir)$"]["name"](<bbox>);
);
out center tags;
```

Ví dụ đường lớn:

```overpass
[out:json][timeout:240][maxsize:268435456];
way["highway"~"^(motorway|trunk)$"](<bbox>);
out tags geom;
```

Transit nên có query riêng theo `railway=station`, `station=*`,
`public_transport=station` hoặc mạng/operator phù hợp với vùng. Đừng trộn mọi
bus stop vào nếu UI chỉ nói về ga đường sắt.

### E6. Chọn và kiểm chứng nguồn

Thứ tự ưu tiên:

1. Nguồn chính phủ hoặc đơn vị vận hành cho danh tính, địa chỉ và anchor.
2. OpenStreetMap cho POI, hình học đường và mạng giao thông.
3. Trang chính thức của địa điểm để xác nhận tên, loại và địa chỉ.
4. Nguồn tìm kiếm phụ chỉ để phát hiện ứng viên; không dùng làm nguồn sự thật
   duy nhất nếu có nguồn chính thức.

Mỗi lần research phải lưu:

- Ngày snapshot tuyệt đối.
- Tên nguồn.
- Loại giấy phép/ghi công cần hiển thị.
- Query hoặc tham số đầu vào.
- Response thô hoặc cache đủ để tái tính.
- Danh sách override thủ công và lý do.

Với điểm sinh hoạt cộng đồng:

- Chỉ dùng địa điểm công khai như trung tâm văn hóa, khu thương mại, vườn di
  sản hoặc tổ chức cộng đồng có địa chỉ công khai.
- Xác nhận địa điểm bằng ít nhất một nguồn chính thức; hai nguồn nếu tên hoặc
  địa chỉ không rõ.
- Gọi filter theo đúng đối tượng đo, ví dụ “Gần khu thương mại / sinh hoạt cộng
  đồng Việt”.
- Có thể rút gọn thành “Gần khu người Việt” trên chip nếu phần giải thích ghi rõ
  phương pháp.
- Tuyệt đối không suy đoán sắc tộc cư dân từ họ tên, ngôn ngữ, nhà hàng, dữ liệu
  census hay hình ảnh khu phố.

### E7. Chuẩn hóa POI

OpenStreetMap trả `node`, `way` và `relation`. Chuẩn hóa thành point:

```python
def element_point(element):
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    if element.get("center"):
        return float(element["center"]["lat"]), float(element["center"]["lon"])
    return None
```

Chỉ giữ record:

- Có tên đủ để giải thích cho người dùng.
- Có tọa độ/center hợp lệ.
- Có tag đúng taxonomy.
- Nằm trong vùng hợp lý.

Khử trùng theo tên chuẩn hóa + khoảng cách nhỏ:

```python
normalized = re.sub(r"[^a-z0-9]+", "", name.casefold())
duplicate = same_normalized_name and distance_miles < 0.08
```

Giữ lại record không tên trong thống kê chỉ khi đã có quy tắc rõ ràng và UI
không cần nêu tên. Mặc định nên loại vì filter cần giải thích được.

### E8. Tính khoảng cách đúng loại hình học

#### Điểm tới điểm

Dùng Haversine:

```python
EARTH_RADIUS_MILES = 3958.7613

def haversine_miles(lat1, lon1, lat2, lon2):
    # Chuyển sang radian và tính cung lớn ngắn nhất.
    ...
```

Dùng cho:

- Community anchor.
- Hồ/bãi biển dạng anchor.
- Công viên, nhà hàng, mua sắm và ga đã chuẩn hóa thành point.

#### Điểm tới đường

Đối với cao tốc, đo tới từng segment của geometry rồi lấy khoảng cách nhỏ nhất.
Không đo tới:

- Tâm toàn tuyến.
- Điểm đặt nhãn.
- Lối ra xa hơn đoạn đường chính.

Ở quy mô vùng đô thị, có thể chiếu cục bộ sang `x/y` theo miles và tính khoảng
cách từ điểm tới đoạn thẳng. Nếu vùng quá lớn hoặc cần độ chính xác cao hơn, dùng
thư viện geospatial và projection phù hợp.

#### Mật độ

Với nhà hàng, “điểm gần nhất” không phản ánh lựa chọn. Tính:

```json
{
  "nearest": {"name": "Example Restaurant", "distance_miles": 0.21},
  "counts": {"0.5": 4, "1": 13, "2": 41}
}
```

Có thể áp dụng count cho công viên/mua sắm, nhưng chỉ dùng trong match nếu hợp
đồng filter nói rõ.

### E9. Thiết kế ba mức gần

Ba mức có mục đích:

- `strict`: ưu tiên đi bộ hoặc quãng di chuyển rất ngắn, tùy loại tiện ích.
- `balanced`: mức mặc định hợp lý cho sinh hoạt thường ngày.
- `broad`: chấp nhận di chuyển xa hơn để không bỏ sót lựa chọn.

Baseline đã dùng thành công cho danh sách nhà ở South Bay:

| Category | Strict | Balanced | Broad |
|---|---:|---:|---:|
| Cộng đồng Việt công khai | 4 mi | 6 mi | 10 mi |
| Hồ/hồ chứa | 2 mi | 4 mi | 8 mi |
| Biển | 18 mi | 22 mi | 30 mi |
| Cao tốc | 0,5 mi | 1,25 mi | 2 mi |
| Công viên | 0,25 mi | 0,75 mi | 1 mi |
| Mua sắm | 0,5 mi | 0,75 mi | 1,5 mi |
| Ga/transit | 0,75 mi | 1,25 mi | 2 mi |

Nhà hàng dùng mật độ:

| Mode | Bán kính | Số nhà hàng tối thiểu |
|---|---:|---:|
| Strict | 0,5 mi | 3 |
| Balanced | 1 mi | 5 |
| Broad | 2 mi | 5 |

Đây là baseline theo vùng, không phải chân lý chung. Khi dùng cho thành phố
khác:

1. Chốt ý nghĩa sản phẩm của từng mode.
2. Xem phân bố khoảng cách và density bằng percentile/histogram.
3. Kiểm tra 5–10 listing ở các đầu phân bố trên bản đồ.
4. Điều chỉnh theo mật độ đô thị và loại tiện ích.
5. Ghi lý do thay đổi.
6. Chạy lại toàn bộ snapshot và test.

Không chọn ngưỡng bằng cách thử đến khi một căn cụ thể được đưa vào hoặc loại
ra. Ngưỡng là quy tắc sản phẩm, không phải công cụ chỉnh kết quả.

### E10. Tạo cờ match thuần dữ liệu

```python
for mode in ("strict", "balanced", "broad"):
    for category, threshold in thresholds[mode].items():
        flags[mode][category] = (
            amenities[category]["distance_miles"] <= threshold
        )

    radius = restaurant_radii[mode]
    key = format_radius_key(radius)
    flags[mode]["restaurants"] = (
        amenities["restaurants"]["counts"][key]
        >= restaurant_min_counts[mode]
    )
```

Yêu cầu:

- Hàm quyết định phải deterministic.
- Không đọc DOM.
- Không phụ thuộc thứ tự listing.
- Không dùng chuỗi tóm tắt để quyết định.
- Mọi category có boolean ở cả ba mode.
- Tính lại được chỉ từ geocode + normalized POI + methodology.

### E11. Tạo tóm tắt nhưng không phóng đại

Chọn tối đa ba highlight đạt mode `balanced`, theo thứ tự ưu tiên sản phẩm.

Ví dụ:

```text
khu thương mại / sinh hoạt cộng đồng Việt cách khoảng 3,2 dặm
· 18 nhà hàng trong 1 dặm
· công viên cách khoảng 0,4 dặm
```

Nếu không có highlight:

```text
Vị trí ngoại ô; các tiện ích chính cần di chuyển xa hơn.
```

Không viết:

- “Chỉ 5 phút” khi chưa có routing.
- “Đi bộ được” chỉ từ khoảng cách đường chim bay.
- “Khu người Việt đông” từ proximity tới một anchor.
- “Trường tốt” nếu chỉ có tên trường.
- “An toàn” nếu không có nguồn và phương pháp chuyên biệt.

### E12. Schema snapshot vị trí

```json
{
  "snapshot_date": "YYYY-MM-DD",
  "methodology": {
    "distance_type": "straight_line",
    "distance_unit": "miles",
    "thresholds_miles": {},
    "restaurant_radii_miles": {},
    "restaurant_min_counts": {},
    "notes_vi": "Khoảng cách là đường chim bay...",
    "sources": []
  },
  "category_labels": {},
  "listings": {
    "ML12345678": {
      "geocode": {
        "precision": "address",
        "source": "U.S. Census Geocoder"
      },
      "amenities": {
        "park": {
          "name": "Example Park",
          "distance_miles": 0.42,
          "counts": {"0.5": 1, "1": 3, "2": 8}
        },
        "restaurants": {
          "name": "Example Restaurant",
          "distance_miles": 0.18,
          "counts": {"0.5": 4, "1": 13, "2": 41}
        }
      },
      "matches": {
        "strict": {"park": false, "restaurants": true},
        "balanced": {"park": true, "restaurants": true},
        "broad": {"park": true, "restaurants": true}
      },
      "location_summary_vi": "13 nhà hàng trong 1 dặm · công viên cách khoảng 0,4 dặm",
      "mls_evidence_categories": ["park"]
    }
  }
}
```

Snapshot công khai không nhất thiết chứa `lat/lon` của từng căn. Có thể giữ tọa
độ trong cache riêng và chỉ xuất provenance + khoảng cách cần cho website.

### E13. Validation snapshot

Trước build:

```python
assert len(location_records) == len(listings)
assert set(location_records) == {item["mls"] for item in listings}
assert all(item["geocode"]["precision"] for item in location_records.values())
```

Kiểm tra thêm:

- Không có `NaN`, `Infinity` hoặc khoảng cách âm.
- Tất cả category bắt buộc tồn tại.
- `nearest.distance_miles` khớp tính lại từ cache.
- Count không giảm khi bán kính tăng: `0.5 <= 1 <= 2`.
- Nếu `strict=True` thì `balanced=True`; nếu `balanced=True` thì `broad=True`,
  trừ khi chính sách mode không lồng nhau và đã ghi rõ.
- Tên nearest không rỗng.
- Mọi override có precision thấp hơn `address` và có nguồn.
- Snapshot date là ngày tuyệt đối, không dùng “hôm nay”.
- Sources và attribution có trong dữ liệu hoặc giao diện.

In log từng record:

```text
03/48 ML12345678 community=3.2 park=0.4 restaurants=13 balanced=community,park,restaurants
```

Cuối run:

```json
{"listings": 48, "missing_geocodes": 0, "missing_categories": 0}
```

### E14. Ghép dữ liệu vào build

Build nhận hai input độc lập:

```bash
python3 scripts/build_site.py \
  data/listings-source.json \
  --locations data/location-insights.json
```

Ghép bằng MLS, không ghép bằng thứ tự mảng:

```python
location_by_mls = location_data["listings"]
prepared = [
    prepare_listing(item, location_by_mls[item["mls"]])
    for item in source["listings"]
]
```

Đưa ra client phần cần thiết:

```json
{
  "location": {
    "amenities": {},
    "matches": {},
    "summary_vi": "",
    "mls_evidence_categories": []
  }
}
```

Không sửa trực tiếp `assets/js/listings-data.js`; file đó phải được build lại từ
JSON.

### E15. Biến research thành filter website

#### State tối thiểu

```javascript
const selectedAmenities = new Set();
const mode = proximityMode.value;       // strict | balanced | broad
const logic = amenityLogic.value;       // all | any
```

#### Điều kiện lọc

```javascript
const checks = selected.map(
  (category) => item.location.matches[mode][category],
);

const matchesAmenities =
  !selected.length ||
  (logic === "all" ? checks.every(Boolean) : checks.some(Boolean));
```

Filter vị trí phải compose với:

- Từ khóa.
- Số phòng ngủ.
- Giá.
- Các filter bất động sản khác.

Điều kiện cuối:

```javascript
return matchesSearch &&
  matchesBeds &&
  matchesPrice &&
  matchesAmenities;
```

#### Count trên chip

Count mỗi chip là số listing đạt riêng category ở mode hiện tại, trước khi áp
logic `all/any`:

```javascript
const matches = listings.filter(
  (item) => item.location.matches[mode][category],
).length;
```

Điều này giúp người dùng biết độ rộng của tiêu chí. Kết quả tổng vẫn phải tính
lại sau khi kết hợp mọi filter.

#### Logic `all` và `any`

- `all`: căn nhà phải đạt mọi tiện ích đã chọn.
- `any`: căn nhà chỉ cần đạt ít nhất một tiện ích đã chọn.
- Không có tiện ích được chọn: không loại căn nào theo vị trí.

Label UI phải nói rõ “Đáp ứng tất cả” và “Đáp ứng ít nhất một”.

### E16. Sắp xếp theo độ phù hợp

Nếu người dùng chọn tiện ích, có thể tự chuyển sort mặc định sang “Phù hợp vị
trí nhất”. Điểm phải ưu tiên match nhưng vẫn phân biệt các căn cùng match:

```javascript
function locationScore(item, selected, mode) {
  return selected.reduce((score, category) => {
    const matched = item.location.matches[mode][category];
    const distance = item.location.amenities[category].distance_miles || 0;
    const densityBonus =
      category === "restaurants"
        ? Math.min(item.location.amenities.restaurants.counts["1"], 30) / 30
        : 0;
    return score + (matched ? 10 : 0) + densityBonus + 1 / (1 + distance);
  }, 0);
}
```

Nguyên tắc:

- Match boolean có trọng số lớn nhất.
- Khoảng cách chỉ phá hòa trong cùng nhóm match.
- Density bonus có trần để một khu quá dày không lấn át mọi tiêu chí.
- Cuối cùng dùng `index` hoặc MLS làm tie-breaker ổn định.
- Nếu không chọn tiện ích, giữ thứ tự mặc định.

### E17. Hiển thị lý do căn nhà khớp

Card nên hiển thị tối đa ba tag từ các tiện ích đang chọn và đã match. Nếu chưa
chọn, có thể hiển thị các highlight mode `balanced`.

Tooltip hoặc detail cần có:

- Tên địa điểm gần nhất.
- Khoảng cách.
- Với nhà hàng: số lượng trong bán kính quy định.

Trang chi tiết nên có đủ mọi category:

```text
Nhãn → giá trị chính → địa điểm gần nhất → dấu “MLS có nhắc tới” nếu có
```

Dấu “MLS có nhắc tới” chỉ là provenance của lời rao, không làm thay đổi cờ.

### E18. UX filter trên desktop và mobile

Desktop:

- Filter đầu trang gọn nhưng thấy được các chip.
- Khi cuộn tới danh sách, có thể dock thanh tóm tắt vào header.
- Thanh dock chỉ tóm tắt state; drawer chứa controls đầy đủ.
- Dock/undock không làm nội dung nhảy vị trí.

Mobile:

- Ban đầu ẩn drawer để kết quả đầu tiên xuất hiện sớm.
- Dùng CTA rõ nghĩa như `Lọc theo nhu cầu`, không dùng nhãn mơ hồ.
- Có icon filter, `aria-controls`, `aria-expanded`.
- Badge số filter đang áp dụng chỉ hiện khi lớn hơn `0`.
- CTA đổi trạng thái rõ khi drawer mở hoặc đang có filter.
- Nút chạm đủ lớn, không tràn ngang.
- Hỗ trợ `prefers-reduced-motion`.

Cả hai:

- Có “Xóa bộ lọc”.
- Hiện số căn kết quả.
- Có empty state.
- Có thể bỏ từng filter từ summary.
- Nhấn `Escape` đóng drawer và trả focus.
- Màu không phải tín hiệu duy nhất; dùng text, icon và `aria-pressed`.

### E19. Attribution, giới hạn và ngôn ngữ an toàn

Nếu dùng OpenStreetMap, hiển thị attribution phù hợp:

```text
© OpenStreetMap contributors, ODbL
```

Ghi rõ:

- Khoảng cách là đường chim bay.
- Không phải thời gian lái xe.
- Dữ liệu có ngày snapshot và có thể thay đổi.
- Người mua cần xác minh thông tin quan trọng.

Không dùng filter để đưa ra kết luận thuộc nhóm được bảo vệ hoặc lời hứa:

- Không “khu an toàn”.
- Không “khu dân cư người Việt”.
- Không “trường tốt nhất”.
- Không “đầu tư chắc chắn tăng giá”.
- Không “đi làm 10 phút” nếu chưa có routing theo thời điểm.

### E20. Quality gate cho research và filter

Kiểm thử dữ liệu:

- Đủ một insight cho mỗi MLS.
- Category và mode đầy đủ.
- Cờ lồng nhau hợp lý.
- Count theo bán kính đơn điệu.
- Không khoảng cách bất thường.
- Không anchor không nguồn.
- Không địa chỉ riêng/tọa độ nhạy cảm bị xuất ngoài nhu cầu.

Kiểm thử trình duyệt:

- Chip hiển thị count đã chốt từ snapshot.
- Chọn một category trả đúng số căn.
- `all` trả tập giao; `any` trả tập hợp.
- Đổi mode cập nhật count và kết quả.
- Clear trả về toàn bộ listing.
- Sort “phù hợp vị trí” deterministic.
- Card và detail nêu đúng tên/khoảng cách.
- Method note có “đường chim bay” và giới hạn nhân khẩu học.
- Mobile drawer, badge, sticky filter và accessibility hoạt động.
- Không overflow, console error hoặc page error.

Không chỉ test “kết quả giảm”. Với một snapshot cố định, phải assert một số
count và địa chỉ đại diện để phát hiện thay đổi thuật toán ngoài ý muốn.

### E21. Runbook bắt buộc cho Agent

Khi bắt đầu một dự án mới, Agent phải thực hiện đúng thứ tự sau:

1. **Định nghĩa nhu cầu.**
   - Liệt kê category filter.
   - Với mỗi category, ghi input, output, lỗi, side effect và quyền.
   - Chốt nghĩa của label trước khi query dữ liệu.
2. **Đọc dữ liệu nhà.**
   - Xác nhận count, MLS duy nhất và địa chỉ đầy đủ.
   - Parse các dữ kiện cốt lõi.
   - Trích tín hiệu vị trí từ mô tả nhưng gắn nhãn là lời MLS.
3. **Geocode.**
   - Tạo batch input.
   - Lưu response thô.
   - Kiểm tra precision và vùng.
   - Dừng nếu còn listing không có tọa độ hợp lệ.
4. **Thu thập dữ liệu nền.**
   - Tạo bbox và query file.
   - Tải POI, transit và geometry đường.
   - Lưu response thô cùng ngày lấy và nguồn.
   - Dừng nếu category bắt buộc không có dữ liệu.
5. **Research anchor đặc biệt.**
   - Lập danh sách ứng viên.
   - Xác nhận bằng nguồn chính thức.
   - Lưu tên, tọa độ, loại, nguồn và ghi chú.
6. **Chuẩn hóa.**
   - Parse node/way/relation.
   - Lọc theo taxonomy.
   - Khử trùng.
   - In count trước/sau.
7. **Tính insight.**
   - Tính nearest, density và point-to-segment.
   - Áp ngưỡng đã chốt.
   - Sinh summary và provenance.
8. **Review outlier.**
   - Khoảng cách nhỏ nhất/lớn nhất.
   - Listing có density cao nhất.
   - Geocode precision thấp.
   - Category không có match hoặc match gần như toàn bộ.
9. **Đóng snapshot.**
   - Ghi ngày, phương pháp, nguồn, query và ngưỡng.
   - Validate schema/invariant.
   - Chỉ sau đó mới build website.
10. **Tạo UI và test.**
    - Filter phải đọc từ snapshot.
    - Assert count/tập kết quả đại diện.
    - Test desktop, mobile và trang chi tiết.

Nếu một bước cần quyết định của con người, dừng và hỏi một câu ngắn. Ví dụ:

```text
Filter “gần transit” nên chỉ tính ga đường sắt, hay gồm cả trạm VTA light rail?
```

Không tự mở rộng nghĩa filter để làm tăng số kết quả.

### E22. Manifest và trace để tái chạy

Nên tạo:

```text
.m/location/
  research-manifest.json
  census-input.csv
  census-output.csv
  poi-query.overpass
  osm-pois.json
  transit-query.overpass
  osm-transit.json
  road-query.overpass
  roads-*.json
  anchors.json
  enrich.log
```

`research-manifest.json` mẫu:

```json
{
  "run_id": "location-YYYYMMDD-HHMMSS",
  "started_at": "YYYY-MM-DDTHH:MM:SSZ",
  "completed_at": "YYYY-MM-DDTHH:MM:SSZ",
  "listing_source": "data/listings-source.json",
  "listing_count": 48,
  "bbox": {
    "south": 36.88,
    "west": -122.08,
    "north": 37.50,
    "east": -121.28
  },
  "sources": [
    {
      "name": "U.S. Census Geocoder",
      "artifact": "census-output.csv",
      "status": "success"
    },
    {
      "name": "OpenStreetMap contributors",
      "artifact": "osm-pois.json",
      "license": "ODbL",
      "status": "success"
    }
  ],
  "overrides": [],
  "commands": [],
  "result": {
    "status": "success",
    "missing_geocodes": 0,
    "missing_categories": 0
  }
}
```

Trace phải đủ trả lời:

- Dữ liệu nào đã được dùng?
- Lấy ngày nào?
- Query nào tạo ra artifact nào?
- Lệnh nào sinh snapshot?
- Có override nào?
- Run thành công hay thất bại, vì sao?
- File nào đã thay đổi?

Không đưa token, URL portal riêng, email hoặc response nhạy cảm vào manifest.

---

## Pha F — Dịch sang tiếng Việt

## F1. Chia nội dung thành ba loại

### Loại 1: Nhãn cố định

Ví dụ:

```python
LABELS = {
    "Beds Total": "Tổng số phòng ngủ",
    "Baths Total": "Tổng số phòng tắm",
    "Sq Ft Total": "Diện tích sử dụng",
    "Cooling": "Hệ thống làm mát",
    "Heating": "Hệ thống sưởi",
    "Kitchen": "Nhà bếp",
    "Listed By": "Môi giới niêm yết",
}
```

Dịch bằng dictionary, không gọi API từng lần.

### Loại 2: Giá trị kỹ thuật lặp lại

Ví dụ:

```python
EXACT_VALUES = {
    "Active": "Đang rao bán",
    "Detached": "Nhà đơn lập",
    "Central AC": "Điều hòa trung tâm",
    "Central Forced Air": "Sưởi không khí cưỡng bức trung tâm",
    "Attached Garage": "Gara liền nhà",
    "Pool - In Ground": "Hồ bơi âm đất",
}
```

Thêm phrase dictionary cho chuỗi ghép:

```python
PHRASE_VALUES = {
    "Walk-in Closet": "Tủ quần áo không cửa ngăn",
    "Primary Suite/Retreat": "Suite phòng ngủ chính / không gian nghỉ riêng",
    "Tankless Water Heater": "Máy nước nóng không bình chứa",
}
```

### Loại 3: Mô tả dài riêng từng căn

Có thể dùng dịch vụ dịch làm bản nháp, nhưng bắt buộc:

- Bảo vệ thuật ngữ.
- Bảo vệ số đo.
- Hậu kiểm bằng glossary.
- Đọc lại toàn bộ.
- Sửa theo từng listing nếu cần.

## F2. Bảo vệ đơn vị bằng placeholder

Không gửi thẳng:

```text
3,080 sq ft
```

vào dịch vụ dịch rồi hy vọng nó giữ nguyên. Một số dịch vụ có thể đổi thành “3.080 m²” nhưng không quy đổi.

Quy trình đúng:

1. Regex mọi dạng:
   - `square feet`
   - `square foot`
   - `sq. ft.`
   - `sqft`
   - `sf`
   - số có `+` hoặc `±`
   - `acre`
2. Thay bằng token:

```text
ZXAREA0ZX
```

3. Dịch phần còn lại.
4. Khôi phục:

```text
3.080 ft² (≈ 286,1 m²)
```

## F3. Hệ số quy đổi

Dùng:

```text
1 ft² = 0,092903 m²
1 acre = 4.046,8564224 m²
```

Công thức:

```python
square_meters = square_feet * 0.092903
acre_meters = acres * 4046.8564224
```

Định dạng Việt Nam:

- Dấu chấm phân tách hàng nghìn.
- Dấu phẩy phần thập phân.
- m² thường làm tròn một chữ số cho diện tích nhà/lô.

Ví dụ:

```text
2.500 ft² (≈ 232,3 m²)
```

Đơn giá:

```text
USD/ft²
USD/m² = USD/ft² ÷ 0,092903
```

## F4. Thuật ngữ phải được kiểm soát

Các từ cần glossary:

- ADU → `ADU (nhà ở phụ)`
- HOA → `hiệp hội chủ nhà`
- escrow → giữ `escrow` và diễn giải nếu cần
- rent-back → `thời gian người bán ở lại sau giao dịch`
- primary suite → `suite phòng ngủ chính`
- full bath → `phòng tắm đầy đủ`
- half bath → `phòng vệ sinh phụ`
- forced air → `không khí cưỡng bức`
- cul-de-sac → `đường cụt`
- curb appeal → `mặt tiền thu hút`
- pot filler → `vòi rót nước trên bếp`
- plantation shutters → `rèm chớp plantation`
- in-ground pool → `hồ bơi âm đất`
- solar owned → `hệ thống điện mặt trời sở hữu riêng`

Giữ nguyên:

- Tên đường.
- Tên thành phố.
- Tên trường.
- Tên hãng: Wolf, Thermador, Sub-Zero, Bosch...
- MLS.
- ADU/EV/HOA khi độc giả cần nhận biết thuật ngữ Mỹ.

## F5. Thứ tự ưu tiên khi dịch giá trị

1. Exact dictionary.
2. Quy tắc số đo/giá/ngày.
3. Phrase dictionary.
4. Bản dịch kỹ thuật đã hậu kiểm.
5. Giá trị gốc nếu là tên riêng hoặc chưa chắc chắn.

Không ép dịch mọi từ tiếng Anh. Tên riêng và mã kỹ thuật dịch sai còn tệ hơn giữ nguyên.

## F6. Biên tập thủ công

Sau dịch:

1. In đủ mô tả của mọi listing.
2. Đọc lần lượt như biên tập viên.
3. Tìm các dấu hiệu dịch máy:
   - chủ ngữ lạ
   - “nhà để xe” thay vì “gara”
   - “bồn tắm” thay cho “phòng tắm”
   - “hòn đảo” thay cho “đảo bếp”
   - “bán trước” thay cho “mua trước khi hoàn thiện”
   - câu chứa dấu chấm giữa số đo và danh từ
4. Lưu fix trong build script hoặc dữ liệu nguồn, không sửa tay HTML sinh ra.

Mọi sửa phải sống qua lần `npm run build` tiếp theo.

---

## Pha G — Tải ảnh cục bộ

### G1. Vì sao phải tải

URL ảnh MLS thường chứa:

- key
- token
- kích thước
- session-derived signature

Chúng có thể hết hạn. Website chỉ trỏ ảnh remote sẽ hỏng sau này.

### G2. Đường dẫn ổn định

```text
assets/properties/<mls-lowercase>/001.jpg
assets/properties/<mls-lowercase>/002.jpg
```

### G3. Downloader an toàn

Yêu cầu:

- Thread pool có giới hạn.
- Timeout.
- Retry.
- User-Agent.
- Xác nhận `Content-Type: image/*`.
- Ghi `.part`, rồi `os.replace`.
- Skip file đã tồn tại và đủ lớn.
- In tiến độ có giới hạn.
- Thất bại bất kỳ ảnh nào thì exit khác 0.

### G4. Xác minh ảnh

Ít nhất kiểm tra:

- File tồn tại.
- Kích thước > 1 KB.
- JPEG bắt đầu `FF D8`.
- JPEG kết thúc `FF D9`.
- Số file thực tế bằng tổng URL ảnh.

Không chỉ tin HTTP 200.

---

## Pha H — Sinh website tĩnh

## H1. Kiến trúc khuyến nghị

```text
index.html
listings/NN-slug.html
assets/css/styles.css
assets/js/site.js
assets/js/listings-data.js
assets/fonts/
assets/properties/
data/listings-source.json
data/listings.json
scripts/build_site.py
scripts/download_images.py
tests/site.spec.js
```

### H2. Tại sao dùng `listings-data.js`

Nếu `index.html` được mở trực tiếp bằng `file://`, fetch JSON có thể bị chặn. Dùng:

```javascript
window.HOUSE_LISTINGS = [...];
```

giúp website chạy không cần server.

Vẫn giữ `data/listings.json` để tái sử dụng bằng công cụ khác.

### H3. Trang danh sách

Nên có:

- Header thương hiệu.
- Hero.
- Tổng số căn.
- Tìm địa chỉ/MLS.
- Lọc số phòng ngủ.
- Lọc giá.
- Lọc theo vị trí và tiện ích từ snapshot nghiên cứu.
- Chọn mức gần và cách kết hợp `all`/`any`.
- Hiển thị lý do căn nhà khớp và số kết quả trên từng chip.
- Sắp xếp giá/diện tích.
- Sắp xếp theo độ phù hợp vị trí khi có tiêu chí được chọn.
- Card có ảnh, giá, địa chỉ, MLS, phòng ngủ, phòng tắm, ft² và m².
- Empty state.
- Footer và disclaimer.

### H4. Trang chi tiết

Nên có:

- Địa chỉ, giá, trạng thái, MLS.
- Gallery 3 ảnh đầu.
- Lightbox toàn bộ ảnh.
- Facts bar.
- Mô tả chia thành các đoạn đọc được; tránh một khối văn bản quá dài.
- Bảng thông tin chung/nội thất/ngoại thất/bổ sung.
- Link Google Maps.
- Khối “Tiện ích quanh nhà” có khoảng cách, địa điểm gần nhất, mật độ và
  provenance nếu mô tả MLS có nhắc tới.
- Nút sao chép MLS.
- Điều hướng căn trước/căn sau.
- Disclaimer.

### H5. Slug

```python
slug = f"{index + 1:02d}-{slugify(address)}"
```

Chuẩn hóa Unicode NFKD, bỏ dấu để URL ổn định.

### H6. Nhận diện thương hiệu

Lấy màu thật từ logo, không đoán. Có thể dùng PIL để phân tích màu chủ đạo.

Đối với thương hiệu Nhà Mỹ Cali:

```text
#0041b0
```

Nhưng skill phải nhận màu từ input cho dự án khác.

Kiểm tra:

- Logo đủ lớn.
- Logo không méo.
- Logo nhìn rõ trên footer.
- Slogan đúng trên mọi trang.
- `theme-color` phù hợp.
- Màu cũ không còn sót.

### H7. Font tiếng Việt

Để tránh chữ có dấu trồi lên/sụt xuống do font fallback:

1. Dùng font có hỗ trợ ngôn ngữ `vi`.
2. Nhúng font cục bộ bằng `@font-face`.
3. Có đúng file cho các weight sử dụng.
4. Chỉ dùng weight thật, ví dụ 400 và 700.
5. Đặt:

```css
font-synthesis: none;
font-kerning: normal;
text-rendering: optimizeLegibility;
```

6. Chuẩn hóa nội dung Unicode NFC.
7. Dùng Playwright `document.fonts.check`.

Không khai báo weight 750/800 nếu chỉ có font 700; trình duyệt sẽ nội suy nét.

### H8. Responsive

Kiểm tra ít nhất:

- 1440 px desktop.
- 768 px tablet.
- 390 px mobile.

Trên mobile:

- Một cột listing.
- Không overflow ngang.
- Header không chồng menu.
- Logo/slogan còn đọc được.
- Gallery và bảng thông tin xếp dọc.
- Nút có kích thước chạm hợp lý.
- Drawer filter đóng/mở được, badge số filter đúng và CTA nói rõ mục đích.

---

## Pha I — Kiểm thử và quality gate

## I1. Syntax và build

```bash
python3 -m py_compile \
  scripts/scrape_mls.py \
  scripts/translate_data.py \
  scripts/enrich_locations.py \
  scripts/build_site.py \
  scripts/download_images.py
node --check assets/js/site.js
npm run build
```

### I2. Kiểm tra tĩnh

Xác nhận:

- Số listing đúng.
- Số HTML = 1 + số listing.
- Mỗi `detail_url` tồn tại.
- Logo có trên mọi trang.
- ft²/m² đầy đủ.
- Không còn ảnh remote trong dữ liệu cuối.
- Không có email.
- Không có portal URL riêng.
- Không link nội bộ bị thiếu.
- Không ảnh thiếu/hỏng.
- Không nhãn tiếng Anh rõ ràng còn sót ngoài tên riêng.
- Số location insight đúng bằng số listing và MLS join đủ.
- Mỗi listing có đủ category/mode.
- Count theo bán kính đơn điệu.
- Không khoảng cách âm/NaN/Infinity.
- Methodology có snapshot date, nguồn, ngưỡng và loại khoảng cách.

### I3. Playwright desktop

Test:

- Đúng số card.
- Logo và slogan hiển thị.
- Font cục bộ đã tải.
- Màu thương hiệu đúng.
- Không overflow.
- Ảnh có `naturalWidth > 0`.
- Search trả đúng listing.
- Filter làm giảm số card.
- Count trên chip khớp snapshot.
- `all`, `any` và ba mode trả đúng tập listing.
- Clear filter khôi phục toàn bộ listing.
- Sort độ phù hợp ổn định.
- Sticky filter không làm nhảy nội dung.
- Nhấp card mở đúng trang.
- Facts bar có m².
- Trang chi tiết có đủ category vị trí và đúng địa điểm/khoảng cách đại diện.
- Gallery/lightbox next/close hoạt động.
- Console errors và page errors bằng 0.

### I4. Playwright mobile

Test:

- Viewport 390×844.
- Grid một cột.
- Header hợp lý.
- Không overflow.
- Logo đủ lớn.
- Trang chi tiết không overflow.
- Nút nổi hoặc back-to-top không che nội dung.
- CTA “Lọc theo nhu cầu” mở drawer, badge filter đúng và không tràn ngang.
- Drawer đóng bằng toggle và `Escape`; ARIA state đúng.

### I5. Smoke test toàn bộ trang con

Lặp qua mọi listing:

```javascript
for (const detail of details) {
  await page.goto(base + detail.href);
  await expect(page.locator("h1")).toHaveText(detail.address);
  await expect(page.locator(".facts-bar")).toContainText(`${detail.squareMeters} m²`);
  expect(await heroImage.evaluate(img => img.naturalWidth)).toBeGreaterThan(0);
}
```

Đây là gate bắt buộc. Căn đầu tiên chạy đúng không chứng minh 26 căn còn lại đúng.

### I6. Kiểm tra bảo toàn nội dung

Nếu chia mô tả thành lead, paragraph, feature list và note:

- Ghép lại text render.
- Chuẩn hóa whitespace.
- So sánh với `description_vi`.

Không được làm mất câu khi cải thiện khả năng đọc.

---

## 7. Playbook xử lý lỗi

### Lỗi 1: Portal báo N listing nhưng marker chỉ N-1

Nguyên nhân:

- Record tải muộn.
- Comment marker thiếu.

Xử lý:

- Duyệt index dự kiến `0..N-1`.
- Lấy MLS/key từ trang chi tiết.
- Kiểm tra unique.

### Lỗi 2: POST trả lại trang mẹ

Nguyên nhân:

- ViewState cũ.
- Sai form action.
- Mất session.

Xử lý:

- GET lại trang mẹ.
- Parse lại hidden fields.
- Dùng cùng session.
- Lấy `EVENTARGUMENT` từ HTML hiện tại.

### Lỗi 3: Chỉ lấy được 2–3 ảnh

Nguyên nhân:

- Chỉ đọc `<img>`.

Xử lý:

- Đọc gallery map trong JavaScript.
- Tìm URL `GetMedia`.
- Regex variant ảnh medium/full.

### Lỗi 4: Mô tả của vài căn quá ngắn

Nguyên nhân:

- Template thêm nhãn sau description.
- Parser dùng vị trí cuối.

Xử lý:

- In toàn bộ vùng trước `General Description`.
- Chọn đoạn dài nhất hợp lệ.
- Tạo rule cho template ngoại lệ.

### Lỗi 5: Trường học bị ghép sai

Nguyên nhân:

- Table flatten thành chuỗi label/value.

Xử lý:

- State machine theo role elementary/middle/high.
- Nhận biết label bắt đầu `/` là học khu.

### Lỗi 6: Bản dịch tự đổi sai ft² sang m²

Nguyên nhân:

- Dịch vụ dịch diễn giải đơn vị.

Xử lý:

- Placeholder trước dịch.
- Tự tính m².
- Hậu kiểm số lượng `ft²` và `m²`.

### Lỗi 7: Thuật ngữ dịch vô nghĩa

Ví dụ:

- forced air
- rent-back
- pot filler
- primary suite
- curb appeal

Xử lý:

- Exact glossary.
- Phrase glossary.
- Post-edit dictionary.
- Đọc lại toàn bộ mô tả.

### Lỗi 8: Font tiếng Việt không đều

Nguyên nhân:

- Font thiếu glyph.
- Browser fallback.
- Weight giả.
- Unicode decomposed.

Xử lý:

- Font local có `lang=vi`.
- NFC.
- `font-synthesis: none`.
- Chỉ dùng weight có file.
- Test `document.fonts.check`.

### Lỗi 9: Playwright không chạy vì thiếu shared library

Không vội sửa hệ thống. Có thể:

1. Dùng `ldd` tìm library thiếu.
2. `apt-get download` gói cần thiết.
3. `dpkg-deb -x` vào `.m/pw-libs`.
4. Thêm vào `LD_LIBRARY_PATH` trong npm test.

Không commit binary hệ thống nếu repo không cần.

### Lỗi 10: Python HTTP server báo BrokenPipe trong test

Thường do browser hủy request ảnh khi chuyển trang. Nếu:

- test vẫn pass
- browser không báo lỗi
- ảnh chính tải được

thì đây không phải regression website.

### Lỗi 11: Một số địa chỉ mới không geocode chính xác

Nguyên nhân:

- Dự án mới chưa có trong dữ liệu địa chỉ.
- Số nhà chưa được phát hành hoặc geocoder chỉ biết tên đường.

Xử lý:

- Kiểm tra địa chỉ và ZIP.
- Tìm đường/khu phát triển bằng nguồn bản đồ thứ hai.
- Dùng override có `precision=street` hoặc `approximate_street`.
- Lưu nguồn, ngày và lý do.
- Không gắn nhãn `address` cho tọa độ xấp xỉ.

### Lỗi 12: POI bị trùng và count nhà hàng quá cao

Nguyên nhân:

- Cùng địa điểm xuất hiện dưới node/way/relation.
- Tên khác kiểu viết hoa, dấu câu hoặc hậu tố.

Xử lý:

- Chuẩn hóa tên bằng `casefold` và bỏ ký tự không chữ/số.
- Khử trùng theo tên chuẩn hóa + khoảng cách nhỏ.
- So sánh count trước/sau dedupe.
- Kiểm tra thủ công các khu có mật độ cao bất thường.

### Lỗi 13: Cao tốc gần nhưng hệ thống báo xa

Nguyên nhân:

- Đo tới tâm tuyến hoặc center của way.
- Query thiếu geometry hoặc thiếu mảnh đường.

Xử lý:

- Query `out tags geom`.
- Chia đường thành segment.
- Tính khoảng cách point-to-segment.
- Kiểm tra bbox có bao phủ đoạn gần listing.

### Lỗi 14: Count filter đúng nhưng ý nghĩa filter sai

Nguyên nhân:

- Taxonomy query không khớp label UI.
- Ví dụ dùng mọi bus stop cho label “Ga đường sắt”.

Xử lý:

- Viết lại hợp đồng category.
- Lọc tag/network/operator đúng đối tượng.
- Đổi label nếu dữ liệu thực tế rộng hơn.
- Tạo test cho một địa điểm đại diện.

### Lỗi 15: `strict` có nhiều kết quả hơn `balanced`

Nguyên nhân:

- Ngưỡng không lồng nhau.
- Sai key radius dạng `"1"` và `"1.0"`.
- Cờ bị đọc từ mode khác.

Xử lý:

- Validate `strict <= balanced <= broad` theo từng category.
- Chuẩn hóa radius key ở một hàm.
- In diff MLS vi phạm.
- Không build khi invariant thất bại.

### Lỗi 16: Filter “gần khu người Việt” tạo rủi ro diễn giải

Nguyên nhân:

- UI không nói rõ đang đo tới địa điểm công khai.
- Agent suy đoán đặc điểm cư dân.

Xử lý:

- Chỉ dùng anchor thương mại, văn hóa và sinh hoạt cộng đồng công khai.
- Ghi rõ không suy đoán sắc tộc cư dân.
- Lưu provenance của từng anchor.
- Đổi label dài trong phần phương pháp nếu chip cần rút gọn.

### Lỗi 17: Người dùng hiểu khoảng cách là thời gian lái xe

Nguyên nhân:

- UI chỉ hiện số dặm mà thiếu method note.
- Tóm tắt dùng từ “mất X phút”.

Xử lý:

- Ghi “đường chim bay, không phải thời gian lái xe”.
- Không ước tính phút nếu chưa dùng routing.
- Nếu thêm routing, lưu mode, thời điểm, nguồn và traffic assumptions riêng.

---

## 8. Quy trình Git khi người dùng yêu cầu commit/push

### Bước 1. Kiểm tra repo

```bash
git status --short --branch
git remote -v
git log --oneline --decorate -5
```

### Bước 2. Không stage artifact ngoài yêu cầu

Thường bỏ:

- `.m/session.jsonl`
- `.m/warns.jsonl`
- HTML debug nguồn
- URL/token riêng
- screenshot tạm nếu repo không theo dõi
- cache geocode/OSM thô trong `.m/location/` nếu repo chỉ cần snapshot cuối
- `node_modules`

### Bước 3. Kiểm tra secret trước commit

```bash
grep -RInE 'https?://.*(token|ID=|eml=)|[\w.+-]+@[\w.-]+' Skills data README.md
```

Đánh giá từng hit; không commit URL portal riêng tư.

### Bước 4. Stage có chọn lọc

```bash
git add Skills/translate_houselisting_skill.md
git diff --cached --check
git diff --cached --stat
```

### Bước 5. Commit và push

```bash
git commit -m "Document house listing translation workflow"
git push origin HEAD
```

### Bước 6. Xác minh

```bash
git status --short --branch
git log -1 --oneline --decorate
```

Push chỉ được coi là hoàn tất khi remote xác nhận thành công.

---

## 9. Chuỗi lệnh chuẩn cho một dự án đã có đủ dữ liệu

```bash
# 1. Tạo hoặc xác minh snapshot vị trí từ cache research
npm run locations

# 2. Tải hoặc xác minh ảnh
python3 scripts/download_images.py data/listings-source.json --workers 12

# 3. Sinh website
npm run build

# 4. Kiểm tra syntax
python3 -m py_compile \
  scripts/scrape_mls.py \
  scripts/translate_data.py \
  scripts/enrich_locations.py \
  scripts/build_site.py \
  scripts/download_images.py
node --check assets/js/site.js

# 5. Test trình duyệt
npm test

# 6. Xem thủ công
npm run serve
```

Với dự án mới, phải hoàn thành scraper và translation pipeline trước chuỗi lệnh này.

---

## 10. Checklist bàn giao

### Dữ liệu

- [ ] Số listing đúng với nguồn.
- [ ] Không MLS trùng.
- [ ] Không địa chỉ trùng ngoài chủ ý.
- [ ] Mọi listing có mô tả.
- [ ] Mọi listing có ảnh.
- [ ] Không lỗi parser.
- [ ] Mỗi MLS có đúng một location insight.
- [ ] Mọi geocode có precision và source.
- [ ] Mọi category có nearest/density cần thiết.
- [ ] Mọi mode có cờ boolean đầy đủ.
- [ ] Không khoảng cách âm/NaN/Infinity.
- [ ] Count bán kính tăng đơn điệu.

### Research vị trí

- [ ] Taxonomy filter đã được chốt trước khi chọn ngưỡng.
- [ ] Query/cache đủ để tái chạy.
- [ ] Snapshot date là ngày tuyệt đối.
- [ ] Methodology ghi loại khoảng cách, đơn vị, ngưỡng và nguồn.
- [ ] Override tọa độ có lý do và precision thấp hơn.
- [ ] Cao tốc được đo tới đoạn đường gần nhất.
- [ ] POI đã khử trùng.
- [ ] Community anchor là địa điểm công khai có nguồn.
- [ ] Không suy đoán sắc tộc hoặc đặc điểm cư dân.
- [ ] Attribution giấy phép dữ liệu được hiển thị.

### Dịch thuật

- [ ] Nhãn đã Việt hóa.
- [ ] Giá trị kỹ thuật đã Việt hóa.
- [ ] Mô tả đã đọc và hiệu đính.
- [ ] ADU/HOA/escrow được diễn giải đúng.
- [ ] Tên riêng và thương hiệu được giữ.
- [ ] Không `m2`; chỉ dùng `m²`.
- [ ] Mọi ft² quan trọng có m² đi kèm.

### Ảnh

- [ ] Tất cả ảnh lưu cục bộ.
- [ ] Không file thiếu.
- [ ] Không JPEG hỏng.
- [ ] Gallery giữ đúng thứ tự.

### Giao diện

- [ ] Logo đúng.
- [ ] Slogan đúng.
- [ ] Màu thương hiệu đúng.
- [ ] Font tiếng Việt local.
- [ ] Không weight giả.
- [ ] Desktop/tablet/mobile không overflow.
- [ ] Search/filter/sort hoạt động.
- [ ] `strict`, `balanced`, `broad` cập nhật count và kết quả đúng.
- [ ] `all` và `any` có nghĩa rõ và trả đúng tập.
- [ ] Card nêu lý do căn nhà khớp.
- [ ] Trang chi tiết có khối tiện ích quanh nhà.
- [ ] Có note “đường chim bay, không phải thời gian lái xe”.
- [ ] Mobile CTA filter rõ nghĩa, badge và ARIA đúng.
- [ ] Lightbox hoạt động.

### Quyền riêng tư

- [ ] Không email.
- [ ] Không portal token.
- [ ] Không ViewState.
- [ ] Không URL nguồn riêng tư trong tài liệu công khai.

### Kiểm thử

- [ ] Build pass.
- [ ] Python syntax pass.
- [ ] JavaScript syntax pass.
- [ ] Playwright desktop pass.
- [ ] Playwright mobile pass.
- [ ] Count chip đại diện được assert.
- [ ] Tập giao `all` và tập hợp `any` được assert.
- [ ] Clear filter khôi phục toàn bộ listing.
- [ ] Sticky/mobile drawer không làm layout nhảy hoặc overflow.
- [ ] Tất cả trang chi tiết pass.
- [ ] Console/page errors bằng 0.

### Git

- [ ] Chỉ stage file có chủ ý.
- [ ] `git diff --cached --check` pass.
- [ ] Commit thành công.
- [ ] Push thành công.
- [ ] Branch khớp remote.

---

## 11. Definition of Done

Tác vụ chỉ hoàn thành khi:

1. Số trang con bằng số listing nguồn.
2. Mỗi trang con hiển thị đúng căn nhà của nó.
3. Toàn bộ nội dung cần thiết đã được Việt hóa và hiệu đính.
4. Diện tích có quy đổi m² chính xác.
5. Mỗi căn có insight vị trí được tính từ geocode và dữ liệu tiện ích có nguồn.
6. Snapshot vị trí ghi rõ ngày, phương pháp, ngưỡng, đơn vị và giới hạn.
7. Filter theo nhu cầu trả kết quả đúng ở `strict`, `balanced`, `broad`,
   `all` và `any`, đồng thời giải thích được lý do.
8. Không có suy đoán nhân khẩu học hoặc lời hứa sai về thời gian di chuyển.
9. Ảnh được lưu cục bộ và kiểm tra toàn vẹn.
10. Giao diện đúng thương hiệu và responsive.
11. Font tiếng Việt hiển thị đồng nhất.
12. Build có thể tái chạy từ dữ liệu trong repo.
13. Toàn bộ test tự động pass.
14. Không có PII hoặc token nguồn trong artifact công khai.
15. Nếu người dùng yêu cầu Git: commit và push đã được remote xác nhận.

---

## 12. Tóm tắt tư duy cho Agent

Đừng bắt đầu bằng cách sao chép HTML. Hãy coi portal như một API chưa được tài liệu hóa:

```text
Portal động
  → session + POST navigation
  → dữ liệu thô
  → dữ liệu chuẩn hóa
  → đọc tín hiệu vị trí trong MLS
  → geocode + POI/đường có provenance
  → khoảng cách/mật độ + cờ filter
  → dịch có bảo vệ đơn vị
  → glossary + biên tập
  → ảnh cục bộ
  → build tĩnh + filter giải thích được
  → test dữ liệu + desktop + mobile + toàn bộ trang con
  → commit có chọn lọc
```

Mỗi pha phải tạo bằng chứng kiểm tra được. Nếu không thể chứng minh đã lấy đủ
listing, hiểu đúng dữ kiện từng căn, research vị trí từ nguồn hợp lệ, tính đúng
khoảng cách/mật độ, dịch đúng đơn vị, tải đủ ảnh, filter đúng tập kết quả và mở
được mọi trang con, chưa được coi là xong.
