// Run after cloud_smoke.py; credentials and short-lived tickets are never logged.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { chromium } = process.env.CPA2_RUNTIME_MODULES
  ? createRequire(path.join(process.env.CPA2_RUNTIME_MODULES, 'package.json'))('playwright')
  : require('playwright');
const app = path.resolve(__dirname, '..');
const values = Object.fromEntries(fs.readFileSync(path.join(app, 'web/.env.clerk.production'), 'utf8').split(/\r?\n/).filter(line => line.includes('=') && !line.startsWith('#')).map(line => { const index = line.indexOf('='); return [line.slice(0, index), line.slice(index + 1).replace(/^"|"$/g, '')]; }));
const state = JSON.parse(fs.readFileSync(path.join(app, 'web/.vercel/cloud-qa.json'), 'utf8'));

async function ticket(user) {
  const response = await fetch('https://api.clerk.com/v1/sign_in_tokens', { method: 'POST', headers: { Authorization: `Bearer ${values.CLERK_SECRET_KEY}`, 'Content-Type': 'application/json', 'User-Agent': 'CPA2-Cloud-QA/0.1' }, body: JSON.stringify({ user_id: user.id, expires_in_seconds: 300 }) });
  if (!response.ok) throw new Error(`Could not prepare QA sign-in: HTTP ${response.status}`);
  return (await response.json()).token;
}

