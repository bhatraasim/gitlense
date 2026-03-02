# Development (single process, auto-reload)
uv run fastapi dev main.py

# Production (multiple workers, no reload)
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4




uv run celery -A worker.celery_app worker --loglevel=info --pool=solo
