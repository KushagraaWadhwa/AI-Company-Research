"""
Celery application configuration for asynchronous task processing.
"""

import os
from celery import Celery
from app.core.config import settings

# Create Celery instance
celery_app = Celery(
    "ai_copilot",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.workers.tasks"]  # Include task modules
)

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing and execution
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_persistent=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_disable_rate_limits=False,
    
    # Task retry settings
    task_default_retry_delay=60,  # 60 seconds
    task_max_retries=3,
    
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    
    # Security
    worker_hijack_root_logger=False,
    worker_log_color=False,
)

# Task routes configuration
celery_app.conf.task_routes = {
    "app.workers.tasks.run_startup_analysis": {"queue": "analysis"},
}

# Optional: Configure additional queues
celery_app.conf.task_create_missing_queues = True

if __name__ == "__main__":
    celery_app.start()
