web: gunicorn app:app --workers 1 --timeout 120
worker: python -c "from models import db; from app import app; db.init_app(app); print('Worker ready')"
