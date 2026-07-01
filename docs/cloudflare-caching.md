# Cloudflare Caching für die öffentlichen Assets

Wie der öffentliche Bucket `mail-signatures` auf `assets.bauer-group.com` hinter Cloudflare
gecacht wird. Signierte S3-Requests und die API bleiben ungecacht.

## Der Trick: feste Edge-TTL (Override)

MinIO sendet bei **jeder** Antwort `Vary: Origin` (CORS-Schutz, spec-konform). Cloudflare
cacht standardmäßig nur `Vary: Accept-Encoding` — mit Edge-TTL **„Respect origin"** bleibt die
Antwort daher bei `Cf-Cache-Status: BYPASS` (MinIO sendet kein `Cache-Control`).

**Lösung ohne Header-Edit:** in der Cache Rule eine **feste Edge-TTL (Override)** setzen —
damit cacht Cloudflare die Assets **trotz** `Vary: Origin`. Der Vary-Header darf stehen bleiben.

> Ein `Vary`-Header-Edit per Transform Rule ist **nicht möglich** (Cloudflare erlaubt auf
> `Vary` weder `Set` noch `Remove`) — dank Edge-TTL-Override aber auch **nicht nötig**.

## Cache Rule

Mail-Signaturen werden i. d. R. **unter gleichem Dateinamen** aktualisiert — Cache-Busting via
URL ist also nicht möglich. Daher **kurz** cachen; das Stale-Fenster ≈ **Edge-TTL**.

Navigation: **Caching → Cache Rules → Create rule**

| Feld | Wert                                                                                                                                                   |
|------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| Name | `assets-public-cache`                                                                                                                                  |
| When | `(http.host eq "assets.bauer-group.com" and starts_with(http.request.uri.path, "/mail-signatures/") and not http.request.uri.query contains "X-Amz-")` |
| Then | Eligibility **Eligible for cache** · **Edge TTL: Override → 5 min** · **Browser TTL: Override → 1 min**                                                |

> **Wichtig:** Edge-TTL auf **Override** (fester Wert) stellen, **nicht** „Respect origin" —
> sonst bleibt es wegen `Vary: Origin` + fehlendem `Cache-Control` bei `BYPASS`.

Optional davor eine Regel `Bypass cache` für alles andere auf `assets.bauer-group.com`, um
versehentliches Caching der API-Endpunkte auszuschließen.

## Frische bei gleichem Dateinamen

**Ohne Purge (aktueller Stand):** kurze Edge-TTL (5 min). Nach einem Update erscheint der neue
Stand **spätestens nach ~5 min** — dann revalidiert die Edge per `ETag` gegen MinIO (billig,
meist `304`). Die Browser-TTL (1 min) steuert, wie schnell der einzelne Browser wieder nachfragt.

**Mit Purge-Worker (Upgrade):** Der **minio-worker** aus dem
[MinIO-Stack](https://github.com/bauer-group/CS-MinIO) (HTTP-Receiver + Huey-Consumer, Provider
Cloudflare/Bunny) purged bei put/delete die Cloudflare-Edge der geänderten Objekt-URL. Damit
kann die **Edge-TTL lang** werden (z. B. 1 Tag) bei weiterhin **kurzer Browser-TTL** (Purge
erreicht Browser nicht). Voraussetzung: Worker in die Compose aufnehmen (`WORKER_MODE`
receiver/consumer), `WEBHOOK_AUTH_TOKEN` + `CF_PURGE_API_TOKEN` + `CF_ZONE_ID` setzen und einen
`notifications`-Block via `config/tenants/_stack.json` generieren (Merge-Script kennt die
Sektion bereits). Token/Zone-ID: Cloudflare-Dashboard → *Purge Cache*-Token bzw.
Overview → API → Zone-ID (**nicht** Account-ID).

⚠️ **Die lange Edge-TTL ist nur sicher, WENN der Worker purged.** Solange OnlineAssetsShare
keinen Worker betreibt, bei der **kurzen** Edge-TTL (5 min) bleiben — sonst bis zu 1 Tag stale.

> Optional zusätzlich `Cache-Control` pro Objekt beim Upload setzen (z. B.
> `public, max-age=60, stale-while-revalidate=300`) — siehe [`traefik-caching.md`](./traefik-caching.md).

## Test

```bash
curl -sI https://assets.bauer-group.com/mail-signatures/<key> | grep -i "cf-cache-status"
# Erwartung: 1. Abruf MISS -> 2. Abruf HIT (Vary: Origin bleibt, stoert dank Override nicht)
```

## Hintergrund

- Cloudflare Cache Rules = **last-match-wins** ([Docs](https://developers.cloudflare.com/cache/how-to/cache-rules/order/)).
- Cloudflare respektiert nur `Vary: Accept-Encoding`; andere Vary-Werte machen die Antwort mit
  „Respect origin" uncachebar ([Cache Rules settings](https://developers.cloudflare.com/cache/how-to/cache-rules/settings/)) — eine **feste Edge-TTL (Override)** cacht dennoch.
- `Vary` lässt sich per Transform Rule **nicht** ändern (weder `Set` noch `Remove`).
- `Vary: Origin` ist die spec-konforme CORS-Absicherung — für öffentliche Assets faktisch
  überflüssig, aber unschädlich, sobald die Edge-TTL fest ist.
