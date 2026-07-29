#!/usr/bin/env python3
"""Build the static Nhà Mỹ Cali website from translated MLS JSON."""

from __future__ import annotations

import argparse
import html
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SECTION_NAMES = {
    "General Description": "Thông tin chung",
    "Interior": "Nội thất",
    "Exterior": "Ngoại thất",
    "Additional Information": "Thông tin bổ sung",
}
LABELS = {
    "Beds Total": "Tổng số phòng ngủ",
    "Baths Total": "Tổng số phòng tắm",
    "Baths Full": "Phòng tắm đầy đủ",
    "Baths Half": "Phòng vệ sinh phụ",
    "Sq Ft Total": "Diện tích sử dụng",
    "Structure Size Source": "Nguồn số liệu diện tích nhà",
    "Secondary Living Space Description (ADU)": "Mô tả nhà ở phụ (ADU)",
    "Secondary Living Space Sq Ft": "Diện tích nhà ở phụ",
    "Apprx Lot": "Diện tích lô đất xấp xỉ",
    "Apprx Acres": "Diện tích theo mẫu Anh",
    "Age": "Tuổi công trình",
    "Year Built": "Năm xây dựng",
    "Parcel Number": "Mã thửa đất",
    "DOM": "Số ngày trên thị trường",
    "Walk Score": "Điểm thuận tiện đi bộ",
    "County": "Quận",
    "Land Use County": "Mục đích sử dụng đất",
    "Property Sub Type": "Phân loại bất động sản",
    "Building Type": "Kiểu công trình",
    "Additional Listing Info/ Special Info": "Thông tin rao bán đặc biệt",
    "City Limits YN": "Nằm trong địa giới thành phố",
    "City Transfer Tax YN": "Có thuế chuyển nhượng thành phố",
    "Incorporated Y/N": "Thuộc khu vực hợp nhất",
    "Green Rated YN": "Chứng nhận công trình xanh",
    "Building Height Min": "Chiều cao công trình tối thiểu",
    "Zoning": "Quy hoạch",
    "Original List Price": "Giá rao bán ban đầu",
    "List Price": "Giá đang rao bán",
    "Price/SqFt": "Đơn giá mỗi ft²",
    "Original List Date": "Ngày rao bán ban đầu",
    "Listing Date": "Ngày rao bán",
    "Elem": "Trường tiểu học",
    "Middle School": "Trường trung học cơ sở",
    "High": "Trường trung học",
    "Bathroom": "Phòng tắm",
    "Bedrooms": "Phòng ngủ",
    "Cooling": "Hệ thống làm mát",
    "Heating": "Hệ thống sưởi",
    "Dining Room": "Phòng ăn",
    "Family Room": "Phòng sinh hoạt gia đình",
    "Fireplace": "Lò sưởi",
    "Flooring": "Sàn",
    "Amenities Misc": "Tiện nghi khác",
    "Kitchen": "Nhà bếp",
    "Laundry": "Khu giặt",
    "Other Rooms": "Phòng khác",
    "Communications": "Hạ tầng liên lạc",
    "Construction Type": "Loại kết cấu",
    "Yard Grounds": "Sân vườn",
    "Foundation": "Móng",
    "Garage Spaces": "Số chỗ đậu xe trong gara",
    "Parking Spaces": "Tổng số chỗ đậu xe",
    "Parking Features": "Hình thức đậu xe",
    "Carport Min": "Số chỗ đậu xe có mái che",
    "Horse Property": "Bất động sản phù hợp nuôi ngựa",
    "Horse Property Features": "Tiện ích dành cho ngựa",
    "Lot Description": "Đặc điểm lô đất",
    "Property Condition": "Tình trạng bất động sản",
    "Pool": "Hồ bơi",
    "Roof": "Mái",
    "Style": "Phong cách kiến trúc",
    "View": "Tầm nhìn",
    "Sewer Septic": "Thoát nước / bể tự hoại",
    "Water": "Nguồn nước",
    "Utilities": "Tiện ích công cộng",
    "HOA Fee": "Phí hiệp hội chủ nhà (HOA)",
    "HOA Fee Frequency": "Chu kỳ thu phí HOA",
    "HOA Name Text": "Tên hiệp hội chủ nhà",
    "HOA Phone": "Điện thoại HOA",
    "Listed By": "Môi giới niêm yết",
    "Co List By": "Đồng môi giới niêm yết",
}
EXACT_VALUES = {
    "Active": "Đang rao bán",
    "Yes": "Có",
    "No": "Không",
    "None": "Không có",
    "Other": "Khác",
    "Not Applicable": "Không áp dụng",
    "Assessor": "Cơ quan định giá thuế",
    "Detached": "Nhà đơn lập",
    "Attached": "Nhà liền kề",
    "Res. Single Family": "Nhà ở đơn lập cho một gia đình",
    "SFR": "Nhà ở đơn lập cho một gia đình",
    "Public": "Công cộng",
    "Central AC": "Điều hòa trung tâm",
    "Central Forced Air": "Sưởi không khí cưỡng bức trung tâm",
    "Central Forced Air - Gas": "Sưởi không khí cưỡng bức trung tâm dùng gas",
    "Forced Air": "Sưởi không khí cưỡng bức",
    "Attached Garage": "Gara liền nhà",
    "Separate Family Room": "Phòng sinh hoạt gia đình riêng",
    "Kitchen/Family Room Combo": "Bếp liền phòng sinh hoạt gia đình",
    "Formal Room": "Phòng ăn trang trọng",
    "Dining Area": "Khu vực ăn uống",
    "Composition": "Tấm lợp composite",
    "Tile": "Ngói",
    "Concrete Slab": "Sàn móng bê tông",
    "Concrete Perimeter": "Móng bê tông chu vi",
    "Concrete Perimeter and Slab": "Móng bê tông chu vi và sàn bê tông",
    "Crawl Space": "Khoảng trống kỹ thuật dưới sàn",
    "Wood Frame": "Khung gỗ",
    "Monthly": "Hàng tháng",
    "Neighborhood": "Khu dân cư",
}
TECHNICAL_FIXES = {
    "Nhà để xe": "Gara",
    "nhà để xe": "gara",
    "Garage": "Gara",
    "Ga-ra": "Gara",
    "Đảo có bồn rửa": "Đảo bếp có bồn rửa",
    "Đảo": "Đảo bếp",
    "Xử lý rác": "Máy nghiền rác thực phẩm",
    "Máy hút mùi": "Máy hút mùi trên bếp",
    "Phòng gia đình": "Phòng sinh hoạt gia đình",
    "phòng gia đình": "phòng sinh hoạt gia đình",
    "Không quân cưỡng bức miền Trung": "Sưởi không khí cưỡng bức trung tâm",
    "không khí cưỡng bức trung tâm": "Sưởi không khí cưỡng bức trung tâm",
    "Khí cưỡng bức trung tâm": "Sưởi không khí cưỡng bức trung tâm",
    "Cây phong": "Gỗ cứng",
    "Vâng - Đã chia sẻ": "Giếng nước dùng chung",
    "Vòi phun nước - Xe ô tô": "Hệ thống tưới tự động",
    "bình tưới - Ôtô": "hệ thống tưới tự động",
    "Phòng tắm bùn": "Phòng mudroom",
    "Ban công/Hiên": "Ban công / sân hiên",
    "Ban công/sân hiên": "Ban công / sân hiên",
    "Hàng rào": "Có hàng rào",
    "Trên đường": "Đậu xe trên phố",
    "Bãi đậu xe ngoài đường": "Bãi đậu xe bên ngoài",
    "Đồng hồ nước cá nhân": "Đồng hồ nước riêng",
    "Đồng hồ điện cá nhân": "Đồng hồ điện riêng",
    "Đồng hồ đo gas cá nhân": "Đồng hồ gas riêng",
    "Âm thanh/Video có sẵn": "Đi dây sẵn âm thanh / video",
    "Nối mạng": "Hệ thống mạng",
    "Dãy lò nướng - Gas": "Bếp gas kèm lò nướng",
    "Lò nướng - Âm tường": "Lò nướng âm tủ",
    "Lò nướng - Tích hợp": "Lò nướng âm tủ",
    "Phòng đựng thức ăn": "Tủ / phòng đựng thực phẩm",
    "Khu vực nướng thịt": "Khu BBQ",
    "Wet Bar": "Quầy bar có bồn rửa",
    "Quầy Wet": "Quầy bar có bồn rửa",
}


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")


