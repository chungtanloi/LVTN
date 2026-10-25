/* Uses an existing Playwright install; no browsers or accounts are provisioned. */
const assert = require('node:assert/strict');
const path = require('node:path');
const { createRequire } = require('node:module');
const runtimeModules = process.env.CPA2_RUNTIME_MODULES;
const { chromium } = runtimeModules ? createRequire(path.join(runtimeModules, 'package.json'))('playwright') : require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.CPA2_BROWSER_EXE ? { executablePath: process.env.CPA2_BROWSER_EXE } : {}) });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.CPA2_WEB_URL || 'http://127.0.0.1:3000');
    await page.waitForFunction(() => Number.parseInt(document.querySelector('.stat-value')?.textContent ?? '0') > 0);
    assert.match(await page.title(), /CPA²/);
    await page.getByRole('button', { name: 'Bắt đầu tư vấn', exact: true }).click();
    await page.getByRole('button', { name: 'Em đủ điều kiện tốt nghiệp chưa?', exact: true }).click();
    await page.getByRole('button', { name: /Xem chứng chỉ & nguồn quy chế/ }).waitFor({ timeout: 45000 });
    await page.getByRole('button', { name: /Xem chứng chỉ & nguồn quy chế/ }).click();
    await page.getByRole('heading', { name: 'Chứng chỉ kết luận', exact: true }).waitFor();
    assert.ok(await page.locator('.proof-step').count() > 0);
    await page.getByRole('button', { name: 'Đóng chứng chỉ' }).click();
    await page.getByRole('textbox', { name: 'Câu hỏi tư vấn' }).fill('Học phí bao nhiêu?');
    await page.getByRole('button', { name: 'Gửi câu hỏi' }).click();
    await page.getByText('Học phí bao nhiêu?', { exact: true }).waitFor();
    assert.match(await page.locator('.answer-text').innerText(), /chưa hiểu|chưa hỗ trợ/i);
    await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click();
    await page.getByRole('combobox', { name: 'Học phần cần thêm' }).selectOption('CT101');
    await page.getByRole('spinbutton', { name: 'Điểm thang 10', exact: true }).fill('8.5');
    await page.getByRole('button', { name: 'Thêm', exact: true }).click();
    assert.equal(await page.getByRole('spinbutton', { name: 'Điểm CT101', exact: true }).inputValue(), '8.5');
    await page.getByRole('checkbox', { name: /Tôi đồng ý xử lý hồ sơ/ }).check();
    await page.getByRole('button', { name: 'Lưu hồ sơ', exact: true }).click();
    await page.getByText('Đã lưu hồ sơ. Kết quả tư vấn mới sẽ dùng phiên bản này.', { exact: true }).waitFor();
    await page.getByRole('button', { name: 'Kế hoạch học tập', exact: true }).click();
    await page.getByRole('button', { name: 'Tạo đề xuất học phần' }).click();
    await page.getByRole('heading', { name: 'Học phần đề xuất', exact: true }).waitFor({ timeout: 45000 });
    await page.getByRole('button', { name: 'Kho quy chế', exact: true }).click();
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('điểm W');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.locator('.passage').first().waitFor({ timeout: 45000 });
    await page.getByRole('button', { name: 'Lịch sử tư vấn', exact: true }).click();
    assert.equal(await page.locator('.history-card').count(), 2);
    // A same-origin check must reject cross-site requests to the local bypass.
    const forbidden = await page.request.post(new URL('/api/demo/lookup', page.url()).href, { headers: { Origin: 'https://untrusted.example' }, data: { question: 'điểm W' } });
    assert.equal(forbidden.status(), 403);
    await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
    await page.screenshot({ path: path.join(__dirname, '..', 'dashboard-desktop.png'), fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.setViewportSize({ width: 390, height: 844 });
    await page.screenshot({ path: path.join(__dirname, '..', 'dashboard-mobile.png'), fullPage: true });
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.getByRole('button', { name: 'Mở menu' }).click();
    await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click();
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.getByRole('button', { name: 'Mở menu' }).click();
    await page.getByRole('button', { name: 'Cài đặt & dữ liệu', exact: true }).click();
    await page.getByRole('button', { name: 'Xóa dữ liệu', exact: true }).click();
    await page.getByRole('button', { name: 'Xác nhận xóa', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Đã xóa dữ liệu CPA².' }).waitFor();
    assert.deepEqual(errors, []);
    console.log('PASS: dashboard, solver answer, proof, unsupported query, profile edit/save, recommendation, search, immutable history, CSRF, mobile, delete; no browser errors.');
  } finally { await browser.close(); }
})().then(() => process.exit(0)).catch(error => { console.error(error); process.exit(1); });
