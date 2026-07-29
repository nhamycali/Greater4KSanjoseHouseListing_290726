#!/usr/bin/env python3
"""Translate normalized MLS data to Vietnamese with protected measurements."""

from __future__ import annotations

import argparse
import concurrent.futures
import html
import json
import re
import threading
import time
from pathlib import Path

import requests


ROOT = Path(__file__).resolve().parents[1]
TRANSLATE_URL = "https://translate.googleapis.com/translate_a/single"
THREAD_LOCAL = threading.local()

NO_TRANSLATE_LABELS = {
    "Parcel Number",
    "Zoning",
    "County",
    "Listed By",
    "Co List By",
    "HOA Name Text",
    "HOA Phone",
    "Elem",
    "Middle School",
    "High",
}

EXACT_VALUES = {
    "Active": "Đang rao bán",
    "New Listing": "Tin mới",
    "List Price Decreased": "Đã giảm giá rao bán",
    "Not yet available for viewing appointments": "Chưa nhận lịch hẹn xem nhà",
    "Yes": "Có",
    "No": "Không",
    "None": "Không có",
    "Other": "Khác",
    "Not Applicable": "Không áp dụng",
    "Detached": "Nhà đơn lập",
    "Attached": "Nhà liền kề",
    "Public": "Công cộng",
    "Assessor": "Cơ quan định giá thuế",
    "Res. Single Family": "Nhà ở đơn lập cho một gia đình",
    "SFR": "Nhà ở đơn lập cho một gia đình",
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

PROTECTED_TERMS = (
    "Sub-Zero",
    "Thermador",
    "Porcelanosa",
    "HomeLight",
    "Caltrain",
    "Willow Glen",
    "San Jose",
    "Morgan Hill",
    "San Martin",
    "Gilroy",
    "Campbell",
    "Milpitas",
    "Santa Clara",
    "Viking",
    "Wolf",
    "Bosch",
    "Pella",
    "Carrier",
    "Google Nest",
    "ADU",
    "HOA",
    "MLS",
    "EV",
    "LVP",
    "escrow",
)

POST_EDITS = {
    "dãy phòng chính": "suite phòng ngủ chính",
    "phòng chính": "phòng ngủ chính",
    "nhà để xe": "gara",
    "ga-ra": "gara",
    "hòn đảo bếp": "đảo bếp",
    "hòn đảo": "đảo bếp",
    "máy rửa bát": "máy rửa chén",
    "máy rửa chén bát": "máy rửa chén",
    "phòng gia đình": "phòng sinh hoạt gia đình",
    "không khí cưỡng bức": "không khí cưỡng bức",
    "đi bộ trong tủ quần áo": "tủ quần áo không cửa ngăn",
    "tủ quần áo đi bộ": "tủ quần áo không cửa ngăn",
    "bếp của đầu bếp": "bếp dành cho người yêu nấu nướng",
    "nhà bếp của đầu bếp": "bếp dành cho người yêu nấu nướng",
    "năng lượng mặt trời thuộc sở hữu": "hệ thống điện mặt trời sở hữu riêng",
    "tấm pin mặt trời thuộc sở hữu": "tấm pin mặt trời sở hữu riêng",
    "ngõ cụt": "đường cụt",
    "sức hấp dẫn lề đường": "mặt tiền thu hút",
    "bể bơi trong lòng đất": "hồ bơi âm đất",
    "bể bơi": "hồ bơi",
    "phòng bột": "phòng vệ sinh phụ",
    "phòng tắm nửa": "phòng vệ sinh phụ",
    "phòng tắm đầy đủ": "phòng tắm đầy đủ",
    "mái hiên bao quanh": "hiên nhà bao quanh",
    "kế hoạch sàn": "mặt bằng",
    "sơ đồ tầng": "mặt bằng",
    "thác nước": "kiểu waterfall",
    "đảo giải trí": "đảo bếp phục vụ tiếp khách",
    "nhà khách": "nhà dành cho khách",
    "tài sản": "bất động sản",
    "nơi nghỉ": "bất động sản",
    "chỗ nghỉ": "bất động sản",
    "cơ hội bán trước": "cơ hội mua trước khi hoàn thiện",
    "sơ đồ mặt bằng theo phong cách mở": "mặt bằng mở",
    "sơ đồ mặt bằng": "mặt bằng",
    "kế hoạch sàn": "mặt bằng",
    "suite chính": "suite phòng ngủ chính",
    "dãy phòng sơ cấp cơ sở": "suite phòng ngủ chính ở tầng trệt",
    "dãy phòng riêng dành cho khách": "suite dành cho khách",
    "dãy phòng dành cho khách": "suite dành cho khách",
    "dãy phòng ngủ": "suite phòng ngủ",
    "phòng thưởng": "phòng đa năng",
    "phòng trò chơi": "phòng giải trí",
    "phòng bột": "phòng vệ sinh phụ",
    "bồn tắm nắng": "phòng tắm nắng",
    "căn phòng lớn": "phòng sinh hoạt chung",
    "phòng lớn lớn": "phòng sinh hoạt chung rộng rãi",
    "nhà bếp ăn uống": "bếp có khu vực ăn uống",
    "nhà bếp sành điệu": "bếp cao cấp",
    "nhà bếp dành cho người sành ăn": "bếp cao cấp",
    "nhà bếp ẩm thực": "bếp dành cho người yêu nấu nướng",
    "đầu bếp kén chọn nhất": "người yêu nấu nướng kỹ tính nhất",
    "người sành ăn": "người yêu nấu nướng",
    "nghệ sĩ giải trí": "người thích tiếp khách",
    "thiên đường của một người thích tiếp khách": "không gian lý tưởng để tiếp khách",
    "luồng không khí trong nhà-ngoài trời": "sự kết nối liền mạch giữa trong nhà và ngoài trời",
    "luồng không khí trong nhà và ngoài trời": "sự kết nối liền mạch giữa trong nhà và ngoài trời",
    "đi bộ trong tủ quần áo": "tủ quần áo không cửa ngăn",
    "tủ quần áo đi bộ": "tủ quần áo không cửa ngăn",
    "tủ lạnh đựng rượu": "tủ rượu vang",
    "tủ lạnh chứa rượu": "tủ rượu vang",
    "bồn tắm giống như spa": "phòng tắm phong cách spa",
    "bồn tắm kiểu spa": "phòng tắm phong cách spa",
    "bồn tắm lấy cảm hứng từ spa": "phòng tắm phong cách spa",
    "bồn tắm spa": "phòng tắm phong cách spa",
    "ngôi nhà chìa khóa trao tay": "ngôi nhà hoàn thiện, sẵn sàng dọn vào ở",
    "kiệt tác chìa khóa trao tay": "căn nhà hoàn thiện, sẵn sàng dọn vào ở",
    "người mua để xác minh": "người mua cần xác minh",
    "được quản lý cẩn thận": "được chọn lọc kỹ lưỡng",
    "được quản lý chu đáo": "được chọn lọc kỹ lưỡng",
    "được cập nhật được": "đã được nâng cấp",
    "một tìm kiếm đáng yêu": "một lựa chọn đáng giá",
    "thật là một tìm kiếm đáng yêu": "một lựa chọn thật đáng giá",
    "không thải carbon": "phát thải carbon bằng 0",
    "hệ thống dây điện sẵn sàng cho EV": "hệ thống dây điện chờ sạc EV",
    "EV sẵn sàng": "sẵn sàng cho EV",
    "ổ cắm sạc EV": "đầu chờ sạc EV",
    "nhà kho 6 tầng": "chuồng ngựa 6 ô",
    "phòng đóng hộp": "phòng bảo quản thực phẩm",
    "làm nhà trẻ": "làm phòng em bé",
    "vườn nho đơn lẻ": "vườn nho riêng",
    "đảo bếp thùng": "đảo quầy bar",
    "bóng ném": "pickleball",
    "Feng Shai": "phong thủy",
    "cổ phần công nghệ": "cổ phiếu công nghệ",
    "hoàn lại tiền thuê": "ở lại sau giao dịch",
    "Ưu đãi đến hạn": "Hạn nhận đề nghị mua",
    "các kết xuất": "hình ảnh phối cảnh",
    "thuộc tính chủ đề": "bất động sản đang rao bán",
    "không mô tả tài sản chủ thể": "không nhất thiết phản ánh chính xác căn nhà đang rao bán",
    "không mô tả thuộc tính chủ đề": "không nhất thiết phản ánh chính xác căn nhà đang rao bán",
    "ĐỘC QUYỀN VIEW NHÀ": "NHÀ CÓ TẦM NHÌN ĐẸP",
    "trên mặt đất": "ở tầng trệt",
    "cống riêng": "đường cụt riêng",
    "được neo đậu": "được kết nối",
    "không dùng bình": "không bình chứa",
    "phòng tắm nửa": "phòng vệ sinh phụ",
}

DESCRIPTION_FIXES = {
    "ML82043080": {
        "Di sản lịch sử hiếm có này Trang trại Dunne":
            "Khu điền trang lịch sử hiếm có Dunne Ranch này",
        "một khu phức hợp gia đình tư nhân":
            "một khuôn viên gia đình riêng",
        "phòng bảo quản thực phẩm":
            "phòng bảo quản đồ đóng hộp",
        "những điểm nhấn bằng kính màu":
            "các ô kính màu",
    },
    "ML82044063": {
        "4320 Virginia Ave.": "432 Virginia Avenue",
        "có thời gian vui vẻ": "tiếp khách",
        "bồn tắm kiểu spa": "phòng tắm phong cách spa",
        "bổ sung thêm về": "có thêm khoảng",
    },
    "ML82029605": {
        "Cottage dành cho khách biệt lập": "Nhà nhỏ dành cho khách biệt lập",
        "Những tài sản tầm cỡ này không chỉ được mua - chúng còn được bảo mật.":
            "Những bất động sản tầm cỡ này hiếm khi xuất hiện trên thị trường.",
    },
    "ML82045273": {
        "Sân sau mơ ước của người thích tiếp khách":
            "Sân sau lý tưởng để tiếp khách",
        "những cây nho, nho, rượu vang của bạn":
            "mang đến cơ hội làm rượu vang riêng",
        "Một đảo quầy bar với bồn rửa bằng đồng":
            "Quầy bar trung tâm có bồn rửa bằng đồng",
    },
    "ML82034271": {
        "Nhà bếp dành cho người sành ăn": "Bếp dành cho người yêu nấu nướng",
        "phòng làm việc hoặc phòng làm việc riêng":
            "phòng làm việc riêng",
    },
    "ML82041742": {
        "Cung cấp khoảng.": "Có khoảng",
        "dãy phòng sơ cấp cơ sở ở tầng chính":
            "suite phòng ngủ chính ở tầng trệt",
        "gara 600+ ft²": "gara rộng hơn 600 ft²",
        "một chiếc Tudor": "một căn nhà Tudor",
    },
    "ML82055376": {
        "có 5BR, 3,5 BA": "có 5 phòng ngủ, 3,5 phòng tắm",
        "ngôi nhà xa nhất": "căn có tiến độ thi công cao nhất",
    },
    "ML82054319": {
        "bóng ném": "pickleball",
        "Feng Shai": "phong thủy",
        "Người mua để xác minh": "Người mua cần xác minh",
    },
    "ML82038101": {
        "TRANG TRẠI BORELLO": "BORELLO RANCH",
        "được nhiều người thèm muốn": "được nhiều người ưa chuộng",
        "Phòng ngủ chính rộng rãi": "Suite phòng ngủ chính rộng rãi",
    },
    "ML82046737": {
        "bồn tắm được nâng cấp": "phòng tắm đã nâng cấp",
        "Nơi nghỉ này": "Bất động sản này",
    },
    "ML82047622": {
        "phụ kiện nồi": "vòi rót nước trên bếp",
        "giá treo khăn nóng": "thanh sưởi khăn",
        "tủ đựng đồ hơi nước": "tủ hấp quần áo",
    },
    "CRPW26111576": {
        "nhà bếp dành cho người giải trí": "bếp phục vụ tiếp khách",
        "khu mở rộng ADU": "phương án xây thêm ADU",
        "không bị chậm trễ trong việc thu hồi đất và lập kế hoạch thiết kế":
            "mà không phải bắt đầu lại từ khâu mua đất và thiết kế",
    },
    "ML82051861": {
        "không có trong sf đã nêu": "không tính trong diện tích công bố",
        "Nhà bếp tuyệt đẹp của đầu bếp": "Bếp đẹp dành cho người yêu nấu nướng",
        "dòng sản phẩm dân dụng lấy cảm hứng từ Thomas Kellers":
            "dòng thiết bị gia dụng cao cấp lấy cảm hứng từ Thomas Keller",
    },
    "ML82055283": {
        "bao gồm nhà bếp riêng ADU và lối vào phòng ngủ chính":
            "bao gồm ADU có bếp và lối vào riêng",
        "đảo bếp giải trí ngoại cỡ": "đảo bếp cỡ lớn phục vụ tiếp khách",
    },
    "ML82041024": {
        "căn phòng tuyệt vời": "phòng sinh hoạt chung",
        "năng lượng mặt trời riêng..": "hệ thống điện mặt trời sở hữu riêng.",
    },
    "ML82050614": {
        "khách hàng hoặc thu nhập cho thuê":
            "khách lưu trú hoặc tạo thu nhập cho thuê",
        "ADU kèm theo": "ADU liền nhà",
    },
    "ML82047799": {
        "Năm gara có thể chứa tối đa sáu phương tiện":
            "Khu gara 5 ô có thể chứa tối đa 6 xe",
        "vợ chồng": "gia đình nhiều thế hệ",
    },
    "ML82049870": {
        "Giường thứ 5/phòng đa năng": "Phòng ngủ thứ 5 / phòng đa năng",
        "nó có sân sau riêng tư khác thường":
            "căn nhà có sân sau riêng tư hiếm thấy",
    },
    "ML82049205": {
        "Vị trí lý tưởng chỉ cách trung tâm mua sắm, ăn uống và giải trí vài phút.":
            "Vị trí lý tưởng, chỉ cách khu mua sắm, ăn uống và giải trí vài phút.",
    },
    "ML82051868": {
        "kiệt tác một chủ sở hữu": "bất động sản chỉ qua một đời chủ",
        "khu bảo tồn này": "không gian riêng này",
    },
    "ML82051916": {
        "5 suite phòng ngủ, mỗi dãy phòng":
            "5 suite phòng ngủ, mỗi phòng",
    },
    "ML82049857": {
        "5 phòng ngủ, 3,5 phòng ngủ": "5 phòng ngủ, 3,5 phòng tắm",
        "Lựa chọn trường học xổ số tới Steindorf STEAM.":
            "Có thể đăng ký theo diện bốc thăm vào trường Steindorf STEAM.",
        "Bán AS-IS": "Bán theo hiện trạng (AS-IS)",
    },
    "ML82051518": {
        "Người thợ thủ công ở Công viên Naglee này":
            "Ngôi nhà Craftsman tại Naglee Park này",
        "Nhà bếp đảo rộng rãi": "Bếp rộng với đảo trung tâm",
    },
    "ML82050644": {
        "một khu vườn được xây dựng lại với những chậu cây":
            "khu vườn được cải tạo với các bồn cây",
        "bãi đậu xe RV & Thuyền": "chỗ đậu RV và thuyền",
    },
    "ML82051509": {
        "tòa nhà hoàn toàn mới": "ngôi nhà xây mới hoàn toàn",
        "ADU cấp cơ sở cấp chính": "ADU ở tầng chính",
    },
    "ML82047908": {
        "Giá để bán!": "Mức giá hấp dẫn!",
        "tạo nên những nơi nghỉ dưỡng giống như spa":
            "tạo cảm giác thư giãn như spa",
    },
    "ML82055295": {
        "TẦM NHÌN TUYỆT VỜI TỪ SÂN SÂN VÀ suite phòng ngủ chính.":
            "TẦM NHÌN TUYỆT ĐẸP TỪ SÂN SAU VÀ SUITE PHÒNG NGỦ CHÍNH.",
        "Vị trí Cul-De-Sac": "Vị trí cuối đường cụt",
        "Các trường học có giá tốt nhất": "Các trường học được đánh giá cao gồm",
    },
}

AREA_PATTERN = re.compile(
    r"""
    (?P<number>\d[\d,]*(?:\.\d+)?)
    (?P<approx>\s*[+±]?)
    \s*
    (?P<unit>
        square\s+feet|square\s+foot|sq\.?\s*ft\.?|sqft|sf|acres?|acre
    )
    """,
    re.IGNORECASE | re.VERBOSE,
)


def vi_number(value: float, decimals: int = 1) -> str:
    text = f"{value:,.{decimals}f}" if decimals else f"{value:,.0f}"
    return text.replace(",", "X").replace(".", ",").replace("X", ".")


def localized_measurement(match: re.Match[str]) -> str:
    raw_number = match.group("number")
    number = float(raw_number.replace(",", ""))
    approximate = match.group("approx").strip()
    unit = match.group("unit").lower()
    if unit.startswith("acre"):
        source = vi_number(number, 3).rstrip("0").rstrip(",")
        return f"{source}{approximate} mẫu Anh (≈ {vi_number(number * 4046.8564224, 1)} m²)"
    source = vi_number(number, 0)
    return f"{source}{approximate} ft² (≈ {vi_number(number * 0.092903, 1)} m²)"


def protect_text(text: str) -> tuple[str, dict[str, str]]:
    replacements: dict[str, str] = {}

    def protect_measurement(match: re.Match[str]) -> str:
        token = f"ZXAREA{len(replacements)}ZX"
        replacements[token] = localized_measurement(match)
        return token

    protected = AREA_PATTERN.sub(protect_measurement, text)
    for term in sorted(PROTECTED_TERMS, key=len, reverse=True):
        protected = re.sub(
            rf"\b{re.escape(term)}\b",
            lambda match: _protect_term(match.group(0), replacements),
            protected,
            flags=re.IGNORECASE,
        )
    return protected, replacements


def _protect_term(term: str, replacements: dict[str, str]) -> str:
    token = f"ZXTERM{len(replacements)}ZX"
    replacements[token] = term
    return token


def session() -> requests.Session:
    if not hasattr(THREAD_LOCAL, "session"):
        client = requests.Session()
        client.headers["User-Agent"] = "Mozilla/5.0"
        THREAD_LOCAL.session = client
    return THREAD_LOCAL.session


def request_translation(text: str, attempts: int = 4) -> str:
    for attempt in range(attempts):
        try:
            response = session().get(
                TRANSLATE_URL,
                params={"client": "gtx", "sl": "en", "tl": "vi", "dt": "t", "q": text},
                timeout=45,
            )
            response.raise_for_status()
            return "".join(part[0] for part in response.json()[0] if part and part[0])
        except Exception:
            if attempt == attempts - 1:
                raise
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError("translation failed")


def post_edit(text: str) -> str:
    output = html.unescape(text).replace("m2", "m²")
    for source, target in POST_EDITS.items():
        output = re.sub(re.escape(source), target, output, flags=re.IGNORECASE)
    output = re.sub(r"\s+([,.;:!?])", r"\1", output)
    output = re.sub(r"\s+", " ", output).strip()
    return output


def edit_description(text: str, mls: str) -> str:
    output = post_edit(text)
    for source, target in DESCRIPTION_FIXES.get(mls, {}).items():
        output = output.replace(source, target)
    return output


def clean_mojibake(value: object) -> object:
    if isinstance(value, dict):
        return {key: clean_mojibake(item) for key, item in value.items()}
    if isinstance(value, list):
        return [clean_mojibake(item) for item in value]
    if isinstance(value, str):
        return (
            value.replace("ÃÂ±", "±")
            .replace("Â±", "±")
            .replace("Â®", "®")
            .replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
        )
    return value


def translate_text(text: str) -> str:
    text = (
        text.replace("ÃÂ±", "±")
        .replace("Â±", "±")
        .replace("Â®", "®")
        .replace("\u200b", "")
    )
    protected, replacements = protect_text(text)
    translated = request_translation(protected)
    for token, value in replacements.items():
        translated = translated.replace(token, value)
    return post_edit(translated)


def needs_translation(label: str, value: str) -> bool:
    if not value or label in NO_TRANSLATE_LABELS or value in EXACT_VALUES:
        return False
    if re.fullmatch(r"[\d\s$,.%()+/#&·:/-]+", value):
        return False
    if re.fullmatch(r"[A-Z0-9-]{1,12}", value):
        return False
    if label in {
        "Sq Ft Total",
        "Apprx Lot",
        "Apprx Acres",
        "Price/SqFt",
        "Original List Price",
        "List Price",
        "Original List Date",
        "Listing Date",
    }:
        return False
    return True


def factual_fallback(item: dict[str, object], short_description: str = "") -> str:
    square_feet = str(item["sqft"])
    lot = str(item["lot"])
    introduction = (
        f"MLS chỉ cung cấp mô tả ngắn: {short_description}. "
        if short_description
        and "available for viewing" not in str(item["description"]).lower()
        else "MLS không cung cấp phần mô tả chi tiết cho bất động sản này. "
    )
    return (
        introduction
        +
        f"Căn nhà tại {item['address']}, {item['city']} có {item['bedrooms']} phòng ngủ, "
        f"{item['bathrooms']} phòng tắm, diện tích sử dụng "
        f"{localized_measurement(AREA_PATTERN.search(square_feet + ' sq ft'))}, "
        f"trên lô đất {localized_measurement(AREA_PATTERN.search(lot))}, "
        f"xây dựng năm {item['year']}. Vui lòng xác minh thông tin với môi giới niêm yết."
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / ".m" / "listings-translated.json")
    parser.add_argument("--workers", type=int, default=8)
    parser.add_argument("--reviewed-data", type=Path)
    args = parser.parse_args()

    data = json.loads(args.source.read_text(encoding="utf-8"))
    listings = data["listings"]
    jobs: dict[tuple[str, str], str] = {}
    for item in listings:
        description = str(item["description"])
        if description:
            jobs[("description", str(item["index"]))] = description
        for section, pairs in item["sections"].items():
            for label, value in pairs:
                if needs_translation(label, value):
                    jobs[(f"value:{section}:{label}", value)] = value

    translations: dict[tuple[str, str], str] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(translate_text, text): key for key, text in jobs.items()}
        for completed, future in enumerate(concurrent.futures.as_completed(futures), 1):
            key = futures[future]
            translations[key] = future.result()
            if completed % 50 == 0 or completed == len(futures):
                print(f"{completed}/{len(futures)} text blocks translated", flush=True)

    for item in listings:
        description_key = ("description", str(item["index"]))
        translated_description = translations.get(description_key, "")
        item["description_vi"] = (
            translated_description
            if len(str(item["description"])) >= 80
            else factual_fallback(item, translated_description)
        )
        sections_translated: dict[str, dict[str, str]] = {}
        for section, pairs in item["sections"].items():
            section_values: dict[str, str] = {}
            for label, value in pairs:
                key = (f"value:{section}:{label}", value)
                if value in EXACT_VALUES:
                    section_values[value] = EXACT_VALUES[value]
                elif key in translations:
                    section_values[value] = translations[key]
            sections_translated[section] = section_values
        item["sections_translated"] = sections_translated

    if args.reviewed_data:
        reviewed = json.loads(args.reviewed_data.read_text(encoding="utf-8"))["listings"]
        reviewed_by_mls = {item["mls"]: item for item in reviewed}
        reused = 0
        for item in listings:
            prior = reviewed_by_mls.get(item["mls"])
            if prior and prior.get("description_vi"):
                item["description_vi"] = prior["description_vi"]
                reused += 1
        print(f"Reused {reused} reviewed descriptions by MLS", flush=True)

    for item in listings:
        item["description_vi"] = edit_description(item["description_vi"], item["mls"])
    listings = clean_mojibake(listings)

    output = {
        "source": {
            "name": "MLSListings Matrix Portal",
            "snapshot_date": "2026-07-29",
            "listing_count": len(listings),
        },
        "listings": listings,
        "errors": data.get("errors", []),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {len(listings)} translated listings to {args.output}")


if __name__ == "__main__":
    main()
