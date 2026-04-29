#!/usr/bin/env bash
pip install -r requirements.txt
export FLASK_APP=app.py
flask db upgrade
python fixtures/seed_db_direct.py || echo "Seed skipped"
