import os
from dotenv import load_dotenv
import shutil
import time
import logging
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


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
        return
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
    send_telegram_message(f'✅ Pulizia completata per {game_type} in {folder}')

class GameFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            time.sleep(2)  # Attendi che la copia sia finita
            folder = event.src_path
            flatten_folder(folder)
            clean_game_folder(folder)

def main():
    observer = Observer()
    event_handler = GameFolderHandler()
    observer.schedule(event_handler, FOLDER_WATCHED, recursive=False)
    observer.start()
    logging.info(f'In ascolto su {FOLDER_WATCHED}...')
    send_telegram_message(f'🚀 Game Folder Cleaner avviato e in ascolto su {FOLDER_WATCHED}')
    try:
        while True:
            time.sleep(CHECK_INTERVAL)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == '__main__':
    main()
