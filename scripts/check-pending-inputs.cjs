// Optional browser regression. Start the demo, then run with Playwright installed.
const {chromium} = require(process.env.PLAYWRIGHT_MODULE || 'playwright');
const assert = require('node:assert/strict');
(async () => {
  const browser = await chromium.launch({headless:true});
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.DEMO_URL || 'http://127.0.0.1:5173');
    await page.getByText('Demo delivery handbook', {exact:true}).waitFor();
    async function delayedSubmit(path, button, inputs) {
      let release;
      let arrived;
      let finished;
      const held = new Promise(resolve => release = resolve);
      const completed = new Promise(resolve => finished = resolve);
      const requestStarted = new Promise(resolve => arrived = resolve);
      const pattern = '**/api/' + path;
      await page.route(pattern, async route => {
        if (route.request().method() !== 'POST') return route.continue();
        arrived();
        await held;
        finished();
        await route.continue();
      });
      await page.getByRole('button', {name:button, exact:true}).click();
      await requestStarted;
      const disabled = await Promise.all(inputs.map(input => input.isDisabled()));
      release();
      await completed;
      return disabled;
    }
    const question = page.getByLabel('Question', {exact:true});
    await question.fill('When are release reviews?');
    const questionDisabled = await delayedSubmit('ask', 'Ask ↗', [question]);
    await page.getByText('Release reviews happen every Thursday.', {exact:true}).first().waitFor();
    assert.equal(await question.isEnabled(), true);
    const title = page.getByLabel('Title', {exact:true});
    const text = page.getByRole('textbox', {name:/Plain text/});
    await title.fill('Pending form regression');
    await text.fill('The pending regression workshop starts at noon.');
    const ingestDisabled = await delayedSubmit('documents', 'Index document', [title, text]);
    await page.getByText('Document indexed. Ask a question using its key terms.', {exact:true}).waitFor();
    assert.equal(await title.isEnabled(), true);
    assert.equal(await text.isEnabled(), true);
    assert.deepEqual(questionDisabled, [true], 'Question must be protected from edits while its submitted request is pending');
    assert.deepEqual(ingestDisabled, [true,true], 'Document drafts must be protected from edits while ingestion is pending');
    assert.deepEqual(errors, []);
    console.log('PASS: delayed question and ingestion POSTs protect drafts; inputs re-enable; no page errors');
  } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exit(1); });
