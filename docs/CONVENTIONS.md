# CONVENTIONS — le regole del repo

<!-- Tipo: how-to. Le regole da rispettare prima di toccare il repo. -->

## Regole di codice

- **50 righe per funzione.** Una funzione che le supera va spezzata nella PR che la
  tocca, non in una PR a parte.
- **500 righe per file.** Oltre si divide in moduli. `game_folder_cleaner.py` oggi
  e' sopra il limite: e' un debito registrato in `docs/REFERENCE.md` -> "Limiti
  noti", non una licenza a non toccarlo.
- **Niente fallback silenziosi.** Un `except: pass` che nasconde un errore reale e' un
  bug. Se l'errore e' previsto, loggalo; se non lo e', fallo risalire.
- **Niente file usa-e-getta.** I file di test temporanei, gli script di debug, i
  `.DS_Store` e i `__pycache__/` non vanno committati.
- **I segreti non sono nel repo.** Token e chat_id sono placeholder (`<token>`,
  `<chat_id>`). Nel cluster arrivano dal Secret, in locale dal `.env`.

## Regole di repo

- **In root solo**: `README.md`, `AGENTS.md`, il manifest del linguaggio
  (`requirements.txt`), `.gitignore`, `.dockerignore`, `.gitattributes`, `Dockerfile`,
  le cartelle.
- **`README.md` breve**: cosa e', avvio, struttura, indice che punta ai doc. I
  contenuti di dettaglio stanno in `docs/`.
- **I doc stanno in `docs/`**, in pochi file consolidati per scope (massimo ~8).
- **Un doc per concetto.** Se due doc dicono la stessa cosa, si consolidano nella PR
  che se ne accorge.
- **Un doc che mente e' peggio di nessuna doc**: va corretto o cancellato NELLA
  STESSA PR che lo smentisce.
- **Un file `.md` vuoto o di 0 byte va eliminato**, non preservato.

## Regole di PR

- **Branch + PR, mai push su `main`.**
- **Conventional commit**: `docs:`, `feat:`, `fix:`, `refactor:`, `chore:`, `deps:`.
- **I doc si aggiornano nella stessa PR che li invalida.** Se sposti una funzione,
  aggiorni la mappa in quella PR, non dopo.
- **Solo documentazione nelle PR di doc**: non si tocca codice. Se un file viola le
  regole (es. troppo lungo), si segnala in "Limiti noti", non si sistema.

## Tipi di doc

| Tipo | File | Regola |
|---|---|---|
| reference | `docs/REFERENCE.md` | fatti, neutro, completo. MAI opinioni. |
| explanation | `docs/ARCHITECTURE.md` | come funziona / perche' una scelta. |
| how-to | `docs/CONVENTIONS.md`, `docs/OPERATIONS.md` | passi per un obiettivo. |
| tutorial | — | imparare facendo; raro, non ancora presente. |

## La mappa

- Una riga per **richiesta**, non per area.
- **MAI numeri di riga**: le righe si muovono, i simboli no.
- **MAI elenchi di directory**: non aiutano a trovare un file.
- Ogni riga punta a un **file reale** e a un **simbolo reale**, verificato con la
  ricerca del codice.
