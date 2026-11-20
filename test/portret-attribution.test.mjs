import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import vm from 'node:vm';

const html = readFileSync(new URL('../portret-pupila.html', import.meta.url), 'utf8');
const code = readFileSync(new URL('../assets/portret-pupila/attribution.js', import.meta.url), 'utf8');
const destination = 'https://portret-pupila.myshopify.com/pages/contact#portret-zapytanie';
const campaign = 'utm_source=tiktok&utm_medium=organic_social&utm_campaign=pierwsza_sprzedaz_14dni_20261117';
function run(search, hrefs = [destination]) {
  const anchors = hrefs.map(href => ({href}));
  vm.runInNewContext(code, {
    URL, URLSearchParams, window: {location: {search}},
    document: {querySelectorAll(selector) { assert.equal(selector, 'a[href]'); return anchors; }}
  });
  return anchors.map(a => a.href);
}

test('Shopify product and contact links retain the approved inbound campaign', () => {
  assert.match(html, /<script src="assets\/portret-pupila\/attribution.js" defer><\/script>/);
  const storefront = [...html.matchAll(/href="([^"]+)"/g)]
    .map(([, href]) => href.replaceAll('&amp;', '&'))
    .filter(href => href.startsWith('https://portret-pupila.myshopify.com/'));
  assert.equal(storefront.length, 10);
  const forwarded = run('?' + campaign + '&utm_content=bio', storefront);
  for (const [index, href] of forwarded.entries()) {
    const url = new URL(href);
    const original = new URL(storefront[index]);
    assert.equal(url.pathname, original.pathname);
    assert.equal(url.hash, original.hash);
    assert.equal(url.searchParams.get('utm_content'), 'bio');
    assert.equal(url.searchParams.get('utm_source'), 'tiktok');
    assert.equal(url.searchParams.get('utm_medium'), 'organic_social');
    assert.equal(url.searchParams.get('utm_campaign'), 'pierwsza_sprzedaz_14dni_20261117');
    assert.equal(url.searchParams.size, 4);
  }
});

test('unlisted fields and private-looking values are not forwarded', () => {
  const [href]=run('?'+campaign+'&email=qa%40example.invalid&phone=123456789&utm_content=qa%40example.invalid&utm_term=private&order=123&token=secret');
  const q=new URL(href).searchParams;
  assert.deepEqual([...q.keys()], ['utm_source','utm_medium','utm_campaign']);
  assert.doesNotMatch(href,/qa|example|private|token|order|123456789/);
});

test('unrelated pages, foreign hosts and deceptive host suffixes stay unchanged', () => {
  const other=['https://www.tiktok.com/@portret.pupila', 'https://portret-pupila.myshopify.com.evil.invalid/pages/contact', 'https://portret-pupila.myshopify.com/products/demo', '#pakiety', 'https://evil.invalid/pages/contact'];
  assert.deepEqual(run('?'+campaign,other),other);
});

test('missing, duplicate or unknown required values preserve the inquiry fallback', () => {
  for (const query of ['', '?utm_source=tiktok', '?'+campaign+'&utm_source=facebook', '?'+campaign.replace('tiktok','person@example.invalid'), '?'+campaign.replace('pierwsza_sprzedaz_14dni_20261117','unknown')]) {
    assert.deepEqual(run(query),[destination]);
  }
});

test('campaign labels do not require cookies, local storage or an analytics connection', () => {
  assert.doesNotMatch(code,/localStorage|sessionStorage|document\.cookie|fetch\(|XMLHttpRequest|sendBeacon/);
  const once=run('?'+campaign+'&utm_content=ta_mina');
  assert.deepEqual(run('?'+campaign+'&utm_content=ta_mina',once),once);
});
