import assert from 'node:assert/strict';
import { readFileSync, existsSync } from 'node:fs';
import test from 'node:test';
const html = readFileSync(new URL('../portret-pupila.html', import.meta.url), 'utf8');
const destination = 'https://portret-pupila.myshopify.com/pages/contact#portret-zapytanie';
const links = [...html.matchAll(/<a\s+([^>]+)>([\s\S]*?)<\/a>/g)].map(([, attributes, body]) => ({ attributes, body: body.replace(/<[^>]+>/g, '').trim(), href: attributes.match(/href="([^"]+)"/)?.[1] }));

test('all product inquiry calls to action route to the native Shopify contact form', () => {
  const inquiry = links.filter(link => /Zapytaj|Przejdź do formularza sklepu/.test(link.body));
  assert.ok(inquiry.length >= 9);
  inquiry.forEach(link => assert.equal(link.href, destination, link.body));
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