def parse_number(value: str) -> float | None:
    match = re.search(r"[\d,.]+", value)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def vi_number(value: float, decimals: int = 1) -> str:
    text = f"{value:,.{decimals}f}" if decimals else f"{value:,.0f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def area_value(value: str, acres: bool = False) -> str:
    number = parse_number(value)
    if number is None:
        return value
    if acres:
        return f"{vi_number(number, 3)} mẫu Anh (≈ {vi_number(number * 4046.8564224, 1)} m²)"
    suffix = ""
    if "(Tax)" in value:
        suffix = " · nguồn: hồ sơ thuế"
    elif "(Other)" in value:
        suffix = " · nguồn khác"
    return f"{vi_number(number, 0)} ft² (≈ {vi_number(number * 0.092903, 1)} m²){suffix}"


def clean_technical(value: str) -> str:
    output = value.replace("Â®", "®").replace("\u200b", "").strip()
    for source, target in TECHNICAL_FIXES.items():
        output = output.replace(source, target)
    output = re.sub(r"\s+([,.;:])", r"\1", output)
    return output


def translated_value(item: dict, section: str, label: str, value: str) -> str:
    if label in {"Elem", "Middle School", "High"}:
        name, _, district = value.partition("·")
        school = name.strip().lstrip("/").strip()
        district = district.strip().lstrip("/").strip()
        if not district and value.strip().startswith("/"):
            district = school
            school = ""
        if school and district:
            return f"{school} · Học khu {district}"
        if district:
            return f"Học khu {district}"
        return school or "Không có dữ liệu"
    if label in {"Sq Ft Total", "Apprx Lot", "Secondary Living Space Sq Ft"}:
        return area_value(value)
    if label == "Apprx Acres":
        return area_value(value, acres=True)
    if label == "Price/SqFt":
        number = parse_number(value)
        if number is not None:
            return (
                f"{vi_number(number, 2)} USD/ft² "
                f"(≈ {vi_number(number / 0.092903, 2)} USD/m²)"
            )
    if value.startswith("$"):
        return value.replace("$", "") + " USD"
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", value):
        month, day, year = value.split("/")
        return f"{day}/{month}/{year}"
    if value in EXACT_VALUES:
        return EXACT_VALUES[value]
    draft = item.get("sections_translated", {}).get(section, {}).get(value, value)
    return clean_technical(draft)


