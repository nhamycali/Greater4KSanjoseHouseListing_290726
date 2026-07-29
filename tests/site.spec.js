const { test, expect } = require("@playwright/test");
const path = require("node:path");
const { pathToFileURL } = require("node:url");

function captureErrors(page) {
  const errors = [];
  page.on("console", (message) => {
    if (message.type() === "error") errors.push(`console: ${message.text()}`);
  });
  page.on("pageerror", (error) => errors.push(`page: ${error.message}`));
  return errors;
}

test("desktop list, filters, detail and gallery work", async ({ page }) => {
  const errors = captureErrors(page);
  await page.goto("http://127.0.0.1:8080/index.html", { waitUntil: "networkidle" });
  await expect(page.locator(".listing-card")).toHaveCount(48);
  await expect(page.locator(".brand small")).toHaveText("Giúp người Việt an tâm mua nhà Mỹ");
  expect(await page.evaluate(() => document.fonts.check('16px "NMC Sans"', "Nhà Mỹ Cali"))).toBeTruthy();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
  expect(await page.locator(".listing-card img").first().evaluate((image) => image.naturalWidth)).toBeGreaterThan(0);

  await page.locator("#searchInput").fill("Greenrock");
  await expect(page.locator(".listing-card")).toHaveCount(1);
  await expect(page.locator(".card-address")).toHaveText("2698 Greenrock Road");
  await page.locator("#searchInput").fill("");
  await expect(page.locator(".listing-card")).toHaveCount(48);

  await page.locator("#priceFilter").selectOption("under3300");
  const filtered = await page.locator(".listing-card").count();
  expect(filtered).toBeGreaterThan(0);
  expect(filtered).toBeLessThan(48);
  await page.locator("#priceFilter").selectOption("all");

  await expect(
    page.locator('[data-amenity="vietnamese_community"] b'),
  ).toHaveText("29");
  await expect(page.locator('[data-amenity="coast"] b')).toHaveText("30");
  await page.locator('[data-amenity="vietnamese_community"]').click();
  await expect(page.locator(".listing-card")).toHaveCount(29);
  await expect(page.locator(".card-address").first()).toHaveText("346 S 16th Street");
  await page.locator('[data-amenity="restaurants"]').click();
  await page.locator('[data-amenity="shopping"]').click();
  await expect(page.locator(".listing-card")).toHaveCount(20);
  await page.locator("#amenityLogic").selectOption("any");
  await expect(page.locator(".listing-card")).toHaveCount(38);
  await page.locator("#proximityMode").selectOption("strict");
  await expect(
    page.locator('[data-amenity="vietnamese_community"] b'),
  ).toHaveText("19");
  await expect(page.locator(".filter-method")).toContainText(
    "không suy đoán sắc tộc cư dân",
  );
  await page.locator("#clearFilters").click();
  await expect(page.locator(".listing-card")).toHaveCount(48);

  await page.locator('[data-amenity="vietnamese_community"]').click();
  await page.locator('[data-amenity="coast"]').click();
  await expect(page.locator(".listing-card")).toHaveCount(14);
  const desktopListGeometry = await page.evaluate(() => {
    const results = document.querySelector("#danh-sach");
    const header = document.querySelector(".site-header");
    return {
      top: results.getBoundingClientRect().top + window.scrollY,
      headerHeight: header.getBoundingClientRect().height,
    };
  });
  await page.evaluate(({ top, headerHeight }) => {
    window.scrollTo({ top: top - headerHeight - 4, behavior: "instant" });
  }, desktopListGeometry);
  await expect(page.locator(".site-header")).not.toHaveClass(/is-filter-docked/);
  const desktopBeforeDock = await page.evaluate(() => ({
    scrollY: window.scrollY,
    headingTop: document.querySelector(".section-heading").getBoundingClientRect().top,
  }));
  await page.evaluate(() => window.scrollBy({ top: 8, behavior: "instant" }));
  await expect(page.locator(".site-header")).toHaveClass(/is-filter-docked/);
  const desktopAfterDock = await page.evaluate(() => ({
    scrollY: window.scrollY,
    headingTop: document.querySelector(".section-heading").getBoundingClientRect().top,
  }));
  expect(desktopAfterDock.scrollY - desktopBeforeDock.scrollY).toBe(8);
  expect(desktopAfterDock.headingTop - desktopBeforeDock.headingTop).toBeCloseTo(-8, 0);
  await expect(page.locator("#headerFilterHost .sticky-filter-bar")).toBeVisible();
  await expect(page.locator("#filterHome #searchWrap")).toBeAttached();
  await expect(page.locator(".active-filter-summary")).toContainText("14 căn");
  await expect(page.locator(".active-filter-summary")).toContainText(
    "Khu người Việt",
  );
  await expect(page.locator(".active-filter-summary")).toContainText("Biển");
  const desktopDockedHeader = await page.evaluate(() => {
    const header = document.querySelector(".site-header").getBoundingClientRect();
    return {
      top: header.top,
      height: header.height,
      viewportHeight: window.innerHeight,
    };
  });
  expect(desktopDockedHeader.top).toBe(0);
  expect(desktopDockedHeader.height).toBeLessThan(
    desktopDockedHeader.viewportHeight * 0.09,
  );
  await page
    .locator('[data-remove-filter="amenity"][data-filter-value="coast"]')
    .click();
  await expect(page.locator(".listing-card")).toHaveCount(29);
  await expect(page.locator(".active-filter-summary")).not.toContainText("Biển");
  await page.locator("#filterDrawerToggle").click();
  await expect(page.locator("#filterDrawer")).toBeVisible();
  await expect(page.locator("#filterDrawerToggle")).toHaveAttribute(
    "aria-expanded",
    "true",
  );
  await page.locator("#clearFilters").click();
  await expect(page.locator(".listing-card")).toHaveCount(48);
  await expect(page.locator("#filterDrawerToggle")).toHaveAttribute("aria-expanded", "false");
  await expect(page.locator(".site-header")).not.toHaveClass(/is-filter-open/);

  await page.locator(".listing-card a").first().click();
  await expect(page.locator(".detail-heading h1")).toHaveText("610 San Felipe Road");
  await expect(page.locator(".facts-bar")).toContainText("333,7 m²");
  await expect(page.locator(".location-insights")).toBeVisible();
  await expect(page.locator(".location-insight-grid article")).toHaveCount(8);
  await expect(page.locator(".location-insights")).toContainText(
    "Trung tâm Văn hóa Việt-Mỹ",
  );
  await expect(page.locator(".location-insights")).toContainText("34,0 dặm");
  await expect(page.locator(".detail-section")).toHaveCount(4);
  expect(await page.locator(".gallery-main img").evaluate((image) => image.naturalWidth)).toBeGreaterThan(0);
  await page.locator(".gallery-main").click();
  await expect(page.locator("#lightbox")).toBeVisible();
  await expect(page.locator(".lightbox-count")).toHaveText("Ảnh 1 / 52");
  await page.locator(".lightbox-next").click();
  await expect(page.locator(".lightbox-count")).toHaveText("Ảnh 2 / 52");
  await page.locator(".lightbox-close").click();
  await expect(page.locator("#lightbox")).toBeHidden();
  expect(errors).toEqual([]);
});

