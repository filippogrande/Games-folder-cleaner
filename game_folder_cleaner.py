import os
from dotenv import load_dotenv
import shutil
import time
import logging
import requests


import csv
from datetime import datetime

def wait_for_stable_folder(folder, stable_seconds=20, check_interval=2):
    """Attende che la dimensione della cartella non cambi per stable_seconds."""
    last_size = -1
    stable_time = 0
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
        time.sleep(check_interval)


# Configurazione
load_dotenv()
FOLDER_WATCHED = os.getenv('FOLDER_WATCHED')  # <-- Configura nel file .env
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '10'))  # secondi

# Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def send_telegram_message(message):
    url = f'https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage'
    data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        logging.error(f'Errore invio Telegram: {e}')

def is_renpy_game(folder):
    return os.path.isdir(os.path.join(folder, 'game', 'saves'))

def is_rpgm_game(folder):
    return os.path.isdir(os.path.join(folder, 'www', 'save'))

def flatten_folder(folder):
    # Se la struttura è /game name/gamename/game/saves, rimuovi un livello
    base = os.path.basename(folder)
    parent = os.path.dirname(folder)
    candidate = os.path.join(folder, base)
    if os.path.isdir(os.path.join(candidate, 'game', 'saves')) or os.path.isdir(os.path.join(candidate, 'www', 'save')):
        # Sposta tutto su un livello sopra
        for item in os.listdir(candidate):
            shutil.move(os.path.join(candidate, item), os.path.join(folder, item))
        shutil.rmtree(candidate)
        logging.info(f'Rimossa cartella annidata: {candidate}')

def log_folder_action(folder, action, result, space_saved=None):
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

def get_total_space_saved():
    log_file = os.path.join(FOLDER_WATCHED, 'folders_log.csv')
    total = 0.0
    if not os.path.isfile(log_file):
        return 0.0
    with open(log_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            try:
                val = float(row.get('space_saved_MB', '0') or 0)
                total += val
            except Exception:
                pass
    return total

def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if os.path.isfile(fp):
                try:
                    total_size += os.path.getsize(fp)
                except Exception:
                    pass
    return total_size

def is_folder_already_processed(folder):
    log_file = os.path.join(FOLDER_WATCHED, 'folders_log.csv')
    if not os.path.isfile(log_file):
        return False
    with open(log_file, 'r', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if row['folder'] == folder:
                return True
    return False

def clean_game_folder(folder):
    if is_renpy_game(folder):
        save_path = os.path.join(folder, 'game', 'saves')
        keep = [save_path]
        game_type = 'RenPy'
    elif is_rpgm_game(folder):
        save_path = os.path.join(folder, 'www', 'save')
        keep = [save_path]
        game_type = 'RPGM'
    else:
        send_telegram_message(f'❌ Tipo di gioco non riconosciuto in {folder}')
        log_folder_action(folder, 'clean', 'Tipo di gioco non riconosciuto')
        return
    # Calcola dimensione prima
    size_before = get_folder_size(folder)
    # Elimina tutto tranne le cartelle di salvataggio
    for root, dirs, files in os.walk(folder):
        for d in dirs:
            full_path = os.path.join(root, d)
            if full_path not in keep:
                try:
                    shutil.rmtree(full_path)
                    logging.info(f'Eliminata cartella: {full_path}')
                except Exception as e:
                    logging.error(f'Errore eliminazione {full_path}: {e}')
        for f in files:
            file_path = os.path.join(root, f)
            if not file_path.startswith(tuple(keep)):
                try:
                    os.remove(file_path)
                    logging.info(f'Eliminato file: {file_path}')
                except Exception as e:
                    logging.error(f'Errore eliminazione {file_path}: {e}')
    # Calcola dimensione dopo
    size_after = get_folder_size(folder)
    space_saved = (size_before - size_after) / (1024 * 1024)  # MB
    total_saved = get_total_space_saved() + space_saved
    send_telegram_message(
        f'✅ Pulizia completata per {game_type} in {folder}.\n'
        f'Spazio risparmiato in questa cartella: {space_saved:.2f} MB\n'
        f'Totale risparmiato: {total_saved:.2f} MB'
    )
    log_folder_action(folder, 'clean', f'Pulizia completata per {game_type}', space_saved)


def scan_and_process_folders():
    send_telegram_message(f'🔄 Inizio scan cartelle in {FOLDER_WATCHED}')
    if not os.path.isdir(FOLDER_WATCHED):
        logging.warning(f"La cartella da monitorare non esiste: {FOLDER_WATCHED}")
        return
    nuove_cartelle = []
    for entry in os.listdir(FOLDER_WATCHED):
        folder = os.path.join(FOLDER_WATCHED, entry)
        if os.path.isdir(folder) and not is_folder_already_processed(folder):
            logging.info(f"Nuova cartella trovata: {folder}")
            wait_for_stable_folder(folder)
            flatten_folder(folder)
            clean_game_folder(folder)
            nuove_cartelle.append(folder)
    total_saved = get_total_space_saved()
    send_telegram_message(
        f'✅ Fine ciclo pulizia. Cartelle lavorate: {len(nuove_cartelle)}\n'
        f'Totale spazio risparmiato: {total_saved:.2f} MB'
    )

def main():
    logging.info(f'In ascolto su {FOLDER_WATCHED}...')
    send_telegram_message(f'🚀 Game Folder Cleaner avviato e in ascolto su {FOLDER_WATCHED}')
    try:
        while True:
            scan_and_process_folders()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logging.info('Interrotto da tastiera.')

if __name__ == '__main__':
    main()
