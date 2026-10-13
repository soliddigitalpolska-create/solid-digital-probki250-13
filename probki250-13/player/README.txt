WŁASNY PROTOTYP TECHNICZNY — 13.10.2026

Publiczna strona:
- frontend Web Audio z 7 własnymi, krótkimi, syntetycznymi nagraniami;
- 7 profili współdzieli te same 7 testów; nie mamy 525+ utworów klienta;
- publiczna strona nie egzekwuje dostępu backendem i nie przyjmuje płatności.

Rzeczywisty backend lokalny:
- Python standard library, SQLite, signed/revocable/expiring links;
- jedna aktywna lease urządzenia, 30 s, heartbeat co 10 s;
- losowanie po pełnym cyklu, bez natychmiastowej powtórki na granicy;
- krótkie podpisane bilety audio sprawdzają token i aktualną lease;
- backend binds 127.0.0.1 only; no hosted live backend or CDN;
- SQLite state must stay outside the public sample folder.

Uruchamianie testów:
python -m unittest -v test_backend
node test_scheduler.cjs

Uruchamianie własnego backendu lokalnego:
Set PLAYER_SIGNING_SECRET, PLAYER_ADMIN_KEY, PLAYER_WEBHOOK_SECRET to fresh,
random values with at least 32 characters in the local process environment.
Set PLAYER_DB_PATH to a private SQLite path outside the public folder.
Optional PLAYER_PORT (default 8892). Run python player_backend.py.
No secret defaults, no .env in this source kit, no secret logging.

Admin routes (Bearer PLAYER_ADMIN_KEY), loopback only:
POST /api/admin/issue {"ttl":86400} -> own test link, not evidence of payment.
POST /api/admin/revoke {"id":"issued_link_id"}.
POST /api/admin/order {"id":"own_test_order","amount_minor":19900,"ttl":86400}.

Payment event adapter is a GENERIC SIMULATOR, not any PSP SDK or real BLIK.
POST /api/mock/webhook requires local admin and X-Demo-Timestamp,
X-Demo-Signature=HMAC-SHA256(webhook_secret,timestamp+'.'+raw_body).
Expected body: event_id,order_id,status,amount_minor,currency.
Only a matching, signed paid event activates a test token; pending does not.
Replay is idempotent; refunded/failed revokes already granted test access.
Production requires the chosen PSP's own signature protocol, sandbox,
client-owned account and confirmed payment fulfillment through webhooks.
The redirect/return page must not activate access by itself.

Limitations:
- no production PSP/CDN integration, no actual purchase or client music;
- lease is concurrency management, not DRM or uncopyable downloaded audio;
- Web Audio scheduling tests validate adjacent timestamps, not every browser;
- no physical iOS/Android devices or Safari tests have yet been performed;
- production must include client-file validation, CDN signing, actual-device
  listening tests, interrupted-network handling and deployment checks.
- Root must verify real UI playback before describing the GUI as checked.
