#!/bin/bash

echo "====== Running: /app/prestart.sh"
. /app/prestart.sh

echo "====== Starting: gunicorn"
gunicorn -k "uvicorn.workers.UvicornWorker" -c "/gunicorn_conf.py" --capture-output "app.main:app"