(async () => {
  const browser = await chromium.launch({ headless: true, ...(process.env.CPA2_BROWSER_EXE ? { executablePath: process.env.CPA2_BROWSER_EXE } : {}) });
  const errors = [];
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    page.on('pageerror', error => errors.push(error.message));
    // Readiness is checked by the app controls below, independently of slow assets.
    await page.goto('https://cpa2-web.vercel.app', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('button', { name: /Đăng nhập để bắt đầu/ }).waitFor({ timeout: 30000 });
    await page.waitForFunction(() => window.Clerk?.loaded);
    const token = await ticket(state.users[0]);
    await page.evaluate(async token => {
      const attempt = await window.Clerk.client.signIn.create({ strategy: 'ticket', ticket: token });
      if (attempt.status !== 'complete') throw new Error('QA sign-in did not finish.');
      await window.Clerk.setActive({ session: attempt.createdSessionId });
    }, token);
    await page.getByRole('heading', { name: /Học tập có định hướng/ }).waitFor({ timeout: 45000 });
    await page.waitForFunction(() => Number.parseInt(document.querySelector('.stat-value')?.textContent ?? '0') > 0);
    console.log('PASS browser: Clerk session -> Convex auth -> personal dashboard.');
    if (process.env.CPA2_SOURCES_ONLY !== '1') {
      await page.getByRole('button', { name: /^Tư vấn học vụ/ }).click();
      await page.getByRole('textbox', { name: 'Câu hỏi tư vấn' }).fill('Em đủ điều kiện tốt nghiệp chưa?');
      await page.getByRole('button', { name: 'Gửi câu hỏi', exact: true }).click();
      await page.waitForFunction(() => document.querySelector('.user-message p')?.textContent === 'Em đủ điều kiện tốt nghiệp chưa?' && !document.querySelector('.thinking'), undefined, { timeout: 50000 });
      await page.getByRole('button', { name: /Xem chứng chỉ & nguồn quy chế/ }).click();
      await page.getByRole('heading', { name: 'Chứng chỉ kết luận', exact: true }).waitFor();
      assert.ok(await page.locator('.proof-step').count() > 20);
      assert.match(await page.locator('.proof-step').first().innerText(), /tot_nghiep/);
      await page.screenshot({ path: path.join(app, 'cloud-proof.png'), fullPage: true });
      await page.getByRole('button', { name: 'Đóng chứng chỉ' }).click();
      console.log('PASS browser: question -> Convex action -> Render -> visible proof and citations.');
      await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.getByRole('heading', { name: /Học tập có định hướng/ }).waitFor({ timeout: 30000 });
      await page.getByRole('button', { name: 'Lịch sử tư vấn', exact: true }).click();
      await page.locator('.history-card').first().waitFor();
      assert.ok(await page.locator('.history-card').count() >= 3);
      console.log('PASS browser: authenticated session and history survive reload.');
      await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click();
      await page.getByRole('spinbutton', { name: 'Điểm CT101', exact: true }).fill('8.6');
      await page.getByRole('spinbutton', { name: 'Tín chỉ được công nhận/chuyển đổi', exact: true }).fill('0');
      await page.getByRole('checkbox', { name: /Tôi đồng ý lưu hồ sơ/ }).check();
      await page.getByRole('button', { name: 'Lưu hồ sơ', exact: true }).click();
      await page.getByRole('status').filter({ hasText: 'Đã lưu hồ sơ.' }).waitFor({ timeout: 40000 });
      console.log('PASS browser: consent + grade edit -> new persisted profile revision.');
      if (process.env.CPA2_CHECK_PDF === '1') {
        const input = page.locator('input[type="file"][accept*="application/pdf"]');
        await input.setInputFiles(path.join(app, 'web/.vercel/qa-transcript.pdf'));
        await page.getByRole('heading', { name: 'Bản nháp OCR — cần rà soát' }).waitFor({ timeout: 270000 });
        assert.ok(await page.getByText('Tôi đã đối chiếu các dữ kiện được nhận với bảng điểm gốc.').isVisible());
        await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-pdf-review.png'), fullPage: true });
        console.log('PASS browser: PDF picker -> upload -> scheduled OCR -> visible review draft.');
      }
    }
    await page.getByRole('button', { name: 'Kho quy chế', exact: true }).click();
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('điểm W');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.locator('.passage').first().waitFor({ timeout: 150000 });
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('Môn CT177 có tiên quyết là gì?');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('.passage')?.textContent.includes('— CT177'), undefined, { timeout: 150000 });
    assert.ok((await page.locator('.passage').first().innerText()).includes('CT101'));
    await page.screenshot({ path: path.join(app, 'cloud-rag.png'), fullPage: true });
    console.log('PASS browser: ranked lookup keeps CT177 and its actual CT101 prerequisite.');
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('QĐ3266 Điều 14 đăng ký tín chỉ');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.waitForFunction(() => {
      const cards = [...document.querySelectorAll('.passage')];
      return cards.length > 0 && cards.every(card => card.querySelector('.subtle-tag')?.textContent.startsWith('qd3266:D14:'));
    }, undefined, { timeout: 150000 });
    // Clean Article 14 is now short enough to display without expansion.
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('điểm W');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('.passage .subtle-tag')?.textContent === 'qd3266:D22:K5', undefined, { timeout: 150000 });
    const source = page.locator('.passage').filter({ has: page.getByText('Xem toàn bộ đoạn nguồn', { exact: true }) }).first();
    await source.locator('summary').click();
    const excerpt = await source.locator(':scope > p').first().innerText();
    const full = await source.locator('details p').innerText();
    assert.ok(full.length > excerpt.length && full.includes(excerpt));
    assert.ok(excerpt.length <= 300);
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-rag-v3.png'), fullPage: true });
    console.log('PASS browser: exact article reference -> query excerpt -> expandable original source.');
    assert.ok(!(await page.locator('.passage').allTextContents()).join(' ').includes('PHÁT HIỆN ÂM TÍNH'));
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('QĐ3266 Điều 22 khoản 4 quy định gì?');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('.passage .subtle-tag')?.textContent === 'qd3266:D22:K4', undefined, { timeout: 150000 });
    assert.ok((await page.locator('.passage').first().innerText()).includes('công bố'));
    assert.equal(await page.getByRole('link', { name: 'Mở PDF gốc · trang 14', exact: true }).getAttribute('href'), '/quy-che/qd3266.pdf#page=14');
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-source-corrected.png'), fullPage: true });
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('Môn này có tiên quyết không?');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.getByRole('heading', { name: 'Cần thêm thông tin', exact: true }).waitFor({ timeout: 150000 });
    assert.equal(await page.locator('.passage').count(), 0);
    await page.getByRole('button', { name: 'Môn CT177 có tiên quyết là gì?', exact: true }).click();
    assert.equal(await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).inputValue(), 'Môn CT177 có tiên quyết là gì?');
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-source-clarification.png'), fullPage: true });
    const manifest = JSON.parse(fs.readFileSync(path.join(app, '../CPA2_KhaoSat/w14_rag/source_pdf_manifest_v1.json'), 'utf8'));
    for (const document of manifest) {
      const response = await page.request.get('https://cpa2-web.vercel.app' + document.public_path, { timeout: 45000 });
      assert.equal(response.status(), 200);
      const bytes = await response.body();
      assert.equal(bytes.length, document.size);
      assert.equal(require('node:crypto').createHash('sha256').update(bytes).digest('hex'), document.sha256);
    }
    console.log('PASS browser: clean clause, matching original public PDF bytes, and clarification instead of guessing.');
    await page.getByRole('button', { name: 'Tổng quan', exact: true }).click();
    await page.screenshot({ path: path.join(app, 'cloud-dashboard.png'), fullPage: true });
    await page.setViewportSize({ width: 390, height: 844 });
    await page.waitForFunction(() => document.querySelector('.sidebar').getBoundingClientRect().right <= 0);
    assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
    await page.screenshot({ path: path.join(app, 'cloud-mobile.png'), fullPage: true });
    console.log('PASS browser: live regulation lookup, desktop and mobile layout.');
    assert.deepEqual(errors, []);
    console.log('PASS browser: no JavaScript page errors.');
  } finally { await browser.close(); }
})().then(() => process.exit(0)).catch(error => { console.error(error.message); process.exit(1); });
