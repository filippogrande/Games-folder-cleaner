# REFERENCE — la mappa del codice

<!-- Tipo: reference. Fatti, neutro, completo. -->
<!-- Ogni riga: un file reale + un simbolo reale. Nessun numero di riga. -->
<!-- Si aggiorna NELLA STESSA PR che sposta qualcosa. -->

## Come si legge

Una riga per richiesta. **Richiesta -> file -> entry point.**
Se per trovare il file ti serve altro, la riga e' sbagliata.

## Entry point

| Vuoi... | File | Entry point |
|---|---|---|
| Capire dove inizia tutto | `game_folder_cleaner.py` | `main()` |
| Aggiungere un flag CLI | `game_folder_cleaner.py` | `parse_args()`, `main()` |
| Cambiare il ciclo di scansione (loop vs run singola) | `game_folder_cleaner.py` | `main()` |
| Cambiare il default della cartella monitorata | `game_folder_cleaner.py` | `DEFAULT_FOLDER_WATCHED`, `FOLDER_WATCHED` |
| Cambiare la versione mostrata nelle notifiche | `game_folder_cleaner.py` | `APP_VERSION` |

## Mappa dei giochi supportati

| Vuoi... | File | Entry point |
|---|---|---|
| Riconoscere un gioco Ren'Py | `game_folder_cleaner.py` | `is_renpy_game()` |
| Riconoscere un gioco RPG Maker | `game_folder_cleaner.py` | `is_rpgm_game()` |
| Capire le strutture accettate (cartelle e livelli) | `game_folder_cleaner.py` | `is_renpy_game()`, `is_rpgm_game()`, `flatten_folder()` |
| Aggiungere un nuovo tipo di gioco | `game_folder_cleaner.py` | `is_renpy_game()`, `is_rpgm_game()`, `clean_game_folder()` |

### Strutture supportate

Riconoscimento per **struttura dei path**, non per nome di gioco.

Ren'Py — i salvataggi stanno in `game/saves`:

```
GameName/
├── game/
│   ├── saves/
│   │   ├── persistent
│   │   ├── save1.save
│   │   └── save2.save
│   ├── scripts/
│   ├── images/
│   └── audio/
├── lib/
├── renpy/
└── GameName.exe
```

Ren'Py con un livello annidato (`GameName/GameName-v1.0/...`) — supportato: il
livello viene spostato su da `flatten_folder()`.

RPG Maker — i salvataggi stanno in `www/save`:

```
GameName/
├── www/
│   ├── save/
│   │   ├── config.rpgsave
│   │   ├── file1.rpgsave
│   │   └── global.rpgsave
│   ├── js/
│   ├── img/
│   └── audio/
├── locales/
├── nw.exe
└── package.json
```

RPG Maker con un livello annidato (`GameName/GameName-v2.1/...`) — supportato, stesso
meccanismo.

Risultato dopo la pulizia: resta solo la cartella del gioco con dentro la sua
cartella di salvataggi (`game/saves` o `www/save`) e il contenuto dei salvataggi.

## Logica di pulizia

| Vuoi... | File | Entry point |
|---|---|---|
| Decidere cosa tenere e cosa cancellare | `game_folder_cleaner.py` | `clean_game_folder()` |
| Vedere quali path sono protetti dalla cancellazione | `game_folder_cleaner.py` | `clean_game_folder()` -> `keep_dirs`, `keep_paths` |
| Gestire la struttura annidata `NOME_GIOCO-vX.Y/` | `game_folder_cleaner.py` | `flatten_folder()` |
| Attendere che una copia sia finita prima di toccare | `game_folder_cleaner.py` | `wait_for_stable_folder()` |
| Impostare permessi prima di pulire | `game_folder_cleaner.py` | `set_permissions()` |
| Misurare la dimensione di una cartella | `game_folder_cleaner.py` | `get_folder_size()` |
| Sapere se una cartella e' gia' stata processata | `game_folder_cleaner.py` | `is_folder_already_processed()` |
| Leggere il totale dello spazio risparmiato | `game_folder_cleaner.py` | `get_total_space_saved()` |

## Notifiche Telegram

| Vuoi... | File | Entry point |
|---|---|---|
| Inviare un messaggio Telegram | `game_folder_cleaner.py` | `send_telegram_message()` |
| Limitare le notifiche ripetute | `game_folder_cleaner.py` | `telegram_notify_guarded()` |
| Forzare una notifica importante | `game_folder_cleaner.py` | `telegram_force_notify()` |
| Cambiare l'intervallo anti-spam (default 5 min) | `game_folder_cleaner.py` | `TELEGRAM_NOTIFICATION_INTERVAL` |
| Disattivare Telegram | `game_folder_cleaner.py` | `TELEGRAM_ENABLED` |

### Messaggi inviati

