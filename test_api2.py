import requests

s = requests.Session()
r = s.get('http://127.0.0.1:5001/login')
csrf_token = r.text.split('name="csrf_token" value="')[1].split('"')[0]

r2 = s.post('http://127.0.0.1:5001/login', data={'email':'rajesh.kumar@srmap.edu.in', 'password':'rajesh@123', 'csrf_token':csrf_token, 'login_role':'faculty'})
print('Login:', r2.url)

r3 = s.get('http://127.0.0.1:5001/api/attendance/setup-data')
print('Setup Data Status:', r3.status_code)

r4 = s.post('http://127.0.0.1:5001/api/attendance/session/stop', json={'session_token':'dummy'})
print('Stop Session Status:', r4.status_code)
print('Stop Session Response:', r4.text)
