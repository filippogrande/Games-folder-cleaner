# Game Folder Cleaner

Game Folder Cleaner è uno script Python che monitora una cartella (locale o NFS) e pulisce automaticamente le sottocartelle di giochi RenPy e RPGM, mantenendo solo i salvataggi. Invia notifiche Telegram sugli eventi principali e tiene traccia delle cartelle lavorate in un file CSV.

## Funzionalità

- Scan periodico della cartella principale (intervallo configurabile)
- Riconoscimento automatico giochi RenPy e RPGM
- Pulizia automatica: elimina tutto tranne i salvataggi
- Notifiche Telegram (avvio, fine ciclo, errori)
- Log CSV delle cartelle lavorate
- Attesa automatica per copia file non ancora terminata

## Requisiti

- Python 3.8+
- I pacchetti in `requirements.txt`:
  - requests
  - python-dotenv

## Configurazione

1. Crea un file `.env` nella root del progetto con queste variabili:

   ```
   FOLDER_WATCHED=/percorso/alla/cartella/da/monitorare
   TELEGRAM_BOT_TOKEN=il_tuo_token
   TELEGRAM_CHAT_ID=il_tuo_chat_id
   CHECK_INTERVAL=86400
   ```

   (86400 = 24h, puoi ridurre per test)

2. Installa le dipendenze:

   ```sh
   pip install -r requirements.txt
   ```

3. Avvia lo script:
   ```sh
   python game_folder_cleaner.py
   ```

## Esecuzione come servizio (opzionale)

Puoi configurare lo script come servizio systemd per l'avvio automatico. Vedi la documentazione nel codice o chiedi supporto.

## Esempi di strutture supportate

### RenPy Games

**Struttura iniziale supportata:**

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

**Struttura con livello aggiuntivo (supportata):**

```
GameName/
└── GameName-v1.0/
    ├── game/
    │   ├── saves/
    │   │   ├── persistent
    │   │   ├── save1.save
    │   │   └── save2.save
    │   ├── scripts/
    │   └── images/
    ├── lib/
    └── GameName.exe
```

**Risultato dopo la pulizia:**

```
GameName/
└── game/
    └── saves/
        ├── persistent
        ├── save1.save
        └── save2.save
```

### RPGM Games

**Struttura iniziale supportata:**

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

**Struttura con livello aggiuntivo (supportata):**

```
GameName/
└── GameName-v2.1/
    ├── www/
    │   ├── save/
    │   │   ├── config.rpgsave
    │   │   ├── file1.rpgsave
    │   │   └── global.rpgsave
    │   ├── js/
    │   └── img/
    ├── locales/
    └── nw.exe
```

**Risultato dopo la pulizia:**

```
GameName/
└── www/
    └── save/
        ├── config.rpgsave
        ├── file1.rpgsave
        └── global.rpgsave
```

## Note

- Il file `folders_log.csv` viene salvato nella cartella monitorata.
- Ogni cartella viene processata una sola volta.
- Riceverai notifiche Telegram all'avvio, a ogni scan e a fine ciclo.

## Licenza

MIT
