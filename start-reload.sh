#!/bin/bash

echo "====== Running: /app/prestart.sh"
. /app/prestart.sh

echo "====== Starting: uvicorn --reload"
uvicorn --reload --host 0.0.0.0 --port 80 --log-level info "app.main:app"
