import os
from dotenv import load_dotenv
import shutil
import time
import logging
import requests
import csv
from datetime import datetime

# Stato globale per tracciare l'ultima notifica Telegram inviata
last_telegram_notification = 0
TELEGRAM_NOTIFICATION_INTERVAL = 300  # 5 minuti

def telegram_notify_guarded(message):
    """Invia una notifica Telegram solo se non ne è stata inviata una negli ultimi 5 minuti."""
    global last_telegram_notification
    now = time.time()
    if now - last_telegram_notification >= TELEGRAM_NOTIFICATION_INTERVAL:
        send_telegram_message(message)
        last_telegram_notification = now

def telegram_force_notify(message):
    """Invia sempre una notifica Telegram e aggiorna il timer."""
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
        # Log interno ogni 30 secondi
        if elapsed - last_log >= log_interval:
            logging.info(f"[wait_for_stable_folder] {folder}: dimensione attuale {total_size / (1024*1024):.2f} MB, stabile da {stable_time}s")
            last_log = elapsed
        # Notifica Telegram ogni 5 minuti se non ne è stata inviata una recentemente
        telegram_notify_guarded(f'⏳ Attesa stabilità cartella {folder}: attuale {total_size / (1024*1024):.2f} MB, stabile da {stable_time}s')
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
    # Riconosce sia /game/saves che /QUALCOSA/game/saves (un solo livello)
    if os.path.isdir(os.path.join(folder, 'game', 'saves')):
        return True
    # Cerca un solo livello sotto
    for entry in os.listdir(folder):
        sub = os.path.join(folder, entry)
        if os.path.isdir(sub) and os.path.isdir(os.path.join(sub, 'game', 'saves')):
            return True
    return False

def is_rpgm_game(folder):
    # Riconosce sia /www/save che /QUALCOSA/www/save (un solo livello)
    if os.path.isdir(os.path.join(folder, 'www', 'save')):
        return True
    for entry in os.listdir(folder):
        sub = os.path.join(folder, entry)
        if os.path.isdir(sub) and os.path.isdir(os.path.join(sub, 'www', 'save')):
            return True
    return False

def flatten_folder(folder):
    # Se la struttura è /NOME_GIOCO/QUALCOSA/game/saves o /NOME_GIOCO/QUALCOSA/www/save, sposta tutto su un livello sopra
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
    for idx, f in enumerate(to_delete_files, 1):
        try:
            os.remove(f)
            logging.info(f'Eliminato file: {f} ({idx}/{total_files})')
        except Exception as e:
            logging.error(f'Errore eliminazione {f}: {e}')
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


def scan_and_process_folders():
    telegram_force_notify(f'🔄 Inizio scan cartelle in {FOLDER_WATCHED}')
    if not os.path.isdir(FOLDER_WATCHED):
        logging.warning(f"La cartella da monitorare non esiste: {FOLDER_WATCHED}")
        return
    nuove_cartelle = []
    entries = os.listdir(FOLDER_WATCHED)
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

def main():
    logging.info(f'In ascolto su {FOLDER_WATCHED}...')
    telegram_force_notify(f'🚀 Game Folder Cleaner avviato e in ascolto su {FOLDER_WATCHED}')
    try:
        while True:
            scan_and_process_folders()
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        logging.info('Interrotto da tastiera.')

if __name__ == '__main__':
    main()