def prepare_listing(source: dict, location_insight: dict) -> dict:
    item = dict(source)
    index = int(item["index"])
    item["slug"] = f"{index + 1:02d}-{slugify(item['address'])}"
    item["detail_url"] = f"listings/{item['slug']}.html"
    item["city_vi"] = item["city"]
    item["status_vi"] = EXACT_VALUES.get(item["status"], item["status"])
    sqft = parse_number(item["sqft"]) or 0
    lot = parse_number(item["lot"]) or 0
    item["sqft_m2"] = vi_number(sqft * 0.092903, 1)
    item["lot_m2"] = vi_number(lot * 0.092903, 1)
    item["sqft_display"] = vi_number(sqft, 0)
    item["lot_display"] = vi_number(lot, 0)
    item["price_number"] = int(re.sub(r"\D", "", item["price"]) or 0)
    item["sqft_number"] = int(sqft)
    item["beds_number"] = float(parse_number(item["bedrooms"]) or 0)
    item["baths_number"] = float(parse_number(item["bathrooms"]) or 0)
    item["location"] = {
        "amenities": location_insight["amenities"],
        "matches": location_insight["matches"],
        "summary_vi": location_insight["location_summary_vi"],
        "mls_evidence_categories": location_insight["mls_evidence_categories"],
    }
    item["sections_vi"] = []
    for section, pairs in item["sections"].items():
        item["sections_vi"].append(
            {
                "name": SECTION_NAMES.get(section, section),
                "fields": [
                    {
                        "label": LABELS.get(label, label),
                        "value": translated_value(item, section, label, value),
                    }
                    for label, value in pairs
                ],
            }
        )
    item["images"] = [
        f"assets/properties/{item['mls'].lower()}/{number:03d}.jpg"
        for number, _ in enumerate(item["images"], 1)
    ]
    for unused in (
        "key",
        "description",
        "sections",
        "sections_translated",
        "visible_text_count",
    ):
        item.pop(unused, None)
    return item


