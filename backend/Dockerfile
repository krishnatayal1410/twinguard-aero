FROM python:3.12-slim
WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt
COPY backend /app/backend
COPY models /app/models
COPY scripts /app/scripts
RUN useradd --create-home --uid 10001 twinguard && mkdir -p /app/data/runtime && chown -R twinguard:twinguard /app/data
USER twinguard
ENV PYTHONPATH=/app/backend MODEL_DIR=/app/models
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1 --no-access-log"]
