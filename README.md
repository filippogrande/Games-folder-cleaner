# Game Folder Cleaner

Script Python che monitora una cartella (locale o NFS) e pulisce le sottocartelle di
 giochi Ren'Py e RPG Maker, tenendo solo i salvataggi. Invia notifiche Telegram e
tiene un CSV delle cartelle lavorate.

## Avvio rapido

1. Crea `.env` in root (vedi `docs/OPERATIONS.md` per i valori):

```
FOLDER_WATCHED=/percorso/alla/cartella/da/monitorare
TELEGRAM_BOT_TOKEN=<token>
TELEGRAM_CHAT_ID=<chat_id>
CHECK_INTERVAL=86400
```

2. `pip install -r requirements.txt`
3. `python game_folder_cleaner.py`

Senza `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID` le notifiche sono disattivate e i
messaggi finiscono solo nel log.

## Struttura

| File | Contiene |
|---|---|
| `game_folder_cleaner.py` | tutto il codice |
| `Dockerfile` | immagine (una scansione e poi esce) |
| `requirements.txt` | dipendenze (`requests`, `python-dotenv`) |
| `k8s/` | manifest Kubernetes |
| `.github/` | CI: pubblica l'immagine Docker |

## Documenti

- `AGENTS.md` — punto di ingresso: indice, comandi, regole
- `docs/REFERENCE.md` — la mappa: richiesta -> file -> entry point
- `docs/ARCHITECTURE.md` — come funziona
- `docs/CONVENTIONS.md` — le regole del repo
- `docs/OPERATIONS.md` — installazione, avvio, deploy, nuovo gioco

## Licenza

MIT
