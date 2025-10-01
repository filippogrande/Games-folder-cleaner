import os
import shutil
import time
import logging
import requests
import csv
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Carica .env se presente
load_dotenv()

# Stato globale per tracciare l'ultima notifica Telegram inviata
last_telegram_notification = 0
TELEGRAM_NOTIFICATION_INTERVAL = 300  # 5 minuti

# Defaults pensati per esecuzione in container/k3s
DEFAULT_FOLDER_WATCHED = '/data'
FOLDER_WATCHED = os.getenv('FOLDER_WATCHED', DEFAULT_FOLDER_WATCHED)
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '86400'))  # default 24h

# Determina se Telegram è configurato
TELEGRAM_ENABLED = bool(TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID)

# Logging base; può essere sovrascritto da argparser (debug)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def send_telegram_message(message):
    if not TELEGRAM_ENABLED:
        logging.debug(f"Telegram disabilitato, messaggio non inviato: {message}")
        return
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        resp = requests.post(url, data=data, timeout=10)
        if resp.status_code != 200:
            logging.error(f'Errore invio Telegram ({resp.status_code}): {resp.text}')
    except Exception as e:
        logging.error(f'Errore invio Telegram: {e}')


def telegram_notify_guarded(message):
    """Invia una notifica Telegram solo se non ne è stata inviata una negli ultimi TELEGRAM_NOTIFICATION_INTERVAL secondi."""
    global last_telegram_notification
    now = time.time()
    if now - last_telegram_notification >= TELEGRAM_NOTIFICATION_INTERVAL:
        send_telegram_message(message)
        last_telegram_notification = now


def telegram_force_notify(message):
    """Invia sempre una notifica Telegram e aggiorna il timer (se abilitato)."""
    global last_telegram_notification
    send_telegram_message(message)
    last_telegram_notification = time.time()


def wait_for_stable_folder(folder, stable_seconds=20, check_interval=2):
    """Attende che la dimensione della cartella non cambi per stable_seconds."""
    last_size = -1
    stable_time = 0
    elapsed = 0
    log_interval = 30  # secondi
    last_log = 0
    while stable_time < stable_seconds:
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except Exception:
                        pass
        if total_size == last_size:
            stable_time += check_interval
        else:
            stable_time = 0
            last_size = total_size
        elapsed += check_interval
        # Log interno ogni log_interval secondi
        if elapsed - last_log >= log_interval:
            logging.info(f"[wait_for_stable_folder] {folder}: dimensione attuale {total_size / (1024*1024):.2f} MB, stabile da {stable_time}s")
            last_log = elapsed
            # Notifica di stato a bassa priorità
            telegram_notify_guarded(f'⏳ Attesa stabilità cartella {folder}: attuale {total_size / (1024*1024):.2f} MB, stabile da {stable_time}s')
        time.sleep(check_interval)


def is_renpy_game(folder):
    # Riconosce sia /game/saves che /QUALCOSA/game/saves (un solo livello)
    try:
        if os.path.isdir(os.path.join(folder, 'game', 'saves')):
            return True
        # Cerca un solo livello sotto
        for entry in os.listdir(folder):
            sub = os.path.join(folder, entry)
            if os.path.isdir(sub) and os.path.isdir(os.path.join(sub, 'game', 'saves')):
                return True
    except Exception:
        pass
    return False


def is_rpgm_game(folder):
    try:
        if os.path.isdir(os.path.join(folder, 'www', 'save')):
            return True
        for entry in os.listdir(folder):
            sub = os.path.join(folder, entry)
            if os.path.isdir(sub) and os.path.isdir(os.path.join(sub, 'www', 'save')):
                return True
    except Exception:
        pass
    return False


def flatten_folder(folder):
    # Se la struttura è /NOME_GIOCO/QUALCOSA/game/saves o /NOME_GIOCO/QUALCOSA/www/save, sposta tutto su un livello sopra
    try:
        for entry in os.listdir(folder):
            candidate = os.path.join(folder, entry)
            if os.path.isdir(candidate):
                if os.path.isdir(os.path.join(candidate, 'game', 'saves')) or os.path.isdir(os.path.join(candidate, 'www', 'save')):
                    # Sposta tutto su un livello sopra
                    for item in os.listdir(candidate):
                        shutil.move(os.path.join(candidate, item), os.path.join(folder, item))
                    shutil.rmtree(candidate)
                    logging.info(f'Rimossa cartella annidata: {candidate}')
                    break
    except Exception as e:
        logging.warning(f'Errore in flatten_folder per {folder}: {e}')


