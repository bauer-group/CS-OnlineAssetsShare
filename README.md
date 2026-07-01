# OnlineAssetsShare

Zentraler S3-kompatibler Object Storage der BAUER GROUP. Stellt einen gemeinsamen S3-Endpunkt bereit, der von verschiedenen internen Anwendungen (Mail Signatures, Corporate Identity, etc.) genutzt wird.

| Endpunkt | URL |
|----------|-----|
| S3 API | `https://assets.bauer-group.com` |
| Admin Console | `https://console.assets.bauer-group.com` |

## Architektur

```
                    ┌──────────────────────────────────────────┐
                    │              Traefik / Coolify            │
                    └────┬──────────────────────────┬──────────┘
                         │                          │
              assets.bauer-group.com    console.assets.bauer-group.com
                         │                          │
                  ┌──────┴──────┐            ┌──────┴──────┐
                  │ minio-server│            │admin-console│
                  │   :9000     │◄───────────│   :9090     │
                  └──────┬──────┘            └─────────────┘
                         │
                  ┌──────┴──────┐
                  │ minio-init  │  Provisioniert Buckets, Policies,
                  │ (one-shot)  │  Users, Groups aus config/init.json
                  └─────────────┘
```

**Images** werden von der BAUER GROUP selbst gepflegt: `ghcr.io/bauer-group/cs-minio/`
(Quellcode: [Container-Solution/MinIO](https://github.com/bauer-group/CS-MinIO))

## Schnellstart

```bash
# 1. Umgebung konfigurieren
cp .env.example .env
# Passwörter setzen: MINIO_ROOT_PASSWORD, CONSOLE_PASSWORD, MAIL_SIGNATURE_PASSWORD

# 2. Lokal starten (direkte Ports)
docker compose -f docker-compose.direct.yml up -d

# 3. Zugriff
#    S3 API:  http://localhost:9000
#    Console: http://localhost:9001
```

## Deployment

| Variante | Compose-Datei | Anwendungsfall |
|----------|---------------|----------------|
| **Traefik** | `docker-compose.traefik.yml` | Produktion mit HTTPS, Let's Encrypt |
| **Coolify** | `docker-compose.coolify.yml` | Produktion via Coolify PaaS |
| **Direct** | `docker-compose.direct.yml` | Lokales Testen ohne Reverse Proxy |

```bash
# Traefik (Voraussetzung: Traefik läuft, DNS-Records gesetzt)
docker compose -f docker-compose.traefik.yml up -d

# Coolify: Deploy via Coolify UI, Env-Vars im Dashboard setzen
```

**Coolify-Details:** [docs/coolify-deployment.md](docs/coolify-deployment.md) — „Preserve
Repository During Deployment" und der Fix für den `init.json`-Verzeichnis-Fehler.

## Multi-Tenant Konfiguration

Jede Anwendung die den S3-Dienst nutzt, hat eine eigene JSON-Konfiguration unter `config/tenants/`. Der Init-Container provisioniert beim Start alle Ressourcen idempotent.

### Struktur

```
config/
├── tenants/                  # Pro Anwendung eine JSON-Datei
│   └── mail-signatures.json  # Buckets, Policies, Users, Groups
└── init.json                 # Zusammengeführte Config (generiert)
```

### Tenant-JSON Schema

```json
{
  "buckets":          [{ "name": "...", "region": "...", "versioning": false, "policy": "public" }],
  "policies":         [{ "name": "...", "statements": [{ "Effect": "Allow", "Action": [...], "Resource": [...] }] }],
  "users":            [{ "access_key": "${ENV_VAR}", "secret_key": "${ENV_VAR}", "groups": [...], "policies": [] }],
  "groups":           [{ "name": "...", "policies": [...] }],
  "service_accounts": []
}
```

Werte mit `${ENV_VAR}` werden vom Init-Container zur Laufzeit aus Umgebungsvariablen aufgelöst.

### Neuen Tenant hinzufügen

1. JSON-Datei in `config/tenants/<name>.json` anlegen
2. Eigene Env-Var-Namen verwenden (z.B. `${CI_USER}`, `${CI_PASSWORD}`)
3. Merge-Script ausführen:
   ```bash
   python scripts/merge-tenant-configs.py
   ```
4. `config/init.json` committen
5. In `.env.example` und `.env` die neuen Credential-Variablen hinzufügen
6. In den docker-compose-Dateien die neuen Env-Vars im `minio-init` Environment ergänzen
7. Stack neu starten: `docker compose -f <compose-file> up -d`

### Namenskonventionen

| Ressource | Muster | Beispiel |
|-----------|--------|----------|
| Bucket | Kebab-Case | `mail-signatures` |
| Policy | `p` + PascalCase | `pMailSignatures` |
| Group | `g` + PascalCase | `gMailSignatures` |
| Env-Vars | `UPPER_SNAKE_CASE` | `MAIL_SIGNATURE_USER` |

## Umgebungsvariablen

Alle Variablen sind in `.env.example` dokumentiert. Die wichtigsten:

| Variable | Pflicht | Beschreibung |
|----------|---------|--------------|
| `MINIO_ROOT_PASSWORD` | Ja | Root-Passwort des MinIO Servers |
| `CONSOLE_PASSWORD` | Ja | Passwort für die Admin Console |
| `MAIL_SIGNATURE_USER` | Ja | Access Key für den Mail Signature Service |
| `MAIL_SIGNATURE_PASSWORD` | Ja | Secret Key für den Mail Signature Service |
| `S3_HOSTNAME` | Nein | S3-Endpunkt (Default: `assets.bauer-group.com`) |
| `S3_CONSOLE_HOSTNAME` | Nein | Console-URL (Default: `console.assets.bauer-group.com`) |

Passwörter generieren: `openssl rand -hex 32`

## Consumer-Integration

Anwendungen die diesen S3-Dienst nutzen, konfigurieren ihren S3-Client wie folgt:

```env
S3_ENDPOINT_URL=https://assets.bauer-group.com
S3_ACCESS_KEY_ID=<MAIL_SIGNATURE_USER>
S3_SECRET_ACCESS_KEY=<MAIL_SIGNATURE_PASSWORD>
S3_REGION=eu-central1
```

Path-Style Zugriff auf Objekte: `https://assets.bauer-group.com/<bucket>/<key>`

## Projektstruktur

```
OnlineAssetsShare/
├── config/
│   ├── tenants/                     # Pro-Tenant JSON Konfigurationen
│   │   └── mail-signatures.json
│   └── init.json                    # Generierte Merged-Config
├── docs/
│   └── traefik-caching.md           # Optionale Traefik Caching-Middleware
├── scripts/
│   └── merge-tenant-configs.py      # Merge-Script (Python 3.6+)
├── docker-compose.traefik.yml       # Produktion: Traefik + HTTPS
├── docker-compose.coolify.yml       # Produktion: Coolify PaaS
├── docker-compose.direct.yml        # Test/Dev: Direkte Ports
├── .env.example                     # Dokumentierte Env-Vorlage
└── LICENSE
```

## Weiterführende Dokumentation

- [Coolify Deployment](docs/coolify-deployment.md) — Config-Bind-Mounts aus dem Repo & init.json-Fehlerfix
- [Cloudflare Caching](docs/cloudflare-caching.md) — Vary-Fix & Kurz-TTL für öffentliche Assets hinter Cloudflare
- [Traefik Caching Middleware](docs/traefik-caching.md) — Optionale Cache-Control Header via Traefik
- [Container-Solution/MinIO](https://github.com/bauer-group/CS-MinIO) — Image-Quellcode und Init-Container Dokumentation

## Lizenz

MIT — BAUER GROUP