test("mobile list and detail remain responsive", async ({ page }) => {
  const errors = captureErrors(page);
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("http://127.0.0.1:8080/index.html", { waitUntil: "networkidle" });
  await expect(page.locator(".listing-card")).toHaveCount(48);
  await expect(page.locator(".header-nav")).toBeHidden();
  await expect(page.locator(".amenity-chips button")).toHaveCount(8);
  await expect(page.locator("#filterDrawer")).toBeHidden();
  const compactMobileGeometry = await page.evaluate(() => {
    const results = document.querySelector("#danh-sach").getBoundingClientRect();
    const firstCard = document.querySelector(".listing-card").getBoundingClientRect();
    return { resultsTop: results.top, firstCardTop: firstCard.top, viewportHeight: innerHeight };
  });
  expect(compactMobileGeometry.resultsTop).toBeLessThan(
    compactMobileGeometry.viewportHeight * 0.62,
  );
  expect(compactMobileGeometry.firstCardTop).toBeLessThan(
    compactMobileGeometry.viewportHeight * 0.82,
  );
  await page.locator("#inlineFilterToggle").click();
  await expect(page.locator("#filterDrawer")).toBeVisible();
  const mobileAmenityStyle = await page
    .locator('[data-amenity="vietnamese_community"]')
    .evaluate((button) => {
      const countBadge = button.querySelector("b");
      return {
        buttonRadius: getComputedStyle(button).borderRadius,
        countRadius: getComputedStyle(countBadge).borderRadius,
        countBackground: getComputedStyle(countBadge).backgroundColor,
      };
    });
  expect(mobileAmenityStyle.buttonRadius).toBe("10px");
  expect(mobileAmenityStyle.countRadius).toBe("0px");
  expect(mobileAmenityStyle.countBackground).toBe("rgba(0, 0, 0, 0)");
  await page.locator('[data-amenity="park"]').click();
  await expect(page.locator(".listing-card")).toHaveCount(35);
  await page.locator("#inlineFilterToggle").click();
  await expect(page.locator("#filterDrawer")).toBeHidden();
  const mobileListGeometry = await page.evaluate(() => {
    const results = document.querySelector("#danh-sach");
    const header = document.querySelector(".site-header");
    return {
      top: results.getBoundingClientRect().top + window.scrollY,
      headerHeight: header.getBoundingClientRect().height,
    };
  });
  await page.evaluate(({ top, headerHeight }) => {
    window.scrollTo({ top: top - headerHeight - 4, behavior: "instant" });
  }, mobileListGeometry);
  await expect(page.locator(".site-header")).not.toHaveClass(/is-filter-docked/);
  const beforeDock = await page.evaluate(() => ({
    scrollY: window.scrollY,
    headingTop: document.querySelector(".section-heading").getBoundingClientRect().top,
  }));
  await page.evaluate(() => window.scrollBy({ top: 8, behavior: "instant" }));
  await expect(page.locator(".site-header")).toHaveClass(/is-filter-docked/);
  const afterDock = await page.evaluate(() => ({
    scrollY: window.scrollY,
    headingTop: document.querySelector(".section-heading").getBoundingClientRect().top,
  }));
  expect(afterDock.scrollY - beforeDock.scrollY).toBe(8);
  expect(afterDock.headingTop - beforeDock.headingTop).toBeCloseTo(-8, 0);
  await expect(page.locator("#headerFilterHost .sticky-filter-bar")).toBeVisible();
  await expect(page.locator("#filterHome #searchWrap")).toBeAttached();
  await expect(page.locator("#bedsFilter")).toBeHidden();
  await expect(page.locator("#filterDrawerToggle b")).toHaveText("1");
  await expect(page.locator(".active-filter-summary")).toContainText("35 căn");
  await expect(page.locator(".active-filter-summary")).toContainText("Công viên");
  const mobileDockedHeader = await page.evaluate(() => {
    const header = document.querySelector(".site-header").getBoundingClientRect();
    return {
      top: header.top,
      height: header.height,
      viewportHeight: window.innerHeight,
    };
  });
  expect(mobileDockedHeader.top).toBe(0);
  expect(mobileDockedHeader.height).toBeLessThan(
    mobileDockedHeader.viewportHeight * 0.09,
  );
  const mobileListGap = await page.evaluate(() => {
    const headerBottom = document.querySelector(".site-header").getBoundingClientRect().bottom;
    const headingTop = document.querySelector(".section-heading").getBoundingClientRect().top;
    return headingTop - headerBottom;
  });
  expect(mobileListGap).toBeLessThan(110);
  await page.locator("#filterDrawerToggle").click();
  await expect(page.locator("#bedsFilter")).toBeVisible();
  await expect(page.locator("#filterDrawer")).toBeVisible();
  await page.locator("#filterDrawerToggle").click();
  await expect(page.locator("#filterDrawer")).toBeHidden();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
  const columns = await page.locator(".listing-grid").evaluate(
    (element) => getComputedStyle(element).gridTemplateColumns.split(" ").length,
  );
  expect(columns).toBe(1);
  await page.locator(".listing-card a").first().click();
  await expect(page.locator(".detail-heading h1")).toBeVisible();
  await expect(page.locator(".description-lead")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBeTruthy();
  expect(errors).toEqual([]);
});

test("index works when opened directly with file protocol", async ({ page }) => {
  const errors = captureErrors(page);
  const url = pathToFileURL(path.resolve("index.html")).href;
  await page.goto(url, { waitUntil: "load" });
  await expect(page.locator(".listing-card")).toHaveCount(48);
  expect(await page.locator(".listing-card img").first().evaluate((image) => image.naturalWidth)).toBeGreaterThan(0);
  expect(errors).toEqual([]);
});

test("all 48 detail pages load their own local hero image", async ({ page }) => {
  const errors = captureErrors(page);
  await page.goto("http://127.0.0.1:8080/index.html", { waitUntil: "networkidle" });
  const details = await page.evaluate(() =>
    window.NHA_MY_CALI_LISTINGS.map((item) => ({
      address: item.address,
      description: item.description_vi,
      href: item.detail_url,
      squareMeters: item.sqft_m2,
    })),
  );
  expect(details).toHaveLength(48);
  for (const detail of details) {
    await page.goto(`http://127.0.0.1:8080/${detail.href}`, { waitUntil: "domcontentloaded" });
    await expect(page.locator(".detail-heading h1")).toHaveText(detail.address);
    await expect(page.locator(".facts-bar")).toContainText(`${detail.squareMeters} m²`);
    await expect(page.locator(".description-lead")).toBeVisible();
    await expect(page.locator(".location-insight-grid article")).toHaveCount(8);
    const descriptionBlocks = page.locator(".description-lead, .description-prose p, .property-note");
    const rendered = (await descriptionBlocks.allTextContents()).join(" ");
    const normalize = (text) => text.replace(/\s+/g, " ").trim();
    expect(normalize(rendered)).toBe(normalize(detail.description));
    await expect(page.locator(".detail-section").first()).toBeVisible();
    expect(await page.locator(".gallery-main img").evaluate((image) => image.naturalWidth)).toBeGreaterThan(0);
  }
  expect(errors).toEqual([]);
});
