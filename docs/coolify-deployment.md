# Deployment mit Coolify

Hinweise zum Betrieb von [`docker-compose.coolify.yml`](../docker-compose.coolify.yml) unter
Coolify — insbesondere zum Mounten der Config-Dateien aus dem Git-Repo.

## Config-Dateien aus dem Repo mounten

Der Stack bindet `config/init.json` per **relativem Bind-Mount** aus dem geklonten Repo ein:

```yaml
volumes:
  - ./config/init.json:/app/config/init.json:ro
```

Damit Coolify die Datei **aus dem Repo** nimmt (statt eine leere, im UI zu pflegende
„File Storage"-Ressource anzulegen), sind zwei Dinge nötig:

### 1. „Preserve Repository During Deployment" aktivieren

Ressource → **Settings** → **Preserve Repository During Deployment** = **an**. Nur dann bleibt
das geklonte Repo zur Laufzeit erhalten und relative Bind-Mounts lösen sich zur Repo-Datei auf.

### 2. Keine auto-erzeugte Storage-Ressource stehen lassen

Ressource → **Storages** → einen ggf. für `config/init.json` automatisch angelegten Mount
**löschen** — sonst überschattet er die Repo-Datei.

## Fehler: „cannot overwrite directory … init.json with non-directory"

**Symptom** — der Deploy bricht ab, **bevor** der Stack startet:

```text
cannot overwrite directory ".../config/init.json" with non-directory "..."
Deployment failed: Command execution failed (exit code 1): docker cp ...
```

**Ursache:** In einem früheren Deploy existierte `config/init.json` auf dem Host noch nicht als
Datei. Docker legt eine fehlende Bind-Mount-Quelle automatisch **als Verzeichnis** an. Beim
nächsten Deploy will Coolify das geklonte Repo (mit `init.json` als **Datei**) per `docker cp`
darüberkopieren → Docker verweigert „Verzeichnis mit Nicht-Verzeichnis überschreiben".

**Fix (einmalig):**

1. Storages-Eintrag löschen **und** „Preserve Repository During Deployment" aktivieren
   (siehe oben) — verhindert die erneute Fehl-Anlage.
2. Auf dem Deploy-Server das fehlerhafte Verzeichnis entfernen. Die `<APP_ID>` steht im
   Deploy-Log (`/data/coolify/applications/<APP_ID>`):

   ```bash
   # Pfad zuerst prüfen:
   ls -la /data/coolify/applications/<APP_ID>/config/
   # dann das faelschlich angelegte Verzeichnis entfernen:
   rm -rf /data/coolify/applications/<APP_ID>/config/init.json
   ```

3. **Redeploy.**

> **Bestätigt in Produktion:** Das Aktivieren des Settings allein reicht **nicht** — das bereits
> angelegte Alt-Verzeichnis muss zusätzlich per `rm -rf` entfernt werden. Erst danach läuft der
> Deploy durch.

## Härtung (optional) — Wiederkehr vermeiden

Einzel-Datei-Bind-Mounts sind der fragile Fall. Robuster ist, das **Verzeichnis** zu mounten —
ein bereits existierender Ordner wird nie fälschlich neu angelegt:

```yaml
# statt  ./config/init.json:/app/config/init.json:ro
- ./config:/app/config:ro
```

Der Init-Container liest weiterhin `/app/config/init.json`. Aktuell **nicht** umgesetzt, um die
Compose-Dateien nicht zu ändern — als Option dokumentiert.

## Referenzen

- [Coolify Docs — Docker Compose](https://coolify.io/docs/knowledge-base/docker/compose)
- Coolify Issues [#8107](https://github.com/coollabsio/coolify/issues/8107),
  [#6056](https://github.com/coollabsio/coolify/issues/6056),
  [#3375](https://github.com/coollabsio/coolify/issues/3375)
