# Cloudflare Caching für die öffentlichen Assets

Wie der öffentliche Bucket `mail-signatures` auf `assets.bauer-group.com` hinter Cloudflare
korrekt gecacht wird. Signierte S3-Requests und die API bleiben ungecacht.

## Voraussetzung: `Vary: Origin` ersetzen

MinIO sendet bei **jeder** Antwort `Vary: Origin` (CORS-Schutz, spec-konform). **Cloudflare
cacht aber nur `Vary: Accept-Encoding`** — jeder andere Vary-Wert macht die Antwort uncachebar
(`Cf-Cache-Status: BYPASS`), **egal welche Cache-Regel greift**. Das ist kein MinIO-Bug,
sondern eine CDN-Restriktion. Deshalb zuerst den Header für den öffentlichen Pfad ersetzen:

Navigation: **Rules → Transform Rules → Modify Response Header → Create rule**

| Feld | Wert                                                                                        |
|------|---------------------------------------------------------------------------------------------|
| Name | `assets-strip-vary-origin`                                                                   |
| When | `(http.host eq "assets.bauer-group.com" and starts_with(http.request.uri.path, "/mail-signatures/"))` |
| Then | **Set static** → Header `Vary` = `Accept-Encoding`                                           |

> Nur für **öffentliche** Assets unbedenklich (keine echte Origin-Varianz). Private Buckets
> `Vary: Origin` belassen.

## Cache Rule mit kurzer TTL

Mail-Signaturen werden i. d. R. **unter gleichem Dateinamen** aktualisiert — Cache-Busting via
URL ist also nicht möglich. Daher **kurz** cachen; das Stale-Fenster ≈ **Edge-TTL**.

Navigation: **Caching → Cache Rules → Create rule**

| Feld | Wert                                                                                                                             |
|------|--------------------------------------------------------------------------------------------------------------------------------|
| Name | `assets-public-cache`                                                                                                           |
| When | `(http.host eq "assets.bauer-group.com" and starts_with(http.request.uri.path, "/mail-signatures/") and not http.request.uri.query contains "X-Amz-")` |
| Then | Eligibility **Eligible for cache** · **Edge TTL: 15 min** (override) · **Browser TTL: 5 min** (override)                        |

Optional davor eine Regel `Bypass cache` für alles andere auf `assets.bauer-group.com`, um
versehentliches Caching der API-Endpunkte auszuschließen.

## Frische bei gleichem Dateinamen

Nach einem Update erscheint der neue Stand **spätestens nach ~15 min** — dann revalidiert die
Edge per `ETag` gegen MinIO (billig, meist `304`). Die Browser-TTL (5 min) steuert, wie schnell
der einzelne Browser wieder nachfragt.

Muss es **sofort** frisch sein → **Purge-on-Update**: MinIO-Bucket-Event
(`s3:ObjectCreated:*`) → Webhook → Cloudflare Purge-API der Objekt-URL. Dann kann die TTL lang
sein (voller Cache-Nutzen, sofort frisch).

> Optional zusätzlich `Cache-Control` pro Objekt beim Upload setzen (z. B.
> `public, max-age=300, stale-while-revalidate=900`) — siehe [`traefik-caching.md`](./traefik-caching.md).

## Test

```bash
curl -sI https://assets.bauer-group.com/mail-signatures/<key> | grep -i "cf-cache-status\|vary"
# Erwartung: Vary: Accept-Encoding, 1. MISS → 2. HIT
```

## Hintergrund

- Cloudflare Cache Rules = **last-match-wins** ([Docs](https://developers.cloudflare.com/cache/how-to/cache-rules/order/)).
- Cloudflare respektiert nur `Vary: Accept-Encoding` ([Cache Rules settings](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/)).
- `Vary: Origin` ist die spec-konforme CORS-Absicherung gegen Cache-Poisoning der
  `Access-Control-Allow-Origin`-Header — für öffentliche Assets aber faktisch überflüssig.
