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
    await page.goto('https://cpa2-web.vercel.app');
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
    await page.getByRole('button', { name: /^Tư vấn học vụ/ }).click();
    await page.getByRole('textbox', { name: 'Câu hỏi tư vấn' }).fill('Em đủ điều kiện tốt nghiệp chưa?');
    await page.getByRole('button', { name: 'Gửi câu hỏi', exact: true }).click();
    await page.waitForFunction(() => document.querySelector('.user-message p')?.textContent === 'Em đủ điều kiện tốt nghiệp chưa?' && !document.querySelector('.thinking'), undefined, { timeout: 50000 });
    await page.getByRole('button', { name: /Xem chứng chỉ & nguồn quy chế/ }).click();
    await page.getByRole('heading', { name: 'Chứng chỉ kết luận', exact: true }).waitFor();
    assert.ok(await page.locator('.proof-step').count() > 0);
    await page.screenshot({ path: path.join(app, 'cloud-proof.png'), fullPage: true });
    await page.getByRole('button', { name: 'Đóng chứng chỉ' }).click();
    console.log('PASS browser: question -> Convex action -> Render -> visible proof and citations.');
    await page.reload();
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
    await page.getByRole('button', { name: 'Kho quy chế', exact: true }).click();
    await page.getByRole('textbox', { name: 'Tìm trong quy chế' }).fill('điểm W');
    await page.getByRole('button', { name: 'Tra cứu', exact: true }).click();
    await page.locator('.passage').first().waitFor({ timeout: 40000 });
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
