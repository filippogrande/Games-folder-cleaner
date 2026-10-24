# Game Folder Cleaner (repo `Games-folder-cleaner`)

<!-- Radice della mappa: leggi QUESTO file per primo, sempre. -->
<!-- Tutto cio' che non serve ad OGNI task e' a un link di distanza. -->

Script Python che monitora una cartella (locale o NFS) e pulisce le sottocartelle di
giochi Ren'Py e RPG Maker: elimina tutto tranne i salvataggi, invia notifiche
Telegram e tiene un CSV delle cartelle lavorate.

- Stack: Python 3.11, `requests`, `python-dotenv`; immagine `filippogrande/game-folder-cleaner:latest`
- Deploy: locale (`python game_folder_cleaner.py`), Docker, k3s (CronJob giornaliero)
- Mappa del codice: `docs/REFERENCE.md`

## Comandi

| Azione | Comando |
|---|---|
| Avvio locale | `pip install -r requirements.txt && python game_folder_cleaner.py` |
| Una sola scansione | `python game_folder_cleaner.py --once` |
| Sovrascrivere la cartella | `python game_folder_cleaner.py --folder /percorso` |
| Log di debug | `python game_folder_cleaner.py --debug` |
| Build immagine | `docker build -t game-folder-cleaner:latest .` |
| Run singola dal container | `docker run --rm -v /mnt/games:/data game-folder-cleaner:latest --once` |
| Deploy k3s (CronJob) | `kubectl apply -f k8s/namespace.yaml -f k8s/configmap.yaml -f k8s/cronjob.yaml` |

## Indice — richiesta -> dove

| Vuoi... | Apri |
|---|---|
| Trovare una funzione o un file | `docs/REFERENCE.md` |
| Capire come riconosce il gioco, cosa cancella, come notifica | `docs/ARCHITECTURE.md` |
| Conoscere le regole prima di scrivere codice | `docs/CONVENTIONS.md` |
| Installare, avviare, aggiungere un gioco, deployare | `docs/OPERATIONS.md` |

## Documenti

| Doc | Tipo | A cosa serve |
|---|---|---|
| `docs/REFERENCE.md` | reference | la mappa: richiesta -> file -> entry point |
| `docs/ARCHITECTURE.md` | explanation | come funziona e perche' una scelta |
| `docs/CONVENTIONS.md` | how-to | regole di codice e di repo |
| `docs/OPERATIONS.md` | how-to | installazione, avvio, deploy, nuovo gioco |

## Regole

- Branch + PR, mai push su `main`.
- I doc — incluse le voci di questo indice — si aggiornano NELLA STESSA PR che li invalida.
- Limiti: 50 righe/funzione, 500 righe/file, niente fallback silenziosi, niente file usa-e-getta.
- Niente segreti nei doc: token e chat_id sono placeholder.
- Mappa onesta: una riga che indica un path o un simbolo sbagliato si corregge subito, non si annota.