def log_folder_action(folder, action, result, space_saved=None):
    try:
        os.makedirs(FOLDER_WATCHED, exist_ok=True)
        log_file = os.path.join(FOLDER_WATCHED, 'folders_log.csv')
        file_exists = os.path.isfile(log_file)
        with open(log_file, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            if not file_exists:
                writer.writerow(['timestamp', 'folder', 'action', 'result', 'space_saved_MB'])
            writer.writerow([
                datetime.now().isoformat(),
                folder,
                action,
                result,
                f"{space_saved:.2f}" if space_saved is not None else ''
            ])
    except Exception as e:
        logging.error(f'Impossibile scrivere log azione per {folder}: {e}')


def get_total_space_saved():
    log_file = os.path.join(FOLDER_WATCHED, 'folders_log.csv')
    total = 0.0
    if not os.path.isfile(log_file):
        return 0.0
    try:
        with open(log_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    val = float(row.get('space_saved_MB', '0') or 0)
                    total += val
                except Exception:
                    pass
    except Exception as e:
        logging.error(f'Errore lettura log totale spazio: {e}')
    return total


def get_folder_size(folder):
    total_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    try:
                        total_size += os.path.getsize(fp)
                    except Exception:
                        pass
    except Exception:
        pass
    return total_size


def is_folder_already_processed(folder):
    log_file = os.path.join(FOLDER_WATCHED, 'folders_log.csv')
    if not os.path.isfile(log_file):
        return False
    try:
        with open(log_file, 'r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row.get('folder') == folder:
                    return True
    except Exception:
        pass
    return False


def clean_game_folder(folder):
    try:
        if is_renpy_game(folder):
            save_path = os.path.join(folder, 'game', 'saves')
            keep_paths = {save_path}
            # Mantieni anche la cartella 'game' e la root
            keep_dirs = {os.path.join(folder, 'game'), folder}
            game_type = 'RenPy'
        elif is_rpgm_game(folder):
            save_path = os.path.join(folder, 'www', 'save')
            keep_paths = {save_path}
            keep_dirs = {os.path.join(folder, 'www'), folder}
            game_type = 'RPGM'
        else:
            logging.warning(f"Tipo di gioco non riconosciuto per la cartella: {folder}")
            telegram_force_notify(f'❌ Tipo di gioco non riconosciuto in {folder}')
            log_folder_action(folder, 'clean', 'Tipo di gioco non riconosciuto')
            return
        # Calcola dimensione prima
        size_before = get_folder_size(folder)
        # Elimina tutto tranne la cartella dei salvataggi e la sua gerarchia
        to_delete_dirs = []
        to_delete_files = []
        for root, dirs, files in os.walk(folder):
            # Elimina cartelle che non sono la root, né 'game'/'www', né 'game/saves'/'www/save'
            for d in dirs:
                full_path = os.path.join(root, d)
                # Non eliminare la cartella 'game', 'www', 'game/saves', 'www/save', né la root
                if full_path not in keep_dirs and full_path not in keep_paths:
                    to_delete_dirs.append(full_path)
            for f in files:
                file_path = os.path.join(root, f)
                # Non eliminare file dentro la cartella dei salvataggi
                if not file_path.startswith(save_path + os.sep):
                    to_delete_files.append(file_path)

        total_dirs = len(to_delete_dirs)
        total_files = len(to_delete_files)
        logging.info(f"[clean_game_folder] Da eliminare: {total_dirs} cartelle, {total_files} file in {folder}")

        # Eliminazione cartelle con log e notifiche di progresso
        last_log = time.time()
        last_tg = time.time()
        for idx, d in enumerate(to_delete_dirs, 1):
            try:
                shutil.rmtree(d)
                logging.info(f'Eliminata cartella: {d} ({idx}/{total_dirs})')
            except Exception as e:
                logging.error(f'Errore eliminazione {d}: {e}')
            now = time.time()
            if now - last_log >= 30:
                logging.info(f"[clean_game_folder] Eliminazione cartelle: {idx}/{total_dirs} in {folder}")
                last_log = now
            if now - last_tg >= 300:
                telegram_notify_guarded(f'🗑️ Eliminazione cartelle: {idx}/{total_dirs} in {folder}')
                last_tg = now

        # Eliminazione file con log e notifiche di progresso
        last_log = time.time()
        last_tg = time.time()
        for idx, fpath in enumerate(to_delete_files, 1):
            try:
                os.remove(fpath)
                logging.info(f'Eliminato file: {fpath} ({idx}/{total_files})')
            except Exception as e:
                logging.error(f'Errore eliminazione {fpath}: {e}')
            now = time.time()
            if now - last_log >= 30:
                logging.info(f"[clean_game_folder] Eliminazione file: {idx}/{total_files} in {folder}")
                last_log = now
            if now - last_tg >= 300:
                telegram_notify_guarded(f'🗑️ Eliminazione file: {idx}/{total_files} in {folder}')
                last_tg = now
        # Calcola dimensione dopo
        size_after = get_folder_size(folder)
        space_saved = (size_before - size_after) / (1024 * 1024)  # MB
        total_saved = get_total_space_saved() + space_saved

        # Estrae il nome della cartella del gioco
        game_name = os.path.basename(folder)

        telegram_force_notify(
            f'🧹 Pulito gioco {game_name}\n'
            f'✅ Pulizia completata per {game_type}\n'
            f'Spazio risparmiato in questa cartella: {space_saved:.2f} MB\n'
            f'Totale risparmiato: {total_saved:.2f} MB'
        )
        log_folder_action(folder, 'clean', f'Pulizia completata per {game_type}', space_saved)
    except Exception as e:
        logging.error(f'Errore in clean_game_folder({folder}): {e}')


def scan_and_process_folders():
    telegram_force_notify(f'🔄 Inizio scan cartelle in {FOLDER_WATCHED}')
    if not os.path.isdir(FOLDER_WATCHED):
        logging.warning(f"La cartella da monitorare non esiste: {FOLDER_WATCHED}")
        return
    nuove_cartelle = []
    entries = sorted(os.listdir(FOLDER_WATCHED))
    for idx, entry in enumerate(entries):
        folder = os.path.join(FOLDER_WATCHED, entry)
        if os.path.isdir(folder) and not is_folder_already_processed(folder):
            logging.info(f"Nuova cartella trovata: {folder}")
            telegram_notify_guarded(f'📁 Sto per processare la cartella: {folder} ({idx+1}/{len(entries)})')
            wait_for_stable_folder(folder)
            flatten_folder(folder)
            clean_game_folder(folder)
            nuove_cartelle.append(folder)
        else:
            # Notifica periodica se la scansione è lunga e non ci sono nuove cartelle
            telegram_notify_guarded(f'🔎 Scansione in corso in {FOLDER_WATCHED}... ({idx+1}/{len(entries)})')
    total_saved = get_total_space_saved()
    telegram_force_notify(
        f'✅ Fine ciclo pulizia. Cartelle lavorate: {len(nuove_cartelle)}\n'
        f'Totale spazio risparmiato: {total_saved:.2f} MB'
    )


def parse_args():
    p = argparse.ArgumentParser(description='Game Folder Cleaner')
    p.add_argument('--once', action='store_true', help='Esegui una sola scansione e termina')
    p.add_argument('--folder', type=str, help='Sovrascrive FOLDER_WATCHED')
    p.add_argument('--check-interval', type=int, help='Sovrascrive CHECK_INTERVAL in secondi')
    p.add_argument('--debug', action='store_true', help='Abilita log di debug')
    return p.parse_args()


def main():
    args = parse_args()
    global FOLDER_WATCHED, CHECK_INTERVAL
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    if args.folder:
        FOLDER_WATCHED = args.folder
    if args.check_interval:
        CHECK_INTERVAL = args.check_interval

    # Se in container, esegui una sola scansione di default (comportamento CronJob)
    run_once = args.once or os.getenv('CONTAINER_MODE', '').lower() == 'true'

    logging.info(f'In ascolto su {FOLDER_WATCHED}...')
    telegram_force_notify(f'🚀 Game Folder Cleaner avviato e in ascolto su {FOLDER_WATCHED}')

    try:
        if run_once:
            scan_and_process_folders()
            logging.info('Scansione completata. Uscita.')
            return
        while True:
            scan_and_process_folders()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logging.info('Interrotto da tastiera.')


if __name__ == '__main__':
    main()
