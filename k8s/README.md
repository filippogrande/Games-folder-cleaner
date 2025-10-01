Manifest Kubernetes per eseguire Game Folder Cleaner in k3s.

- `namespace.yaml`: crea namespace `game-folder-cleaner`.
- `secret.yaml`: contiene `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` (usare `kubectl create secret` o `kubectl apply`).
- `configmap.yaml`: contiene `CHECK_INTERVAL`.
- `deployment.yaml`: deployment che monta `/mnt/games` del nodo su `/data` nel container (per esecuzione continua).
- `cronjob.yaml`: CronJob che esegue la pulizia ogni 24h alle 2:00 AM e poi termina (raccomandato).

Esempio di deploy con CronJob (raccomandato):

kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/cronjob.yaml

Per deployment continuo (non raccomandato per questa applicazione):

kubectl apply -f k8s/deployment.yaml
