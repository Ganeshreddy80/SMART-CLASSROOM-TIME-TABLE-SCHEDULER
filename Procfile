web: flask db upgrade && flask seed-admin && python fixtures/seed_data.py && gunicorn app:app --workers 1 --timeout 120 --bind 0.0.0.0:$PORT
worker: python -c "from models import db; from app import app; db.init_app(app); print('Worker ready')"
