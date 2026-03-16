# Traefik Caching Middleware für S3

## Status

**Entfernt** — Caching wird über S3-Objekt-Metadaten gesteuert, nicht über Traefik.

## Hintergrund

Ursprünglich war eine Traefik `headers`-Middleware geplant, die `Cache-Control`-Header
auf alle S3-Responses setzt. Dies wurde entfernt, weil:

- Traefik überschreibt pauschal **alle** Responses (auch API-Antworten wie ListBucket, Fehler, PUT-Responses)
- Unterschiedliche Objekte brauchen unterschiedliche Caching-Policies (z.B. häufig aktualisierte vs. statische Assets)
- Die Anwendungen können beim Upload passende Metadaten pro Objekt setzen (`Cache-Control`, `Content-Type`, etc.)
- MinIO setzt bereits `ETag`-Header für bedingtes Caching

## Konfiguration (falls doch benötigt)

### 1. Umgebungsvariable in `.env`

```env
S3_CACHE_MAX_AGE=86400    # Cache-Control max-age in Sekunden (86400 = 24h)
```

### 2. Traefik Labels auf `minio-server`

Middleware-Definition — nach der `nobuffer`-Middleware einfügen:

```yaml
# ── Middleware: S3 Caching Headers ─────────────────────────────────
- "traefik.http.middlewares.${STACK_NAME:-online-assets}-s3cache.headers.customResponseHeaders.Cache-Control=public, max-age=${S3_CACHE_MAX_AGE:-86400}, stale-while-revalidate=3600"
- "traefik.http.middlewares.${STACK_NAME:-online-assets}-s3cache.headers.customResponseHeaders.Vary=Accept-Encoding"
- "traefik.http.middlewares.${STACK_NAME:-online-assets}-s3cache.headers.customResponseHeaders.X-Content-Type-Options=nosniff"
```

Middleware an den HTTPS-Router anhängen — `nobuffer` um `,${STACK_NAME}-s3cache` erweitern:

```yaml
# Vorher:
- "traefik.http.routers.${STACK_NAME:-online-assets}-s3.middlewares=${STACK_NAME:-online-assets}-nobuffer"

# Nachher:
- "traefik.http.routers.${STACK_NAME:-online-assets}-s3.middlewares=${STACK_NAME:-online-assets}-nobuffer,${STACK_NAME:-online-assets}-s3cache"
```

### 3. Header-Erklärung

| Header | Wert | Zweck |
|--------|------|-------|
| `Cache-Control` | `public, max-age=86400, stale-while-revalidate=3600` | Browser/CDN cacht 24h, danach 1h stale-while-revalidate |
| `Vary` | `Accept-Encoding` | Korrektes CDN-Verhalten bei komprimierten Responses |
| `X-Content-Type-Options` | `nosniff` | Verhindert MIME-Type-Sniffing im Browser |

### 4. Hinweise

- Die Labels müssen in **beiden** Compose-Dateien eingefügt werden (`docker-compose.traefik.yml` und `docker-compose.coolify.yml`)
- `docker-compose.direct.yml` hat kein Traefik — dort ist keine Caching-Middleware nötig
- `S3_CACHE_MAX_AGE` kann für Testumgebungen niedriger gesetzt werden (z.B. `3600` = 1h)
- Die Middleware überschreibt alle `Cache-Control`-Header die MinIO selbst setzt
