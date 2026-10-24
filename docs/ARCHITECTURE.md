# ARCHITECTURE — come funziona

<!-- Tipo: explanation. Come funziona e perche' una scelta. -->

## In una riga

Un processo che gira a intervalli (o una volta sola, in container) scandaglia la
cartella monitorata; per ogni sottocartella non ancora vista attende che la copia
sia finita, si prende i permessi, appiattisce un eventuale livello annidato,
riconosce il tipo di gioco e cancella tutto tranne i salvataggi.

## Il giro completo

1. **Avvio** — `main()` legge gli argomenti, applica `--folder` e
   `--check-interval`, decide se girare una volta sola (`--once` oppure
   `CONTAINER_MODE=true`) e manda la notifica di avvio.
2. **Scansione** — `scan_and_process_folders()` elenca la cartella monitorata in
   ordine alfabetico e per ogni sottocartella chiama
   `is_folder_already_processed()`: se e' gia' nel CSV, la salta.
3. **Attesa stabilita'** — `wait_for_stable_folder()` somma la dimensione di tutti i
   file e aspetta che non cambi per 20 secondi, campionando ogni 2 secondi. Serve a
   non cancellare file che sono ancora in copia.
4. **Permessi** — `set_permissions()` fa `chown` all'utente corrente e `chmod 777`
   ricorsivamente. Se fallisce, la cartella viene saltata e notificata: senza
   permessi la pulizia fallirebbe a meta'.
5. **Appiattimento** — `flatten_folder()` sposta su un livello tutto cio' che sta in
   una sottocartella del tipo `NOME_GIOCO-v1.0/`, poi rimuove quella sottocartella.
6. **Riconoscimento** — `clean_game_folder()` chiede `is_renpy_game()` e
   `is_rpgm_game()`. Se nessuna delle due risponde, notifica "tipo non riconosciuto"
   e la cartella finisce nel CSV con quel risultato.
7. **Pulizia** — si calcola la dimensione prima, si raccolgono cartelle e file da
   eliminare (tutto tranne `game/saves` o `www/save` e la loro gerarchia), si
   eliminano con `shutil.rmtree()` e `os.remove()`, si ricalcola la dimensione e si
   scrive il risultato nel CSV.
8. **Fine ciclo** — notifica con il numero di cartelle lavorate e il totale
   risparmiato, poi l'elenco delle cartelle non riconosciute da risolvere a mano.

## Come riconosce il gioco

Due soli path, piu' un livello di tolleranza:

- Ren'Py: `<cartella>/game/saves`, oppure `<cartella>/<qualcosa>/game/saves`.
- RPG Maker: `<cartella>/www/save`, oppure `<cartella>/<qualcosa>/www/save`.

Il "qualcosa" e' il livello aggiuntivo che `flatten_folder()` sposta su prima del
riconoscimento. Non esiste una mappa di giochi per nome: la struttura dei path e'
l'unico criterio. Se la struttura non corrisponde, il gioco non viene toccato.

## Cosa cancella

Tutto cio' che non e' nella lista dei path protetti. I protetti sono:

- la radice della cartella del gioco;
- la cartella `game` (Ren'Py) o `www` (RPG Maker);
- la cartella dei salvataggi `game/saves` o `www/save`.

I file dentro `game/saves` o `www/save` non vengono toccati; i file altrove dentro la
cartella del gioco vengono eliminati.

## Come notifica

Tre livelli:

- `telegram_force_notify()` — sempre, e aggiorna il timer. Usato per avvio, fine
  ciclo, errori e risultati di pulizia.
- `telegram_notify_guarded()` — solo se sono passati almeno 300 secondi
  (`TELEGRAM_NOTIFICATION_INTERVAL`). Usato per i progressi durante le operazioni
  lunghe, per non fare spam.
- `send_telegram_message()` — la chiamata vera all'API Telegram. Se
  `TELEGRAM_ENABLED` e' falso, il messaggio finisce solo nel log.

Token e chat_id possono essere passati in chiaro o in Base64:
`_looks_like_base64()` e `_maybe_decode_base64()` decidono, perche' i manifest k8s
li passano come `stringData` e quindi arrivano al container codificati.

## Perche' un CSV e non uno stato in memoria

Il CSV `folders_log.csv` e' l'unica memoria del programma: vive nella cartella
monitorata, quindi sopravvive ai riavvii del container.
`is_folder_already_processed()` lo usa per non rifare due volte la stessa cartella,
`get_total_space_saved()` lo usa per il totale. E' anche l'output che un umano
legge.

## Dove gira

- **Locale**: `python game_folder_cleaner.py`, in loop con `CHECK_INTERVAL`.
- **Docker**: `CONTAINER_MODE=true` nel Dockerfile, quindi una scansione e poi esce.
- **k3s**: CronJob giornaliero alle 2:00 (`k8s/cronjob.yaml`), una scansione per pod.

In tutti i casi lo stato tra un giro e l'altro e' il CSV, non la memoria.
