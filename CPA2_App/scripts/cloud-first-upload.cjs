// Run after cloud_smoke.py. Bob deliberately has no saved profile.
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const { chromium } = process.env.CPA2_RUNTIME_MODULES
  ? createRequire(path.join(process.env.CPA2_RUNTIME_MODULES, 'package.json'))('playwright')
  : require('playwright');
const app = path.resolve(__dirname, '..');
const values = Object.fromEntries(fs.readFileSync(path.join(app, 'web/.env.clerk.production'), 'utf8')
  .split(/\r?\n/).filter(line => line.includes('=') && !line.startsWith('#'))
  .map(line => { const i = line.indexOf('='); return [line.slice(0, i), line.slice(i + 1).replace(/^"|"$/g, '')]; }));
const state = JSON.parse(fs.readFileSync(path.join(app, 'web/.vercel/cloud-qa.json'), 'utf8'));

(async () => {
  const browser = await chromium.launch({ headless: true,
    ...(process.env.CPA2_BROWSER_EXE ? { executablePath: process.env.CPA2_BROWSER_EXE } : {}) });
  try {
    const response = await fetch('https://api.clerk.com/v1/sign_in_tokens', {
      method: 'POST', headers: { Authorization: `Bearer ${values.CLERK_SECRET_KEY}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: state.users[1].id, expires_in_seconds: 300 }),
    });
    if (!response.ok) throw new Error(`QA sign-in unavailable: HTTP ${response.status}`);
    const token = (await response.json()).token;
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto('https://cpa2-web.vercel.app', { waitUntil: 'domcontentloaded', timeout: 45000 });
    await page.waitForFunction(() => window.Clerk?.loaded);
    await page.evaluate(async token => {
      const attempt = await window.Clerk.client.signIn.create({ strategy: 'ticket', ticket: token });
      if (attempt.status !== 'complete') throw new Error('QA sign-in incomplete.');
      await window.Clerk.setActive({ session: attempt.createdSessionId });
    }, token);
    await page.getByRole('button', { name: 'Hồ sơ & bảng điểm', exact: true }).click({ timeout: 45000 });
    const input = page.locator('input[type="file"][accept*="application/pdf"]');
    if (process.argv.includes('--expect-blocked')) {
      assert.equal(await input.isDisabled(), true);
      console.log('REPRODUCED: first-account PDF picker is disabled before saving a profile.');
      return;
    }
    assert.equal(await input.isEnabled(), true);
    await page.getByRole('checkbox', { name: 'Tôi đồng ý xử lý và lưu bảng điểm để nhận diện.', exact: true }).check();
    // Click the visible control. setInputFiles alone bypasses a disabled picker.
    if (!process.argv.includes('--resume-review')) {
    const [chooser] = await Promise.all([
      page.waitForEvent('filechooser', { timeout: 10000 }),
      page.getByText('Nhận diện PDF / ảnh (OCR)', { exact: true }).click(),
    ]);
    console.log('PASS first upload: fresh account opens the native file picker.');
    await chooser.setFiles(path.join(app, 'web/.vercel/first-upload.pdf'));
    }
    await page.getByRole('heading', { name: 'Bản nháp OCR — cần rà soát' }).waitFor({ timeout: 270000 });
    assert.match(await page.locator('.ocr-review').innerText(), /Đã nhận diện \d+ dòng học phần;\s*\d+ môn đã qua kiểm chéo/);
    const pendingRows = page.locator('tr[data-review-status="needs_review"]');
    const pendingCount = await pendingRows.count();
    assert.ok(pendingCount > 0, 'Uncertain observed rows must remain visible.');
    assert.equal(await page.locator('tbody tr').first().getAttribute('data-review-status'), 'needs_review');
    assert.equal(await pendingRows.locator('input.score-input').count(), 0);
    await pendingRows.first().locator('.ocr-row-review > summary').click();
    assert.equal(await pendingRows.first().locator('.ocr-row-review').getAttribute('open'), '');
    console.log(`PASS review list: ${pendingCount} warning rows visible first, details open, provisional scores kept out of editable facts.`);
    if (process.env.CPA2_CHECK_APPROVAL === '1') {
      const code = await pendingRows.first().locator('td strong').innerText();
      const sample = JSON.parse(fs.readFileSync(path.join(app, '../CPA2_KhaoSat/w7_student_facts/students/sv_lvtn.json'), 'utf8'));
      const gold = sample.grades[code];
      assert.ok(gold, 'The synthetic warning row must have known gold.');
      const row = page.locator('tbody tr').filter({ has: page.locator('td strong', { hasText: new RegExp(`^${code}$`) }) });
      await row.locator('.ocr-row-editor > summary').click();
      await row.getByRole('spinbutton', { name: /^Tín chỉ rà soát/ }).fill(String(gold.credits));
      await row.getByRole('spinbutton', { name: /^Điểm rà soát/ }).fill(String(gold.thang10 / 10));
      await row.getByRole('combobox', { name: /^Điểm chữ rà soát/ }).selectOption(gold.letter);
      await row.getByRole('button', { name: 'Duyệt dòng này', exact: true }).click();
      await row.locator('.ocr-approved').waitFor({ timeout: 40000 });
      await page.reload({ waitUntil: 'domcontentloaded', timeout: 45000 });
      await page.getByRole('heading', { name: /Hồ sơ & bảng điểm/ }).waitFor({ timeout: 45000 });
      await row.locator('.ocr-approved').waitFor({ timeout: 30000 });
      console.log('PASS row approval: corrected values checked on server, approval survives reload.');
    }
    await page.screenshot({ path: path.join(app, 'web/.vercel/cloud-first-upload.png'), fullPage: true });
    assert.deepEqual(errors, []);
    console.log('PASS first upload: PDF -> Convex -> OCR draft without saving a profile; no JavaScript errors.');
  } finally {
    await browser.close();
  }
})().then(() => process.exit(0)).catch(error => { console.error(error.message); process.exit(1); });
