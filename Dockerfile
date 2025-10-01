FROM python:3.11-slim

# Crea un utente non-root
RUN useradd -m appuser || true
WORKDIR /app

# Copia solo i file necessari
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app
RUN chown -R appuser:appuser /app
USER appuser

ENV PYTHONUNBUFFERED=1
ENV FOLDER_WATCHED=/data
ENV CONTAINER_MODE=true

VOLUME ["/data"]

CMD ["python", "game_folder_cleaner.py"]
