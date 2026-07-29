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

  await page.locator(".listing-card a").first().click();
  await expect(page.locator(".detail-heading h1")).toHaveText("610 San Felipe Road");
  await expect(page.locator(".facts-bar")).toContainText("333,7 m²");
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
    const descriptionBlocks = page.locator(".description-lead, .description-prose p, .property-note");
    const rendered = (await descriptionBlocks.allTextContents()).join(" ");
    const normalize = (text) => text.replace(/\s+/g, " ").trim();
    expect(normalize(rendered)).toBe(normalize(detail.description));
    await expect(page.locator(".detail-section").first()).toBeVisible();
    expect(await page.locator(".gallery-main img").evaluate((image) => image.naturalWidth)).toBeGreaterThan(0);
  }
  expect(errors).toEqual([]);
});
