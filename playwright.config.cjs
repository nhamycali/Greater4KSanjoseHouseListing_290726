module.exports = {
  testDir: "./tests",
  testMatch: "site.spec.js",
  timeout: 90000,
  workers: 1,
  reporter: [["list"]],
  webServer: {
    command: "python3 -m http.server 8080 --bind 127.0.0.1",
    url: "http://127.0.0.1:8080/index.html",
    reuseExistingServer: true,
  },
  use: {
    browserName: "chromium",
    viewport: { width: 1440, height: 1000 },
  },
};

