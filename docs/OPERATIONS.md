# OPERATIONS — operazioni ricorrenti

<!-- Tipo: how-to. Passi per un obiettivo. -->

## Requisiti

- Python 3.8+ (l'immagine usa 3.11)
- Dipendenze: `requests`, `python-dotenv` (`requirements.txt`)

## Installazione e avvio locale

1. Crea `.env` in root:

   ```
   FOLDER_WATCHED=/percorso/alla/cartella/da/monitorare
   TELEGRAM_BOT_TOKEN=<token>
   TELEGRAM_CHAT_ID=<chat_id>
   CHECK_INTERVAL=86400
   ```

   `CHECK_INTERVAL` e' in secondi (86400 = 24h). `TELEGRAM_BOT_TOKEN` e
   `TELEGRAM_CHAT_ID` possono essere in chiaro o in Base64.

2. `pip install -r requirements.txt`
3. `python game_folder_cleaner.py`

Senza `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` le notifiche sono disattivate e i
messaggi finiscono solo nel log.

### Flag

| Flag | Effetto |
|---|---|
| `--once` | una scansione e poi esce |
| `--folder <path>` | sovrascrive `FOLDER_WATCHED` |
| `--check-interval <s>` | sovrascrive `CHECK_INTERVAL` |
| `--debug` | log a livello DEBUG |

### Variabili d'ambiente

| Variabile | Default | A cosa serve |
|---|---|---|
| `FOLDER_WATCHED` | `/data` | cartella monitorata |
| `CHECK_INTERVAL` | `86400` | secondi tra un ciclo e l'altro |
| `TELEGRAM_BOT_TOKEN` | — | token del bot (chiaro o Base64) |
| `TELEGRAM_CHAT_ID` | — | chat di destinazione (chiaro o Base64) |
| `APP_VERSION` | `1.0.1` | versione mostrata nelle notifiche |
| `CONTAINER_MODE` | — | `true` = una scansione e poi esce |

## Aggiungere un gioco supportato

Il riconoscimento e' per **struttura dei path**, non per nome di gioco. Due casi:

1. **La struttura e' gia' coperta** (`game/saves` o `www/save`, anche con un livello
   annidato): non serve toccare nulla. Il gioco viene riconosciuto al prossimo ciclo.
2. **Serve un path nuovo**: aggiungi una funzione `is_<tipo>_game()` in
   `game_folder_cleaner.py` sul modello di `is_renpy_game()`/`is_rpgm_game()`, poi
   aggiornala in `clean_game_folder()` (che decide cosa proteggere) e in
   `flatten_folder()` (che appiattisce il livello annidato). Aggiorna anche
   `docs/REFERENCE.md` -> "Mappa dei giochi supportati".

Un gioco con una struttura non riconosciuta non viene toccato: finisce nel CSV con
`Tipo di gioco non riconosciuto` e in una notifica Telegram a fine ciclo.

## Docker

```sh
docker build -t game-folder-cleaner:latest .
docker run --rm -v /mnt/games/test:/data \
    -e TELEGRAM_BOT_TOKEN=<token> -e TELEGRAM_CHAT_ID=<chat_id> \
    game-folder-cleaner:latest --once
```

Il Dockerfile imposta `CONTAINER_MODE=true` e `FOLDER_WATCHED=/data`, quindi il
container fa una scansione e termina: va usato come CronJob, non come servizio
sempre attivo.

## k3s / Kubernetes

Manifest in `k8s/`:

| File | Contiene |
|---|---|
| `namespace.yaml` | namespace `game-folder-cleaner` |
| `configmap.yaml` | `CHECK_INTERVAL` |
| `secret.yaml` | `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` (da riempire o creare via `kubectl create secret`) |
| `cronjob.yaml` | CronJob giornaliero alle 2:00 (raccomandato) |
| `deployment.yaml` | Deployment continuo (non raccomandato) |
| `k3s-all-in-one.yaml` | tutti i manifest in uno, piu' ServiceAccount/Role e PVC di esempio |

### Deploy con il CronJob (raccomandato)

```sh
kubectl apply -f k8s/namespace.yaml
kubectl create secret generic telegram-secret -n game-folder-cleaner \
    --from-literal=TELEGRAM_BOT_TOKEN="<token>" \
    --from-literal=TELEGRAM_CHAT_ID="<chat_id>"
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/cronjob.yaml
```

### Volume

`cronjob.yaml` e `deployment.yaml` montano `/mnt/games` del nodo su `/data` del
container con `hostPath`. In produzione preferisci un PVC se il cluster ha un
provisioner; `k8s/k3s-all-in-one.yaml` ne contiene uno di esempio.

### Debug

```sh
kubectl exec -n game-folder-cleaner -it <pod> -- python game_folder_cleaner.py --once --debug
```

### Pulizia

```sh
kubectl delete -f k8s/cronjob.yaml -n game-folder-cleaner
kubectl delete -f k8s/configmap.yaml -n game-folder-cleaner
kubectl delete secret telegram-secret -n game-folder-cleaner
kubectl delete -f k8s/namespace.yaml
```

## CI

`.github/workflows/docker-publish.yml` builda e pubblica
`filippogrande/game-folder-cleaner:latest` e `...:<sha>` (amd64 + arm64) su Docker Hub
a ogni push su `main`. Non esegue test: non ce ne sono.
