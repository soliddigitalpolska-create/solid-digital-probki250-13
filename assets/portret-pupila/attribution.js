/* Forward only known campaign labels to our storefront. No storage or analytics request. */
(() => {
  'use strict';
  const incoming = new URLSearchParams(window.location.search);
  const allowed = {
    utm_source: ['tiktok', 'instagram', 'facebook', 'youtube'],
    utm_medium: ['organic_social', 'social', 'dm', 'community', 'creator'],
    utm_campaign: ['pierwsza_sprzedaz_14dni_20261117'],
    utm_content: ['bio', 'portret', 'profil', 'przyklad', 'szczegoly', 'wybor_zdjecia', 'dwa_klimaty', 'ta_mina', 'co_dostajesz_99', '500_zdjec']
  };
  const storefrontPaths = new Set([
    '/pages/contact',
    '/products/pp-cyfrowy',
    '/products/pierwsze-swieta-z-pupilem-miniportret-na-plotnie-20-20-cm'
  ]);
  const selected = new URLSearchParams();
  for (const [key, values] of Object.entries(allowed)) {
    const supplied = incoming.getAll(key);
    if (supplied.length === 1 && values.includes(supplied[0])) selected.set(key, supplied[0]);
  }
  // Ambiguous, unsupported or incomplete campaigns leave the working fallback link intact.
  if (!['utm_source', 'utm_medium', 'utm_campaign'].every(key => selected.has(key))) return;
  for (const anchor of document.querySelectorAll('a[href]')) {
    let destination;
    try { destination = new URL(anchor.href); } catch { continue; }
    if (destination.origin !== 'https://portret-pupila.myshopify.com' || !storefrontPaths.has(destination.pathname)) continue;
    for (const [key, value] of selected) destination.searchParams.set(key, value);
    anchor.href = destination.href;
  }
})();