| Momento | Messaggio |
|---|---|
| Avvio | `Game Folder Cleaner v<version> avviato e in ascolto su <cartella>` |
| Inizio scansione | `Inizio scan cartelle in <cartella>` |
| Cartella in elaborazione | `Sto per processare la cartella: <cartella> (X/Y)` |
| Attesa stabilita' | `Attesa stabilità cartella <cartella>: attuale X MB, stabile da X s` |
| Progresso scansione | `Scansione in corso in <cartella>... (X/Y)` |
| Progresso eliminazione cartelle | `Eliminazione cartelle: X/Y in <cartella>` |
| Progresso eliminazione file | `Eliminazione file: X/Y in <cartella>` |
| Pulizia completata | `Pulito gioco <nome>` + `Pulizia completata per <RenPy/RPGM>` + spazio risparmiato |
| Fine ciclo | `Fine ciclo pulizia. Cartelle lavorate: X` + `Totale spazio risparmiato: X MB` |
| Tipo non riconosciuto | `Tipo di gioco non riconosciuto in <cartella>` |
| Permessi falliti | `Fallita impostazione permessi per <cartella>: ...` |
| Errori di I/O | `Errore eliminazione <path>: <errore>` |

I messaggi di progresso usano `telegram_notify_guarded()` (al piu' uno ogni 5 minuti);
avvio, fine ciclo, errori e risultati usano `telegram_force_notify()` (sempre).

## Path dei save

| Vuoi... | File | Entry point |
|---|---|---|
| Vedere dove cerca i salvataggi Ren'Py | `game_folder_cleaner.py` | `is_renpy_game()`, `clean_game_folder()` |
| Vedere dove cerca i salvataggi RPG Maker | `game_folder_cleaner.py` | `is_rpgm_game()`, `clean_game_folder()` |
| Capire dove finisce il CSV delle azioni | `game_folder_cleaner.py` | `log_folder_action()` |

## Configurazione

| Vuoi... | File | Entry point |
|---|---|---|
| Cambiare la cartella monitorata | `game_folder_cleaner.py` | `FOLDER_WATCHED`, `DEFAULT_FOLDER_WATCHED` |
| Cambiare l'intervallo tra i cicli | `game_folder_cleaner.py` | `CHECK_INTERVAL` |
| Passare token/chat_id in chiaro o in Base64 | `game_folder_cleaner.py` | `_looks_like_base64()`, `_maybe_decode_base64()` |
| Cambiare il setup del logging | `game_folder_cleaner.py` | `logging.basicConfig()` in testa al file |
| Cambiare le variabili del container | `Dockerfile` -> `ENV` |
| Cambiare l'intervallo in produzione | `k8s/configmap.yaml` -> `data.CHECK_INTERVAL` |

## Deploy e container

| Vuoi... | Dove |
|---|---|
| Cambiare l'immagine, l'entrypoint o l'utente | `Dockerfile` |
| Cambiare i manifest k8s | `k8s/namespace.yaml`, `k8s/configmap.yaml`, `k8s/cronjob.yaml`, `k8s/deployment.yaml`, `k8s/secret.yaml`, `k8s/k3s-all-in-one.yaml` |
| Cambiare l'orario del CronJob | `k8s/cronjob.yaml` -> `spec.schedule` |
| Cambiare il volume montato | `k8s/cronjob.yaml` -> `spec.jobTemplate.spec.template.spec.volumes` |
| Gestire le dipendenze | `.github/dependabot.yml` |
| Cosa la CI esegue | `.github/workflows/docker-publish.yml` |
| Cosa entra nel build context | `.dockerignore` |

## Log delle azioni

| Vuoi... | File | Entry point |
|---|---|---|
| Scrivere una riga nel CSV | `game_folder_cleaner.py` | `log_folder_action()` |
| Leggere il totale risparmiato dal CSV | `game_folder_cleaner.py` | `get_total_space_saved()` |
| Leggere l'elenco delle cartelle non riconosciute | `game_folder_cleaner.py` | `scan_and_process_folders()` |

Il CSV e' `folders_log.csv`, scritto nella cartella monitorata. Colonne:
`timestamp`, `folder`, `action`, `result`, `space_saved_MB`.

## Limiti noti (dove la mappa e' sottile)

- `game_folder_cleaner.py` e' un unico file di circa 520 righe: supera il limite di 500
  righe/file di `docs/CONVENTIONS.md`. Non e' stato diviso in questa PR (solo
  documentazione): va fatto a parte, e la mappa va aggiornata nella stessa PR.
- `clean_game_folder()` e' lunga piu' di 100 righe e `set_permissions()` piu' di 70:
  entrambe oltre il limite di 50 righe/funzione.
- Non esistono test: nessuna directory `tests/` e nessun workflow di CI che li
  esegua. La CI pubblica solo l'immagine Docker.
- Il riconoscimento dei giochi si basa su due soli path (`game/saves`, `www/save`) e
  su un solo livello annidato: un gioco con una struttura diversa viene segnalato
  come non riconosciuto, non pulito.
- `.gitignore` copriva solo `.env`: `__pycache__/` e `.DS_Store` erano tracciati da
  git. In questa PR sono stati rimossi e aggiunti a `.gitignore`.
- Il README precedente indicava "configura come servizio systemd, vedi la
  documentazione nel codice": non esiste alcun unit systemd nel repo. La sezione e'
  stata rimossa.