def json_for_script(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")


def index_page(count: int, city_count: int, minimum: int, maximum: int) -> str:
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0041b0">
  <meta name="description" content="{count} căn nhà cao cấp tại Silicon Valley, được Nhà Mỹ Cali biên soạn bằng tiếng Việt.">
  <title>{count} căn nhà cao cấp tại Silicon Valley | Nhà Mỹ Cali</title>
  <link rel="icon" href="NhaMyCai_logo.png" type="image/png">
  <link rel="stylesheet" href="assets/css/styles.css">
</head>
<body data-page="results">
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="index.html" aria-label="Nhà Mỹ Cali - Trang chủ">
        <img src="NhaMyCai_logo.png" alt="Nhà Mỹ Cali">
        <span><strong>Nhà Mỹ Cali</strong><small>Giúp người Việt an tâm mua nhà Mỹ</small></span>
      </a>
      <nav class="header-nav" aria-label="Điều hướng chính">
        <a class="active" href="#danh-sach">Danh sách nhà</a>
        <a href="#huong-dan">Hướng dẫn</a>
      </nav>
    </div>
  </header>
  <main>
    <section class="hero">
      <div class="hero-inner">
        <div class="hero-copy">
          <p class="eyebrow">Tuyển chọn tại Silicon Valley, California</p>
          <h1>{count} căn nhà dành cho bạn</h1>
          <p>Danh sách trải rộng qua {city_count} thành phố, với mức giá từ {minimum / 1_000_000:.2f} đến {maximum / 1_000_000:.2f} triệu USD. Toàn bộ thông tin được trình bày bằng tiếng Việt và có quy đổi diện tích sang mét vuông.</p>
        </div>
        <div class="hero-stat" aria-label="Tổng số bất động sản"><strong>{count}</strong><span>bất động sản</span></div>
      </div>
    </section>
    <section class="search-panel" aria-label="Tìm và lọc bất động sản">
      <div class="search-wrap">
        <label class="search-box">
          <span class="sr-only">Tìm theo địa chỉ, khu vực hoặc mã MLS</span>
          <svg aria-hidden="true" viewBox="0 0 24 24"><path d="m21 21-4.35-4.35m2.35-5.65A8 8 0 1 1 3 11a8 8 0 0 1 16 0Z"/></svg>
          <input id="searchInput" type="search" placeholder="Tìm địa chỉ, khu vực hoặc mã MLS…">
        </label>
        <select id="bedsFilter" aria-label="Lọc theo số phòng ngủ">
          <option value="0">Tất cả số phòng ngủ</option>
          <option value="4">Từ 4 phòng ngủ</option>
          <option value="5">Từ 5 phòng ngủ</option>
          <option value="6">Từ 6 phòng ngủ</option>
        </select>
        <select id="priceFilter" aria-label="Lọc theo mức giá">
          <option value="all">Tất cả mức giá</option>
          <option value="under3300">Dưới 3,3 triệu USD</option>
          <option value="3300to3700">3,3–3,7 triệu USD</option>
          <option value="over3700">Trên 3,7 triệu USD</option>
        </select>
        <select id="sortSelect" aria-label="Sắp xếp danh sách">
          <option value="default">Thứ tự từ MLS</option>
          <option value="location-fit">Phù hợp vị trí nhất</option>
          <option value="price-desc">Giá cao đến thấp</option>
          <option value="price-asc">Giá thấp đến cao</option>
          <option value="area-desc">Diện tích lớn đến nhỏ</option>
        </select>
        <div class="amenity-filter" id="amenityFilter">
          <div class="amenity-filter-head">
            <div>
              <strong>Lọc thông minh theo vị trí & tiện ích</strong>
              <span>Chọn nhiều tiêu chí để tìm căn phù hợp với sinh hoạt hằng ngày.</span>
            </div>
            <button id="clearFilters" type="button">Xóa bộ lọc</button>
          </div>
          <div class="amenity-controls">
            <label>
              <span>Mức độ gần</span>
              <select id="proximityMode" aria-label="Chọn mức độ gần">
                <option value="strict">Rất gần</option>
                <option value="balanced" selected>Gần, hợp lý</option>
                <option value="broad">Mở rộng bán kính</option>
              </select>
            </label>
            <label>
              <span>Cách kết hợp</span>
              <select id="amenityLogic" aria-label="Cách kết hợp tiện ích">
                <option value="all">Đáp ứng tất cả</option>
                <option value="any">Đáp ứng ít nhất một</option>
              </select>
            </label>
          </div>
          <div class="amenity-chips" aria-label="Chọn tiện ích gần nhà">
            <button type="button" data-amenity="vietnamese_community"><span>Gần khu người Việt</span><b>0</b></button>
            <button type="button" data-amenity="lake"><span>Gần hồ nước</span><b>0</b></button>
            <button type="button" data-amenity="coast"><span>Gần biển</span><b>0</b></button>
            <button type="button" data-amenity="highway"><span>Gần cao tốc</span><b>0</b></button>
            <button type="button" data-amenity="park"><span>Gần công viên</span><b>0</b></button>
            <button type="button" data-amenity="restaurants"><span>Nhiều nhà hàng gần</span><b>0</b></button>
            <button type="button" data-amenity="shopping"><span>Gần mua sắm</span><b>0</b></button>
            <button type="button" data-amenity="transit"><span>Gần ga / transit</span><b>0</b></button>
          </div>
          <p class="filter-method" id="filterMethod">
            “Gần” dùng khoảng cách đường chim bay với ngưỡng riêng cho từng tiện ích.
          </p>
        </div>
      </div>
    </section>
    <section class="results-section" id="danh-sach">
      <div class="section-heading">
        <div><p class="eyebrow">Danh sách bất động sản</p><h2><span id="resultCount">{count}</span> căn phù hợp</h2></div>
        <p class="area-note">Khoảng cách tiện ích là đường chim bay, không phải thời gian lái xe. Dữ liệu bản đồ: <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors, ODbL</a>.</p>
      </div>
      <div class="listing-grid" id="listingGrid" aria-live="polite"></div>
      <div class="empty-state" id="emptyState" hidden><strong>Không tìm thấy căn nhà phù hợp.</strong><span>Hãy thử thay đổi từ khóa hoặc bộ lọc.</span></div>
    </section>
    <section class="guide" id="huong-dan">
      <div><p class="eyebrow">Cách sử dụng</p><h2>Thông tin rõ ràng, xem nhà dễ hơn</h2></div>
      <ol>
        <li><strong>1</strong><span>Tìm và lọc theo nhu cầu.</span></li>
        <li><strong>2</strong><span>Nhấp vào căn nhà để xem trang chi tiết.</span></li>
        <li><strong>3</strong><span>Dùng thư viện ảnh, thông số và liên kết bản đồ để đánh giá.</span></li>
      </ol>
    </section>
  </main>
  <footer class="site-footer">
    <img src="NhaMyCai_logo.png" alt="">
    <p><strong>Nhà Mỹ Cali</strong> · Giúp người Việt an tâm mua nhà Mỹ.</p>
    <p class="disclaimer">Dữ liệu MLS có thể thay đổi; người mua cần xác minh trước khi giao dịch. Tọa độ từ <a href="https://www.census.gov/programs-surveys/geography/technical-documentation/complete-technical-documentation/census-geocoder.html" target="_blank" rel="noopener">U.S. Census Geocoder</a>; dữ liệu đường và địa điểm <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors, ODbL</a>.</p>
  </footer>
  <script src="assets/js/listings-data.js"></script>
  <script src="assets/js/site.js"></script>
</body>
</html>
"""


def detail_page(item: dict) -> str:
    title = html.escape(f"{item['address']} | Nhà Mỹ Cali")
    description = html.escape(item["description_vi"][:155])
    return f"""<!doctype html>
<html lang="vi">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#0041b0">
  <meta name="description" content="{description}">
  <title>{title}</title>
  <link rel="icon" href="../NhaMyCai_logo.png" type="image/png">
  <link rel="stylesheet" href="../assets/css/styles.css">
</head>
<body data-page="detail" data-listing-index="{item['index']}">
  <header class="site-header">
    <div class="header-inner">
      <a class="brand" href="../index.html" aria-label="Nhà Mỹ Cali - Trang chủ">
        <img src="../NhaMyCai_logo.png" alt="Nhà Mỹ Cali">
        <span><strong>Nhà Mỹ Cali</strong><small>Giúp người Việt an tâm mua nhà Mỹ</small></span>
      </a>
      <nav class="header-nav" aria-label="Điều hướng chính">
        <a href="../index.html#danh-sach">Danh sách nhà</a>
        <a class="active" href="#chi-tiet">Chi tiết</a>
      </nav>
    </div>
  </header>
  <main id="detailRoot"></main>
  <footer class="site-footer detail-footer">
    <img src="../NhaMyCai_logo.png" alt="">
    <p><strong>Nhà Mỹ Cali</strong> · Giúp người Việt an tâm mua nhà Mỹ.</p>
    <p class="disclaimer">Thông tin và số đo do bên niêm yết cung cấp. Người mua cần tự xác minh trước khi giao dịch.</p>
  </footer>
  <script src="../assets/js/listings-data.js"></script>
  <script src="../assets/js/site.js"></script>
</body>
</html>
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument(
        "--locations",
        type=Path,
        default=ROOT / "data" / "location-insights.json",
    )
    args = parser.parse_args()
    source = json.loads(args.source.read_text(encoding="utf-8"))
    location_data = json.loads(args.locations.read_text(encoding="utf-8"))
    if source.get("errors"):
        raise SystemExit(f"Source contains {len(source['errors'])} scrape errors")
    location_by_mls = location_data["listings"]
    listings = [
        prepare_listing(item, location_by_mls[item["mls"]])
        for item in source["listings"]
    ]
    expected = source["source"]["listing_count"]
    if len(listings) != expected:
        raise SystemExit(f"Expected {expected} listings, found {len(listings)}")
    if len({item["mls"] for item in listings}) != len(listings):
        raise SystemExit("Duplicate MLS IDs detected")

    (ROOT / "assets" / "js").mkdir(parents=True, exist_ok=True)
    (ROOT / "data").mkdir(parents=True, exist_ok=True)
    target = ROOT / "listings"
    target.mkdir(parents=True, exist_ok=True)
    for stale in target.glob("*.html"):
        stale.unlink()

    final_data = {
        "source": {
            "name": "MLSListings Matrix Portal",
            "snapshot_date": source["source"]["snapshot_date"],
            "listing_count": len(listings),
            "location_snapshot_date": location_data["snapshot_date"],
            "location_methodology": location_data["methodology"],
        },
        "listings": listings,
    }
    (ROOT / "assets" / "js" / "listings-data.js").write_text(
        f"window.NHA_MY_CALI_LISTINGS={json_for_script(listings)};\n",
        encoding="utf-8",
    )
    (ROOT / "data" / "listings.json").write_text(
        json.dumps(final_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    cities = {item["city"].split(",")[0] for item in listings}
    prices = [item["price_number"] for item in listings]
    (ROOT / "index.html").write_text(
        index_page(len(listings), len(cities), min(prices), max(prices)),
        encoding="utf-8",
    )
    for item in listings:
        (target / f"{item['slug']}.html").write_text(detail_page(item), encoding="utf-8")
    print(f"Built index + {len(listings)} detail pages")


if __name__ == "__main__":
    main()
