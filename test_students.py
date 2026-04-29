from app import app
with app.test_client() as c:
    res = c.get('/api/students').json
    print(len(res), res[0] if res else '')
