(() => {
  "use strict";

  const listings = window.NHA_MY_CALI_LISTINGS || [];
  const detailPage = document.body.dataset.page === "detail";
  const rootPrefix = detailPage ? "../" : "";
  const escapeHtml = (value) =>
    String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  const imagePath = (path) => `${rootPrefix}${path}`;
  const detailPath = (item) => (detailPage ? `${item.slug}.html` : item.detail_url);
  const price = (item) => `${item.price.replace("$", "")} USD`;
  const amenityLabels = {
    vietnamese_community: "Khu người Việt",
    lake: "Hồ nước",
    coast: "Biển",
    highway: "Cao tốc",
    park: "Công viên",
    restaurants: "Nhà hàng",
    shopping: "Mua sắm",
    transit: "Ga / transit",
  };
  const proximityDescriptions = {
    strict:
      "Rất gần: khu Việt ≤ 4 dặm; hồ ≤ 2; biển ≤ 18; cao tốc ≤ 0,5; công viên ≤ 0,25; mua sắm ≤ 0,5; ga ≤ 0,75.",
    balanced:
      "Gần, hợp lý: khu Việt ≤ 6 dặm; hồ ≤ 4; biển ≤ 22; cao tốc ≤ 1,25; công viên/mua sắm ≤ 0,75; ga ≤ 1,25.",
    broad:
      "Mở rộng: khu Việt ≤ 10 dặm; hồ ≤ 8; biển ≤ 30; cao tốc ≤ 2; công viên ≤ 1; mua sắm ≤ 1,5; ga ≤ 2.",
  };

  function viDecimal(value, decimals = 1) {
    return Number(value).toLocaleString("vi-VN", {
      minimumFractionDigits: decimals,
      maximumFractionDigits: decimals,
    });
  }

  function amenityDetail(item, category) {
    const detail = item.location.amenities[category];
    if (category === "restaurants") {
      return `${detail.counts["1"]} nhà hàng trong 1 dặm`;
    }
    return `${viDecimal(detail.distance_miles)} dặm · ${detail.name}`;
  }

  function locationScore(item, selectedAmenities, mode) {
    if (!selectedAmenities.length) return 0;
    return selectedAmenities.reduce((score, category) => {
      const matched = item.location.matches[mode][category];
      const distance = item.location.amenities[category].distance_miles || 0;
      const densityBonus =
        category === "restaurants"
          ? Math.min(item.location.amenities.restaurants.counts["1"], 30) / 30
          : 0;
      return score + (matched ? 10 : 0) + densityBonus + 1 / (1 + distance);
    }, 0);
  }

  function resultCard(item, selectedAmenities = [], mode = "balanced") {
    const matchedAmenities = selectedAmenities.filter(
      (category) => item.location.matches[mode][category],
    );
    const locationReasons = (matchedAmenities.length
      ? matchedAmenities
      : Object.keys(amenityLabels).filter((category) => item.location.matches.balanced[category])
    ).slice(0, 3);
    return `
      <article class="listing-card">
        <a href="${escapeHtml(detailPath(item))}" aria-label="Xem ${escapeHtml(item.address)}">
          <div class="card-image">
            <img src="${escapeHtml(imagePath(item.images[0]))}" alt="${escapeHtml(item.address)}" loading="lazy">
            <span class="card-badge">${escapeHtml(item.status_vi)}</span>
            <span class="card-count">${item.images.length} ảnh</span>
          </div>
          <div class="card-body">
            <p class="card-price">${escapeHtml(price(item))}</p>
            <h3 class="card-address">${escapeHtml(item.address)}</h3>
            <p class="card-location">${escapeHtml(item.city_vi)}</p>
            <p class="card-mls">MLS#: ${escapeHtml(item.mls)}</p>
            <div class="location-tags">
              ${locationReasons
                .map(
                  (category) =>
                    `<span title="${escapeHtml(amenityDetail(item, category))}">${escapeHtml(
                      amenityLabels[category],
                    )}</span>`,
                )
                .join("")}
            </div>
            <div class="card-facts">
              <span><strong>${escapeHtml(item.bedrooms)}</strong>Phòng ngủ</span>
              <span><strong>${escapeHtml(item.bathrooms)}</strong>Phòng tắm</span>
              <span><strong>${escapeHtml(item.sqft_m2)} m²</strong>${escapeHtml(item.sqft_display)} ft²</span>
            </div>
            <p class="card-location-summary">${escapeHtml(item.location.summary_vi)}</p>
            <p class="card-description">${escapeHtml(item.description_vi)}</p>
            <span class="card-link">Xem chi tiết</span>
          </div>
        </a>
      </article>`;
  }

  function initResults() {
    const grid = document.querySelector("#listingGrid");
    if (!grid) return;
    const search = document.querySelector("#searchInput");
    const beds = document.querySelector("#bedsFilter");
    const priceFilter = document.querySelector("#priceFilter");
    const sort = document.querySelector("#sortSelect");
    const proximityMode = document.querySelector("#proximityMode");
    const amenityLogic = document.querySelector("#amenityLogic");
    const amenityButtons = [...document.querySelectorAll("[data-amenity]")];
    const clearFilters = document.querySelector("#clearFilters");
    const filterMethod = document.querySelector("#filterMethod");
    const searchPanel = document.querySelector(".search-panel");
    const searchWrap = document.querySelector("#searchWrap");
    const filterHome = document.querySelector("#filterHome");
    const headerFilterHost = document.querySelector("#headerFilterHost");
    const siteHeader = document.querySelector(".site-header");
    const activeFilterSummary = document.querySelector("#activeFilterSummary");
    const filterDrawerToggle = document.querySelector("#filterDrawerToggle");
    const count = document.querySelector("#resultCount");
    const empty = document.querySelector("#emptyState");
    const selectedAmenities = new Set();
    let stickyThreshold = Number.POSITIVE_INFINITY;
    let latestResultCount = listings.length;

    const activeFilterCount = () => {
      let active = selectedAmenities.size;
      if (search.value.trim()) active += 1;
      if (beds.value !== "0") active += 1;
      if (priceFilter.value !== "all") active += 1;
      return active;
    };

    const updateFilterToggle = () => {
      const active = activeFilterCount();
      filterDrawerToggle.querySelector("b").textContent = active;
      filterDrawerToggle.classList.toggle("has-active-filters", active > 0);
    };

    const filterSummaryItems = () => {
      const items = [...selectedAmenities].map((category) => ({
        type: "amenity",
        value: category,
        label: amenityLabels[category],
      }));
      const term = search.value.trim();
      if (term) items.push({ type: "search", value: "", label: `“${term.slice(0, 24)}”` });
      if (beds.value !== "0") {
        items.push({ type: "beds", value: "", label: `Từ ${beds.value} phòng ngủ` });
      }
      const priceLabels = {
        under3300: "Dưới 3,3 triệu",
        "3300to3700": "3,3–3,7 triệu",
        over3700: "Trên 3,7 triệu",
      };
      if (priceFilter.value !== "all") {
        items.push({
          type: "price",
          value: "",
          label: priceLabels[priceFilter.value],
        });
      }
      if (proximityMode.value !== "balanced") {
        items.push({
          type: "proximity",
          value: "",
          label: proximityMode.value === "strict" ? "Rất gần" : "Bán kính mở rộng",
        });
      }
      if (amenityLogic.value === "any" && selectedAmenities.size > 1) {
        items.push({ type: "logic", value: "", label: "Ít nhất một tiêu chí" });
      }
      return items;
    };

    const updateActiveFilterSummary = () => {
      const items = filterSummaryItems();
      activeFilterSummary.innerHTML = `
        <span class="summary-count">${latestResultCount} căn</span>
        ${
          items.length
            ? items
                .map(
                  (item) =>
                    `<button type="button" data-remove-filter="${escapeHtml(
                      item.type,
                    )}" data-filter-value="${escapeHtml(item.value)}" aria-label="Bỏ ${escapeHtml(
                      item.label,
                    )}">${escapeHtml(item.label)}</button>`,
                )
                .join("")
            : '<span class="summary-empty">Chưa chọn tiêu chí</span>'
        }`;
    };

    const setDockedState = (docked) => {
      const wasDocked = siteHeader.classList.contains("is-filter-docked");
      if (docked === wasDocked) return;
      siteHeader.classList.toggle("is-filter-docked", docked);
      if (docked) {
        filterHome.style.height = `${searchWrap.offsetHeight}px`;
        headerFilterHost.append(searchWrap);
        siteHeader.classList.remove("is-filter-open");
        filterDrawerToggle.setAttribute("aria-expanded", "false");
      } else {
        filterHome.append(searchWrap);
        filterHome.style.height = "";
        siteHeader.classList.remove("is-filter-open");
        filterDrawerToggle.setAttribute("aria-expanded", "false");
      }
      updateActiveFilterSummary();
    };

    const measureStickyThreshold = () => {
      const wasDocked = siteHeader.classList.contains("is-filter-docked");
      if (wasDocked) setDockedState(false);
      const naturalTop = searchPanel.getBoundingClientRect().top + window.scrollY;
      const headerHeight = siteHeader.offsetHeight;
      stickyThreshold = naturalTop - headerHeight;
      setDockedState(window.scrollY >= stickyThreshold);
    };

    let resizeTimer;
    window.addEventListener(
      "scroll",
      () => setDockedState(window.scrollY >= stickyThreshold),
      { passive: true },
    );
    window.addEventListener("resize", () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(measureStickyThreshold, 120);
    });
    filterDrawerToggle.addEventListener("click", () => {
      if (!siteHeader.classList.contains("is-filter-docked")) return;
      const open = siteHeader.classList.toggle("is-filter-open");
      filterDrawerToggle.setAttribute("aria-expanded", String(open));
    });
    document.addEventListener("keydown", (event) => {
      if (event.key !== "Escape" || !siteHeader.classList.contains("is-filter-open")) {
        return;
      }
      siteHeader.classList.remove("is-filter-open");
      filterDrawerToggle.setAttribute("aria-expanded", "false");
      filterDrawerToggle.focus();
    });
    document.addEventListener("pointerdown", (event) => {
      if (
        !siteHeader.classList.contains("is-filter-open") ||
        siteHeader.contains(event.target)
      ) {
        return;
      }
      siteHeader.classList.remove("is-filter-open");
      filterDrawerToggle.setAttribute("aria-expanded", "false");
    });
    activeFilterSummary.addEventListener("click", (event) => {
      const button = event.target.closest("[data-remove-filter]");
      if (!button) return;
      const type = button.dataset.removeFilter;
      if (type === "amenity") selectedAmenities.delete(button.dataset.filterValue);
      if (type === "search") search.value = "";
      if (type === "beds") beds.value = "0";
      if (type === "price") priceFilter.value = "all";
      if (type === "proximity") proximityMode.value = "balanced";
      if (type === "logic") amenityLogic.value = "all";
      updateAmenityCounts();
      render();
    });

    const updateAmenityCounts = () => {
      const mode = proximityMode.value;
      amenityButtons.forEach((button) => {
        const category = button.dataset.amenity;
        const matches = listings.filter((item) => item.location.matches[mode][category]).length;
        button.querySelector("b").textContent = matches;
        button.classList.toggle("is-active", selectedAmenities.has(category));
        button.setAttribute("aria-pressed", String(selectedAmenities.has(category)));
      });
      updateFilterToggle();
      const restaurantRule =
        mode === "strict"
          ? " Nhà hàng: ít nhất 3 điểm trong 0,5 dặm."
          : ` Nhà hàng: ít nhất 5 điểm trong ${mode === "balanced" ? "1" : "2"} dặm.`;
      filterMethod.textContent =
        `${proximityDescriptions[mode]}${restaurantRule} ` +
        "“Khu người Việt” đo tới các trung tâm thương mại/văn hóa Việt công khai, không suy đoán sắc tộc cư dân.";
    };

    const render = () => {
      const term = search.value.trim().toLocaleLowerCase("vi");
      const selected = [...selectedAmenities];
      const mode = proximityMode.value;
      let output = listings.filter((item) => {
        const amenityNames = Object.values(item.location.amenities)
          .map((detail) => detail.name)
          .join(" ");
        const haystack =
          `${item.address} ${item.city} ${item.mls} ${item.location.summary_vi} ${amenityNames}`
            .toLocaleLowerCase("vi");
        const matchesSearch = !term || haystack.includes(term);
        const matchesBeds = item.beds_number >= Number(beds.value);
        let matchesPrice = true;
        if (priceFilter.value === "under3300") matchesPrice = item.price_number < 3300000;
        if (priceFilter.value === "3300to3700") {
          matchesPrice = item.price_number >= 3300000 && item.price_number <= 3700000;
        }
        if (priceFilter.value === "over3700") matchesPrice = item.price_number > 3700000;
        const amenityMatches = selected.map(
          (category) => item.location.matches[mode][category],
        );
        const matchesAmenities =
          !selected.length ||
          (amenityLogic.value === "all"
            ? amenityMatches.every(Boolean)
            : amenityMatches.some(Boolean));
        return matchesSearch && matchesBeds && matchesPrice && matchesAmenities;
      });
      output = [...output];
      if (sort.value === "location-fit") {
        output.sort(
          (a, b) =>
            locationScore(b, selected, mode) - locationScore(a, selected, mode) ||
            a.index - b.index,
        );
      }
      if (sort.value === "price-desc") output.sort((a, b) => b.price_number - a.price_number);
      if (sort.value === "price-asc") output.sort((a, b) => a.price_number - b.price_number);
      if (sort.value === "area-desc") output.sort((a, b) => b.sqft_number - a.sqft_number);
      grid.innerHTML = output.map((item) => resultCard(item, selected, mode)).join("");
      count.textContent = output.length;
      latestResultCount = output.length;
      empty.hidden = output.length > 0;
      updateFilterToggle();
      updateActiveFilterSummary();
    };
    [search, beds, priceFilter, sort, proximityMode, amenityLogic].forEach((control) =>
      control.addEventListener(control === search ? "input" : "change", render)
    );
    amenityButtons.forEach((button) => {
      button.addEventListener("click", () => {
        const category = button.dataset.amenity;
        if (selectedAmenities.has(category)) selectedAmenities.delete(category);
        else selectedAmenities.add(category);
        if (selectedAmenities.size && sort.value === "default") sort.value = "location-fit";
        updateAmenityCounts();
        render();
      });
    });
    proximityMode.addEventListener("change", updateAmenityCounts);
    clearFilters.addEventListener("click", () => {
      selectedAmenities.clear();
      search.value = "";
      beds.value = "0";
      priceFilter.value = "all";
      sort.value = "default";
      proximityMode.value = "balanced";
      amenityLogic.value = "all";
      updateAmenityCounts();
      render();
    });
    updateAmenityCounts();
    render();
    requestAnimationFrame(measureStickyThreshold);
  }

  function locationInsightsMarkup(item) {
    const order = [
      "vietnamese_community",
      "park",
      "restaurants",
      "shopping",
      "highway",
      "transit",
      "lake",
      "coast",
    ];
    return `
      <section class="location-insights" id="tien-ich-vi-tri">
        <header>
          <div>
            <p class="eyebrow">Nghiên cứu vị trí</p>
            <h2>Tiện ích quanh nhà</h2>
          </div>
          <p>${escapeHtml(item.location.summary_vi)}</p>
        </header>
        <div class="location-insight-grid">
          ${order
            .map((category) => {
              const detail = item.location.amenities[category];
              const evidence = item.location.mls_evidence_categories.includes(category);
              const primary =
                category === "restaurants"
                  ? `${detail.counts["1"]} nhà hàng trong 1 dặm`
                  : `${viDecimal(detail.distance_miles)} dặm`;
              const secondary =
                category === "restaurants"
                  ? `Gần nhất: ${detail.name} · ${viDecimal(detail.distance_miles)} dặm`
                  : detail.name;
              return `
                <article class="${item.location.matches.balanced[category] ? "is-near" : ""}">
                  <span>${escapeHtml(amenityLabels[category])}</span>
                  <strong>${escapeHtml(primary)}</strong>
                  <small>${escapeHtml(secondary)}</small>
                  ${evidence ? "<em>Mô tả MLS có nhắc tới</em>" : ""}
                </article>`;
            })
            .join("")}
        </div>
        <p class="location-method-note">
          Khoảng cách là đường chim bay và mang tính tham khảo. “Khu người Việt” dựa trên
          Little Saigon, trung tâm thương mại, văn hóa và sinh hoạt cộng đồng Việt công khai;
          không suy đoán thành phần cư dân. Dữ liệu địa điểm
          <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noopener">© OpenStreetMap contributors, ODbL</a>.
        </p>
      </section>`;
  }

  function fieldSections(item) {
    return item.sections_vi
      .map(
        (section) => `
          <section class="detail-section">
            <h2>${escapeHtml(section.name)}</h2>
            <dl class="field-table">
              ${section.fields
                .map(
                  (field) => `
                    <div class="field-row">
                      <dt>${escapeHtml(field.label)}</dt>
                      <dd>${escapeHtml(field.value)}</dd>
                    </div>`
                )
                .join("")}
            </dl>
          </section>`
      )
      .join("");
  }

  function splitSentences(text) {
    return text.match(/.+?(?:[.!?]+(?=\s|$)|$)/g)?.map((part) => part.trim()).filter(Boolean) || [];
  }

  function descriptionMarkup(text) {
    const normalized = String(text || "").replace(/\s+/g, " ").trim();
    const sentences = splitSentences(normalized);
    const lead = [];
    if (sentences.length) {
      lead.push(sentences.shift());
      while (sentences.length && lead.length < 2 && lead.join(" ").length < 180) {
        lead.push(sentences.shift());
      }
    }
    const paragraphs = [];
    let current = [];
    let length = 0;
    sentences.forEach((sentence) => {
      if (current.length && (current.length >= 2 || length + sentence.length > 430)) {
        paragraphs.push(current.join(" "));
        current = [];
        length = 0;
      }
      current.push(sentence);
      length += sentence.length;
    });
    if (current.length) paragraphs.push(current.join(" "));
    return `
      <div class="description-body">
        ${lead.length ? `<p class="description-lead">${escapeHtml(lead.join(" "))}</p>` : ""}
        ${paragraphs.length ? `<div class="description-prose">${paragraphs.map((p) => `<p>${escapeHtml(p)}</p>`).join("")}</div>` : ""}
      </div>`;
  }

  function initLightbox(item) {
    const lightbox = document.querySelector("#lightbox");
    if (!lightbox) return;
    const image = lightbox.querySelector("img");
    const counter = lightbox.querySelector(".lightbox-count");
    let current = 0;
    const show = (index) => {
      current = (index + item.images.length) % item.images.length;
      image.src = imagePath(item.images[current]);
      image.alt = `${item.address} — ảnh ${current + 1}`;
      counter.textContent = `Ảnh ${current + 1} / ${item.images.length}`;
    };
    const open = (index = 0) => {
      show(index);
      lightbox.hidden = false;
      document.body.style.overflow = "hidden";
      lightbox.querySelector(".lightbox-close").focus();
    };
    const close = () => {
      lightbox.hidden = true;
      document.body.style.overflow = "";
    };
    document.querySelectorAll("[data-gallery-index]").forEach((button) => {
      button.addEventListener("click", () => open(Number(button.dataset.galleryIndex)));
    });
    lightbox.querySelector(".lightbox-prev").addEventListener("click", () => show(current - 1));
    lightbox.querySelector(".lightbox-next").addEventListener("click", () => show(current + 1));
    lightbox.querySelector(".lightbox-close").addEventListener("click", close);
    lightbox.addEventListener("click", (event) => {
      if (event.target === lightbox) close();
    });
    document.addEventListener("keydown", (event) => {
      if (lightbox.hidden) return;
      if (event.key === "Escape") close();
      if (event.key === "ArrowLeft") show(current - 1);
      if (event.key === "ArrowRight") show(current + 1);
    });
  }

  function initBackToTop() {
    const button = document.createElement("button");
    button.className = "back-to-top";
    button.type = "button";
    button.setAttribute("aria-label", "Về đầu trang");
    button.setAttribute("aria-hidden", "true");
    button.tabIndex = -1;
    button.innerHTML = '<svg aria-hidden="true" viewBox="0 0 24 24"><path d="m6 14 6-6 6 6"/></svg>';
    document.body.append(button);
    let timer;
    const update = () => {
      const visible = window.scrollY > Math.max(480, window.innerHeight * .65);
      button.classList.toggle("is-visible", visible);
      button.setAttribute("aria-hidden", String(!visible));
      button.tabIndex = visible ? 0 : -1;
    };
    window.addEventListener("scroll", () => {
      update();
      button.classList.add("is-scrolling");
      clearTimeout(timer);
      timer = setTimeout(() => button.classList.remove("is-scrolling"), 180);
    }, { passive: true });
    button.addEventListener("click", () => window.scrollTo({ top: 0, behavior: "smooth" }));
    update();
  }

  function initDetail() {
    const root = document.querySelector("#detailRoot");
    if (!root) return;
    const index = Number(document.body.dataset.listingIndex);
    const item = listings[index];
    if (!item) {
      root.innerHTML = '<div class="empty-state"><strong>Không tìm thấy bất động sản.</strong></div>';
      return;
    }
    const previous = listings[index - 1];
    const next = listings[index + 1];
    const image2 = item.images[1] || item.images[0];
    const image3 = item.images[2] || image2;
    const mapQuery = encodeURIComponent(`${item.address}, ${item.city}`);
    root.innerHTML = `
      <section class="detail-top" id="chi-tiet">
        <div class="detail-top-inner">
          <a class="back-link" href="../index.html#danh-sach">← Quay lại danh sách ${listings.length} căn nhà</a>
          <div class="detail-heading">
            <div>
              <p class="eyebrow">Bất động sản ${index + 1} / ${listings.length} · MLS# ${escapeHtml(item.mls)}</p>
              <h1>${escapeHtml(item.address)}</h1>
              <p class="detail-location">${escapeHtml(item.city_vi)}</p>
            </div>
            <div class="detail-price"><strong>${escapeHtml(price(item))}</strong><span>${escapeHtml(item.status_vi)}</span></div>
          </div>
        </div>
      </section>
      <div class="detail-main">
        <section class="gallery" aria-label="Thư viện ảnh ${escapeHtml(item.address)}">
          <button class="gallery-main" data-gallery-index="0" aria-label="Mở ảnh chính"><img src="${escapeHtml(imagePath(item.images[0]))}" alt="${escapeHtml(item.address)}"></button>
          <div class="gallery-side">
            <button data-gallery-index="1" aria-label="Mở ảnh 2"><img src="${escapeHtml(imagePath(image2))}" alt="${escapeHtml(item.address)} — ảnh 2"></button>
            <button data-gallery-index="2" aria-label="Mở thư viện ảnh"><img src="${escapeHtml(imagePath(image3))}" alt="${escapeHtml(item.address)} — ảnh 3"><span class="gallery-more">Xem đủ ${item.images.length} ảnh</span></button>
          </div>
        </section>
        <section class="facts-bar" aria-label="Thông số nổi bật">
          <div class="fact"><small>Phòng ngủ</small><strong>${escapeHtml(item.bedrooms)}</strong></div>
          <div class="fact"><small>Phòng tắm</small><strong>${escapeHtml(item.bathrooms)}</strong></div>
          <div class="fact"><small>Diện tích sử dụng</small><strong>${escapeHtml(item.sqft_display)} ft²<br>≈ ${escapeHtml(item.sqft_m2)} m²</strong></div>
          <div class="fact"><small>Diện tích lô đất</small><strong>${escapeHtml(item.lot_display)} ft²<br>≈ ${escapeHtml(item.lot_m2)} m²</strong></div>
          <div class="fact"><small>Năm xây dựng</small><strong>${escapeHtml(item.year)}</strong></div>
        </section>
        ${locationInsightsMarkup(item)}
        <div class="detail-layout">
          <div>
            <article class="detail-content">
              <div class="description-block">
                <header class="description-heading"><p class="eyebrow">Giới thiệu bất động sản</p><h2>Mô tả chi tiết</h2><p class="description-kicker">Thông tin tổng quan, không gian sống và những điểm đáng chú ý của căn nhà.</p></header>
                ${descriptionMarkup(item.description_vi)}
                <div class="conversion-note">Quy đổi diện tích: 1 ft² = 0,092903 m². Các số m² được làm tròn đến 1 chữ số thập phân.</div>
              </div>
            </article>
            ${fieldSections(item)}
            <nav class="detail-pagination" aria-label="Chuyển giữa các bất động sản">
              ${previous ? `<a href="${escapeHtml(previous.slug)}.html"><small>← Căn trước</small><strong>${escapeHtml(previous.address)}</strong></a>` : "<span></span>"}
              ${next ? `<a href="${escapeHtml(next.slug)}.html"><small>Căn tiếp theo →</small><strong>${escapeHtml(next.address)}</strong></a>` : "<span></span>"}
            </nav>
          </div>
          <aside class="detail-sidebar">
            <section class="contact-card">
              <p class="eyebrow">Nhà Mỹ Cali</p><h2>Bạn quan tâm căn nhà này?</h2>
              <p>Lưu lại mã MLS và liên hệ môi giới phụ trách để xác minh lịch xem nhà, giá và tình trạng mới nhất.</p>
              <div class="contact-actions">
                <a class="button" href="https://www.google.com/maps/search/?api=1&query=${mapQuery}" target="_blank" rel="noopener">Mở trên Google Maps</a>
                <button class="button secondary" id="copyMls" type="button" data-mls="${escapeHtml(item.mls)}">Sao chép mã MLS</button>
              </div>
            </section>
            <div class="mini-card"><small>Mã MLS</small><strong>${escapeHtml(item.mls)}</strong></div>
            <div class="mini-card"><small>Loại hình</small><strong>${escapeHtml(item.building_type === "Detached" ? "Nhà đơn lập" : item.building_type)}</strong></div>
            <div class="mini-card"><small>Thư viện ảnh</small><strong>${item.images.length} ảnh</strong></div>
          </aside>
        </div>
      </div>
      <div class="lightbox" id="lightbox" hidden role="dialog" aria-modal="true" aria-label="Xem ảnh bất động sản">
        <button class="lightbox-close" type="button" aria-label="Đóng">×</button>
        <button class="lightbox-prev" type="button" aria-label="Ảnh trước">‹</button>
        <div class="lightbox-image-wrap"><img src="" alt=""><div class="lightbox-count"></div></div>
        <button class="lightbox-next" type="button" aria-label="Ảnh tiếp theo">›</button>
      </div>`;
    const copyButton = document.querySelector("#copyMls");
    copyButton.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(copyButton.dataset.mls);
        copyButton.textContent = "Đã sao chép mã MLS";
      } catch {
        copyButton.textContent = `MLS: ${copyButton.dataset.mls}`;
      }
    });
    initLightbox(item);
  }

  initResults();
  initDetail();
  initBackToTop();
})();
