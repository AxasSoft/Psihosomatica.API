#!/bin/bash

## Run migrations
alembic upgrade head

## Let the DB start and add superuser
# Запускать лучше один раз при первом запуске
# python -u /app/app/prestart.py
