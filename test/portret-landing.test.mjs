import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import test from 'node:test';
const html = readFileSync(new URL('../portret-pupila.html', import.meta.url), 'utf8');
const storeOrigin = 'https://portret-pupila.myshopify.com';
const miniportret = '/products/pierwsze-swieta-z-pupilem-miniportret-na-plotnie-20-20-cm';
const links = [...html.matchAll(/<a\s+([^>]+)>([\s\S]*?)<\/a>/g)].map(([, attributes, body]) => ({ attributes, body: body.replace(/<[^>]+>/g, '').trim(), href: attributes.match(/href="([^"]+)"/)?.[1] }));

test('miniportret has direct shop links and other inquiries keep the contact form', () => {
  const shopLinks = links.filter(link => link.href?.startsWith(storeOrigin + '/'));
  const productLinks = [];
  const contactLinks = [];
  const placements = new Set();
  for (const link of shopLinks) {
    const url = new URL(link.href.replaceAll('&amp;', '&'));
    assert.equal(url.searchParams.get('utm_source'), 'portret_landing');
    assert.equal(url.searchParams.get('utm_medium'), 'referral');
    assert.equal(url.searchParams.get('utm_campaign'), 'miniportret_99_20261120');
    placements.add(url.searchParams.get('utm_content'));
    if (url.pathname === miniportret) {
      productLinks.push(link);
      assert.match(link.body, /miniportret/i);
      assert.equal(url.hash, '');
    } else {
      contactLinks.push(link);
      assert.equal(url.pathname, '/pages/contact');
      assert.equal(url.hash, '#portret-zapytanie');
    }
  }
  assert.equal(productLinks.length, 4);
  assert.equal(contactLinks.length, 6);
  assert.equal(placements.size, 10);
});

test('no unverified upload, payment checkout or automatic free assessment remains', () => {
  assert.doesNotMatch(html, /<iframe|buy\.stripe\.com|checkout\.stripe\.com|portret-pupila-zdjecie|data-package|data-addon|Sprawdź moje zdjęcie · 0 zł/);
  assert.match(html, /To zapytanie, bez płatności i rezerwacji terminu/);
});

test('main offer and first package agree on the mini canvas with DPD', () => {
  const firstPackage = html.match(/<article class="package[^>]*>([\s\S]*?)<\/article>/)?.[1];
  assert.match(firstPackage, /Miniportret Pupila/);
  assert.match(firstPackage, /99/);
  assert.match(firstPackage, /20 × 20 cm/);
  assert.match(firstPackage, /DPD/);
  assert.match(html, /<title>[^<]*zapytaj/);
});

test('local images and in-page links resolve', () => {
  for (const [,src] of html.matchAll(/<img[^>]+src="([^"]+)"/g)) {
    assert.ok(existsSync(new URL('../' + src, import.meta.url)), src);
  }
  const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map(x => x[1]));
  links.filter(link => link.href?.startsWith('#') && link.href !== '#').forEach(link => assert.ok(ids.has(link.href.slice(1)), link.href));
});
