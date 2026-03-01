from celery import Celery
from config import settings

celery_app = Celery(
    "gitlens",
    broker=settings.REDIS_URL,      # redis://localhost:6379/0
    backend=settings.REDIS_URL,     # Store results here too
    include=["app.workers.tasks"]   # Import path to tasks
)

# Optional: Configure Celery settings
celery_app.conf.update(
    # Serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # Task behavior
    task_track_started=True,        # Show "STARTED" status, not just PENDING/SUCCESS
    task_time_limit=3600,           # 1 hour max per task (kill if stuck)
    task_soft_time_limit=3300,      # 55 min warning (cleanup before hard kill)
    
    # Results
    result_expires=3600,            # Delete results after 1 hour
    result_backend=settings.REDIS_URL,
    
    # Retries
    task_default_retry_delay=60,    # Wait 1 min before retry
    task_max_retries=3,             # Try 3 times max
    
    # Worker
    worker_prefetch_multiplier=1,   # One task at a time (memory heavy: cloning repos)
    worker_concurrency=1,           # Start with 1 worker (increase later)
)