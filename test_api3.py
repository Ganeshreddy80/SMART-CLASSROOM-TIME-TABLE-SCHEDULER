import requests
import json

s = requests.Session()
r = s.get('http://127.0.0.1:5001/login')
csrf_token = r.text.split('name="csrf_token" value="')[1].split('"')[0]

r2 = s.post('http://127.0.0.1:5001/login', data={'email':'rajesh.kumar@srmap.edu.in', 'password':'rajesh@123', 'csrf_token':csrf_token, 'login_role':'faculty'})
r3 = s.get('http://127.0.0.1:5001/api/attendance/setup-data')
print('Setup Data:', r3.json())
