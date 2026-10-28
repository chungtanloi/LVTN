// Alice has a synthetic one-row OCR profile seeded for correction/approval QA.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { chromium } = createRequire(path.join(process.env.CPA2_RUNTIME_MODULES, 'package.json'))('playwright');
const app = path.resolve(__dirname, '..');
const values = Object.fromEntries(fs.readFileSync(path.join(app, 'web/.env.clerk.production'), 'utf8')
  .split(/\r?\n/).filter((l) => l.includes('=') && !l.startsWith('#'))
  .map((l) => { const i = l.indexOf('='); return [l.slice(0, i), l.slice(i + 1).replace(/^"|"$/g, '')]; }));
const state = JSON.parse(fs.readFileSync(path.join(app, 'web/.vercel/cloud-qa.json'), 'utf8'));
(async () => {
  const browser = await chromium.launch({ headless: true, executablePath: process.env.CPA2_BROWSER_EXE });
  try {
    const response = await fetch('https://api.clerk.com/v1/sign_in_tokens', {
      method: 'POST', headers: { Authorization: `Bearer ${values.CLERK_SECRET_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: state.users[0].id, expires_in_seconds: 300 }),
    });
    if (!response.ok) throw new Error(`QA sign-in HTTP ${response.status}`);
    const token = (await response.json()).token;
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    const errors = []; page.on('pageerror', (e) => errors.push(e.message));
    await page.goto('https://cpa2-web.vercel.app', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForFunction(() => window.Clerk?.loaded);
    await page.evaluate(async (token) => {
      const attempt = await window.Clerk.client.signIn.create({ strategy: 'ticket', ticket: token });
      if (attempt.status !== 'complete') throw new Error('QA sign-in incomplete.');
      await window.Clerk.setActive({ session: attempt.createdSessionId });
    }, token);
    await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click({ timeout: 45000 });
    await page.getByRole('checkbox', { name: 'Tôi đồng ý xử lý và lưu bảng điểm để nhận diện.', exact: true }).check();
    const row = page.locator('tbody tr').filter({ has: page.locator('strong', { hasText: /^CT101$/ }) });
    assert.equal(await row.getAttribute('data-review-status'), 'needs_review');
    await row.locator('.ocr-row-editor > summary').click();
    await row.getByRole('spinbutton', { name: /^Điểm rà soát/ }).fill('9.7');
    await row.getByRole('combobox', { name: /^Điểm chữ rà soát/ }).selectOption('B');
    await row.getByRole('button', { name: 'Duyệt dòng này', exact: true }).click();
    await row.locator('.ocr-row-editor [role="alert"]').filter({ hasText: 'Điểm chữ' }).waitFor({ timeout: 35000 });
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-approval-edit.png'), fullPage: true });
    console.log('PASS approval: mismatched numerical/letter grades rejected with an inline error.');
    await row.getByRole('combobox', { name: /^Điểm chữ rà soát/ }).selectOption('A');
    await row.getByRole('button', { name: 'Duyệt dòng này', exact: true }).click();
    await page.getByRole('heading', { name: 'Bảng điểm đã kiểm tra — chờ lưu' }).waitFor({ timeout: 35000 });
    assert.equal(await row.getAttribute('data-review-status'), 'accepted');
    await row.locator('.ocr-approved').waitFor();
    await page.getByRole('checkbox', { name: 'Tôi đã đối chiếu các dữ kiện được nhận với bảng điểm gốc.', exact: true }).check();
    await page.getByRole('button', { name: 'Lưu hồ sơ', exact: true }).click();
    await page.getByRole('status').filter({ hasText: 'Đã lưu hồ sơ.' }).waitFor({ timeout: 40000 });
    await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click({ timeout: 45000 });
    await row.locator('.ocr-approved').waitFor({ timeout: 30000 });
    assert.equal(await row.getAttribute('data-review-status'), 'accepted');
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-approved-saved.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log('PASS approval: fix -> server recheck -> approved -> save -> reload retains the reviewed grade.');
  } finally { await browser.close(); }
})().then(() => process.exit(0)).catch((e) => { console.error(e.message); process.exit(1); });
