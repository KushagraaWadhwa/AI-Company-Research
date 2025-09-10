#!/usr/bin/env python3
"""
Startup script for the Celery worker.
"""

import os
import sys
from app.workers.celery_app import celery_app

if __name__ == "__main__":
    # Configure Celery worker arguments
    worker_args = [
        "worker",
        "--loglevel=info",
        "--concurrency=2",
        "--queues=default,analysis"
    ]
    
    # Add any additional arguments from command line
    if len(sys.argv) > 1:
        worker_args.extend(sys.argv[1:])
    
    print("Starting Celery worker...")
    print(f"Arguments: {' '.join(worker_args)}")
    
    celery_app.worker_main(worker_args)
