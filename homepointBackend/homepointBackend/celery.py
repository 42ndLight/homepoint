# celery.py
import os
from celery import Celery

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepointBackend.settings')

app = Celery('homepointBackend')

# Using a string here means the worker doesn't have to serialize
# the object to child processes. -namespace='CELERY' means all celery-related
# configuration keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Additional runtime resilience tuning (reads env vars for easy overrides)
app.conf.update(
    broker_pool_limit=int(os.environ.get('CELERY_BROKER_POOL_LIMIT', 10)),
    broker_connection_timeout=int(os.environ.get('CELERY_BROKER_CONNECTION_TIMEOUT', 30)),
    broker_heartbeat=int(os.environ.get('CELERY_BROKER_HEARTBEAT', 15)),
    broker_transport_options={
        'visibility_timeout': int(os.environ.get('CELERY_VISIBILITY_TIMEOUT', 3600)),
    },
    broker_connection_retry=True,
    broker_connection_max_retries=None,
    result_expires=int(os.environ.get('CELERY_RESULT_EXPIRES', 60*60*24)),
    task_ignore_result=False,
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
